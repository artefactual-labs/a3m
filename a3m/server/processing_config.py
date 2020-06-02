"""Processing configuration.

This module lists the processing configuration fields where the user has the
ability to establish predefined choices via the user interface, and handles
processing config file operations.
"""
import logging
from pathlib import Path

from django.conf import settings
from lxml import etree


logger = logging.getLogger(__name__)

PROCESSING_XML_FILE = "processingMCP.xml"


class ProcessingConfigError(Exception):
    pass


def parse_processing_xml(path, workflow):
    """Parse, validate and return processing config XML document.

    Validation is performed against the workflow dataset.
    """
    if not path.is_file():
        raise ProcessingConfigError(f"Configuration file not found: {path}")

    try:
        processing_xml = etree.parse(str(path))
    except etree.LxmlError:
        raise ProcessingConfigError(
            f"Error parsing XML at {path} for pre-configured choice"
        )

    preconfigured_applies = []

    # Confirm that all pre-configured choices match a real workflow entity.
    for preconfigured_choice in processing_xml.findall(".//preconfiguredChoice"):
        applies_to = preconfigured_choice.find("appliesTo").text
        go_to_chain = preconfigured_choice.find("goToChain").text
        try:
            link = workflow.get_link(applies_to)
        except KeyError:
            raise ProcessingConfigError(
                f"Pre-configured choice {applies_to} (appliesTo) not found in workflow"
            )

        matched = False
        manager = link.config["@manager"]
        if manager == "linkTaskManagerReplacementDicFromChoice":
            for replacement in link.config["replacements"]:
                if go_to_chain == replacement["id"]:
                    matched = True
        else:
            try:
                workflow.get_chain(go_to_chain)
            except KeyError:
                pass
            else:
                matched = True
        if not matched:
            raise ProcessingConfigError(
                f"Pre-configured choice {go_to_chain} (goToChain) not found in workflow"
            )
        preconfigured_applies.append(applies_to)

    # Confirm that all workflow decions are addressed.
    for link_id in workflow.get_links():
        try:
            link = workflow.get_link(link_id)
        except KeyError:
            continue
        manager = link.config["@manager"]
        if manager not in (
            "linkTaskManagerChoice",
            "linkTaskManagerReplacementDicFromChoice",
        ):
            continue
        if link_id not in preconfigured_applies:
            raise ProcessingConfigError(
                f"Workflow link {link_id} ({manager}) is not pre-configured by {path.name}"
            )

    return processing_xml


def validate_processing_configs(workflow):
    """Validate all local processing configurations."""
    config_dir = Path(settings.SHARED_DIRECTORY, "processingConfigs")
    matches = config_dir.glob("*.xml")
    if not matches:
        raise ProcessingConfigError(f"{config_dir} is not set up")
    for path in matches:
        parse_processing_xml(path, workflow)


def load_processing_xml(package_path, workflow):
    """Load the processing configuration made available in the package."""
    return parse_processing_xml(Path(package_path, PROCESSING_XML_FILE), workflow)


def load_preconfigured_choice(package_path, workflow_link_id, workflow):
    choice = None

    processing_xml = load_processing_xml(package_path, workflow)
    if processing_xml is not None:
        for preconfigured_choice in processing_xml.findall(".//preconfiguredChoice"):
            if preconfigured_choice.find("appliesTo").text == str(workflow_link_id):
                choice = preconfigured_choice.find("goToChain").text

    return choice
