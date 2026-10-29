"""Exercise the installed CLI and inspect its exported preservation package."""

import hashlib
import json
import os
import re
import subprocess
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote

import bagit
import boto3
import pytest
from botocore.config import Config
from pytest_bdd import given
from pytest_bdd import scenarios
from pytest_bdd import then
from pytest_bdd import when

scenarios("ingest.feature")

NS = {
    "mets": "http://www.loc.gov/METS/",
    "premis": "http://www.loc.gov/premis/v3",
    "xlink": "http://www.w3.org/1999/xlink",
}


@pytest.fixture
def workspace(tmp_path, request):
    reports = Path(os.environ.get("ACCEPTANCE_REPORTS", "reports")) / request.node.name
    reports.mkdir(parents=True, exist_ok=True)
    return {"root": tmp_path, "reports": reports, "data": tmp_path / "data"}


@given("a local JPEG 2000 image with spaces in its name")
def local_image(workspace):
    transfer = workspace["root"] / "transfer"
    transfer.mkdir()
    source = transfer / "image with spaces.jp2"
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=c=blue:s=32x32",
            "-frames:v",
            "1",
            "-c:v",
            "jpeg2000",
            str(source),
        ],
        check=True,
        capture_output=True,
        timeout=30,
    )
    workspace["source"] = transfer
    workspace["original"] = source.read_bytes()


@given("a local source that does not exist")
def missing_source(workspace):
    workspace["source"] = workspace["root"] / "missing.jp2"


@given("an empty S3 bucket")
def s3_bucket(workspace):
    endpoint = os.environ["ACCEPTANCE_S3_ENDPOINT"]
    client = boto3.client(
        "s3",
        endpoint_url=endpoint,
        region_name="us-east-1",
        aws_access_key_id="acceptance",
        aws_secret_access_key="acceptance-secret",
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
            connect_timeout=5,
            read_timeout=10,
            retries={"mode": "standard", "total_max_attempts": 2},
        ),
    )
    bucket = f"a3m-acceptance-{uuid.uuid4().hex}"
    client.create_bucket(Bucket=bucket)
    assert client.list_objects_v2(Bucket=bucket).get("Contents", []) == []
    workspace.update(s3_client=client, s3_bucket=bucket)
    workspace["s3_env"] = {
        "A3M_S3_ENABLED": "true",
        "A3M_S3_ENDPOINT_URL": endpoint,
        "A3M_S3_REGION_NAME": "us-east-1",
        "A3M_S3_ACCESS_KEY_ID": "acceptance",
        "A3M_S3_SECRET_ACCESS_KEY": "acceptance-secret",
        "A3M_S3_USE_SSL": "false",
        "A3M_S3_ADDRESSING_STYLE": "path",
        "A3M_S3_SIGNATURE_VERSION": "s3v4",
        "A3M_S3_BUCKET": bucket,
    }


@when("I ingest it with the a3m command")
def ingest(workspace):
    env = os.environ.copy()
    env.update(
        XDG_DATA_HOME=str(workspace["data"]),
        A3M_DEBUG="yes",
        A3M_WORKER_THREADS="2",
    )
    env.update(workspace.get("s3_env", {}))
    command = ["a3m", "--no-input", "--name=acceptance", workspace["source"].as_uri()]
    # Write logs as the process runs so timeouts still leave useful diagnostics.
    with (workspace["reports"] / "cli.log").open("w") as output:
        workspace["result"] = subprocess.run(
            command,
            env=env,
            stdout=output,
            stderr=subprocess.STDOUT,
            timeout=300,
        )


def cli_log(workspace):
    return (workspace["reports"] / "cli.log").read_text()


def completed_aips(workspace):
    return list((workspace["data"] / "a3m" / "share" / "completed").glob("*"))


@then("the command succeeds")
def command_succeeds(workspace):
    assert workspace["result"].returncode == 0, cli_log(workspace)
    assert "Processing completed successfully!" in cli_log(workspace)


@then("S3 stores the complete AIP under its package identifier")
def stored_aip(workspace):
    match = re.search(
        r"^AIP ([0-9a-f-]{36}) is being generated", cli_log(workspace), re.M
    )
    assert match is not None, cli_log(workspace)
    package_id = str(uuid.UUID(match[1]))
    client, bucket = workspace["s3_client"], workspace["s3_bucket"]
    listing = client.list_objects_v2(Bucket=bucket)
    assert not listing["IsTruncated"]
    objects = listing.get("Contents", [])
    assert len(objects) == 1
    assert objects[0]["Key"] == package_id
    aips = completed_aips(workspace)
    assert len(aips) == 1, cli_log(workspace)
    response = client.get_object(Bucket=bucket, Key=package_id)
    with response["Body"] as body:
        content = body.read()
    assert response["ContentLength"] == len(content)
    assert content == aips[0].read_bytes()
    downloaded = workspace["root"] / "downloaded" / aips[0].name
    downloaded.parent.mkdir()
    downloaded.write_bytes(content)
    workspace["downloaded_aip"] = downloaded
    (workspace["reports"] / "s3.json").write_text(
        json.dumps(
            {"bucket": bucket, "key": package_id, "bytes": len(content)}, indent=2
        )
        + "\n"
    )


