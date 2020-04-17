#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Unit tests for the various components associated with PID (persistent
identifier binding and declaration in Archivematica.

The tests in this module cover both the two bind_pid(s) microservice jobs but
also limited unit testing in create_mets_v2 (AIP METS generation).
"""
from __future__ import unicode_literals

import os
from itertools import chain

import pytest
import vcr
from django.core.management import call_command

from a3m import namespaces as ns
from a3m.client.clientScripts import bind_pid
from a3m.client.clientScripts import bind_pids
from a3m.client.clientScripts import create_mets_v2
from a3m.client.clientScripts.pid_declaration import DeclarePIDs
from a3m.client.clientScripts.pid_declaration import DeclarePIDsException
from a3m.client.job import Job
from a3m.main.models import Directory
from a3m.main.models import File
from a3m.main.models import SIP


THIS_DIR = os.path.dirname(os.path.abspath(__file__))

vcr_cassettes = vcr.VCR(
    cassette_library_dir=os.path.join(THIS_DIR, "fixtures", "vcr_cassettes"),
    path_transformer=vcr.VCR.ensure_suffix(".yaml"),
)


class TestPIDComponents(object):
    """PID binding and declaration test runner class."""

    # Information we'll refer back to in our tests.
    package_uuid = "cb5ebaf5-beda-40b4-8d0c-fefbd546b8de"
    fake_package_uuid = "eb6b860e-611c-45c8-8d3e-b9396ed6c751"
    do_not_bind = "Configuration indicates that PIDs should not be bound."
    incomplete_configuration_msg = "A value for parameter"
    bound_uri = "http://195.169.88.240:8017/12345/"
    bound_hdl = "12345/"
    traditional_identifiers = ("UUID",)
    bound_identifier_types = ("hdl", "URI")
    pid_exid = "EXÎD"
    pid_ulid = "ULID"
    declared_identifier_types = (pid_exid, pid_ulid)
    package_files = [
        "directory_tree.txt",
        "image 001.jpg",
        "Dōcumēnt001.doc",
        "METS.xml",
        "identifiers.json",
    ]
    # At time of writing, the Bind PIDs functions only binds to the content
    # folders and the SIP itself, it doesn't bind to the metadata or
    # submissionDocumentation directories in the package.
    package_directories = ["images/", "documents"]
    pid_declaration_dir = "pid_declaration"

    @property
    def job(self):
        """Cleanly initiate a new Job so we don't maintain unnecessary state in
        this object as the tests continue.
        """
        return Job("stub", "stub", [])

    @staticmethod
    @pytest.fixture(scope="class")
    def django_db_setup(django_db_blocker):
        """Load the various database fixtures required for our tests."""
        pid_dir = "pid_binding"
        fixture_files = ["sip.json", "transfer.json", "files.json", "directories.json"]
        fixtures = []
        for fixture in fixture_files:
            fixtures.append(os.path.join(THIS_DIR, "fixtures", pid_dir, fixture))
        with django_db_blocker.unblock():
            for fixture in fixtures:
                call_command("loaddata", fixture)

    def _get_settings(self):
        return {
            "resolve_url_template_file_access": "https://access.iisg.nl/access/{{ naming_authority }}/{{ pid }}",
            "resolve_url_template_file_preservation": "https://access.iisg.nl/preservation/{{ naming_authority }}/{{ pid }}",
            "handle_resolver_url": "http://195.169.88.240:8017/",
            "resolve_url_template_file": "https://access.iisg.nl/access/{{ naming_authority }}/{{ pid }}",
            "pid_request_verify_certs": "False",
            "resolve_url_template_archive": "https://access.iisg.nl/dip/{{ naming_authority }}/{{ pid }}",
            "resolve_url_template_mets": "https://access.iisg.nl/mets/{{ naming_authority }}/{{ pid }}",
            "pid_web_service_key": "84214c59-8694-48d5-89b5-d40a88cd7768",
            "handle_archive_pid_source": "accession_no",
            "pid_web_service_endpoint": "https://pid.socialhistoryservices.org/secure",
            "resolve_url_template_file_original": "https://access.iisg.nl/original/{{ naming_authority }}/{{ pid }}",
            "naming_authority": "12345",
            "pid_request_body_template": "<?xml version='1.0' encoding='UTF-8'?>\r\n        <soapenv:Envelope\r\n            xmlns:soapenv='http://schemas.xmlsoap.org/soap/envelope/'\r\n            xmlns:pid='http://pid.socialhistoryservices.org/'>\r\n            <soapenv:Body>\r\n                <pid:UpsertPidRequest>\r\n                    <pid:na>{{ naming_authority }}</pid:na>\r\n                    <pid:handle>\r\n                        <pid:pid>{{ naming_authority }}/{{ pid }}</pid:pid>\r\n                        <pid:locAtt>\r\n                            <pid:location weight='1' href='{{ base_resolve_url }}'/>\r\n                            {% for qrurl in qualified_resolve_urls %}\r\n                                <pid:location\r\n                                    weight='0'\r\n                                    href='{{ qrurl.url }}'\r\n                                    view='{{ qrurl.qualifier }}'/>\r\n                            {% endfor %}\r\n                        </pid:locAtt>\r\n                    </pid:handle>\r\n                </pid:UpsertPidRequest>\r\n            </soapenv:Body>\r\n        </soapenv:Envelope>",
        }

    @pytest.mark.django_db
    def test_bind_pids_no_config(self, caplog, settings):
        """Test the output of the code without any args.

        In this instance, we want bind_pids to think that there is some
        configuration available but we haven't provided any other information.
        We should see the microservice job exit without failing for the user.
        An example scenario might be when the user has bind PIDs on in their
        processing configuration but no handle server information configured.
        """
        settings.BIND_PID_HANDLE = {}
        assert (
            bind_pids.main(self.job, None, None) == 1
        ), "Incorrect return value for bind_pids with incomplete configuration."
        assert caplog.records[0].message.startswith(self.incomplete_configuration_msg)

    @pytest.mark.django_db
    def test_bind_pids(self, mocker, settings):
        """Test the bind_pids function end-to-end and ensure that the
        result is that which is anticipated.

        The bind_pids module is responsible for binding persistent identifiers
        to the SIP and the SIP's directories so we only test that here.
        """
        settings.BIND_PID_HANDLE = self._get_settings()
        # We might want to return a unique accession number, but we can also
        # test here using the package UUID, the function's fallback position.
        mocker.patch.object(
            bind_pids, "_get_unique_acc_no", return_value=self.package_uuid
        )
        mocker.patch.object(
            bind_pids, "_validate_handle_server_config", return_value=None
        )
        with vcr_cassettes.use_cassette(
            "test_bind_pids_to_sip_and_dirs.yaml"
        ) as cassette:
            # Primary entry-point for the bind_pids microservice job.
            bind_pids.main(self.job, self.package_uuid, "")
        assert cassette.all_played
        sip_mdl = SIP.objects.filter(uuid=self.package_uuid).first()
        assert len(sip_mdl.identifiers.all()) == len(
            self.bound_identifier_types
        ), "Number of SIP identifiers is greater than anticipated"
        dirs = Directory.objects.filter(sip=self.package_uuid).all()
        assert len(dirs) == len(
            self.package_directories
        ), "Number of directories is incorrect"
        for mdl in chain(dirs, (sip_mdl,)):
            bound = [(idfr.type, idfr.value) for idfr in mdl.identifiers.all()]
            assert len(bound) == len(self.bound_identifier_types)
            pid_types = []
            for pid in bound:
                pid_types.append(pid[0])
            assert (
                "hdl" in pid_types
            ), "An expected hdl persistent identifier isn't in the result set"
            assert "URI" in pid_types, "An expected URI isn't in the result set"
            bound_hdl = "{}{}".format(self.bound_hdl, mdl.pk)
            bound_uri = "{}{}".format(self.bound_uri, mdl.pk)
            pids = []
            for pid in bound:
                pids.append(pid[1])
            assert bound_hdl in pids, "Handle PID bound to SIP is incorrect"
            assert bound_uri in pids, "URI PID bound to SIP is incorrect"
            # Once we know we're creating identifiers as expected, test to ensure
            # that those identifiers are output as expected by the METS functions
            # doing that work.
            dir_dmd_sec = create_mets_v2.getDirDmdSec(mdl, "")
            id_type = dir_dmd_sec.xpath(
                "//premis:objectIdentifierType", namespaces={"premis": ns.premisNS}
            )
            id_value = dir_dmd_sec.xpath(
                "//premis:objectIdentifierValue", namespaces={"premis": ns.premisNS}
            )
            id_types = [item.text for item in id_type]
            id_values = [item.text for item in id_value]
            identifiers_dict = dict(zip(id_types, id_values))
            for key in identifiers_dict.keys():
                assert key in chain(
                    self.traditional_identifiers, self.bound_identifier_types
                )
            assert bound_hdl in identifiers_dict.values()
            assert bound_uri in identifiers_dict.values()

    @pytest.mark.django_db
    def test_bind_pid_no_config(self, caplog, settings):
        """Test the output of the code when bind_pids is set to True but there
        are no handle settings in the Dashboard. Conceivably then the dashboard
        settings could be in-between two states, complete and not-complete,
        here we test for the two opposites on the assumption they'll be the
        most visible errors to the user.
        """
        settings.BIND_PID_HANDLE = {}
        assert bind_pid.main(self.job, self.package_uuid) == 1
        assert caplog.records[0].message.startswith(self.incomplete_configuration_msg)

    @pytest.mark.django_db
    def test_bind_pid(self, settings):
        """Test the bind_pid function end-to-end and ensure that the
        result is that which is anticipated.

        The bind_pid module is responsible for binding persistent identifiers
        to the SIP's files and so we test for that here.
        """
        settings.BIND_PID_HANDLE = self._get_settings()
        files = File.objects.filter(sip=self.package_uuid).all()
        assert len(files) is len(
            self.package_files
        ), "Number of files returned from package is incorrect"
        for file_ in files:
            with vcr_cassettes.use_cassette("test_bind_pid_to_files.yaml") as cassette:
                bind_pid.main(self.job, file_.pk)
        assert cassette.all_played
        for file_mdl in files:
            bound = {idfr.type: idfr.value for idfr in file_mdl.identifiers.all()}
            assert (
                "hdl" in bound
            ), "An expected hdl persistent identifier isn't in the result set"
            assert "URI" in bound, "An expected URI isn't in the result set"
            bound_hdl = "{}{}".format(self.bound_hdl, file_mdl.pk)
            bound_uri = "{}{}".format(self.bound_uri, file_mdl.pk)
            assert bound.get("hdl") == bound_hdl
            assert bound.get("URI") == bound_uri
            # Then test to see that the PREMIS objects are created correctly in
            # the AIP METS generation code.
            file_level_premis = create_mets_v2.create_premis_object(file_mdl.pk)
            id_type = file_level_premis.xpath(
                "//premis:objectIdentifierType", namespaces={"premis": ns.premisNS}
            )
            id_value = file_level_premis.xpath(
                "//premis:objectIdentifierValue", namespaces={"premis": ns.premisNS}
            )
            id_types = [item.text for item in id_type]
            id_values = [item.text for item in id_value]
            identifiers_dict = dict(zip(id_types, id_values))
            for key in identifiers_dict.keys():
                assert key in chain(
                    self.traditional_identifiers, self.bound_identifier_types
                ), "Identifier type not in expected schemes list"
            assert bound_hdl in identifiers_dict.values()
            assert bound_uri in identifiers_dict.values()

    @pytest.mark.django_db
    def test_bind_pid_no_settings(self, caplog, settings):
        """Test the output of the code when bind_pids is set to True but there
        are no handle settings in the Dashboard. Conceivably then the dashboard
        settings could be in-between two states, complete and not-complete,
        here we test for the two opposites on the assumption they'll be the
        most visible errors to the user.
        """
        file_count = 5
        settings.BIND_PID_HANDLE = {}
        files = File.objects.filter(sip=self.package_uuid).all()
        assert (
            files is not None
        ), "Files haven't been retrieved from the model as expected"
        for file_ in files:
            bind_pid.main(self.job, file_.pk)
        for file_number in range(file_count):
            assert caplog.records[file_number].message.startswith(
                self.incomplete_configuration_msg
            )

    @pytest.mark.django_db
    def test_pid_declaration(self, mocker, settings):
        """Test that the overall functionality of the PID declaration functions
        work as expected.
        """
        settings.BIND_PID_HANDLE = self._get_settings()
        job = self.job
        files_no = 2
        dirs_no = 2
        example_ulid = "EXAMPLE0RE60SW7SVM2C8EGQAD"
        example_uri = "https://éxample.com/"
        expected_identifiers = 2
        identifers_file = "identifiers.json"
        identifiers_loc = os.path.join(
            THIS_DIR, "fixtures", self.pid_declaration_dir, identifers_file
        )
        all_identifier_types = (
            self.traditional_identifiers
            + self.bound_identifier_types
            + self.declared_identifier_types
        )
        mocker.patch.object(
            DeclarePIDs, "_retrieve_identifiers_path", return_value=identifiers_loc
        )
        DeclarePIDs(job).pid_declaration(unit_uuid=self.package_uuid, sip_directory="")
        # Declare PIDs allows us to assign PIDs to very specific objects in a
        # transfer.
        sip_mdl = SIP.objects.filter(uuid=self.package_uuid).first()
        files = File.objects.filter(sip=self.package_uuid, filegrpuse="original").all()
        dir_mdl = Directory.objects.filter(
            currentlocation__contains="%SIPDirectory%objects/"
        )
        assert len(files) == files_no, "Number of files returned is incorrect"
        assert len(dir_mdl) == dirs_no, "Number of directories returned is incorrect"
        for mdl in chain((sip_mdl,), files, dir_mdl):
            bound = {idfr.type: idfr.value for idfr in mdl.identifiers.all()}
            assert (
                len(bound) == expected_identifiers
            ), "Number of identifiers is incorrect"
            assert set(bound.keys()) == set(
                self.declared_identifier_types
            ), "Returned keys are not in expected list"
            for key, value in bound.items():
                assert value, "Returned an empty value for an identifier"
                if key == self.pid_exid:
                    assert example_uri in value, "Example URI type not preserved"
                if key == self.pid_ulid:
                    assert len(example_ulid) == len(value)
        # Use the previous PID binding vcr cassettes to ensure declared PIDs can
        # co-exist with bound ones.
        mocker.patch.object(
            bind_pids, "_get_unique_acc_no", return_value=self.package_uuid
        )
        mocker.patch.object(
            bind_pids, "_validate_handle_server_config", return_value=None
        )
        with vcr_cassettes.use_cassette(
            "test_bind_pids_to_sip_and_dirs.yaml"
        ) as cassette:
            # Primary entry-point for the bind_pids microservice job.
            bind_pids.main(self.job, self.package_uuid, "")
        for mdl in chain((sip_mdl,), dir_mdl):
            dir_dmd_sec = create_mets_v2.getDirDmdSec(mdl, "")
            id_type = dir_dmd_sec.xpath(
                "//premis:objectIdentifierType", namespaces={"premis": ns.premisNS}
            )
            id_value = dir_dmd_sec.xpath(
                "//premis:objectIdentifierValue", namespaces={"premis": ns.premisNS}
            )
            assert len(id_type) == len(
                all_identifier_types
            ), "Identifier type count is incorrect"
            assert len(id_value) == len(
                all_identifier_types
            ), "Identifier value count is incorrect"
            for key, value in dict(zip(id_type, id_value)).items():
                if key == self.pid_exid:
                    assert example_uri in value, "Example URI not preserved"
                if key == self.pid_ulid:
                    assert len(example_ulid) == len(value)
        for file_ in files:
            with vcr_cassettes.use_cassette("test_bind_pid_to_files.yaml") as cassette:
                bind_pid.main(self.job, file_.pk)
            assert cassette.all_played
        for file_mdl in files:
            file_level_premis = create_mets_v2.create_premis_object(file_mdl.pk)
            id_type = file_level_premis.xpath(
                "//premis:objectIdentifierType", namespaces={"premis": ns.premisNS}
            )
            id_value = file_level_premis.xpath(
                "//premis:objectIdentifierValue", namespaces={"premis": ns.premisNS}
            )
            assert len(id_type) == len(
                all_identifier_types
            ), "Identifier type count is incorrect"
            assert len(id_value) == len(
                all_identifier_types
            ), "Identifier value count is incorrect"
            for key, value in dict(zip(id_type, id_value)).items():
                if key == self.pid_exid:
                    assert example_uri in value, "Example URI not preserved"
                if key == self.pid_ulid:
                    assert len(example_ulid) == len(value)

    @pytest.mark.django_db
    def test_pid_declaration_exceptions(self, mocker):
        """Ensure that the PID declaration feature exits when the JSOn cannot
        be loaded.
        """
        job = self.job
        # Test behavior when there isn't an identifiers.json file, e.g. we
        # simulate this by passing an incorrect Unit UUID.
        DeclarePIDs(job).pid_declaration(
            unit_uuid=self.fake_package_uuid, sip_directory=""
        )
        assert (
            "No identifiers.json file found" in job.get_stderr().strip()
        ), "Expecting no identifiers.json file, but got something else"
        # Test behavior when identifiers.json is badly formatted.
        bad_identifers_file = "bad_identifiers.json"
        bad_identifiers_loc = os.path.join(
            THIS_DIR, "fixtures", self.pid_declaration_dir, bad_identifers_file
        )
        mocker.patch.object(
            DeclarePIDs, "_retrieve_identifiers_path", return_value=bad_identifiers_loc
        )
        try:
            DeclarePIDs(job).pid_declaration(unit_uuid="", sip_directory="")
        except DeclarePIDsException as err:
            assert "No JSON object could be decoded" in str(
                err
            ), "Error message something other than anticipated for invalid JSON"
