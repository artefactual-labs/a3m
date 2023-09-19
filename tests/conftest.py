import pathlib

import pytest


@pytest.fixture(autouse=True)
def set_xml_catalog_files(monkeypatch):
    """Use local XML schemas for validation."""
    monkeypatch.setenv(
        "XML_CATALOG_FILES",
        str(
            pathlib.Path(__file__).parent.parent
            / "a3m/client/assets/catalog/catalog.xml"
        ),
    )
