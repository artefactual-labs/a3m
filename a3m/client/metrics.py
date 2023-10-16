"""
Exposes various metrics via Prometheus.
"""
import functools
import importlib
import pkgutil

from django.conf import settings
from django.db.models import Sum
from django.utils import timezone
from prometheus_client import Counter
from prometheus_client import Gauge
from prometheus_client import Histogram

from a3m.client import clientScripts
from a3m.common_metrics import PACKAGE_FILE_COUNT_BUCKETS
from a3m.common_metrics import PACKAGE_SIZE_BUCKETS
from a3m.common_metrics import PROCESSING_TIME_BUCKETS
from a3m.common_metrics import TASK_DURATION_BUCKETS
from a3m.main.models import File
from a3m.main.models import Transfer


job_counter = Counter(
    "mcpclient_job_total",
    "Number of jobs processed, labeled by script",
    ["script_name"],
)
job_processed_timestamp = Gauge(
    "mcpclient_job_success_timestamp",
    "Timestamp of most recent job processed, labeled by script",
    ["script_name"],
)
job_error_counter = Counter(
    "mcpclient_job_error_total",
    "Number of failures processing jobs, labeled by script",
    ["script_name"],
)
job_error_timestamp = Gauge(
    "mcpclient_job_error_timestamp",
    "Timestamp of most recent job failure, labeled by script",
    ["script_name"],
)

task_execution_time_histogram = Histogram(
    "mcpclient_task_execution_time_seconds",
    "Histogram of worker task execution times in seconds, labeled by script",
    ["script_name"],
    buckets=TASK_DURATION_BUCKETS,
)

transfer_started_counter = Counter(
    "mcpclient_transfer_started_total", "Number of Transfers started"
)
transfer_started_timestamp = Gauge(
    "mcpclient_transfer_started_timestamp", "Timestamp of most recent transfer started"
)
transfer_completed_counter = Counter(
    "mcpclient_transfer_completed_total", "Number of Transfers completed"
)
transfer_completed_timestamp = Gauge(
    "mcpclient_transfer_completed_timestamp",
    "Timestamp of most recent transfer completed",
)
transfer_error_counter = Counter(
    "mcpclient_transfer_error_total",
    "Number of transfer failures, by error type",
    ["failure_type"],
)
transfer_error_timestamp = Gauge(
    "mcpclient_transfer_error_timestamp",
    "Timestamp of most recent transfer failure, by error type",
    ["failure_type"],
)
transfer_files_histogram = Histogram(
    "mcpclient_transfer_files",
    "Histogram of number of files included in transfers",
    buckets=PACKAGE_FILE_COUNT_BUCKETS,
)
transfer_size_histogram = Histogram(
    "mcpclient_transfer_size_bytes",
    "Histogram of number bytes in transfers",
    buckets=PACKAGE_SIZE_BUCKETS,
)

sip_started_counter = Counter("mcpclient_sip_started_total", "Number of SIPs started")
sip_started_timestamp = Gauge(
    "mcpclient_sip_started_timestamp", "Timestamp of most recent SIP started"
)
sip_error_counter = Counter(
    "mcpclient_sip_error_total",
    "Number of SIP failures, by error type",
    ["failure_type"],
)
sip_error_timestamp = Gauge(
    "mcpclient_sip_error_timestamp",
    "Timestamp of most recent SIP failure, by error type",
    ["failure_type"],
)

aips_stored_counter = Counter("mcpclient_aips_stored_total", "Number of AIPs stored")
aips_stored_timestamp = Gauge(
    "mcpclient_aips_stored_timestamp", "Timestamp of most recent AIP stored"
)
aip_processing_time_histogram = Histogram(
    "mcpclient_aip_processing_seconds",
    "Histogram of AIP processing time, from first file recorded in DB to storage in SS",
    buckets=PROCESSING_TIME_BUCKETS,
)
aip_files_stored_histogram = Histogram(
    "mcpclient_aip_files_stored",
    "Histogram of number of files stored in AIPs. Note, this includes metadata, derivatives, etc.",
    buckets=PACKAGE_FILE_COUNT_BUCKETS,
)
aip_size_histogram = Histogram(
    "mcpclient_aip_size_bytes",
    "Histogram of number of bytes stored in AIPs. Note, this includes metadata, derivatives, etc.",
    buckets=PACKAGE_SIZE_BUCKETS,
)

