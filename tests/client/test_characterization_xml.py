import uuid

import pytest
from lxml import etree

from a3m.client.clientScripts.create_mets_v2 import create_premis_object
from a3m.main.models import File
from a3m.main.models import FPCommandOutput


@pytest.mark.django_db
def test_characterization_metadata_cannot_read_external_entities(tmp_path):
    file = File.objects.create(uuid=str(uuid.uuid4()), originallocation="object.txt")
    output = FPCommandOutput.objects.create(
        file=file,
        rule_id="97d5ca63-58de-4f6c-bddc-d858fbd07433",
        content=(
            '<!DOCTYPE characterization [<!ENTITY format "text">]>'
            "<characterization><format>&format;</format></characterization>"
        ),
    )

    premis = create_premis_object(file.uuid)
    assert premis.findtext(".//characterization/format") == "text"

    secret = tmp_path / "secret.txt"
    secret.write_text("private data")
    output.content = (
        f'<!DOCTYPE characterization [<!ENTITY secret SYSTEM "{secret.as_uri()}">]>'
        "<characterization>&secret;</characterization>"
    )
    output.save(update_fields=["content"])

    with pytest.raises(etree.XMLSyntaxError):
        create_premis_object(file.uuid)