@then("one valid BagIt AIP contains the unchanged original")
def original_is_preserved(workspace):
    aips = completed_aips(workspace)
    assert len(aips) == 1, cli_log(workspace)
    archive = workspace.get("downloaded_aip", aips[0])
    assert archive.suffix == ".7z"
    extracted = workspace["root"] / "extracted"
    subprocess.run(
        ["7z", "x", str(archive), f"-o{extracted}"],
        check=True,
        capture_output=True,
        timeout=30,
    )
    bags = list(extracted.iterdir())
    assert len(bags) == 1
    bag = bags[0]
    assert bagit.Bag(str(bag)).validate()
    originals = list((bag / "data" / "objects").rglob("*.jp2"))
    assert len(originals) == 1
    assert originals[0].read_bytes() == workspace["original"]
    workspace.update(bag=bag, preserved_original=originals[0])


@then("the AIP contains a TIFF preservation copy")
def preservation_copy(workspace):
    derivatives = list((workspace["bag"] / "data" / "objects").rglob("*.tif"))
    assert len(derivatives) == 1
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-of", "json", str(derivatives[0])],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    stream = json.loads(result.stdout)["streams"][0]
    assert (stream["codec_name"], stream["width"], stream["height"]) == ("tiff", 32, 32)
    workspace["derivative"] = derivatives[0]


@then("METS records both files with fixity and a normalization event")
def preservation_metadata(workspace):
    mets_files = list((workspace["bag"] / "data").glob("METS.*.xml"))
    assert len(mets_files) == 1
    mets = ET.parse(mets_files[0])
    objects = {}
    for use, path in (
        ("original", workspace["preserved_original"]),
        ("preservation", workspace["derivative"]),
    ):
        files = mets.findall(f".//mets:fileGrp[@USE='{use}']/mets:file", NS)
        assert len(files) == 1
        file = files[0]
        location = file.find("mets:FLocat", NS)
        assert location is not None
        href = unquote(location.attrib[f"{{{NS['xlink']}}}href"])
        assert (mets_files[0].parent / href).resolve() == path.resolve()
        metadata = mets.find(f"mets:amdSec[@ID='{file.attrib['ADMID']}']", NS)
        assert metadata is not None
        obj = metadata.find(".//premis:object", NS)
        assert obj is not None
        fixity = obj.find("premis:objectCharacteristics/premis:fixity", NS)
        assert fixity is not None
        assert (
            fixity.findtext("premis:messageDigestAlgorithm", namespaces=NS) == "sha256"
        )
        assert (
            fixity.findtext("premis:messageDigest", namespaces=NS)
            == hashlib.sha256(path.read_bytes()).hexdigest()
        )
        objects[use] = obj
    events = mets.findall(".//premis:event", NS)
    normalization = [
        event
        for event in events
        if event.findtext("premis:eventType", namespaces=NS) == "normalization"
    ]
    assert len(normalization) == 1
    event = normalization[0]
    assert event.findtext(
        "premis:eventOutcomeInformation/premis:eventOutcomeDetail/"
        "premis:eventOutcomeDetailNote",
        namespaces=NS,
    ).endswith(workspace["derivative"].name)
    relationship = objects["preservation"].find(
        "premis:relationship[premis:relationshipSubType='has source']", NS
    )
    assert relationship is not None
    assert relationship.findtext(
        "premis:relatedObjectIdentifier/premis:relatedObjectIdentifierValue",
        namespaces=NS,
    ) == objects["original"].findtext(
        "premis:objectIdentifier/premis:objectIdentifierValue", namespaces=NS
    )
    assert relationship.findtext(
        "premis:relatedEventIdentifier/premis:relatedEventIdentifierValue",
        namespaces=NS,
    ) == event.findtext(
        "premis:eventIdentifier/premis:eventIdentifierValue", namespaces=NS
    )


@then("the command fails")
def command_fails(workspace):
    assert workspace["result"].returncode == 1, cli_log(workspace)
    assert "Processing completed successfully!" not in cli_log(workspace)
    assert "Path given does not point to an existing file or directory" in " ".join(
        cli_log(workspace).split()
    )


@then("no completed AIP is produced")
def no_aip(workspace):
    assert completed_aips(workspace) == [], cli_log(workspace)
