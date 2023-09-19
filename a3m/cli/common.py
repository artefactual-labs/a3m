import os
import pathlib
import sys
import warnings

import django
from django.conf import settings


def suppress_warnings():
    """Suppress SyntaxWarning.

    Hiding SyntaxWarning from users since it can be misleading.
    """
    if settings.DEBUG or sys.warnoptions:
        return
    warnings.simplefilter("ignore", SyntaxWarning)


def init_django():
    """Initialize our Django project.

    Why do we need this? Django does not let us import models unless Django
    itself is set up. The alternative is lazy imports but we are not taking
    that approach at the moment.
    """
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "a3m.settings.common")
    django.setup()


def configure_xml_catalog_files():
    """Use local XML schemas for validation."""
    os.environ["XML_CATALOG_FILES"] = str(
        pathlib.Path(__file__).parent.parent / "client/assets/catalog/catalog.xml"
    )
