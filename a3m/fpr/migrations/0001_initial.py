# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

import autoslug.fields
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Format",
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
                    "uuid",
                    models.UUIDField(
                        help_text="Unique identifier",
                        unique=True,
                        max_length=36,
                        editable=False,
                        blank=True,
                    ),
                ),
                (
                    "description",
                    models.CharField(
                        help_text="Common name of format",
                        max_length=128,
                        verbose_name="description",
                    ),
                ),
                (
                    "slug",
                    autoslug.fields.AutoSlugField(
                        editable=False,
                        populate_from="description",
                        unique=True,
                        verbose_name="slug",
                    ),
                ),
            ],
            options={"ordering": ["group", "description"], "verbose_name": "Format"},
        ),
        migrations.CreateModel(
            name="FormatGroup",
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
                    "uuid",
                    models.UUIDField(
                        help_text="Unique identifier",
                        unique=True,
                        max_length=36,
                        editable=False,
                        blank=True,
                    ),
                ),
                (
                    "description",
                    models.CharField(max_length=128, verbose_name="description"),
                ),
                (
                    "slug",
                    autoslug.fields.AutoSlugField(
                        editable=False,
                        populate_from="description",
                        unique=True,
                        verbose_name="slug",
                    ),
                ),
            ],
            options={"ordering": ["description"], "verbose_name": "Format group"},
        ),
        migrations.CreateModel(
            name="FormatVersion",
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
                ("enabled", models.BooleanField(default=True, verbose_name="enabled")),
                (
                    "lastmodified",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="last modified"
                    ),
                ),
                (
                    "uuid",
                    models.UUIDField(
                        help_text="Unique identifier",
                        unique=True,
                        max_length=36,
                        editable=False,
                        blank=True,
                    ),
                ),
                (
                    "version",
                    models.CharField(
                        max_length=10, null=True, verbose_name="version", blank=True
                    ),
                ),
                (
                    "pronom_id",
                    models.CharField(
                        max_length=32, null=True, verbose_name="pronom id", blank=True
                    ),
                ),
                (
                    "description",
                    models.CharField(
                        help_text="Formal name to go in the METS file.",
                        max_length=128,
                        null=True,
                        verbose_name="description",
                        blank=True,
                    ),
                ),
                (
                    "access_format",
                    models.BooleanField(default=False, verbose_name="access format"),
                ),
                (
                    "preservation_format",
                    models.BooleanField(
                        default=False, verbose_name="preservation format"
                    ),
                ),
                (
                    "slug",
                    autoslug.fields.AutoSlugField(
                        always_update=True,
                        populate_from="description",
                        unique_with=("format",),
                        editable=False,
                    ),
                ),
                (
                    "format",
                    models.ForeignKey(
                        related_name="version_set",
                        verbose_name="the related format",
                        to_field="uuid",
                        to="fpr.Format",
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
                (
                    "replaces",
                    models.ForeignKey(
                        verbose_name="the related model",
                        to_field="uuid",
                        blank=True,
                        to="fpr.FormatVersion",
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "ordering": ["format", "description"],
                "verbose_name": "Format version",
            },
        ),
        migrations.CreateModel(
            name="FPCommand",
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
                ("enabled", models.BooleanField(default=True, verbose_name="enabled")),
                (
                    "lastmodified",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="last modified"
                    ),
                ),
                (
                    "uuid",
                    models.UUIDField(
                        help_text="Unique identifier",
                        unique=True,
                        max_length=36,
                        editable=False,
                        blank=True,
                    ),
                ),
                (
                    "description",
                    models.CharField(max_length=256, verbose_name="description"),
                ),
                ("command", models.TextField(verbose_name="command")),
                (
                    "script_type",
                    models.CharField(
                        max_length=16,
                        verbose_name="script type",
                        choices=[
                            ("bashScript", "Bash script"),
                            ("pythonScript", "Python script"),
                            ("command", "Command line"),
                            ("as_is", "No shebang needed"),
                        ],
                    ),
                ),
                (
                    "output_location",
                    models.TextField(
                        null=True, verbose_name="output location", blank=True
                    ),
                ),
                (
                    "command_usage",
                    models.CharField(
                        max_length=16,
                        verbose_name="command usage",
                        choices=[
                            ("characterization", "Characterization"),
                            ("event_detail", "Event Detail"),
                            ("extraction", "Extraction"),
                            ("normalization", "Normalization"),
                            ("transcription", "Transcription"),
                            ("validation", "Validation"),
                            ("verification", "Verification"),
                        ],
                    ),
                ),
                (
                    "event_detail_command",
                    models.ForeignKey(
                        related_name="+",
                        verbose_name="the related event detail command",
                        to_field="uuid",
                        blank=True,
                        to="fpr.FPCommand",
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
                (
                    "output_format",
                    models.ForeignKey(
                        verbose_name="the related output format",
                        to_field="uuid",
                        blank=True,
                        to="fpr.FormatVersion",
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
                (
                    "replaces",
                    models.ForeignKey(
                        verbose_name="the related model",
                        to_field="uuid",
                        blank=True,
                        to="fpr.FPCommand",
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "ordering": ["description"],
                "verbose_name": "Format policy command",
            },
        ),
        migrations.CreateModel(
            name="FPRule",
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
                ("enabled", models.BooleanField(default=True, verbose_name="enabled")),
                (
                    "lastmodified",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="last modified"
                    ),
                ),
                (
                    "uuid",
                    models.UUIDField(
                        help_text="Unique identifier",
                        unique=True,
                        max_length=36,
                        editable=False,
                        blank=True,
                    ),
                ),
                (
                    "purpose",
                    models.CharField(
                        max_length=32,
                        verbose_name="purpose",
                        choices=[
                            ("access", "Access"),
                            ("characterization", "Characterization"),
                            ("extract", "Extract"),
                            ("preservation", "Preservation"),
                            ("thumbnail", "Thumbnail"),
                            ("transcription", "Transcription"),
                            ("validation", "Validation"),
                            ("policy_check", "Validation against a policy"),
                            ("default_access", "Default access"),
                            ("default_characterization", "Default characterization"),
                            ("default_thumbnail", "Default thumbnail"),
                        ],
                    ),
                ),
                (
                    "count_attempts",
                    models.IntegerField(default=0, verbose_name="count attempts"),
                ),
                (
                    "count_okay",
                    models.IntegerField(default=0, verbose_name="count okay"),
                ),
                (
                    "count_not_okay",
                    models.IntegerField(default=0, verbose_name="count not okay"),
                ),
                (
                    "command",
                    models.ForeignKey(
                        to="fpr.FPCommand",
                        to_field="uuid",
                        verbose_name="the related command",
                        on_delete=models.CASCADE,
                    ),
                ),
                (
                    "format",
                    models.ForeignKey(
                        to="fpr.FormatVersion",
                        to_field="uuid",
                        verbose_name="the related format",
                        on_delete=models.CASCADE,
                    ),
                ),
                (
                    "replaces",
                    models.ForeignKey(
                        verbose_name="the related model",
                        to_field="uuid",
                        blank=True,
                        to="fpr.FPRule",
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={"verbose_name": "Format policy rule"},
        ),
        migrations.CreateModel(
            name="FPTool",
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
                    "uuid",
                    models.UUIDField(
                        help_text="Unique identifier",
                        unique=True,
                        max_length=36,
                        editable=False,
                        blank=True,
                    ),
                ),
                (
                    "description",
                    models.CharField(
                        help_text="Name of tool",
                        max_length=256,
                        verbose_name="description",
                    ),
                ),
                ("version", models.CharField(max_length=64, verbose_name="version")),
                ("enabled", models.BooleanField(default=True, verbose_name="enabled")),
                (
                    "slug",
                    autoslug.fields.AutoSlugField(
                        editable=False,
                        populate_from="_slug",
                        unique=True,
                        verbose_name="slug",
                    ),
                ),
            ],
            options={"verbose_name": "Normalization tool"},
        ),
        migrations.CreateModel(
            name="IDCommand",
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
                ("enabled", models.BooleanField(default=True, verbose_name="enabled")),
                (
                    "lastmodified",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="last modified"
                    ),
                ),
                (
                    "uuid",
                    models.UUIDField(
                        help_text="Unique identifier",
                        unique=True,
                        max_length=36,
                        editable=False,
                        blank=True,
                    ),
                ),
                (
                    "description",
                    models.CharField(
                        help_text="Name to identify script",
                        max_length=256,
                        verbose_name="description",
                    ),
                ),
                (
                    "config",
                    models.CharField(
                        max_length=4,
                        verbose_name="configuration",
                        choices=[
                            ("PUID", "PUID"),
                            ("MIME", "MIME type"),
                            ("ext", "File extension"),
                        ],
                    ),
                ),
                (
                    "script",
                    models.TextField(
                        help_text="Script to be executed.", verbose_name="script"
                    ),
                ),
                (
                    "script_type",
                    models.CharField(
                        max_length=16,
                        verbose_name="script type",
                        choices=[
                            ("bashScript", "Bash script"),
                            ("pythonScript", "Python script"),
                            ("command", "Command line"),
                            ("as_is", "No shebang needed"),
                        ],
                    ),
                ),
                (
                    "replaces",
                    models.ForeignKey(
                        verbose_name="the related model",
                        to_field="uuid",
                        blank=True,
                        to="fpr.IDCommand",
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "ordering": ["description"],
                "verbose_name": "Format identification command",
            },
        ),
        migrations.CreateModel(
            name="IDRule",
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
                ("enabled", models.BooleanField(default=True, verbose_name="enabled")),
                (
                    "lastmodified",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="last modified"
                    ),
                ),
                (
                    "uuid",
                    models.UUIDField(
                        help_text="Unique identifier",
                        unique=True,
                        max_length=36,
                        editable=False,
                        blank=True,
                    ),
                ),
                ("command_output", models.TextField(verbose_name="command output")),
                (
                    "command",
                    models.ForeignKey(
                        to="fpr.IDCommand",
                        to_field="uuid",
                        verbose_name="the related command",
                        on_delete=models.CASCADE,
                    ),
                ),
                (
                    "format",
                    models.ForeignKey(
                        to="fpr.FormatVersion",
                        to_field="uuid",
                        verbose_name="the related format",
                        on_delete=models.CASCADE,
                    ),
                ),
                (
                    "replaces",
                    models.ForeignKey(
                        verbose_name="the related model",
                        to_field="uuid",
                        blank=True,
                        to="fpr.IDRule",
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={"verbose_name": "Format identification rule"},
        ),
        migrations.CreateModel(
            name="IDTool",
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
                    "uuid",
                    models.UUIDField(
                        help_text="Unique identifier",
                        unique=True,
                        max_length=36,
                        editable=False,
                        blank=True,
                    ),
                ),
                (
                    "description",
                    models.CharField(
                        help_text="Name of tool",
                        max_length=256,
                        verbose_name="description",
                    ),
                ),
                ("version", models.CharField(max_length=64, verbose_name="version")),
                ("enabled", models.BooleanField(default=True, verbose_name="enabled")),
                (
                    "slug",
                    autoslug.fields.AutoSlugField(
                        editable=False,
                        populate_from="_slug",
                        always_update=True,
                        unique=True,
                        verbose_name="slug",
                    ),
                ),
            ],
            options={"verbose_name": "Format identification tool"},
        ),
        migrations.AddField(
            model_name="idcommand",
            name="tool",
            field=models.ForeignKey(
                verbose_name="the related tool",
                to_field="uuid",
                to="fpr.IDTool",
                null=True,
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="fpcommand",
            name="tool",
            field=models.ForeignKey(
                verbose_name="the related tool",
                to_field="uuid",
                to="fpr.FPTool",
                null=True,
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="fpcommand",
            name="verification_command",
            field=models.ForeignKey(
                related_name="+",
                verbose_name="the related verification command",
                to_field="uuid",
                blank=True,
                to="fpr.FPCommand",
                null=True,
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="format",
            name="group",
            field=models.ForeignKey(
                verbose_name="the related group",
                to_field="uuid",
                to="fpr.FormatGroup",
                null=True,
                on_delete=models.CASCADE,
            ),
        ),
    ]
