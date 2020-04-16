from __future__ import division

import json
import logging.config
import math
import multiprocessing
import os

import StringIO

from a3m.appconfig import Config
from a3m.appconfig import process_watched_directory_interval

CONFIG_MAPPING = {
    "watch_directory_method": {
        "section": "a3m",
        "option": "watch_directory_method",
        "type": "string",
    },
    "watch_directory_interval": {
        "section": "a3m",
        "process_function": process_watched_directory_interval,
    },
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
    "watch_directory": {
        "section": "a3m",
        "option": "watch_directory",
        "type": "string",
    },
    "gearman_server": {"section": "a3m", "option": "gearman_server", "type": "string"},
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
    "clamav_server": {"section": "a3m", "option": "clamav_server", "type": "string"},
    "clamav_pass_by_stream": {
        "section": "a3m",
        "option": "clamav_pass_by_stream",
        "type": "boolean",
    },
    "clamav_client_timeout": {
        "section": "a3m",
        "option": "clamav_client_timeout",
        "type": "float",
    },
    "clamav_client_backend": {
        "section": "a3m",
        "option": "clamav_client_backend",
        "type": "string",
    },
    # float for megabytes to preserve fractions on in-code operations on bytes
    "clamav_client_max_file_size": {
        "section": "a3m",
        "option": "clamav_client_max_file_size",
        "type": "float",
    },
    "clamav_client_max_scan_size": {
        "section": "a3m",
        "option": "clamav_client_max_scan_size",
        "type": "float",
    },
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
}


CONFIG_DEFAULTS = """[a3m]

gearman_server = localhost:4730
watch_directory = /var/archivematica/sharedDirectory/watchedDirectories/
shared_directory = /var/archivematica/sharedDirectory/
temp_dir = /var/archivematica/sharedDirectory/tmp
processing_directory = /var/archivematica/sharedDirectory/currentlyProcessing/
rejected_directory = %%sharedPath%%rejected/
watch_directory_method = poll
watch_directory_interval = 1
batch_size = 128
rpc_threads = 4
prometheus_bind_address =
prometheus_bind_port =
time_zone = UTC
capture_client_script_output = true
removable_files = Thumbs.db, Icon, Icon\r, .DS_Store
clamav_server = /var/run/clamav/clamd.ctl
clamav_pass_by_stream = True
clamav_client_timeout = 86400
clamav_client_backend = clamscanner     ; Options: clamdscanner or clamscanner
clamav_client_max_file_size = 42        ; MB
clamav_client_max_scan_size = 42        ; MB
db_engine = django.db.backends.sqlite3
db_name = /var/archivematica/sharedDirectory/a3m.sqlite
db_user =
db_password =
db_host =
db_port =
secret_key = 12345
rpc_bind_address = 0.0.0.0:8000
"""


config = Config(env_prefix="A3M", attrs=CONFIG_MAPPING)
config.read_defaults(StringIO.StringIO(CONFIG_DEFAULTS))
config.read_files(["/etc/a3m/a3m.cfg"])


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
    }
}

MIDDLEWARE_CLASSES = ()

TEMPLATES = ()

INSTALLED_APPS = (
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "a3m.main",
    "a3m.fpr",
)

SECRET_KEY = config.get("secret_key")

USE_TZ = True
TIME_ZONE = config.get("time_zone")

# Configure logging manually
LOGGING_CONFIG = None

# Location of the logging configuration file that we're going to pass to
# `logging.config.fileConfig` unless it doesn't exist.
LOGGING_CONFIG_FILE = "/etc/a3m/logging.json"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "detailed": {
            "format": "%(levelname)-8s %(threadName)s %(asctime)s %(module)s:%(funcName)s:%(lineno)d:  %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "detailed",
        }
    },
    "loggers": {"archivematica": {"level": "DEBUG"}},
    "root": {"handlers": ["console"], "level": "WARNING"},
}

if os.path.isfile(LOGGING_CONFIG_FILE):
    with open(LOGGING_CONFIG_FILE, "rt") as f:
        LOGGING = logging.config.dictConfig(json.load(f))
else:
    logging.config.dictConfig(LOGGING)


def concurrent_packages_default():
    """Default to 1/2 of CPU count, rounded up."""
    cpu_count = multiprocessing.cpu_count()
    return int(math.ceil(cpu_count / 2))


SHARED_DIRECTORY = config.get("shared_directory")
TEMP_DIRECTORY = config.get("temp_directory")
WATCH_DIRECTORY = config.get("watch_directory")
REJECTED_DIRECTORY = config.get("rejected_directory")
PROCESSING_DIRECTORY = config.get("processing_directory")
GEARMAN_SERVER = config.get("gearman_server")
WATCH_DIRECTORY_METHOD = config.get("watch_directory_method")
WATCH_DIRECTORY_INTERVAL = config.get("watch_directory_interval")
BATCH_SIZE = config.get("batch_size")
CONCURRENT_PACKAGES = config.get(
    "concurrent_packages", default=concurrent_packages_default()
)
RPC_THREADS = config.get("rpc_threads")
WORKER_THREADS = config.get("worker_threads", default=multiprocessing.cpu_count() + 1)
REMOVABLE_FILES = config.get("removable_files")
CLAMAV_SERVER = config.get("clamav_server")
CLAMAV_PASS_BY_STREAM = config.get("clamav_pass_by_stream")
CLAMAV_CLIENT_TIMEOUT = config.get("clamav_client_timeout")
CLAMAV_CLIENT_BACKEND = config.get("clamav_client_backend")
CLAMAV_CLIENT_MAX_FILE_SIZE = config.get("clamav_client_max_file_size")
CLAMAV_CLIENT_MAX_SCAN_SIZE = config.get("clamav_client_max_scan_size")
CAPTURE_CLIENT_SCRIPT_OUTPUT = config.get("capture_client_script_output")
DEFAULT_CHECKSUM_ALGORITHM = "sha256"
RPC_BIND_ADDRESS = config.get("rpc_bind_address")


# Prometheus

PROMETHEUS_BIND_ADDRESS = config.get("prometheus_bind_address")
try:
    PROMETHEUS_BIND_PORT = int(config.get("prometheus_bind_port"))
except ValueError:
    PROMETHEUS_ENABLED = False
else:
    PROMETHEUS_ENABLED = True


BIND_PID_HANDLE = {}

INSTANCE_ID = "fec7bcf7-45db-4a22-8ceb-e94377db3476"

DEBUG = False
