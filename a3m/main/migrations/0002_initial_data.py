import os

from django.core.management import call_command
from django.db import migrations


def load_fixtures(apps, schema_editor):
    fixture_file = os.path.join(os.path.dirname(__file__), "initial-data.json")
    call_command("loaddata", fixture_file, app_label="main", verbosity=0)


class Migration(migrations.Migration):
    dependencies = [("main", "0001_initial")]

    operations = [migrations.RunPython(load_fixtures)]
