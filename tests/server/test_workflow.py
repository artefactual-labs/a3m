import os
from io import StringIO

import pytest
from django.utils.translation import ugettext_lazy

from a3m.server import translation
from a3m.server import workflow


ASSETS_DIR = os.path.join(
    os.path.dirname(
        os.path.dirname(os.path.abspath(os.path.join(__file__, os.pardir)))
    ),
    "a3m",
    "assets",
)

FIXTURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


def test_invert_job_statuses(mocker):
    mocker.patch(
        "a3m.server.jobs.Job.STATUSES",
        (
            (1, ugettext_lazy("Uno")),
            (2, ugettext_lazy("Dos")),
            (3, ugettext_lazy("Tres")),
        ),
    )
    ret = workflow._invert_job_statuses()
    assert ret == {"Uno": 1, "Dos": 2, "Tres": 3}


def test_load_invalid_document():
    blob = StringIO("""{}""")
    with pytest.raises(workflow.SchemaValidationError):
        workflow.load(blob)


def test_load_invalid_json():
    blob = StringIO("""{_}""")
    with pytest.raises(ValueError):
        workflow.load(blob)


@pytest.mark.parametrize(
    "path",
    (
        os.path.join(ASSETS_DIR, "workflow.json"),
        os.path.join(FIXTURES_DIR, "workflow-integration-test.json"),
    ),
)
def test_load_valid_document(path):
    with open(path) as fp:
        wf = workflow.load(fp)

    links = wf.get_links()
    assert len(links) > 0
    first_link = next(iter(links.values()))
    assert repr(first_link) == f"Link <{first_link.id}>"
    assert isinstance(first_link, workflow.Link)
    assert first_link.config == first_link._src["config"]

    # Workflow __str__ method
    assert str(wf) == "Links {}".format(len(links))

    # Test normalization of job statuses.
    link = next(iter(links.values()))
    valid_statuses = list(workflow._STATUSES.values())
    assert link["fallback_job_status"] in valid_statuses
    for item in link["exit_codes"].values():
        assert item["job_status"] in valid_statuses

    # Test get_label method in LinkBase.
    assert (
        first_link.get_label("description")
        == first_link._src["description"][translation.FALLBACK_LANG]
    )
    assert first_link.get_label("foobar") is None


def test_link_browse_methods(mocker):
    with open(os.path.join(ASSETS_DIR, "workflow.json")) as fp:
        wf = workflow.load(fp)
    ln = wf.get_link("1ba589db-88d1-48cf-bb1a-a5f9d2b17378")
    assert ln.get_next_link(code="0").id == "087d27be-c719-47d8-9bbb-9a7d8b609c44"
    assert ln.get_status_id(code="0") == workflow._STATUSES["Completed successfully"]
    assert ln.get_next_link(code="1").id == "b2ef06b9-bca4-49da-bc5c-866d7b3c4bb1"
    assert ln.get_status_id(code="1") == workflow._STATUSES["Failed"]


def test_get_schema():
    schema = workflow._get_schema()
    assert schema["$id"] == "https://a3m.readthedocs.io/workflow/schema/v1.json"


def test_get_schema_not_found(mocker):
    mocker.patch("a3m.server.workflow._LATEST_SCHEMA", "non-existen-schema")
    with pytest.raises(IOError):
        workflow._get_schema()
