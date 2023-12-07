import json
import logging.config
import math
import multiprocessing
import os
from io import StringIO
from pathlib import Path
from typing import Any

import django_stubs_ext
from platformdirs import user_data_dir

from a3m.appconfig import Config


django_stubs_ext.monkeypatch()


CONFIG_MAPPING = {
    "debug": {"section": "a3m", "option": "debug", "type": "boolean"},
    "batch_size": {"section": "a3m", "option": "batch_size", "type": "int"},
    "concurrent_packages": {
        "section": "a3m",
        "option": "concurrent_packages",
        "type": "int",
    },
    "rpc_threads": {"section": "a3m", "option": "rpc_threads", "type": "int"},
    "worker_threads": {"section": "a3m", "option": "worker_threads", "type": "int"},
    "shared_directory": {
        "section": "a3m",
        "option": "shared_directory",
        "type": "string",
    },
    "temp_directory": {"section": "a3m", "option": "temp_dir", "type": "string"},
    "processing_directory": {
        "section": "a3m",
        "option": "processing_directory",
        "type": "string",
    },
    "rejected_directory": {
        "section": "a3m",
        "option": "rejected_directory",
        "type": "string",
    },
    "capture_client_script_output": {
        "section": "a3m",
        "option": "capture_client_script_output",
        "type": "boolean",
    },
    "removable_files": {
        "section": "a3m",
        "option": "removable_files",
        "type": "string",
    },
    "secret_key": {"section": "a3m", "option": "secret_key", "type": "string"},
    "prometheus_bind_address": {
        "section": "a3m",
        "option": "prometheus_bind_address",
        "type": "string",
    },
    "prometheus_bind_port": {
        "section": "a3m",
        "option": "prometheus_bind_port",
        "type": "string",
    },
    "time_zone": {"section": "a3m", "option": "time_zone", "type": "string"},
    "db_engine": {"section": "a3m", "option": "db_engine", "type": "string"},
    "db_name": {"section": "a3m", "option": "db_name", "type": "string"},
    "db_user": {"section": "a3m", "option": "db_user", "type": "string"},
    "db_password": {"section": "a3m", "option": "db_password", "type": "string"},
    "db_host": {"section": "a3m", "option": "db_host", "type": "string"},
    "db_port": {"section": "a3m", "option": "db_port", "type": "string"},
    "rpc_bind_address": {
        "section": "a3m",
        "option": "rpc_bind_address",
        "type": "string",
    },
    "s3_enabled": {"section": "a3m", "option": "s3_enabled", "type": "boolean"},
    "s3_endpoint_url": {
        "section": "a3m",
        "option": "s3_endpoint_url",
        "type": "string",
    },
    "s3_region_name": {"section": "a3m", "option": "s3_region_name", "type": "string"},
    "s3_access_key_id": {
        "section": "a3m",
        "option": "s3_access_key_id",
        "type": "string",
    },
    "s3_secret_access_key": {
        "section": "a3m",
        "option": "s3_secret_access_key",
        "type": "string",
    },
    "s3_use_ssl": {"section": "a3m", "option": "s3_use_ssl", "type": "boolean"},
    "s3_addressing_style": {
        "section": "a3m",
        "option": "s3_addressing_style",
        "type": "string",
    },
    "s3_signature_version": {
        "section": "a3m",
        "option": "s3_signature_version",
        "type": "string",
    },
    "s3_bucket": {"section": "a3m", "option": "s3_bucket", "type": "string"},
    "org_id": {"section": "a3m", "option": "org_id", "type": "string"},
    "org_name": {"section": "a3m", "option": "org_name", "type": "string"},
}


CONFIG_DEFAULTS = """[a3m]

debug = False
batch_size = 128
rpc_threads = 4
prometheus_bind_address =
prometheus_bind_port =
time_zone = UTC
capture_client_script_output = True
removable_files = Thumbs.db, Icon, Icon\r, .DS_Store
secret_key = 12345
rpc_bind_address = 0.0.0.0:7000

db_engine = django.db.backends.sqlite3
db_name =
db_user =
db_password =
db_host =
db_port =

s3_enabled = False
s3_endpoint_url =
s3_region_name =
s3_access_key_id =
s3_secret_access_key =
s3_use_ssl = False
s3_addressing_style = path
s3_signature_version = s3v4
s3_bucket =

shared_directory =
temp_dir =
processing_directory =
rejected_directory =

org_id =
org_name =
"""


def get_data_dir():
    # A3M-TODO: when we run a command with an unknown uid (Compose)
    home_dir = Path.home()
    if str(home_dir) == "/":
        return Path("/home/a3m/.local/share/a3m")

    return Path(user_data_dir("a3m", "Artefactual"))


def _get_data_dir_defaults(config):
    data_dir = get_data_dir()
    config_dict = {"a3m": {}}

    def format_path(subdir):
        return os.path.join(str(data_dir / "share" / subdir), "")

    if not config.get("shared_directory"):
        config_dict["a3m"].update(
            {
                "shared_directory": format_path(""),
                "temp_dir": format_path("tmp"),
                "processing_directory": format_path("currentlyProcessing"),
                "rejected_directory": format_path("rejected"),
            }
        )

    if not config.get("db_name"):
        config_dict["a3m"].update({"db_name": data_dir / "db.sqlite"})

    # Create home directory if we're going to use it.
    if config_dict["a3m"]:
        data_dir.mkdir(parents=True, exist_ok=True)

    return config_dict


