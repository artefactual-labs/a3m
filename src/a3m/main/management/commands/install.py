# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from django.core.management.base import BaseCommand, CommandError
from django.http import QueryDict
from django.utils import termcolors
from django import forms

from helpers import set_setting
from main.management.steps import (
    create_super_user,
    setup_pipeline,
    setup_pipeline_in_ss,
)


class SettingsForm(forms.Form):
    """Base class form to save settings to DashboardSettings."""

    def save(self, *args, **kwargs):
        """Save all the form fields to the DashboardSettings table."""
        for key in self.cleaned_data:
            # Save the value
            set_setting(key, self.cleaned_data[key])


class StorageSettingsForm(SettingsForm):
    class StripCharField(forms.CharField):
        """
        Strip the value of leading and trailing whitespace.
        This won't be needed in Django 1.9, see
        https://docs.djangoproject.com/en/1.9/ref/forms/fields/#django.forms.CharField.strip.
        """

        def to_python(self, value):
            return super(forms.CharField, self).to_python(value).strip()

    storage_service_url = forms.CharField(
        label="Storage Service URL",
        help_text="Full URL of the storage service. E.g. https://192.168.168.192:8000",
    )
    storage_service_user = forms.CharField(
        label="Storage Service User",
        help_text="User in the storage service to authenticate as. E.g. test",
    )
    storage_service_apikey = StripCharField(
        label="API key",
        help_text="API key of the storage service user. E.g. 45f7684483044809b2de045ba59dc876b11b9810",
    )
    storage_service_use_default_config = forms.BooleanField(
        required=False,
        initial=True,
        label="Use default configuration",
        help_text="You have to manually set up a custom configuration if the default configuration is not selected.",
    )


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--username", required=True)
        parser.add_argument("--email", required=True)
        parser.add_argument("--password", required=True)
        parser.add_argument("--api-key", required=True)
        parser.add_argument("--org-name", required=True)
        parser.add_argument("--org-id", required=True)
        parser.add_argument("--ss-url", required=True)
        parser.add_argument("--ss-user", required=True)
        parser.add_argument("--ss-api-key", required=True)
        parser.add_argument("--whitelist", required=False)
        parser.add_argument("--site-url", required=False)

    def save_ss_settings(self, options):
        POST = QueryDict("", mutable=True)
        POST.update(
            {
                "storage_service_url": options["ss_url"],
                "storage_service_user": options["ss_user"],
                "storage_service_apikey": options["ss_api_key"],
            }
        )
        form = StorageSettingsForm(POST)
        if not form.is_valid():
            raise CommandError("SS attributes are invalid")
        form.save()

    def handle(self, *args, **options):
        # Not needed in Django 1.9+.
        self.style.SUCCESS = termcolors.make_style(opts=("bold",), fg="green")

        setup_pipeline(options["org_name"], options["org_id"], options["site_url"])
        create_super_user(
            options["username"],
            options["email"],
            options["password"],
            options["api_key"],
        )
        self.save_ss_settings(options)
        setup_pipeline_in_ss(use_default_config=True)
        set_setting("api_whitelist", options["whitelist"])
        self.stdout.write(self.style.SUCCESS("Done!\n"))