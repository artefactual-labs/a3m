import os
from uuid import uuid4

from django.db import transaction
from django.utils import timezone

from a3m import databaseFunctions
from a3m import fileOperations
from a3m.dicts import ReplacementDict
from a3m.dicts import setup_dicts
from a3m.executeOrRunSubProcess import executeOrRun
from a3m.fpr.registry import FPR
from a3m.fpr.registry import Rule
from a3m.fpr.registry import RulePurpose
from a3m.main.models import Derivation
from a3m.main.models import File


def insert_transcription_event(status, file_uuid, rule, relative_location):
    outcome = "transcribed" if status == 0 else "not transcribed"

    tool = rule.command.tool
    event_detail = 'program={}; version={}; command="{}"'.format(
        tool.description, tool.version, rule.command.command.replace('"', r"\"")
    )

    event_uuid = str(uuid4())

    databaseFunctions.insertIntoEvents(
        fileUUID=file_uuid,
        eventIdentifierUUID=event_uuid,
        eventType="transcription",
        eventDetail=event_detail,
        eventOutcome=outcome,
        eventOutcomeDetailNote=relative_location,
    )

    return event_uuid


def insert_file_into_database(
    task_uuid, file_uuid, sip_uuid, event_uuid, rule, output_path, relative_path
):
    transcription_uuid = str(uuid4())
    today = timezone.now()
    fileOperations.addFileToSIP(
        relative_path,
        transcription_uuid,
        sip_uuid,
        task_uuid,
        today,
        sourceType="creation",
        use="text/ocr",
    )

    fileOperations.updateSizeAndChecksum(
        transcription_uuid, output_path, today, str(uuid4())
    )

    databaseFunctions.insertIntoDerivations(
        sourceFileUUID=file_uuid,
        derivedFileUUID=transcription_uuid,
        relatedEventUUID=event_uuid,
    )


def fetch_rules_for(file_obj) -> list[Rule]:
    return FPR.get_file_rules(file_obj, purpose=RulePurpose.TRANSCRIPTION)


def fetch_rules_for_derivatives(file_obj) -> tuple[File | None, list[Rule]]:
    derivs = Derivation.objects.filter(source_file=file_obj)
    for deriv in derivs:
        derived_file = deriv.derived_file
        rules = fetch_rules_for(derived_file)
        if rules:
            return (derived_file, rules)

    return None, []


def main(job, task_uuid, file_uuid):
    setup_dicts()

    succeeded = True

    file_obj = File.objects.get(uuid=file_uuid)

    # Normally we don't transcribe derivatives (access copies, preservation copies);
    # however, some useful transcription tools can't handle some formats that
    # are common as the primary copies. For example, tesseract can't handle JPEG2000.
    # If there are no rules for the primary format passed in, try to look at each
    # derivative until a transcribable derivative is found.
    #
    # Skip derivatives to avoid double-scanning them; only look at them as a fallback.
    if file_obj.filegrpuse != "original":
        job.print_error(f"{file_uuid} is not an original; not transcribing")
        return 0

    rules = fetch_rules_for(file_obj)
    if not rules:
        file_obj, rules = fetch_rules_for_derivatives(file_obj)

    if not rules:
        job.print_error(
            "No rules found for file {} and its derivatives; not transcribing".format(
                file_uuid
            )
        )
        return 0
    else:
        if file_obj.filegrpuse == "original":
            noun = "original"
        else:
            noun = file_obj.filegrpuse + " derivative"
        job.print_error(f"Transcribing {noun} {file_obj.uuid}")

    rd = ReplacementDict.frommodel(file_=file_obj, type_="file")

    for rule in rules:
        script = rule.command.command
        if rule.command.script_type.value in ("bashScript", "command"):
            (script,) = rd.replace(script)
            args = []
        else:
            args = rd.to_gnu_options

        exitstatus, stdout, stderr = executeOrRun(
            rule.command.script_type, script, arguments=args, capture_output=True
        )
        job.write_output(stdout)
        job.write_error(stderr)
        if exitstatus != 0:
            succeeded = False

        output_path = rd.replace(rule.command.output_location)[0]
        relative_path = output_path.replace(rd["%SIPDirectory%"], "%SIPDirectory%")
        event = insert_transcription_event(exitstatus, file_uuid, rule, relative_path)

        if os.path.isfile(output_path):
            insert_file_into_database(
                task_uuid,
                file_uuid,
                rd["%SIPUUID%"],
                event,
                rule,
                output_path,
                relative_path,
            )

    return 0 if succeeded else 1


def call(jobs):
    with transaction.atomic():
        for job in jobs:
            with job.JobContext():
                task_uuid = job.args[1]
                file_uuid = job.args[2]

                job.set_status(main(job, task_uuid, file_uuid))