config = Config(env_prefix="A3M", attrs=CONFIG_MAPPING)
config.read_defaults(StringIO(CONFIG_DEFAULTS))
config.read_files(["/etc/a3m/a3m.cfg"])
config.read_dict(_get_data_dir_defaults(config))


# Django

DATABASES = {
    "default": {
        "ENGINE": config.get("db_engine"),
        "NAME": config.get("db_name"),
        "USER": config.get("db_user"),
        "PASSWORD": config.get("db_password"),
        "HOST": config.get("db_host"),
        "PORT": config.get("db_port"),
        "CONN_MAX_AGE": 3600,
        "OPTIONS": {"timeout": 5},
    }
}

MIDDLEWARE_CLASSES = ()

TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates"}]

INSTALLED_APPS = ("a3m.main",)

SECRET_KEY = config.get("secret_key")

USE_TZ = True
TIME_ZONE = config.get("time_zone")

# Configure logging manually
LOGGING_CONFIG = None

# Location of the logging configuration file that we're going to pass to
# `logging.config.fileConfig` unless it doesn't exist.
LOGGING_CONFIG_FILE = "/etc/a3m/logging.json"

LOGGING: dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "detailed": {
            "format": "%(levelname)-8s <%(asctime)s>: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "detailed",
        }
    },
    "loggers": {"a3m": {"level": "INFO"}, "bagit": {"level": "WARNING"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}

DEBUG = config.get("debug")

if DEBUG:
    LOGGING["formatters"]["detailed"][
        "format"
    ] = "%(levelname)-8s <%(process)d:%(threadName)s> <%(asctime)s> %(module)s:%(funcName)s:%(lineno)d: %(message)s"
    LOGGING["handlers"]["console"]["level"] = "DEBUG"
    LOGGING["root"]["level"] = "DEBUG"
    LOGGING["loggers"] = {
        "a3m": {"level": "DEBUG"},
        # Use "DEBUG" to log database queries.
        "django.db.backends": {"level": "WARNING"},
    }


if os.path.isfile(LOGGING_CONFIG_FILE):
    with open(LOGGING_CONFIG_FILE) as f:
        logging.config.dictConfig(json.load(f))
else:
    logging.config.dictConfig(LOGGING)


def concurrent_packages_default():
    """Default to 1/2 of CPU count, rounded up."""
    if "sqlite" in DATABASES["default"]["ENGINE"]:
        # A3M-TODO: this needs to be investigated further, but having multiple
        # writer in SQLite seems counterproductive.
        return 1
    cpu_count = multiprocessing.cpu_count()
    return int(math.ceil(cpu_count / 2))


BATCH_SIZE = config.get("batch_size")
CONCURRENT_PACKAGES = config.get(
    "concurrent_packages", default=concurrent_packages_default()
)
RPC_THREADS = config.get("rpc_threads")
WORKER_THREADS = config.get("worker_threads", default=multiprocessing.cpu_count() + 1)
REMOVABLE_FILES = config.get("removable_files")
CAPTURE_CLIENT_SCRIPT_OUTPUT = config.get("capture_client_script_output")
DEFAULT_CHECKSUM_ALGORITHM = "sha256"
RPC_BIND_ADDRESS = config.get("rpc_bind_address")


# Shared directories

SHARED_DIRECTORY = config.get("shared_directory")
TEMP_DIRECTORY = config.get("temp_directory")
REJECTED_DIRECTORY = config.get("rejected_directory")
PROCESSING_DIRECTORY = config.get("processing_directory")


# Prometheus

PROMETHEUS_BIND_ADDRESS = config.get("prometheus_bind_address")
try:
    PROMETHEUS_BIND_PORT = int(config.get("prometheus_bind_port"))
except ValueError:
    PROMETHEUS_ENABLED = False
else:
    PROMETHEUS_ENABLED = True


# S3

S3_ENABLED = config.get("s3_enabled")
S3_ENDPOINT_URL = config.get("s3_endpoint_url")
S3_REGION_NAME = config.get("s3_region_name")
S3_ACCESS_KEY_ID = config.get("s3_access_key_id")
S3_SECRET_ACCESS_KEY = config.get("s3_secret_access_key")
S3_USE_SSL = config.get("s3_use_ssl")
S3_ADDRESSING_STYLE = config.get("s3_addressing_style")
S3_SIGNATURE_VERSION = config.get("s3_signature_version")
S3_BUCKET = config.get("s3_bucket")

# ~ S3 config example ~
# S3_ENDPOINT_URL = "https://play.min.io"
# S3_USE_SSL = True
# S3_ACCESS_KEY_ID = "Q3AM3UQ867SPQQA43P2F"
# S3_SECRET_ACCESS_KEY = "zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TG"
# S3_BUCKET = "a3m"

# A3M-TODO: fix this
INSTANCE_ID = "fec7bcf7-45db-4a22-8ceb-e94377db3476"

ORG_ID = config.get("org_id")
ORG_NAME = config.get("org_name")
