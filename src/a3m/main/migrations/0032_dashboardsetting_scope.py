# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import ast

from django.db import migrations, models

from main.models import DashboardSetting, DashboardSettingManager, Job


def data_migration_atom_to_dict(apps, schema_editor):
    """
    Convert old settings into a new DashboardSetting dict, e.g. in the
    scenario where the user had the following settings in the previous form:

        +--------------------------+-----------------------+
        | name                     | value                 |
        +--------------------------+-----------------------+
        | dip_upload_atom_url      | http://localhost/atom |
        | dip_upload_atom_email    | demo@example.com      |
        | dip_upload_atom_password | demo                  |
        | dip_upload_atom_version  | 2                     |
        +--------------------------+-----------------------+

    We're going to convert them into:

        +---------------+-----------------------+-------------------+
        | name          | value                 | scope             |
        +---------------+-----------------------+-------------------+
        | url           | http://localhost/atom | upload-qubit_v0.0 |
        | version       | 2                     | upload-qubit_v0.0 |
        | password      | demo                  | upload-qubit_v0.0 |
        | email         | demo@example.com      | upload-qubit_v0.0 |
        | debug         |                       | upload-qubit_v0.0 |
        | rsync_target  |                       | upload-qubit_v0.0 |
        | rsync_command |                       | upload-qubit_v0.0 |
        | key           |                       | upload-qubit_v0.0 |
        +---------------+-----------------------+-------------------+
                                        * Blank means empty string.

    """

    old_prefix = "dip_upload_atom_"
    fields = (
        "url",
        "email",
        "password",
        "rsync_target",
        "rsync_command",
        "version",
        "debug",
        "key",
    )

    qs = apps.get_model("main", "DashboardSetting").objects.filter(
        name__in=["{}{}".format(old_prefix, field) for field in fields]
    )
    old_dict = dict(qs.values_list("name", "value"))
    new_dict = {
        field: old_dict.get("{}{}".format(old_prefix, field)) for field in fields
    }

    # Set new dict and delete previous tuples. Reminder: migrations run inside
    # a transaction.
    DashboardSetting.objects.set_dict("upload-qubit_v0.0", new_dict)
    qs.delete()


def data_migration_atom_restore_std(apps, schema_editor):
    """
    Restore StandardTaskConfig arguments (we were ovewriting) and update the
    "Upload DIP to AtoM" chains to make use of MicroServiceChoiceReplacementDic
    as we do in AS/ATK uploads.
    """
    StandardTaskConfig = apps.get_model("main", "StandardTaskConfig")
    std = StandardTaskConfig.objects.get(execute="upload-qubit_v0.0")
    std.arguments = '--url="%url%"  --email="%email%" --password="%password%" --uuid="%SIPUUID%" --debug="%debug%" --version="%version%" --rsync-command="%rsync_command%" --rsync-target="%rsync_target%"'
    std.save()

    MicroServiceChainLink = apps.get_model("main", "MicroServiceChainLink")
    MicroServiceChain = apps.get_model("main", "MicroServiceChain")
    MicroServiceChainLinkExitCode = apps.get_model(
        "main", "MicroServiceChainLinkExitCode"
    )
    TaskConfig = apps.get_model("main", "TaskConfig")

    # New UUIDs for a new MSCL, its TaskConfig, and its exit code
    uuids = (
        "7f975ba6-2185-434c-b507-2911f3c77213",
        "a987e8d6-e633-4551-a082-2334a300fa72",
        "c9e90d83-533f-44c3-8220-083a6eb91751",
    )

    # Create new MSCL
    new_mscl = MicroServiceChainLink.objects.create(
        id=uuids[0],
        microservicegroup="Upload DIP",
        defaultexitmessage=Job.STATUS_FAILED,
        defaultnextchainlink_id="651236d2-d77f-4ca7-bfe9-6332e96608ff",
        currenttask=TaskConfig.objects.create(
            id=uuids[1],
            tasktypepkreference="",
            description="Choose config for AtoM DIP upload",
            tasktype_id="9c84b047-9a6d-463f-9836-eafa49743b84",
        ),  # linkTaskManagerReplacementDicFromChoice
    )

    # Create new exit code
    MicroServiceChainLinkExitCode.objects.create(
        id=uuids[2],
        microservicechainlink=new_mscl,
        nextmicroservicechainlink_id="651236d2-d77f-4ca7-bfe9-6332e96608ff",
    )

    # Update MSC
    MicroServiceChain.objects.filter(
        pk="0fe9842f-9519-4067-a691-8a363132ae24", description="Upload DIP to Atom"
    ).update(
        description="Upload DIP to AtoM",  # Cosmetic change (s/Atom/AtoM)
        startinglink=new_mscl,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0031_job_currentstep_choices"),
    ]

    operations = [
        migrations.AddField(
            model_name="dashboardsetting",
            name="scope",
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterModelManagers(
            name="dashboardsetting", managers=[("objects", DashboardSettingManager())]
        ),
        migrations.RunPython(data_migration_atom_to_dict),
        migrations.RunPython(data_migration_atom_restore_std),
    ]
