import argparse
import uuid

from django.db import transaction

from a3m.databaseFunctions import getUTCDate
from a3m.databaseFunctions import insertIntoEvents
from a3m.executeOrRunSubProcess import executeOrRun
from a3m.fpr.models import FormatVersion
from a3m.fpr.models import IDCommand
from a3m.fpr.models import IDRule
from a3m.main.models import File
from a3m.main.models import FileFormatVersion
from a3m.main.models import FileID


def write_identification_event(file_uuid, command, format=None, success=True):
    event_detail_text = 'program="{}"; version="{}"'.format(
        command.tool.description, command.tool.version
    )
    if success:
        event_outcome_text = "Positive"
    else:
        event_outcome_text = "Not identified"

    if not format:
        format = "No Matching Format"

    date = getUTCDate()

    insertIntoEvents(
        fileUUID=file_uuid,
        eventIdentifierUUID=str(uuid.uuid4()),
        eventType="format identification",
        eventDateTime=date,
        eventDetail=event_detail_text,
        eventOutcome=event_outcome_text,
        eventOutcomeDetailNote=format,
    )


def write_file_id(file_uuid, format, output):
    """
    Write the identified format to the DB.

    :param str file_uuid: UUID of the file identified
    :param FormatVersion format: FormatVersion it was identified as
    :param str output: Text that generated the match
    """
    if format.pronom_id:
        format_registry = "PRONOM"
        key = format.pronom_id
    else:
        format_registry = "Archivematica Format Policy Registry"
        key = output

    # Sometimes, this is null instead of an empty string
    version = format.version or ""

    FileID.objects.create(
        file_id=file_uuid,
        format_name=format.format.description,
        format_version=version,
        format_registry_name=format_registry,
        format_registry_key=key,
    )


def _default_idcommand():
    """Retrieve the default ``fpr.IDCommand``.

    We only expect to find one command enabled/active.
    """
    return IDCommand.active.first()


def main(job, file_path, file_uuid, disable_reidentify):
    command = _default_idcommand()
    if command is None:
        job.write_error("Unable to determine IDCommand.\n")
        return 255

    command_uuid = command.uuid
    job.print_output("IDCommand:", command.description)
    job.print_output("IDCommand UUID:", command.uuid)
    job.print_output("IDTool:", command.tool.description)
    job.print_output("IDTool UUID:", command.tool.uuid)
    job.print_output(f"File: ({file_uuid}) {file_path}")

    file_ = File.objects.get(uuid=file_uuid)

    # If reidentification is disabled and a format identification event exists for this file, exit
    if (
        disable_reidentify
        and file_.event_set.filter(event_type="format identification").exists()
    ):
        job.print_output(
            "This file has already been identified, and re-identification is disabled. Skipping."
        )
        return 0

    exitcode, output, err = executeOrRun(
        command.script_type,
        command.script,
        arguments=[file_path],
        printing=False,
        capture_output=True,
    )
    output = output.strip()

    if exitcode != 0:
        job.print_error(f"Error: IDCommand with UUID {command_uuid} exited non-zero.")
        job.print_error(f"Error: {err}")
        return 255

    job.print_output("Command output:", output)
    # PUIDs are the same regardless of tool, so PUID-producing tools don't have "rules" per se - we just
    # go straight to the FormatVersion table to see if there's a matching PUID
    try:
        if command.config == "PUID":
            version = FormatVersion.active.get(pronom_id=output)
        else:
            rule = IDRule.active.get(command_output=output, command=command)
            version = rule.format
    except IDRule.DoesNotExist:
        job.print_error(
            'Error: No FPR identification rule for tool output "{}" found'.format(
                output
            )
        )
        write_identification_event(file_uuid, command, success=False)
        return 255
    except IDRule.MultipleObjectsReturned:
        job.print_error(
            'Error: Multiple FPR identification rules for tool output "{}" found'.format(
                output
            )
        )
        write_identification_event(file_uuid, command, success=False)
        return 255
    except FormatVersion.DoesNotExist:
        job.print_error(f"Error: No FPR format record found for PUID {output}")
        write_identification_event(file_uuid, command, success=False)
        return 255

    (ffv, created) = FileFormatVersion.objects.get_or_create(
        file_uuid=file_, defaults={"format_version": version}
    )
    if not created:  # Update the version if it wasn't created new
        ffv.format_version = version
        ffv.save()
    job.print_output(f"{file_path} identified as a {version.description}")

    write_identification_event(file_uuid, command, format=version.pronom_id)
    write_file_id(file_uuid=file_uuid, format=version, output=output)

    return 0


def call(jobs):
    parser = argparse.ArgumentParser(description="Identify file formats.")
    parser.add_argument("file_path", type=str, help="%relativeLocation%")
    parser.add_argument("file_uuid", type=str, help="%fileUUID%")
    parser.add_argument(
        "--disable-reidentify",
        action="store_true",
        help="Disable identification if it has already happened for this file.",
    )

    with transaction.atomic():
        for job in jobs:
            with job.JobContext():
                args = parser.parse_args(job.args[1:])
                job.set_status(
                    main(
                        job,
                        args.file_path,
                        args.file_uuid,
                        args.disable_reidentify,
                    )
                )
