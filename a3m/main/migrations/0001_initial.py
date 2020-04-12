# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import django_extensions.db.fields
import a3m.main.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('fpr', '0002_initial_data'),
    ]

    operations = [
        migrations.CreateModel(
            name='Agent',
            fields=[
                ('id', models.AutoField(serialize=False, editable=False, primary_key=True, db_column=b'pk')),
                ('identifiertype', models.TextField(null=True, verbose_name='Agent Identifier Type', db_column=b'agentIdentifierType')),
                ('identifiervalue', models.TextField(help_text='Used for premis:agentIdentifierValue and premis:linkingAgentIdentifierValue in the METS file.', null=True, verbose_name='Agent Identifier Value', db_column=b'agentIdentifierValue')),
                ('name', models.TextField(help_text='Used for premis:agentName in the METS file.', null=True, verbose_name='Agent Name', db_column=b'agentName')),
                ('agenttype', models.TextField(default=b'organization', help_text='Used for premis:agentType in the METS file.', verbose_name='Agent Type', db_column=b'agentType')),
            ],
            options={
                'db_table': 'Agents',
            },
        ),
        migrations.CreateModel(
            name='DashboardSetting',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, db_column=b'pk')),
                ('scope', models.CharField(max_length=255, blank=True)),
                ('name', models.CharField(max_length=255, db_column=b'name')),
                ('value', models.TextField(db_column=b'value', blank=True)),
                ('lastmodified', models.DateTimeField(auto_now=True, db_column=b'lastModified')),
            ],
            options={
                'db_table': 'DashboardSettings',
            },
            managers=[
                ('objects', a3m.main.models.DashboardSettingManager()),
            ],
        ),
        migrations.CreateModel(
            name='Derivation',
            fields=[
                ('id', models.AutoField(serialize=False, editable=False, primary_key=True, db_column=b'pk')),
            ],
            options={
                'db_table': 'Derivations',
            },
        ),
        migrations.CreateModel(
            name='Directory',
            fields=[
                ('uuid', models.CharField(max_length=36, serialize=False, primary_key=True, db_column=b'directoryUUID')),
                ('originallocation', a3m.main.models.BlobTextField(db_column=b'originalLocation')),
                ('currentlocation', a3m.main.models.BlobTextField(null=True, db_column=b'currentLocation')),
                ('enteredsystem', models.DateTimeField(auto_now_add=True, db_column=b'enteredSystem')),
            ],
            options={
                'db_table': 'Directories',
            },
        ),
        migrations.CreateModel(
            name='DublinCore',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, db_column=b'pk')),
                ('metadataappliestoidentifier', models.CharField(default=None, max_length=36, null=True, db_column=b'metadataAppliesToidentifier', blank=True)),
                ('title', models.TextField(db_column=b'title', blank=True)),
                ('is_part_of', models.TextField(help_text='Optional: leave blank if unsure', verbose_name='Part of AIC', db_column=b'isPartOf', blank=True)),
                ('creator', models.TextField(db_column=b'creator', blank=True)),
                ('subject', models.TextField(db_column=b'subject', blank=True)),
                ('description', models.TextField(db_column=b'description', blank=True)),
                ('publisher', models.TextField(db_column=b'publisher', blank=True)),
                ('contributor', models.TextField(db_column=b'contributor', blank=True)),
                ('date', models.TextField(help_text='Use ISO 8601 (YYYY-MM-DD or YYYY-MM-DD/YYYY-MM-DD)', db_column=b'date', blank=True)),
                ('type', models.TextField(db_column=b'type', blank=True)),
                ('format', models.TextField(db_column=b'format', blank=True)),
                ('identifier', models.TextField(db_column=b'identifier', blank=True)),
                ('source', models.TextField(db_column=b'source', blank=True)),
                ('relation', models.TextField(db_column=b'relation', blank=True)),
                ('language', models.TextField(help_text='Use ISO 639', db_column=b'language', blank=True)),
                ('coverage', models.TextField(db_column=b'coverage', blank=True)),
                ('rights', models.TextField(db_column=b'rights', blank=True)),
                ('status', models.CharField(default=b'ORIGINAL', max_length=8, db_column=b'status', choices=[(b'ORIGINAL', b'original'), (b'REINGEST', b'parsed from reingest'), (b'UPDATED', b'updated')])),
            ],
            options={
                'db_table': 'Dublincore',
            },
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(serialize=False, editable=False, primary_key=True, db_column=b'pk')),
                ('event_id', django_extensions.db.fields.UUIDField(null=True, db_column=b'eventIdentifierUUID', editable=False, max_length=36, blank=True, unique=True)),
                ('event_type', models.TextField(db_column=b'eventType', blank=True)),
                ('event_datetime', models.DateTimeField(auto_now=True, db_column=b'eventDateTime')),
                ('event_detail', models.TextField(db_column=b'eventDetail', blank=True)),
                ('event_outcome', models.TextField(db_column=b'eventOutcome', blank=True)),
                ('event_outcome_detail', models.TextField(db_column=b'eventOutcomeDetailNote', blank=True)),
                ('agents', models.ManyToManyField(to='main.Agent')),
            ],
            options={
                'db_table': 'Events',
            },
        ),
        migrations.CreateModel(
            name='File',
            fields=[
                ('uuid', models.CharField(max_length=36, serialize=False, primary_key=True, db_column=b'fileUUID')),
                ('originallocation', a3m.main.models.BlobTextField(db_column=b'originalLocation')),
                ('currentlocation', a3m.main.models.BlobTextField(null=True, db_column=b'currentLocation')),
                ('filegrpuse', models.CharField(default=b'Original', max_length=50, db_column=b'fileGrpUse')),
                ('filegrpuuid', models.CharField(max_length=36, db_column=b'fileGrpUUID', blank=True)),
                ('checksum', models.CharField(max_length=128, db_column=b'checksum', blank=True)),
                ('checksumtype', models.CharField(max_length=36, db_column=b'checksumType', blank=True)),
                ('size', models.BigIntegerField(null=True, db_column=b'fileSize', blank=True)),
                ('label', models.TextField(blank=True)),
                ('modificationtime', models.DateTimeField(auto_now_add=True, null=True, db_column=b'modificationTime')),
                ('enteredsystem', models.DateTimeField(auto_now_add=True, db_column=b'enteredSystem')),
                ('removedtime', models.DateTimeField(default=None, null=True, db_column=b'removedTime')),
            ],
            options={
                'db_table': 'Files',
            },
        ),
        migrations.CreateModel(
            name='FileFormatVersion',
            fields=[
                ('id', models.AutoField(serialize=False, editable=False, primary_key=True, db_column=b'pk')),
                ('file_uuid', models.ForeignKey(to='main.File', db_column=b'fileUUID')),
                ('format_version', models.ForeignKey(to='fpr.FormatVersion', db_column=b'fileID', to_field=b'uuid')),
            ],
            options={
                'db_table': 'FilesIdentifiedIDs',
            },
        ),
        migrations.CreateModel(
            name='FileID',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, db_column=b'pk')),
                ('format_name', models.TextField(db_column=b'formatName', blank=True)),
                ('format_version', models.TextField(db_column=b'formatVersion', blank=True)),
                ('format_registry_name', models.TextField(db_column=b'formatRegistryName', blank=True)),
                ('format_registry_key', models.TextField(db_column=b'formatRegistryKey', blank=True)),
                ('file', models.ForeignKey(db_column=b'fileUUID', blank=True, to='main.File', null=True)),
            ],
            options={
                'db_table': 'FilesIDs',
            },
        ),
        migrations.CreateModel(
            name='FPCommandOutput',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('content', models.TextField(null=True)),
                ('file', models.ForeignKey(to='main.File', db_column=b'fileUUID')),
                ('rule', models.ForeignKey(to='fpr.FPRule', db_column=b'ruleUUID', to_field=b'uuid')),
            ],
        ),
        migrations.CreateModel(
            name='Identifier',
            fields=[
                ('id', models.AutoField(serialize=False, editable=False, primary_key=True, db_column=b'pk')),
                ('type', models.TextField(null=True, verbose_name='Identifier Type')),
                ('value', models.TextField(help_text='Used for premis:objectIdentifierType and premis:objectIdentifierValue in the METS file.', null=True, verbose_name='Identifier Value')),
            ],
            options={
                'db_table': 'Identifiers',
            },
        ),
        migrations.CreateModel(
            name='Job',
            fields=[
                ('jobuuid', django_extensions.db.fields.UUIDField(primary_key=True, db_column=b'jobUUID', serialize=False, editable=False, max_length=36, blank=True)),
                ('jobtype', models.CharField(max_length=250, db_column=b'jobType', blank=True)),
                ('createdtime', models.DateTimeField(db_column=b'createdTime')),
                ('createdtimedec', models.DecimalField(default=0.0, decimal_places=10, max_digits=26, db_column=b'createdTimeDec')),
                ('directory', models.TextField(blank=True)),
                ('sipuuid', models.CharField(max_length=36, db_column=b'SIPUUID', db_index=True)),
                ('unittype', models.CharField(max_length=50, db_column=b'unitType', blank=True)),
                ('currentstep', models.IntegerField(default=0, db_column=b'currentStep', choices=[(0, 'Unknown'), (1, 'Awaiting decision'), (2, 'Completed successfully'), (3, 'Executing command(s)'), (4, 'Failed')])),
                ('microservicegroup', models.CharField(max_length=50, db_column=b'microserviceGroup', blank=True)),
                ('hidden', models.BooleanField(default=False)),
                ('microservicechainlink', django_extensions.db.fields.UUIDField(max_length=36, null=True, editable=False, db_column=b'MicroServiceChainLinksPK', blank=True)),
                ('subjobof', models.CharField(max_length=36, db_column=b'subJobOf', blank=True)),
            ],
            options={
                'db_table': 'Jobs',
            },
        ),
        migrations.CreateModel(
            name='MetadataAppliesToType',
            fields=[
                ('id', a3m.main.models.UUIDPkField(primary_key=True, db_column=b'pk', serialize=False, editable=False, max_length=36, blank=True)),
                ('description', models.CharField(max_length=50, db_column=b'description')),
                ('replaces', models.CharField(max_length=36, null=True, db_column=b'replaces', blank=True)),
                ('lastmodified', models.DateTimeField(auto_now=True, db_column=b'lastModified')),
            ],
            options={
                'db_table': 'MetadataAppliesToTypes',
            },
        ),
        migrations.CreateModel(
            name='RightsStatement',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, db_column=b'pk')),
                ('metadataappliestoidentifier', models.CharField(max_length=36, db_column=b'metadataAppliesToidentifier', blank=True)),
                ('rightsstatementidentifiertype', models.TextField(verbose_name='Type', db_column=b'rightsStatementIdentifierType', blank=True)),
                ('rightsstatementidentifiervalue', models.TextField(verbose_name='Value', db_column=b'rightsStatementIdentifierValue', blank=True)),
                ('rightsholder', models.IntegerField(default=0, verbose_name='Rights holder', db_column=b'fkAgent')),
                ('rightsbasis', models.CharField(default=b'Copyright', max_length=64, verbose_name='Basis', db_column=b'rightsBasis', choices=[(b'Copyright', 'Copyright'), (b'Statute', 'Statute'), (b'License', 'License'), (b'Donor', 'Donor'), (b'Policy', 'Policy'), (b'Other', 'Other')])),
                ('status', models.CharField(default=b'ORIGINAL', max_length=8, db_column=b'status', choices=[(b'ORIGINAL', b'original'), (b'REINGEST', b'parsed from reingest'), (b'UPDATED', b'updated')])),
                ('metadataappliestotype', models.ForeignKey(to='main.MetadataAppliesToType', db_column=b'metadataAppliesToType')),
            ],
            options={
                'db_table': 'RightsStatement',
                'verbose_name': 'Rights Statement',
            },
        ),
        migrations.CreateModel(
            name='RightsStatementCopyright',
            fields=[
                ('id', models.AutoField(serialize=False, editable=False, primary_key=True, db_column=b'pk')),
                ('copyrightstatus', models.TextField(default=b'unknown', verbose_name='Copyright status', db_column=b'copyrightStatus', choices=[(b'copyrighted', 'copyrighted'), (b'public domain', 'public domain'), (b'unknown', 'unknown')])),
                ('copyrightjurisdiction', models.TextField(verbose_name='Copyright jurisdiction', db_column=b'copyrightJurisdiction')),
                ('copyrightstatusdeterminationdate', models.TextField(help_text='Use ISO 8061 (YYYY-MM-DD)', null=True, verbose_name='Copyright determination date', db_column=b'copyrightStatusDeterminationDate', blank=True)),
                ('copyrightapplicablestartdate', models.TextField(help_text='Use ISO 8061 (YYYY-MM-DD)', null=True, verbose_name='Copyright start date', db_column=b'copyrightApplicableStartDate', blank=True)),
                ('copyrightapplicableenddate', models.TextField(help_text='Use ISO 8061 (YYYY-MM-DD)', null=True, verbose_name='Copyright end date', db_column=b'copyrightApplicableEndDate', blank=True)),
                ('copyrightenddateopen', models.BooleanField(default=False, help_text='Indicate end date is open', verbose_name='Open End Date', db_column=b'copyrightApplicableEndDateOpen')),
                ('rightsstatement', models.ForeignKey(to='main.RightsStatement', db_column=b'fkRightsStatement')),
            ],
            options={
                'db_table': 'RightsStatementCopyright',
                'verbose_name': 'Rights: Copyright',
            },
        ),
        migrations.CreateModel(
            name='RightsStatementCopyrightDocumentationIdentifier',
            fields=[
                ('id', models.AutoField(serialize=False, editable=False, primary_key=True, db_column=b'pk')),
                ('copyrightdocumentationidentifiertype', models.TextField(verbose_name='Copyright document identification type', db_column=b'copyrightDocumentationIdentifierType')),
                ('copyrightdocumentationidentifiervalue', models.TextField(verbose_name='Copyright document identification value', db_column=b'copyrightDocumentationIdentifierValue')),
                ('copyrightdocumentationidentifierrole', models.TextField(null=True, verbose_name='Copyright document identification role', db_column=b'copyrightDocumentationIdentifierRole', blank=True)),
                ('rightscopyright', models.ForeignKey(to='main.RightsStatementCopyright', db_column=b'fkRightsStatementCopyrightInformation')),
            ],
            options={
                'db_table': 'RightsStatementCopyrightDocumentationIdentifier',
                'verbose_name': 'Rights: Copyright: Docs ID',
            },
        ),
        migrations.CreateModel(
            name='RightsStatementCopyrightNote',
            fields=[
                ('id', models.AutoField(serialize=False, editable=False, primary_key=True, db_column=b'pk')),
                ('copyrightnote', models.TextField(verbose_name='Copyright note', db_column=b'copyrightNote')),
                ('rightscopyright', models.ForeignKey(to='main.RightsStatementCopyright', db_column=b'fkRightsStatementCopyrightInformation')),
            ],
            options={
                'db_table': 'RightsStatementCopyrightNote',
                'verbose_name': 'Rights: Copyright: Note',
            },
        ),
        migrations.CreateModel(
            name='RightsStatementLicense',
            fields=[
                ('id', models.AutoField(serialize=False, editable=False, primary_key=True, db_column=b'pk')),
                ('licenseterms', models.TextField(null=True, verbose_name='License terms', db_column=b'licenseTerms', blank=True)),
                ('licenseapplicablestartdate', models.TextField(help_text='Use ISO 8061 (YYYY-MM-DD)', null=True, verbose_name='License start date', db_column=b'licenseApplicableStartDate', blank=True)),
                ('licenseapplicableenddate', models.TextField(help_text='Use ISO 8061 (YYYY-MM-DD)', null=True, verbose_name='License end date', db_column=b'licenseApplicableEndDate', blank=True)),
                ('licenseenddateopen', models.BooleanField(default=False, help_text='Indicate end date is open', verbose_name='Open End Date', db_column=b'licenseApplicableEndDateOpen')),
                ('rightsstatement', models.ForeignKey(to='main.RightsStatement', db_column=b'fkRightsStatement')),
            ],
            options={
                'db_table': 'RightsStatementLicense',
                'verbose_name': 'Rights: License',
            },
        ),
        migrations.CreateModel(
            name='RightsStatementLicenseDocumentationIdentifier',
            fields=[
                ('id', models.AutoField(serialize=False, editable=False, primary_key=True, db_column=b'pk')),
                ('licensedocumentationidentifiertype', models.TextField(verbose_name='License documentation identification type', db_column=b'licenseDocumentationIdentifierType')),
                ('licensedocumentationidentifiervalue', models.TextField(verbose_name='License documentation identification value', db_column=b'licenseDocumentationIdentifierValue')),
                ('licensedocumentationidentifierrole', models.TextField(null=True, verbose_name='License document identification role', db_column=b'licenseDocumentationIdentifierRole', blank=True)),
                ('rightsstatementlicense', models.ForeignKey(to='main.RightsStatementLicense', db_column=b'fkRightsStatementLicense')),
            ],
            options={
                'db_table': 'RightsStatementLicenseDocumentationIdentifier',
                'verbose_name': 'Rights: License: Docs ID',
            },
        ),
        migrations.CreateModel(
            name='RightsStatementLicenseNote',
            fields=[
                ('id', models.AutoField(serialize=False, editable=False, primary_key=True, db_column=b'pk')),
                ('licensenote', models.TextField(verbose_name='License note', db_column=b'licenseNote')),
                ('rightsstatementlicense', models.ForeignKey(to='main.RightsStatementLicense', db_column=b'fkRightsStatementLicense')),
            ],
            options={
                'db_table': 'RightsStatementLicenseNote',
                'verbose_name': 'Rights: License: Note',
            },
        ),
        migrations.CreateModel(
            name='RightsStatementLinkingAgentIdentifier',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, db_column=b'pk')),
                ('linkingagentidentifiertype', models.TextField(verbose_name='Linking Agent', db_column=b'linkingAgentIdentifierType', blank=True)),
                ('linkingagentidentifiervalue', models.TextField(verbose_name='Linking Agent Value', db_column=b'linkingAgentIdentifierValue', blank=True)),
                ('rightsstatement', models.ForeignKey(to='main.RightsStatement', db_column=b'fkRightsStatement')),
            ],
            options={
                'db_table': 'RightsStatementLinkingAgentIdentifier',
                'verbose_name': 'Rights: Agent',
            },
        ),
        migrations.CreateModel(
            name='RightsStatementOtherRightsDocumentationIdentifier',
            fields=[
                ('id', models.AutoField(serialize=False, editable=False, primary_key=True, db_column=b'pk')),
                ('otherrightsdocumentationidentifiertype', models.TextField(verbose_name='Other rights document identification type', db_column=b'otherRightsDocumentationIdentifierType')),
                ('otherrightsdocumentationidentifiervalue', models.TextField(verbose_name='Other right document identification value', db_column=b'otherRightsDocumentationIdentifierValue')),
                ('otherrightsdocumentationidentifierrole', models.TextField(null=True, verbose_name='Other rights document identification role', db_column=b'otherRightsDocumentationIdentifierRole', blank=True)),
            ],
            options={
                'db_table': 'RightsStatementOtherRightsDocumentationIdentifier',
                'verbose_name': 'Rights: Other: Docs ID',
            },
        ),
        migrations.CreateModel(
            name='RightsStatementOtherRightsInformation',
            fields=[
                ('id', models.AutoField(serialize=False, editable=False, primary_key=True, db_column=b'pk')),
                ('otherrightsbasis', models.TextField(default=b'Other', verbose_name='Other rights basis', db_column=b'otherRightsBasis')),
                ('otherrightsapplicablestartdate', models.TextField(help_text='Use ISO 8061 (YYYY-MM-DD)', null=True, verbose_name='Other rights start date', db_column=b'otherRightsApplicableStartDate', blank=True)),
                ('otherrightsapplicableenddate', models.TextField(help_text='Use ISO 8061 (YYYY-MM-DD)', null=True, verbose_name='Other rights end date', db_column=b'otherRightsApplicableEndDate', blank=True)),
                ('otherrightsenddateopen', models.BooleanField(default=False, help_text='Indicate end date is open', verbose_name='Open End Date', db_column=b'otherRightsApplicableEndDateOpen')),
                ('rightsstatement', models.ForeignKey(to='main.RightsStatement', db_column=b'fkRightsStatement')),
            ],
            options={
                'db_table': 'RightsStatementOtherRightsInformation',
                'verbose_name': 'Rights: Other',
            },
        ),
        migrations.CreateModel(
            name='RightsStatementOtherRightsInformationNote',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, db_column=b'pk')),
                ('otherrightsnote', models.TextField(verbose_name='Other rights note', db_column=b'otherRightsNote')),
                ('rightsstatementotherrights', models.ForeignKey(to='main.RightsStatementOtherRightsInformation', db_column=b'fkRightsStatementOtherRightsInformation')),
            ],
            options={
                'db_table': 'RightsStatementOtherRightsNote',
                'verbose_name': 'Rights: Other: Note',
            },
        ),
        migrations.CreateModel(
            name='RightsStatementRightsGranted',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, db_column=b'pk')),
                ('act', models.TextField(db_column=b'act')),
                ('startdate', models.TextField(help_text='Use ISO 8061 (YYYY-MM-DD)', null=True, verbose_name='Start', db_column=b'startDate', blank=True)),
                ('enddate', models.TextField(help_text='Use ISO 8061 (YYYY-MM-DD)', null=True, verbose_name='End', db_column=b'endDate', blank=True)),
                ('enddateopen', models.BooleanField(default=False, help_text='Indicate end date is open', verbose_name='Open End Date', db_column=b'endDateOpen')),
                ('rightsstatement', models.ForeignKey(to='main.RightsStatement', db_column=b'fkRightsStatement')),
            ],
            options={
                'db_table': 'RightsStatementRightsGranted',
                'verbose_name': 'Rights: Granted',
            },
        ),
        migrations.CreateModel(
            name='RightsStatementRightsGrantedNote',
            fields=[
                ('id', models.AutoField(serialize=False, editable=False, primary_key=True, db_column=b'pk')),
                ('rightsgrantednote', models.TextField(verbose_name='Rights note', db_column=b'rightsGrantedNote')),
                ('rightsgranted', models.ForeignKey(related_name='notes', db_column=b'fkRightsStatementRightsGranted', to='main.RightsStatementRightsGranted')),
            ],
            options={
                'db_table': 'RightsStatementRightsGrantedNote',
                'verbose_name': 'Rights: Granted: Note',
            },
        ),
        migrations.CreateModel(
            name='RightsStatementRightsGrantedRestriction',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, db_column=b'pk')),
                ('restriction', models.TextField(db_column=b'restriction')),
                ('rightsgranted', models.ForeignKey(related_name='restrictions', db_column=b'fkRightsStatementRightsGranted', to='main.RightsStatementRightsGranted')),
            ],
            options={
                'db_table': 'RightsStatementRightsGrantedRestriction',
                'verbose_name': 'Rights: Granted: Restriction',
            },
        ),
        migrations.CreateModel(
            name='RightsStatementStatuteDocumentationIdentifier',
            fields=[
                ('id', models.AutoField(serialize=False, editable=False, primary_key=True, db_column=b'pk')),
                ('statutedocumentationidentifiertype', models.TextField(verbose_name='Statute document identification type', db_column=b'statuteDocumentationIdentifierType')),
                ('statutedocumentationidentifiervalue', models.TextField(verbose_name='Statute document identification value', db_column=b'statuteDocumentationIdentifierValue')),
                ('statutedocumentationidentifierrole', models.TextField(null=True, verbose_name='Statute document identification role', db_column=b'statuteDocumentationIdentifierRole', blank=True)),
            ],
            options={
                'db_table': 'RightsStatementStatuteDocumentationIdentifier',
                'verbose_name': 'Rights: Statute: Docs ID',
            },
        ),
        migrations.CreateModel(
            name='RightsStatementStatuteInformation',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, db_column=b'pk')),
                ('statutejurisdiction', models.TextField(verbose_name='Statute jurisdiction', db_column=b'statuteJurisdiction')),
                ('statutecitation', models.TextField(verbose_name='Statute citation', db_column=b'statuteCitation')),
                ('statutedeterminationdate', models.TextField(help_text='Use ISO 8061 (YYYY-MM-DD)', null=True, verbose_name='Statute determination date', db_column=b'statuteInformationDeterminationDate', blank=True)),
                ('statuteapplicablestartdate', models.TextField(help_text='Use ISO 8061 (YYYY-MM-DD)', null=True, verbose_name='Statute start date', db_column=b'statuteApplicableStartDate', blank=True)),
                ('statuteapplicableenddate', models.TextField(help_text='Use ISO 8061 (YYYY-MM-DD)', null=True, verbose_name='Statute end date', db_column=b'statuteApplicableEndDate', blank=True)),
                ('statuteenddateopen', models.BooleanField(default=False, help_text='Indicate end date is open', verbose_name='Open End Date', db_column=b'statuteApplicableEndDateOpen')),
                ('rightsstatement', models.ForeignKey(to='main.RightsStatement', db_column=b'fkRightsStatement')),
            ],
            options={
                'db_table': 'RightsStatementStatuteInformation',
                'verbose_name': 'Rights: Statute',
            },
        ),
        migrations.CreateModel(
            name='RightsStatementStatuteInformationNote',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, db_column=b'pk')),
                ('statutenote', models.TextField(verbose_name='Statute note', db_column=b'statuteNote')),
                ('rightsstatementstatute', models.ForeignKey(to='main.RightsStatementStatuteInformation', db_column=b'fkRightsStatementStatuteInformation')),
            ],
            options={
                'db_table': 'RightsStatementStatuteInformationNote',
                'verbose_name': 'Rights: Statute: Note',
            },
        ),
        migrations.CreateModel(
            name='SIP',
            fields=[
                ('uuid', models.CharField(max_length=36, serialize=False, primary_key=True, db_column=b'sipUUID')),
                ('createdtime', models.DateTimeField(auto_now_add=True, db_column=b'createdTime')),
                ('currentpath', models.TextField(null=True, db_column=b'currentPath', blank=True)),
                ('hidden', models.BooleanField(default=False)),
                ('aip_filename', models.TextField(null=True, db_column=b'aipFilename', blank=True)),
                ('sip_type', models.CharField(default=b'SIP', max_length=8, db_column=b'sipType', choices=[(b'SIP', 'SIP'), (b'AIC', 'AIC'), (b'AIP-REIN', 'Reingested AIP'), (b'AIC-REIN', 'Reingested AIC')])),
                ('diruuids', models.BooleanField(default=False, db_column=b'dirUUIDs')),
                ('identifiers', models.ManyToManyField(to='main.Identifier')),
            ],
            options={
                'db_table': 'SIPs',
            },
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('taskuuid', models.CharField(max_length=36, serialize=False, primary_key=True, db_column=b'taskUUID')),
                ('createdtime', models.DateTimeField(db_column=b'createdTime')),
                ('fileuuid', models.CharField(max_length=36, null=True, db_column=b'fileUUID', blank=True)),
                ('filename', models.TextField(db_column=b'fileName', blank=True)),
                ('execution', models.CharField(max_length=250, db_column=b'exec', blank=True)),
                ('arguments', models.CharField(max_length=1000, blank=True)),
                ('starttime', models.DateTimeField(default=None, null=True, db_column=b'startTime')),
                ('endtime', models.DateTimeField(default=None, null=True, db_column=b'endTime')),
                ('client', models.CharField(max_length=50, blank=True)),
                ('stdout', models.TextField(db_column=b'stdOut', blank=True)),
                ('stderror', models.TextField(db_column=b'stdError', blank=True)),
                ('exitcode', models.BigIntegerField(null=True, db_column=b'exitCode', blank=True)),
                ('job', models.ForeignKey(to='main.Job', db_column=b'jobuuid')),
            ],
            options={
                'db_table': 'Tasks',
            },
        ),
        migrations.CreateModel(
            name='Taxonomy',
            fields=[
                ('id', a3m.main.models.UUIDPkField(primary_key=True, db_column=b'pk', serialize=False, editable=False, max_length=36, blank=True)),
                ('createdtime', models.DateTimeField(auto_now_add=True, null=True, db_column=b'createdTime')),
                ('name', models.CharField(max_length=255, db_column=b'name', blank=True)),
                ('type', models.CharField(default=b'open', max_length=50)),
            ],
            options={
                'db_table': 'Taxonomies',
            },
        ),
        migrations.CreateModel(
            name='TaxonomyTerm',
            fields=[
                ('id', a3m.main.models.UUIDPkField(primary_key=True, db_column=b'pk', serialize=False, editable=False, max_length=36, blank=True)),
                ('createdtime', models.DateTimeField(auto_now_add=True, null=True, db_column=b'createdTime')),
                ('term', models.CharField(max_length=255, db_column=b'term')),
                ('taxonomy', models.ForeignKey(to='main.Taxonomy', db_column=b'taxonomyUUID')),
            ],
            options={
                'db_table': 'TaxonomyTerms',
            },
        ),
        migrations.CreateModel(
            name='Transfer',
            fields=[
                ('uuid', models.CharField(max_length=36, serialize=False, primary_key=True, db_column=b'transferUUID')),
                ('currentlocation', models.TextField(db_column=b'currentLocation')),
                ('type', models.CharField(max_length=50, db_column=b'type')),
                ('accessionid', models.TextField(db_column=b'accessionID')),
                ('sourceofacquisition', models.TextField(db_column=b'sourceOfAcquisition', blank=True)),
                ('typeoftransfer', models.TextField(db_column=b'typeOfTransfer', blank=True)),
                ('description', models.TextField(blank=True)),
                ('notes', models.TextField(blank=True)),
                ('access_system_id', models.TextField(db_column=b'access_system_id')),
                ('hidden', models.BooleanField(default=False)),
                ('diruuids', models.BooleanField(default=False, db_column=b'dirUUIDs')),
            ],
            options={
                'db_table': 'Transfers',
            },
        ),
        migrations.CreateModel(
            name='TransferMetadataField',
            fields=[
                ('id', a3m.main.models.UUIDPkField(primary_key=True, db_column=b'pk', serialize=False, editable=False, max_length=36, blank=True)),
                ('createdtime', models.DateTimeField(auto_now_add=True, null=True, db_column=b'createdTime')),
                ('fieldlabel', models.CharField(max_length=50, db_column=b'fieldLabel', blank=True)),
                ('fieldname', models.CharField(max_length=50, db_column=b'fieldName')),
                ('fieldtype', models.CharField(max_length=50, db_column=b'fieldType')),
                ('sortorder', models.IntegerField(default=0, db_column=b'sortOrder')),
                ('optiontaxonomy', models.ForeignKey(db_column=b'optionTaxonomyUUID', to='main.Taxonomy', null=True)),
            ],
            options={
                'db_table': 'TransferMetadataFields',
            },
        ),
        migrations.CreateModel(
            name='TransferMetadataFieldValue',
            fields=[
                ('id', a3m.main.models.UUIDPkField(primary_key=True, db_column=b'pk', serialize=False, editable=False, max_length=36, blank=True)),
                ('createdtime', models.DateTimeField(auto_now_add=True, db_column=b'createdTime')),
                ('fieldvalue', models.TextField(db_column=b'fieldValue', blank=True)),
                ('field', models.ForeignKey(to='main.TransferMetadataField', db_column=b'fieldUUID')),
            ],
            options={
                'db_table': 'TransferMetadataFieldValues',
            },
        ),
        migrations.CreateModel(
            name='TransferMetadataSet',
            fields=[
                ('id', a3m.main.models.UUIDPkField(primary_key=True, db_column=b'pk', serialize=False, editable=False, max_length=36, blank=True)),
                ('createdtime', models.DateTimeField(auto_now_add=True, db_column=b'createdTime')),
                ('createdbyuserid', models.IntegerField(db_column=b'createdByUserID')),
            ],
            options={
                'db_table': 'TransferMetadataSets',
            },
        ),
        migrations.CreateModel(
            name='UnitVariable',
            fields=[
                ('id', a3m.main.models.UUIDPkField(primary_key=True, db_column=b'pk', serialize=False, editable=False, max_length=36, blank=True)),
                ('unittype', models.CharField(max_length=50, null=True, db_column=b'unitType', blank=True)),
                ('unituuid', models.CharField(help_text='Semantically a foreign key to SIP or Transfer', max_length=36, null=True, db_column=b'unitUUID')),
                ('variable', models.TextField(null=True, db_column=b'variable')),
                ('variablevalue', models.TextField(null=True, db_column=b'variableValue')),
                ('microservicechainlink', django_extensions.db.fields.UUIDField(max_length=36, null=True, editable=False, db_column=b'microServiceChainLink', blank=True)),
                ('createdtime', models.DateTimeField(auto_now_add=True, db_column=b'createdTime')),
                ('updatedtime', models.DateTimeField(auto_now=True, db_column=b'updatedTime')),
            ],
            options={
                'db_table': 'UnitVariables',
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('system_emails', models.BooleanField(default=True, help_text='If checked, this user will receive system emails, such as Transfer Fail and Normalization Reports.', verbose_name='Send system emails?')),
                ('agent', models.OneToOneField(to='main.Agent')),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'main_userprofile',
            },
        ),
        migrations.AddField(
            model_name='transfermetadatafieldvalue',
            name='set',
            field=models.ForeignKey(to='main.TransferMetadataSet', db_column=b'setUUID'),
        ),
        migrations.AddField(
            model_name='transfer',
            name='transfermetadatasetrow',
            field=models.ForeignKey(db_column=b'transferMetadataSetRowUUID', blank=True, to='main.TransferMetadataSet', null=True),
        ),
        migrations.AddField(
            model_name='rightsstatementstatutedocumentationidentifier',
            name='rightsstatementstatute',
            field=models.ForeignKey(to='main.RightsStatementStatuteInformation', db_column=b'fkRightsStatementStatuteInformation'),
        ),
        migrations.AddField(
            model_name='rightsstatementotherrightsdocumentationidentifier',
            name='rightsstatementotherrights',
            field=models.ForeignKey(to='main.RightsStatementOtherRightsInformation', db_column=b'fkRightsStatementOtherRightsInformation'),
        ),
        migrations.AlterIndexTogether(
            name='job',
            index_together=set([('sipuuid', 'createdtime', 'createdtimedec'), ('sipuuid', 'currentstep', 'microservicegroup', 'microservicechainlink'), ('sipuuid', 'jobtype', 'createdtime', 'createdtimedec'), ('jobtype', 'currentstep')]),
        ),
        migrations.AddField(
            model_name='file',
            name='identifiers',
            field=models.ManyToManyField(to='main.Identifier'),
        ),
        migrations.AddField(
            model_name='file',
            name='sip',
            field=models.ForeignKey(db_column=b'sipUUID', blank=True, to='main.SIP', null=True),
        ),
        migrations.AddField(
            model_name='file',
            name='transfer',
            field=models.ForeignKey(db_column=b'transferUUID', blank=True, to='main.Transfer', null=True),
        ),
        migrations.AddField(
            model_name='event',
            name='file_uuid',
            field=models.ForeignKey(db_column=b'fileUUID', blank=True, to='main.File', null=True),
        ),
        migrations.AddField(
            model_name='dublincore',
            name='metadataappliestotype',
            field=models.ForeignKey(to='main.MetadataAppliesToType', db_column=b'metadataAppliesToType'),
        ),
        migrations.AddField(
            model_name='directory',
            name='identifiers',
            field=models.ManyToManyField(to='main.Identifier'),
        ),
        migrations.AddField(
            model_name='directory',
            name='sip',
            field=models.ForeignKey(db_column=b'sipUUID', blank=True, to='main.SIP', null=True),
        ),
        migrations.AddField(
            model_name='directory',
            name='transfer',
            field=models.ForeignKey(db_column=b'transferUUID', blank=True, to='main.Transfer', null=True),
        ),
        migrations.AddField(
            model_name='derivation',
            name='derived_file',
            field=models.ForeignKey(related_name='original_file_set', db_column=b'derivedFileUUID', to='main.File'),
        ),
        migrations.AddField(
            model_name='derivation',
            name='event',
            field=models.ForeignKey(db_column=b'relatedEventUUID', to_field=b'event_id', blank=True, to='main.Event', null=True),
        ),
        migrations.AddField(
            model_name='derivation',
            name='source_file',
            field=models.ForeignKey(related_name='derived_file_set', db_column=b'sourceFileUUID', to='main.File'),
        ),
        migrations.AlterIndexTogether(
            name='file',
            index_together=set([('sip', 'filegrpuse')]),
        ),
    ]
