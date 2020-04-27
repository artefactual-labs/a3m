"""Processing configuration.

This module lists the processing configuration fields where the user has the
ability to establish predefined choices via the user interface, and handles
processing config file operations.
"""
import logging
import os

from lxml import etree


logger = logging.getLogger(__name__)

PROCESSING_XML_FILE = "processingMCP.xml"


def load_processing_xml(package_path):
    processing_file_path = os.path.join(package_path, PROCESSING_XML_FILE)

    if not os.path.isfile(processing_file_path):
        return None

    try:
        return etree.parse(processing_file_path)
    except etree.LxmlError:
        logger.warning(
            "Error parsing xml at %s for pre-configured choice",
            processing_file_path,
            exc_info=True,
        )
        return None


def load_preconfigured_choice(package_path, workflow_link_id):
    choice = None

    processing_xml = load_processing_xml(package_path)
    if processing_xml is not None:
        for preconfigured_choice in processing_xml.findall(".//preconfiguredChoice"):
            if preconfigured_choice.find("appliesTo").text == str(workflow_link_id):
                choice = preconfigured_choice.find("goToChain").text

    return choice
