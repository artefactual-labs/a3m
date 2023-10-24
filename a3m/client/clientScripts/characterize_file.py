#
# Collects characterization commands for the provided file, then either
# a) Inserts the tool's XML output into the database, or
# b) Prints the tool's stdout, for tools which do not output XML
#
# If a tool has no defined characterization commands, then the default
# will be run instead (currently FITS).
from django.db import transaction
from lxml import etree

from a3m.dicts import replace_string_values
from a3m.dicts import ReplacementDict
from a3m.dicts import setup_dicts
from a3m.executeOrRunSubProcess import executeOrRun
from a3m.fpr.registry import FPR
from a3m.fpr.registry import Rule
from a3m.fpr.registry import RulePurpose
from a3m.main.models import FPCommandOutput


def _insert_command_output(file_uuid, rule_uuid, content):
    return FPCommandOutput.objects.create(
        file_id=file_uuid, rule_id=rule_uuid, content=content
    )


def _get_rules(file_uuid) -> list[Rule]:
    # Check to see whether the file has already been characterized; don't try
    # to characterize it a second time if so.
    if FPCommandOutput.objects.filter(file_id=file_uuid).count() > 0:
        return []

    return FPR.get_file_rules(
        file_uuid,
        purpose=RulePurpose.CHARACTERIZATION,
        # We avoid default_characterization because we don't have FITS in a3m.
        fallback=False,
    )


def main(job, file_path, file_uuid, sip_uuid):
    setup_dicts()

    failed = False
    state = []

    rules = _get_rules(file_uuid)
    if not rules:
        return 0

    for rule in rules:
        if (
            rule.command.script_type == "bashScript"
            or rule.command.script_type == "command"
        ):
            args = []
            command_to_execute = replace_string_values(
                rule.command.command, file_=file_uuid, sip=sip_uuid, type_="file"
            )
        else:
            rd = ReplacementDict.frommodel(file_=file_uuid, sip=sip_uuid, type_="file")
            args = rd.to_gnu_options()
            command_to_execute = rule.command.command

        exitstatus, stdout, stderr = executeOrRun(
            rule.command.script_type.value,
            command_to_execute,
            arguments=args,
            capture_output=True,
        )

        job.write_output(stdout)
        job.write_error(stderr)

        if exitstatus != 0:
            job.write_error(
                "Command {} failed with exit status {}; stderr:".format(
                    rule.command.description, exitstatus
                )
            )
            failed = True
            continue
        # fmt/101 is XML - we want to collect and package any XML output, while
        # allowing other commands to execute without actually collecting their
        # output in the event that they are writing their output to disk.
        # FPCommandOutput can have multiple rows for a given file,
        # distinguished by the rule that produced it.
        if (
            rule.command.output_format
            and rule.command.output_format.pronom_id == "fmt/101"
        ):
            try:
                etree.fromstring(  # nosec B320
                    stdout.encode("utf8"),
                    etree.XMLParser(resolve_entities=False, no_network=True),
                )
                state.append((file_uuid, rule, stdout))
            except etree.XMLSyntaxError:
                failed = True
                job.write_error(
                    'XML output for command "{}" ({}) was not valid XML; not saving to database'.format(
                        rule.command.description, rule.command.id
                    )
                )
        else:
            job.write_error(
                'Tool output for command "{}" ({}) is not XML; not saving to database'.format(
                    rule.command.description, rule.command.id
                )
            )

    with transaction.atomic():
        # Get again and compare rules during transaction
        tx_rules = _get_rules(file_uuid)
        if not tx_rules or list(rules) != list(tx_rules):
            job.write_error(
                f'Rules for file "{file_path}" changed during characterization'
            )
            return 255

        # Save outputs if they are the same
        for file_uuid, rule, stdout in state:
            _insert_command_output(file_uuid, rule.uuid, stdout)
            job.write_output(
                'Saved XML output for command "{}" ({})'.format(
                    rule.command.description, rule.command.uuid
                )
            )

    if failed:
        return 255
    else:
        return 0


def call(jobs):
    for job in jobs:
        with job.JobContext():
            job.set_status(main(job, *job.args[1:]))
