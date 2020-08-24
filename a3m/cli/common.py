import os


def init_django():
    """Initialize our Django project.

    Why do we need this? Django does not let us import models unless Django
    itself is set up. The alternative is lazy imports but we are not taking
    that approach at the moment.
    """
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "a3m.settings.common")
    import django

    django.setup()