# There's no central place to pull these constants from currently
PACKAGE_FAILURE_TYPES = ("fail", "reject")


def skip_if_prometheus_disabled(func):
    @functools.wraps(func)
    def wrapper(*args, **kwds):
        if settings.PROMETHEUS_ENABLED:
            return func(*args, **kwds)
        return None

    return wrapper


def init_counter_labels():
    # Zero our counters to start, by intializing all labels. Non-zero starting points
    # cause problems when measuring rates.

    for _, modname, is_pkg in pkgutil.iter_modules(clientScripts.__path__):
        if not is_pkg:
            continue
        module = importlib.import_module(modname)
        if "call" not in module:
            raise Exception()
        modname = modname.split(".")[-1]
        print(modname)
        job_counter.labels(script_name=modname)
        job_processed_timestamp.labels(script_name=modname)
        job_error_counter.labels(script_name=modname)
        job_error_timestamp.labels(script_name=modname)
        task_execution_time_histogram.labels(script_name=modname)

    for failure_type in PACKAGE_FAILURE_TYPES:
        transfer_error_counter.labels(failure_type=failure_type)
        transfer_error_timestamp.labels(failure_type=failure_type)

    for failure_type in PACKAGE_FAILURE_TYPES:
        sip_error_counter.labels(failure_type=failure_type)
        sip_error_timestamp.labels(failure_type=failure_type)


@skip_if_prometheus_disabled
def job_completed(script_name):
    job_counter.labels(script_name=script_name).inc()
    job_processed_timestamp.labels(script_name=script_name).set_to_current_time()


@skip_if_prometheus_disabled
def job_failed(script_name):
    job_counter.labels(script_name=script_name).inc()
    job_error_counter.labels(script_name=script_name).inc()
    job_error_timestamp.labels(script_name=script_name).set_to_current_time()


@skip_if_prometheus_disabled
def aip_stored(sip_uuid, size):
    aips_stored_counter.inc()
    aips_stored_timestamp.set_to_current_time()
    aip_size_histogram.observe(size)

    try:
        earliest_file = File.objects.filter(sip_id=sip_uuid).earliest("enteredsystem")
    except File.DoesNotExist:
        pass
    else:
        duration = (timezone.now() - earliest_file.enteredsystem).total_seconds()
        aip_processing_time_histogram.observe(duration)

    # We do two queries here, as we may not have format information for everything
    total_file_count = File.objects.filter(sip_id=sip_uuid).count()
    aip_files_stored_histogram.observe(total_file_count)


@skip_if_prometheus_disabled
def transfer_started():
    transfer_started_counter.inc()
    transfer_started_timestamp.set_to_current_time()


@skip_if_prometheus_disabled
def transfer_completed(transfer_uuid):
    try:
        transfer = Transfer.objects.get(uuid=transfer_uuid)
    except Transfer.DoesNotExist:
        return

    transfer_completed_counter.inc()
    transfer_completed_timestamp.set_to_current_time()

    file_queryset = File.objects.filter(transfer=transfer)
    file_count = file_queryset.count()
    transfer_files_histogram.observe(file_count)

    transfer_size = file_queryset.aggregate(total_size=Sum("size"))
    transfer_size_histogram.observe(transfer_size["total_size"])


@skip_if_prometheus_disabled
def transfer_failed(failure_type):
    transfer_error_counter.labels(failure_type=failure_type).inc()
    transfer_error_timestamp.labels(failure_type=failure_type).set_to_current_time()


@skip_if_prometheus_disabled
def sip_started():
    sip_started_counter.inc()
    sip_started_timestamp.set_to_current_time()


@skip_if_prometheus_disabled
def sip_failed(failure_type):
    sip_error_counter.labels(failure_type=failure_type).inc()
    sip_error_timestamp.labels(failure_type=failure_type).set_to_current_time()
