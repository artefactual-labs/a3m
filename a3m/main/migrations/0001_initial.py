# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

import uuid

from django.conf import settings
from django.db import migrations
from django.db import models

import a3m.main.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("fpr", "0002_initial_data"),
    ]

    operations = [
        migrations.CreateModel(
            name="Agent",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        editable=False,
                        primary_key=True,
                        db_column="pk",
                    ),
                ),
                (
                    "identifiertype",
                    models.TextField(
                        null=True,
                        verbose_name="Agent Identifier Type",
                        db_column="agentIdentifierType",
                    ),
                ),
                (
                    "identifiervalue",
                    models.TextField(
                        help_text="Used for premis:agentIdentifierValue and premis:linkingAgentIdentifierValue in the METS file.",
                        null=True,
                        verbose_name="Agent Identifier Value",
                        db_column="agentIdentifierValue",
                    ),
                ),
                (
                    "name",
                    models.TextField(
                        help_text="Used for premis:agentName in the METS file.",
                        null=True,
                        verbose_name="Agent Name",
                        db_column="agentName",
                    ),
                ),
                (
                    "agenttype",
                    models.TextField(
                        default="organization",
                        help_text="Used for premis:agentType in the METS file.",
                        verbose_name="Agent Type",
                        db_column="agentType",
                    ),
                ),
            ],
            options={"db_table": "Agents"},
        ),
        migrations.CreateModel(
            name="Derivation",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        editable=False,
                        primary_key=True,
                        db_column="pk",
                    ),
                )
            ],
            options={"db_table": "Derivations"},
        ),
        migrations.CreateModel(
            name="Directory",
            fields=[
                (
                    "uuid",
                    models.CharField(
                        max_length=36,
                        serialize=False,
                        primary_key=True,
                        db_column="directoryUUID",
                    ),
                ),
                (
                    "originallocation",
                    a3m.main.models.BlobTextField(db_column="originalLocation"),
                ),
                (
                    "currentlocation",
                    a3m.main.models.BlobTextField(
                        null=True, db_column="currentLocation"
                    ),
                ),
                (
                    "enteredsystem",
                    models.DateTimeField(auto_now_add=True, db_column="enteredSystem"),
                ),
            ],
            options={"db_table": "Directories"},
        ),
        migrations.CreateModel(
            name="DublinCore",
            fields=[
                (
                    "id",
                    models.AutoField(serialize=False, primary_key=True, db_column="pk"),
                ),
                (
                    "metadataappliestoidentifier",
                    models.CharField(
                        default=None,
                        max_length=36,
                        null=True,
                        db_column="metadataAppliesToidentifier",
                        blank=True,
                    ),
                ),
                ("title", models.TextField(db_column="title", blank=True)),
                (
                    "is_part_of",
                    models.TextField(
                        help_text="Optional: leave blank if unsure",
                        verbose_name="Part of AIC",
                        db_column="isPartOf",
                        blank=True,
                    ),
                ),
                ("creator", models.TextField(db_column="creator", blank=True)),
                ("subject", models.TextField(db_column="subject", blank=True)),
                ("description", models.TextField(db_column="description", blank=True)),
                ("publisher", models.TextField(db_column="publisher", blank=True)),
                ("contributor", models.TextField(db_column="contributor", blank=True)),
                (
                    "date",
                    models.TextField(
                        help_text="Use ISO 8601 (YYYY-MM-DD or YYYY-MM-DD/YYYY-MM-DD)",
                        db_column="date",
                        blank=True,
                    ),
                ),
                ("type", models.TextField(db_column="type", blank=True)),
                ("format", models.TextField(db_column="format", blank=True)),
                ("identifier", models.TextField(db_column="identifier", blank=True)),
                ("source", models.TextField(db_column="source", blank=True)),
                ("relation", models.TextField(db_column="relation", blank=True)),
                (
                    "language",
                    models.TextField(
                        help_text="Use ISO 639", db_column="language", blank=True
                    ),
                ),
                ("coverage", models.TextField(db_column="coverage", blank=True)),
                ("rights", models.TextField(db_column="rights", blank=True)),
                (
                    "status",
                    models.CharField(
                        default="ORIGINAL",
                        max_length=8,
                        db_column="status",
                        choices=[
                            ("ORIGINAL", "original"),
                            ("REINGEST", "parsed from reingest"),
                            ("UPDATED", "updated"),
                        ],
                    ),
                ),
            ],
            options={"db_table": "Dublincore"},
        ),
        migrations.CreateModel(
            name="Event",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        editable=False,
                        primary_key=True,
                        db_column="pk",
                    ),
                ),
                (
                    "event_id",
                    models.UUIDField(
                        null=True,
                        db_column="eventIdentifierUUID",
                        editable=False,
                        max_length=36,
                        blank=True,
                        unique=True,
                        default=uuid.uuid4,
                    ),
                ),
                ("event_type", models.TextField(db_column="eventType", blank=True)),
                (
                    "event_datetime",
                    models.DateTimeField(auto_now=True, db_column="eventDateTime"),
                ),
                (
                    "event_detail",
                    models.TextField(db_column="eventDetail", blank=True),
                ),
                (
                    "event_outcome",
                    models.TextField(db_column="eventOutcome", blank=True),
                ),
                (
                    "event_outcome_detail",
                    models.TextField(db_column="eventOutcomeDetailNote", blank=True),
                ),
                ("agents", models.ManyToManyField(to="main.Agent")),
            ],
            options={"db_table": "Events"},
        ),
        migrations.CreateModel(
            name="File",
            fields=[
                (
                    "uuid",
                    models.CharField(
                        max_length=36,
                        serialize=False,
                        primary_key=True,
                        db_column="fileUUID",
                    ),
                ),
                (
                    "originallocation",
                    a3m.main.models.BlobTextField(db_column="originalLocation"),
                ),
                (
                    "currentlocation",
                    a3m.main.models.BlobTextField(
                        null=True, db_column="currentLocation"
                    ),
                ),
                (
                    "filegrpuse",
                    models.CharField(
                        default="Original", max_length=50, db_column="fileGrpUse"
                    ),
                ),
                (
                    "filegrpuuid",
                    models.CharField(
                        max_length=36, db_column="fileGrpUUID", blank=True
                    ),
                ),
                (
                    "checksum",
                    models.CharField(max_length=128, db_column="checksum", blank=True),
                ),
                (
                    "checksumtype",
                    models.CharField(
                        max_length=36, db_column="checksumType", blank=True
                    ),
                ),
                (
                    "size",
                    models.BigIntegerField(null=True, db_column="fileSize", blank=True),
                ),
                ("label", models.TextField(blank=True)),
                (
                    "modificationtime",
                    models.DateTimeField(
                        auto_now_add=True, null=True, db_column="modificationTime"
                    ),
                ),
                (
                    "enteredsystem",
                    models.DateTimeField(auto_now_add=True, db_column="enteredSystem"),
                ),
                (
                    "removedtime",
                    models.DateTimeField(
                        default=None, null=True, db_column="removedTime"
                    ),
                ),
            ],
            options={"db_table": "Files"},
        ),
        migrations.CreateModel(
            name="FileFormatVersion",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        editable=False,
                        primary_key=True,
                        db_column="pk",
                    ),
                ),
                (
                    "file_uuid",
                    models.ForeignKey(
                        to="main.File", db_column="fileUUID", on_delete=models.CASCADE
                    ),
                ),
                (
                    "format_version",
                    models.ForeignKey(
                        to="fpr.FormatVersion",
                        db_column="fileID",
                        to_field="uuid",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={"db_table": "FilesIdentifiedIDs"},
        ),
        migrations.CreateModel(
            name="FileID",
            fields=[
                (
                    "id",
                    models.AutoField(serialize=False, primary_key=True, db_column="pk"),
                ),
                ("format_name", models.TextField(db_column="formatName", blank=True)),
                (
                    "format_version",
                    models.TextField(db_column="formatVersion", blank=True),
                ),
                (
                    "format_registry_name",
                    models.TextField(db_column="formatRegistryName", blank=True),
                ),
                (
                    "format_registry_key",
                    models.TextField(db_column="formatRegistryKey", blank=True),
                ),
                (
                    "file",
                    models.ForeignKey(
                        db_column="fileUUID",
                        blank=True,
                        to="main.File",
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={"db_table": "FilesIDs"},
        ),
        migrations.CreateModel(
            name="FPCommandOutput",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("content", models.TextField(null=True)),
                (
                    "file",
                    models.ForeignKey(
                        to="main.File", db_column="fileUUID", on_delete=models.CASCADE
                    ),
                ),
                (
                    "rule",
                    models.ForeignKey(
                        to="fpr.FPRule",
                        db_column="ruleUUID",
                        to_field="uuid",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Identifier",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        editable=False,
                        primary_key=True,
                        db_column="pk",
                    ),
                ),
                ("type", models.TextField(null=True, verbose_name="Identifier Type")),
                (
                    "value",
                    models.TextField(
                        help_text="Used for premis:objectIdentifierType and premis:objectIdentifierValue in the METS file.",
                        null=True,
                        verbose_name="Identifier Value",
                    ),
                ),
            ],
            options={"db_table": "Identifiers"},
        ),
        migrations.CreateModel(
            name="Jo",
            fields=[
                (
                    "jobuuid",
                    models.UUIDField(
                        primary_key=True,
                        db_column="jobUUID",
                        serialize=False,
                        editable=False,
                        max_length=36,
                        blank=True,
                        default=uuid.uuid4,
                    ),
                ),
                (
                    "jobtype",
                    models.CharField(max_length=250, db_column="jobType", blank=True),
                ),
                ("createdtime", models.DateTimeField(db_column="createdTime")),
                (
                    "createdtimedec",
                    models.DecimalField(
                        default=0.0,
                        decimal_places=10,
                        max_digits=26,
                        db_column="createdTimeDec",
                    ),
                ),
                ("directory", models.TextField(blank=True)),
                (
                    "sipuuid",
                    models.CharField(max_length=36, db_column="SIPUUID", db_index=True),
                ),
                (
                    "unittype",
                    models.CharField(max_length=50, db_column="unitType", blank=True),
                ),
                (
                    "currentstep",
                    models.IntegerField(
                        default=0,
                        db_column="currentStep",
                        choices=[
                            (0, "Unknown"),
                            (1, "Awaiting decision"),
                            (2, "Completed successfully"),
                            (3, "Executing command(s)"),
                            (4, "Failed"),
                        ],
                    ),
                ),
                (
                    "microservicegroup",
                    models.CharField(
                        max_length=50, db_column="microserviceGroup", blank=True
                    ),
                ),
                ("hidden", models.BooleanField(default=False)),
                (
                    "microservicechainlink",
                    models.UUIDField(
                        max_length=36,
                        null=True,
                        editable=False,
                        db_column="MicroServiceChainLinksPK",
                        blank=True,
                        default=uuid.uuid4,
                    ),
                ),
            ],
            options={"db_table": "Jobs"},
        ),
        migrations.CreateModel(
            name="MetadataAppliesToType",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True,
                        db_column="pk",
                        serialize=False,
                        editable=False,
                        max_length=36,
                        blank=True,
                        default=uuid.uuid4,
                    ),
                ),
                (
                    "description",
                    models.CharField(max_length=50, db_column="description"),
                ),
                (
                    "replaces",
                    models.CharField(
                        max_length=36, null=True, db_column="replaces", blank=True
                    ),
                ),
                (
                    "lastmodified",
                    models.DateTimeField(auto_now=True, db_column="lastModified"),
                ),
            ],
            options={"db_table": "MetadataAppliesToTypes"},
        ),
        migrations.CreateModel(
            name="RightsStatement",
            fields=[
                (
                    "id",
                    models.AutoField(serialize=False, primary_key=True, db_column="pk"),
                ),
                (
                    "metadataappliestoidentifier",
                    models.CharField(
                        max_length=36,
                        db_column="metadataAppliesToidentifier",
                        blank=True,
                    ),
                ),
                (
                    "rightsstatementidentifiertype",
                    models.TextField(
                        verbose_name="Type",
                        db_column="rightsStatementIdentifierType",
                        blank=True,
                    ),
                ),
                (
                    "rightsstatementidentifiervalue",
                    models.TextField(
                        verbose_name="Value",
                        db_column="rightsStatementIdentifierValue",
                        blank=True,
                    ),
                ),
                (
                    "rightsholder",
                    models.IntegerField(
                        default=0, verbose_name="Rights holder", db_column="fkAgent"
                    ),
                ),
                (
                    "rightsbasis",
                    models.CharField(
                        default="Copyright",
                        max_length=64,
                        verbose_name="Basis",
                        db_column="rightsBasis",
                        choices=[
                            ("Copyright", "Copyright"),
                            ("Statute", "Statute"),
                            ("License", "License"),
                            ("Donor", "Donor"),
                            ("Policy", "Policy"),
                            ("Other", "Other"),
                        ],
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        default="ORIGINAL",
                        max_length=8,
                        db_column="status",
                        choices=[
                            ("ORIGINAL", "original"),
                            ("REINGEST", "parsed from reingest"),
                            ("UPDATED", "updated"),
                        ],
                    ),
                ),
                (
                    "metadataappliestotype",
                    models.ForeignKey(
                        to="main.MetadataAppliesToType",
                        db_column="metadataAppliesToType",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={"db_table": "RightsStatement", "verbose_name": "Rights Statement"},
        ),
        migrations.CreateModel(
            name="RightsStatementCopyright",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        editable=False,
                        primary_key=True,
                        db_column="pk",
                    ),
                ),
                (
                    "copyrightstatus",
                    models.TextField(
                        default="unknown",
                        verbose_name="Copyright status",
                        db_column="copyrightStatus",
                        choices=[
                            ("copyrighted", "copyrighted"),
                            ("public domain", "public domain"),
                            ("unknown", "unknown"),
                        ],
                    ),
                ),
                (
                    "copyrightjurisdiction",
                    models.TextField(
                        verbose_name="Copyright jurisdiction",
                        db_column="copyrightJurisdiction",
                    ),
                ),
                (
                    "copyrightstatusdeterminationdate",
                    models.TextField(
                        help_text="Use ISO 8061 (YYYY-MM-DD)",
                        null=True,
                        verbose_name="Copyright determination date",
                        db_column="copyrightStatusDeterminationDate",
                        blank=True,
                    ),
                ),
                (
                    "copyrightapplicablestartdate",
                    models.TextField(
                        help_text="Use ISO 8061 (YYYY-MM-DD)",
                        null=True,
                        verbose_name="Copyright start date",
                        db_column="copyrightApplicableStartDate",
                        blank=True,
                    ),
                ),
                (
                    "copyrightapplicableenddate",
                    models.TextField(
                        help_text="Use ISO 8061 (YYYY-MM-DD)",
                        null=True,
                        verbose_name="Copyright end date",
                        db_column="copyrightApplicableEndDate",
                        blank=True,
                    ),
                ),
                (
                    "copyrightenddateopen",
                    models.BooleanField(
                        default=False,
                        help_text="Indicate end date is open",
                        verbose_name="Open End Date",
                        db_column="copyrightApplicableEndDateOpen",
                    ),
                ),
                (
                    "rightsstatement",
                    models.ForeignKey(
                        to="main.RightsStatement",
                        db_column="fkRightsStatement",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "db_table": "RightsStatementCopyright",
                "verbose_name": "Rights: Copyright",
            },
        ),
        migrations.CreateModel(
            name="RightsStatementCopyrightDocumentationIdentifier",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        editable=False,
                        primary_key=True,
                        db_column="pk",
                    ),
                ),
                (
                    "copyrightdocumentationidentifiertype",
                    models.TextField(
                        verbose_name="Copyright document identification type",
                        db_column="copyrightDocumentationIdentifierType",
                    ),
                ),
                (
                    "copyrightdocumentationidentifiervalue",
                    models.TextField(
                        verbose_name="Copyright document identification value",
                        db_column="copyrightDocumentationIdentifierValue",
                    ),
                ),
                (
                    "copyrightdocumentationidentifierrole",
                    models.TextField(
                        null=True,
                        verbose_name="Copyright document identification role",
                        db_column="copyrightDocumentationIdentifierRole",
                        blank=True,
                    ),
                ),
                (
                    "rightscopyright",
                    models.ForeignKey(
                        to="main.RightsStatementCopyright",
                        db_column="fkRightsStatementCopyrightInformation",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "db_table": "RightsStatementCopyrightDocumentationIdentifier",
                "verbose_name": "Rights: Copyright: Docs ID",
            },
        ),
        migrations.CreateModel(
            name="RightsStatementCopyrightNote",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        editable=False,
                        primary_key=True,
                        db_column="pk",
                    ),
                ),
                (
                    "copyrightnote",
                    models.TextField(
                        verbose_name="Copyright note", db_column="copyrightNote"
                    ),
                ),
                (
                    "rightscopyright",
                    models.ForeignKey(
                        to="main.RightsStatementCopyright",
                        db_column="fkRightsStatementCopyrightInformation",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "db_table": "RightsStatementCopyrightNote",
                "verbose_name": "Rights: Copyright: Note",
            },
        ),
        migrations.CreateModel(
            name="RightsStatementLicense",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        editable=False,
                        primary_key=True,
                        db_column="pk",
                    ),
                ),
                (
                    "licenseterms",
                    models.TextField(
                        null=True,
                        verbose_name="License terms",
                        db_column="licenseTerms",
                        blank=True,
                    ),
                ),
                (
                    "licenseapplicablestartdate",
                    models.TextField(
                        help_text="Use ISO 8061 (YYYY-MM-DD)",
                        null=True,
                        verbose_name="License start date",
                        db_column="licenseApplicableStartDate",
                        blank=True,
                    ),
                ),
                (
                    "licenseapplicableenddate",
                    models.TextField(
                        help_text="Use ISO 8061 (YYYY-MM-DD)",
                        null=True,
                        verbose_name="License end date",
                        db_column="licenseApplicableEndDate",
                        blank=True,
                    ),
                ),
                (
                    "licenseenddateopen",
                    models.BooleanField(
                        default=False,
                        help_text="Indicate end date is open",
                        verbose_name="Open End Date",
                        db_column="licenseApplicableEndDateOpen",
                    ),
                ),
                (
                    "rightsstatement",
                    models.ForeignKey(
                        to="main.RightsStatement",
                        db_column="fkRightsStatement",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "db_table": "RightsStatementLicense",
                "verbose_name": "Rights: License",
            },
        ),
        migrations.CreateModel(
            name="RightsStatementLicenseDocumentationIdentifier",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        editable=False,
                        primary_key=True,
                        db_column="pk",
                    ),
                ),
                (
                    "licensedocumentationidentifiertype",
                    models.TextField(
                        verbose_name="License documentation identification type",
                        db_column="licenseDocumentationIdentifierType",
                    ),
                ),
                (
                    "licensedocumentationidentifiervalue",
                    models.TextField(
                        verbose_name="License documentation identification value",
                        db_column="licenseDocumentationIdentifierValue",
                    ),
                ),
                (
                    "licensedocumentationidentifierrole",
                    models.TextField(
                        null=True,
                        verbose_name="License document identification role",
                        db_column="licenseDocumentationIdentifierRole",
                        blank=True,
                    ),
                ),
                (
                    "rightsstatementlicense",
                    models.ForeignKey(
                        to="main.RightsStatementLicense",
                        db_column="fkRightsStatementLicense",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "db_table": "RightsStatementLicenseDocumentationIdentifier",
                "verbose_name": "Rights: License: Docs ID",
            },
        ),
        migrations.CreateModel(
            name="RightsStatementLicenseNote",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        editable=False,
                        primary_key=True,
                        db_column="pk",
                    ),
                ),
                (
                    "licensenote",
                    models.TextField(
                        verbose_name="License note", db_column="licenseNote"
                    ),
                ),
                (
                    "rightsstatementlicense",
                    models.ForeignKey(
                        to="main.RightsStatementLicense",
                        db_column="fkRightsStatementLicense",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "db_table": "RightsStatementLicenseNote",
                "verbose_name": "Rights: License: Note",
            },
        ),
        migrations.CreateModel(
            name="RightsStatementLinkingAgentIdentifier",
            fields=[
                (
                    "id",
                    models.AutoField(serialize=False, primary_key=True, db_column="pk"),
                ),
                (
                    "linkingagentidentifiertype",
                    models.TextField(
                        verbose_name="Linking Agent",
                        db_column="linkingAgentIdentifierType",
                        blank=True,
                    ),
                ),
                (
                    "linkingagentidentifiervalue",
                    models.TextField(
                        verbose_name="Linking Agent Value",
                        db_column="linkingAgentIdentifierValue",
                        blank=True,
                    ),
                ),
                (
                    "rightsstatement",
                    models.ForeignKey(
                        to="main.RightsStatement",
                        db_column="fkRightsStatement",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "db_table": "RightsStatementLinkingAgentIdentifier",
                "verbose_name": "Rights: Agent",
            },
        ),
        migrations.CreateModel(
            name="RightsStatementOtherRightsDocumentationIdentifier",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        editable=False,
                        primary_key=True,
                        db_column="pk",
                    ),
                ),
                (
                    "otherrightsdocumentationidentifiertype",
                    models.TextField(
                        verbose_name="Other rights document identification type",
                        db_column="otherRightsDocumentationIdentifierType",
                    ),
                ),
                (
                    "otherrightsdocumentationidentifiervalue",
                    models.TextField(
                        verbose_name="Other right document identification value",
                        db_column="otherRightsDocumentationIdentifierValue",
                    ),
                ),
                (
                    "otherrightsdocumentationidentifierrole",
                    models.TextField(
                        null=True,
                        verbose_name="Other rights document identification role",
                        db_column="otherRightsDocumentationIdentifierRole",
                        blank=True,
                    ),
                ),
            ],
            options={
                "db_table": "RightsStatementOtherRightsDocumentationIdentifier",
                "verbose_name": "Rights: Other: Docs ID",
            },
        ),
        migrations.CreateModel(
            name="RightsStatementOtherRightsInformation",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        editable=False,
                        primary_key=True,
                        db_column="pk",
                    ),
                ),
                (
                    "otherrightsbasis",
                    models.TextField(
                        default="Other",
                        verbose_name="Other rights basis",
                        db_column="otherRightsBasis",
                    ),
                ),
                (
                    "otherrightsapplicablestartdate",
                    models.TextField(
                        help_text="Use ISO 8061 (YYYY-MM-DD)",
                        null=True,
                        verbose_name="Other rights start date",
                        db_column="otherRightsApplicableStartDate",
                        blank=True,
                    ),
                ),
                (
                    "otherrightsapplicableenddate",
                    models.TextField(
                        help_text="Use ISO 8061 (YYYY-MM-DD)",
                        null=True,
                        verbose_name="Other rights end date",
                        db_column="otherRightsApplicableEndDate",
                        blank=True,
                    ),
                ),
                (
                    "otherrightsenddateopen",
                    models.BooleanField(
                        default=False,
                        help_text="Indicate end date is open",
                        verbose_name="Open End Date",
                        db_column="otherRightsApplicableEndDateOpen",
                    ),
                ),
                (
                    "rightsstatement",
                    models.ForeignKey(
                        to="main.RightsStatement",
                        db_column="fkRightsStatement",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "db_table": "RightsStatementOtherRightsInformation",
                "verbose_name": "Rights: Other",
            },
        ),
        migrations.CreateModel(
            name="RightsStatementOtherRightsInformationNote",
            fields=[
                (
                    "id",
                    models.AutoField(serialize=False, primary_key=True, db_column="pk"),
                ),
                (
                    "otherrightsnote",
                    models.TextField(
                        verbose_name="Other rights note", db_column="otherRightsNote"
                    ),
                ),
                (
                    "rightsstatementotherrights",
                    models.ForeignKey(
                        to="main.RightsStatementOtherRightsInformation",
                        db_column="fkRightsStatementOtherRightsInformation",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "db_table": "RightsStatementOtherRightsNote",
                "verbose_name": "Rights: Other: Note",
            },
        ),
        migrations.CreateModel(
            name="RightsStatementRightsGranted",
            fields=[
                (
                    "id",
                    models.AutoField(serialize=False, primary_key=True, db_column="pk"),
                ),
                ("act", models.TextField(db_column="act")),
                (
                    "startdate",
                    models.TextField(
                        help_text="Use ISO 8061 (YYYY-MM-DD)",
                        null=True,
                        verbose_name="Start",
                        db_column="startDate",
                        blank=True,
                    ),
                ),
                (
                    "enddate",
                    models.TextField(
                        help_text="Use ISO 8061 (YYYY-MM-DD)",
                        null=True,
                        verbose_name="End",
                        db_column="endDate",
                        blank=True,
                    ),
                ),
                (
                    "enddateopen",
                    models.BooleanField(
                        default=False,
                        help_text="Indicate end date is open",
                        verbose_name="Open End Date",
                        db_column="endDateOpen",
                    ),
                ),
                (
                    "rightsstatement",
                    models.ForeignKey(
                        to="main.RightsStatement",
                        db_column="fkRightsStatement",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "db_table": "RightsStatementRightsGranted",
                "verbose_name": "Rights: Granted",
            },
        ),
        migrations.CreateModel(
            name="RightsStatementRightsGrantedNote",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        editable=False,
                        primary_key=True,
                        db_column="pk",
                    ),
                ),
                (
                    "rightsgrantednote",
                    models.TextField(
                        verbose_name="Rights note", db_column="rightsGrantedNote"
                    ),
                ),
                (
                    "rightsgranted",
                    models.ForeignKey(
                        related_name="notes",
                        db_column="fkRightsStatementRightsGranted",
                        to="main.RightsStatementRightsGranted",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "db_table": "RightsStatementRightsGrantedNote",
                "verbose_name": "Rights: Granted: Note",
            },
        ),
        migrations.CreateModel(
            name="RightsStatementRightsGrantedRestriction",
            fields=[
                (
                    "id",
                    models.AutoField(serialize=False, primary_key=True, db_column="pk"),
                ),
                ("restriction", models.TextField(db_column="restriction")),
                (
                    "rightsgranted",
                    models.ForeignKey(
                        related_name="restrictions",
                        db_column="fkRightsStatementRightsGranted",
                        to="main.RightsStatementRightsGranted",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "db_table": "RightsStatementRightsGrantedRestriction",
                "verbose_name": "Rights: Granted: Restriction",
            },
        ),
        migrations.CreateModel(
            name="RightsStatementStatuteDocumentationIdentifier",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        editable=False,
                        primary_key=True,
                        db_column="pk",
                    ),
                ),
                (
                    "statutedocumentationidentifiertype",
                    models.TextField(
                        verbose_name="Statute document identification type",
                        db_column="statuteDocumentationIdentifierType",
                    ),
                ),
                (
                    "statutedocumentationidentifiervalue",
                    models.TextField(
                        verbose_name="Statute document identification value",
                        db_column="statuteDocumentationIdentifierValue",
                    ),
                ),
                (
                    "statutedocumentationidentifierrole",
                    models.TextField(
                        null=True,
                        verbose_name="Statute document identification role",
                        db_column="statuteDocumentationIdentifierRole",
                        blank=True,
                    ),
                ),
            ],
            options={
                "db_table": "RightsStatementStatuteDocumentationIdentifier",
                "verbose_name": "Rights: Statute: Docs ID",
            },
        ),
        migrations.CreateModel(
            name="RightsStatementStatuteInformation",
            fields=[
                (
                    "id",
                    models.AutoField(serialize=False, primary_key=True, db_column="pk"),
                ),
                (
                    "statutejurisdiction",
                    models.TextField(
                        verbose_name="Statute jurisdiction",
                        db_column="statuteJurisdiction",
                    ),
                ),
                (
                    "statutecitation",
                    models.TextField(
                        verbose_name="Statute citation", db_column="statuteCitation"
                    ),
                ),
                (
                    "statutedeterminationdate",
                    models.TextField(
                        help_text="Use ISO 8061 (YYYY-MM-DD)",
                        null=True,
                        verbose_name="Statute determination date",
                        db_column="statuteInformationDeterminationDate",
                        blank=True,
                    ),
                ),
                (
                    "statuteapplicablestartdate",
                    models.TextField(
                        help_text="Use ISO 8061 (YYYY-MM-DD)",
                        null=True,
                        verbose_name="Statute start date",
                        db_column="statuteApplicableStartDate",
                        blank=True,
                    ),
                ),
                (
                    "statuteapplicableenddate",
                    models.TextField(
                        help_text="Use ISO 8061 (YYYY-MM-DD)",
                        null=True,
                        verbose_name="Statute end date",
                        db_column="statuteApplicableEndDate",
                        blank=True,
                    ),
                ),
                (
                    "statuteenddateopen",
                    models.BooleanField(
                        default=False,
                        help_text="Indicate end date is open",
                        verbose_name="Open End Date",
                        db_column="statuteApplicableEndDateOpen",
                    ),
                ),
                (
                    "rightsstatement",
                    models.ForeignKey(
                        to="main.RightsStatement",
                        db_column="fkRightsStatement",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "db_table": "RightsStatementStatuteInformation",
                "verbose_name": "Rights: Statute",
            },
        ),
        migrations.CreateModel(
            name="RightsStatementStatuteInformationNote",
            fields=[
                (
                    "id",
                    models.AutoField(serialize=False, primary_key=True, db_column="pk"),
                ),
                (
                    "statutenote",
                    models.TextField(
                        verbose_name="Statute note", db_column="statuteNote"
                    ),
                ),
                (
                    "rightsstatementstatute",
                    models.ForeignKey(
                        to="main.RightsStatementStatuteInformation",
                        db_column="fkRightsStatementStatuteInformation",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "db_table": "RightsStatementStatuteInformationNote",
                "verbose_name": "Rights: Statute: Note",
            },
        ),
        migrations.CreateModel(
            name="SIP",
            fields=[
                (
                    "uuid",
                    models.CharField(
                        max_length=36,
                        serialize=False,
                        primary_key=True,
                        db_column="sipUUID",
                    ),
                ),
                (
                    "createdtime",
                    models.DateTimeField(auto_now_add=True, db_column="createdTime"),
                ),
                (
                    "currentpath",
                    models.TextField(null=True, db_column="currentPath", blank=True),
                ),
                ("hidden", models.BooleanField(default=False)),
                (
                    "aip_filename",
                    models.TextField(null=True, db_column="aipFilename", blank=True),
                ),
                (
                    "sip_type",
                    models.CharField(
                        default="SIP",
                        max_length=8,
                        db_column="sipType",
                        choices=[
                            ("SIP", "SIP"),
                            ("AIC", "AIC"),
                            ("AIP-REIN", "Reingested AIP"),
                            ("AIC-REIN", "Reingested AIC"),
                        ],
                    ),
                ),
                ("diruuids", models.BooleanField(default=False, db_column="dirUUIDs")),
                ("identifiers", models.ManyToManyField(to="main.Identifier")),
            ],
            options={"db_table": "SIPs"},
        ),
        migrations.CreateModel(
            name="Task",
            fields=[
                (
                    "taskuuid",
                    models.CharField(
                        max_length=36,
                        serialize=False,
                        primary_key=True,
                        db_column="taskUUID",
                    ),
                ),
                ("createdtime", models.DateTimeField(db_column="createdTime")),
                (
                    "fileuuid",
                    models.CharField(
                        max_length=36, null=True, db_column="fileUUID", blank=True
                    ),
                ),
                ("filename", models.TextField(db_column="fileName", blank=True)),
                (
                    "execution",
                    models.CharField(max_length=250, db_column="exec", blank=True),
                ),
                ("arguments", models.CharField(max_length=1000, blank=True)),
                (
                    "starttime",
                    models.DateTimeField(
                        default=None, null=True, db_column="startTime"
                    ),
                ),
                (
                    "endtime",
                    models.DateTimeField(default=None, null=True, db_column="endTime"),
                ),
                ("client", models.CharField(max_length=50, blank=True)),
                ("stdout", models.TextField(db_column="stdOut", blank=True)),
                ("stderror", models.TextField(db_column="stdError", blank=True)),
                (
                    "exitcode",
                    models.BigIntegerField(null=True, db_column="exitCode", blank=True),
                ),
                (
                    "jo",
                    models.ForeignKey(
                        to="main.Jo", db_column="jobuuid", on_delete=models.CASCADE
                    ),
                ),
            ],
            options={"db_table": "Tasks"},
        ),
        migrations.CreateModel(
            name="Taxonomy",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True,
                        db_column="pk",
                        serialize=False,
                        editable=False,
                        max_length=36,
                        blank=True,
                        default=uuid.uuid4,
                    ),
                ),
                (
                    "createdtime",
                    models.DateTimeField(
                        auto_now_add=True, null=True, db_column="createdTime"
                    ),
                ),
                (
                    "name",
                    models.CharField(max_length=255, db_column="name", blank=True),
                ),
                ("type", models.CharField(default="open", max_length=50)),
            ],
            options={"db_table": "Taxonomies"},
        ),
        migrations.CreateModel(
            name="TaxonomyTerm",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True,
                        db_column="pk",
                        serialize=False,
                        editable=False,
                        max_length=36,
                        blank=True,
                        default=uuid.uuid4,
                    ),
                ),
                (
                    "createdtime",
                    models.DateTimeField(
                        auto_now_add=True, null=True, db_column="createdTime"
                    ),
                ),
                ("term", models.CharField(max_length=255, db_column="term")),
                (
                    "taxonomy",
                    models.ForeignKey(
                        to="main.Taxonomy",
                        db_column="taxonomyUUID",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={"db_table": "TaxonomyTerms"},
        ),
        migrations.CreateModel(
            name="Transfer",
            fields=[
                (
                    "uuid",
                    models.CharField(
                        max_length=36,
                        serialize=False,
                        primary_key=True,
                        db_column="transferUUID",
                    ),
                ),
                ("currentlocation", models.TextField(db_column="currentLocation")),
                ("type", models.CharField(max_length=50, db_column="type")),
                ("accessionid", models.TextField(db_column="accessionID")),
                (
                    "sourceofacquisition",
                    models.TextField(db_column="sourceOfAcquisition", blank=True),
                ),
                (
                    "typeoftransfer",
                    models.TextField(db_column="typeOfTransfer", blank=True),
                ),
                ("description", models.TextField(blank=True)),
                ("notes", models.TextField(blank=True)),
                ("access_system_id", models.TextField(db_column="access_system_id")),
                ("hidden", models.BooleanField(default=False)),
                ("diruuids", models.BooleanField(default=False, db_column="dirUUIDs")),
            ],
            options={"db_table": "Transfers"},
        ),
        migrations.CreateModel(
            name="TransferMetadataField",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True,
                        db_column="pk",
                        serialize=False,
                        editable=False,
                        max_length=36,
                        blank=True,
                        default=uuid.uuid4,
                    ),
                ),
                (
                    "createdtime",
                    models.DateTimeField(
                        auto_now_add=True, null=True, db_column="createdTime"
                    ),
                ),
                (
                    "fieldlabel",
                    models.CharField(max_length=50, db_column="fieldLabel", blank=True),
                ),
                ("fieldname", models.CharField(max_length=50, db_column="fieldName")),
                ("fieldtype", models.CharField(max_length=50, db_column="fieldType")),
                ("sortorder", models.IntegerField(default=0, db_column="sortOrder")),
                (
                    "optiontaxonomy",
                    models.ForeignKey(
                        db_column="optionTaxonomyUUID",
                        to="main.Taxonomy",
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={"db_table": "TransferMetadataFields"},
        ),
        migrations.CreateModel(
            name="TransferMetadataFieldValue",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True,
                        db_column="pk",
                        serialize=False,
                        editable=False,
                        max_length=36,
                        blank=True,
                        default=uuid.uuid4,
                    ),
                ),
                (
                    "createdtime",
                    models.DateTimeField(auto_now_add=True, db_column="createdTime"),
                ),
                ("fieldvalue", models.TextField(db_column="fieldValue", blank=True)),
                (
                    "field",
                    models.ForeignKey(
                        to="main.TransferMetadataField",
                        db_column="fieldUUID",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={"db_table": "TransferMetadataFieldValues"},
        ),
        migrations.CreateModel(
            name="TransferMetadataSet",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True,
                        db_column="pk",
                        serialize=False,
                        editable=False,
                        max_length=36,
                        blank=True,
                        default=uuid.uuid4,
                    ),
                ),
                (
                    "createdtime",
                    models.DateTimeField(auto_now_add=True, db_column="createdTime"),
                ),
                ("createdbyuserid", models.IntegerField(db_column="createdByUserID")),
            ],
            options={"db_table": "TransferMetadataSets"},
        ),
        migrations.CreateModel(
            name="UnitVariable",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True,
                        db_column="pk",
                        serialize=False,
                        editable=False,
                        max_length=36,
                        blank=True,
                        default=uuid.uuid4,
                    ),
                ),
                (
                    "unittype",
                    models.CharField(
                        max_length=50, null=True, db_column="unitType", blank=True
                    ),
                ),
                (
                    "unituuid",
                    models.CharField(
                        help_text="Semantically a foreign key to SIP or Transfer",
                        max_length=36,
                        null=True,
                        db_column="unitUUID",
                    ),
                ),
                ("variable", models.TextField(null=True, db_column="variable")),
                (
                    "variablevalue",
                    models.TextField(null=True, db_column="variableValue"),
                ),
                (
                    "microservicechainlink",
                    models.UUIDField(
                        max_length=36,
                        null=True,
                        editable=False,
                        db_column="microServiceChainLink",
                        blank=True,
                        default=uuid.uuid4,
                    ),
                ),
                (
                    "createdtime",
                    models.DateTimeField(auto_now_add=True, db_column="createdTime"),
                ),
                (
                    "updatedtime",
                    models.DateTimeField(auto_now=True, db_column="updatedTime"),
                ),
            ],
            options={"db_table": "UnitVariables"},
        ),
        migrations.CreateModel(
            name="UserProfile",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "system_emails",
                    models.BooleanField(
                        default=True,
                        help_text="If checked, this user will receive system emails, such as Transfer Fail and Normalization Reports.",
                        verbose_name="Send system emails?",
                    ),
                ),
                (
                    "agent",
                    models.OneToOneField(to="main.Agent", on_delete=models.CASCADE),
                ),
                (
                    "user",
                    models.OneToOneField(
                        to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE
                    ),
                ),
            ],
            options={"db_table": "main_userprofile"},
        ),
        migrations.AddField(
            model_name="transfermetadatafieldvalue",
            name="set",
            field=models.ForeignKey(
                to="main.TransferMetadataSet",
                db_column="setUUID",
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="transfer",
            name="transfermetadatasetrow",
            field=models.ForeignKey(
                db_column="transferMetadataSetRowUUID",
                blank=True,
                to="main.TransferMetadataSet",
                null=True,
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="rightsstatementstatutedocumentationidentifier",
            name="rightsstatementstatute",
            field=models.ForeignKey(
                to="main.RightsStatementStatuteInformation",
                db_column="fkRightsStatementStatuteInformation",
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="rightsstatementotherrightsdocumentationidentifier",
            name="rightsstatementotherrights",
            field=models.ForeignKey(
                to="main.RightsStatementOtherRightsInformation",
                db_column="fkRightsStatementOtherRightsInformation",
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AlterIndexTogether(
            name="jo",
            index_together=set(
                [
                    ("sipuuid", "createdtime", "createdtimedec"),
                    (
                        "sipuuid",
                        "currentstep",
                        "microservicegroup",
                        "microservicechainlink",
                    ),
                    ("sipuuid", "jobtype", "createdtime", "createdtimedec"),
                    ("jobtype", "currentstep"),
                ]
            ),
        ),
        migrations.AddField(
            model_name="file",
            name="identifiers",
            field=models.ManyToManyField(to="main.Identifier"),
        ),
        migrations.AddField(
            model_name="file",
            name="sip",
            field=models.ForeignKey(
                db_column="sipUUID",
                blank=True,
                to="main.SIP",
                null=True,
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="file",
            name="transfer",
            field=models.ForeignKey(
                db_column="transferUUID",
                blank=True,
                to="main.Transfer",
                null=True,
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="event",
            name="file_uuid",
            field=models.ForeignKey(
                db_column="fileUUID",
                blank=True,
                to="main.File",
                null=True,
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="dublincore",
            name="metadataappliestotype",
            field=models.ForeignKey(
                to="main.MetadataAppliesToType",
                db_column="metadataAppliesToType",
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="directory",
            name="identifiers",
            field=models.ManyToManyField(to="main.Identifier"),
        ),
        migrations.AddField(
            model_name="directory",
            name="sip",
            field=models.ForeignKey(
                db_column="sipUUID",
                blank=True,
                to="main.SIP",
                null=True,
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="directory",
            name="transfer",
            field=models.ForeignKey(
                db_column="transferUUID",
                blank=True,
                to="main.Transfer",
                null=True,
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="derivation",
            name="derived_file",
            field=models.ForeignKey(
                related_name="original_file_set",
                db_column="derivedFileUUID",
                to="main.File",
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="derivation",
            name="event",
            field=models.ForeignKey(
                db_column="relatedEventUUID",
                to_field="event_id",
                blank=True,
                to="main.Event",
                null=True,
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="derivation",
            name="source_file",
            field=models.ForeignKey(
                related_name="derived_file_set",
                db_column="sourceFileUUID",
                to="main.File",
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AlterIndexTogether(
            name="file", index_together=set([("sip", "filegrpuse")])
        ),
    ]
