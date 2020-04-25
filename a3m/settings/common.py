import json
import logging.config
import math
import multiprocessing
import os
from io import StringIO
from pathlib import Path

from appdirs import user_data_dir

from a3m.appconfig import Config
from a3m.appconfig import process_watched_directory_interval

CONFIG_MAPPING = {
    "debug": {"section": "a3m", "option": "debug", "type": "boolean"},
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
    "virus_scanning_enabled": {
        "section": "a3m",
        "option": "virus_scanning_enabled",
        "type": "boolean",
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

debug = False
gearman_server = localhost:4730
watch_directory_method = inotify
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
virus_scanning_enabled = False
secret_key = 12345
rpc_bind_address = 0.0.0.0:7000

db_engine = django.db.backends.sqlite3
db_name =
db_user =
db_password =
db_host =
db_port =

shared_directory =
watch_directory =
temp_dir =
processing_directory =
rejected_directory =
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
                "watch_directory": format_path("watchedDirectories"),
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

INSTALLED_APPS = ("a3m.main", "a3m.fpr")

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
            "level": "WARNING",
            "class": "logging.StreamHandler",
            "formatter": "detailed",
        }
    },
    "loggers": {"a3m": {"level": "WARNING"}},
    "root": {"handlers": ["console"], "level": "WARNING"},
}

DEBUG = config.get("debug")

if DEBUG:
    LOGGING["handlers"]["console"]["level"] = "DEBUG"
    LOGGING["loggers"]["a3m"]["level"] = "DEBUG"
    LOGGING["root"]["level"] = "DEBUG"


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
VIRUS_SCANNING_ENABLED = config.get("virus_scanning_enabled")
CAPTURE_CLIENT_SCRIPT_OUTPUT = config.get("capture_client_script_output")
DEFAULT_CHECKSUM_ALGORITHM = "sha256"
RPC_BIND_ADDRESS = config.get("rpc_bind_address")


# Shared directories

SHARED_DIRECTORY = config.get("shared_directory")
TEMP_DIRECTORY = config.get("temp_directory")
WATCH_DIRECTORY = config.get("watch_directory")
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


BIND_PID_HANDLE = {}

INSTANCE_ID = "fec7bcf7-45db-4a22-8ceb-e94377db3476"
