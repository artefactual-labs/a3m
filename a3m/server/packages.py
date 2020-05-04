"""Package management."""
import ast
import collections
import functools
import logging
import os
from dataclasses import dataclass
from enum import auto
from enum import Enum
from uuid import uuid4

from django.conf import settings

from a3m.archivematicaFunctions import strToUnicode
from a3m.main import models
from a3m.server.db import auto_close_old_connections
from a3m.server.jobs import JobChain
from a3m.server.rpc import a3m_pb2


logger = logging.getLogger(__name__)


def _get_setting(name):
    """Retrieve a Django setting decoded as a unicode string."""
    return strToUnicode(getattr(settings, name))


BASE_REPLACEMENTS = {
    r"%tmpDirectory%": os.path.join(_get_setting("SHARED_DIRECTORY"), "tmp", ""),
    r"%processingDirectory%": _get_setting("PROCESSING_DIRECTORY"),
    r"%rejectedDirectory%": _get_setting("REJECTED_DIRECTORY"),
}


def get_file_replacement_mapping(file_obj, unit_directory):
    mapping = BASE_REPLACEMENTS.copy()
    dirname = os.path.dirname(file_obj.currentlocation)
    name, ext = os.path.splitext(file_obj.currentlocation)
    name = os.path.basename(name)

    absolute_path = file_obj.currentlocation.replace(r"%SIPDirectory%", unit_directory)
    absolute_path = absolute_path.replace(r"%transferDirectory%", unit_directory)

    mapping.update(
        {
            r"%fileUUID%": file_obj.pk,
            r"%originalLocation%": file_obj.originallocation,
            r"%currentLocation%": file_obj.currentlocation,
            r"%fileGrpUse%": file_obj.filegrpuse,
            r"%fileDirectory%": dirname,
            r"%fileName%": name,
            r"%fileExtension%": ext[1:],
            r"%fileExtensionWithDot%": ext,
            r"%relativeLocation%": absolute_path,
            # TODO: standardize duplicates
            r"%inputFile%": absolute_path,
            r"%fileFullName%": absolute_path,
        }
    )

    return mapping


class Stage(Enum):
    """Package stages."""

    TRANSFER = auto()
    INGEST = auto()


class Package:
    """Package is the processing unit in a3m.

    It wraps a SIP and borrows its SIP. But it also knows about its transfer
    stage. Some methods return different values depending the stage the
    package is in.
    """

    def __init__(self, name, url, transfer, sip):
        self.name = name
        self.url = url
        self.transfer = transfer
        self.sip = sip
        self.stage = Stage.TRANSFER
        self.aip_filename = None
        self.sip_type = None
        self._current_path = self.transfer.currentlocation

    def __repr__(self):
        return "{class_name}({uuid})".format(
            class_name=self.__class__.__name__, uuid=self.uuid
        )

    @classmethod
    @auto_close_old_connections()
    def create_package(cls, package_queue, executor, workflow, name, url):
        """Launch transfer and return its object immediately."""
        if not name:
            raise ValueError("No transfer name provided.")
        if not url:
            raise ValueError("No url provided.")

        transfer_id = str(uuid4())
        transfer_dir = os.path.join(
            _get_setting("PROCESSING_DIRECTORY"), "transfer", transfer_id, ""
        )
        transfer = models.Transfer.objects.create(
            uuid=transfer_id, currentlocation=transfer_dir
        )
        transfer.set_processing_configuration("default")
        logger.debug("Transfer object created: %s", transfer.pk)

        sip_id = str(uuid4())
        sip_dir = os.path.join(
            _get_setting("PROCESSING_DIRECTORY"), "ingest", sip_id, ""
        )
        sip = models.SIP.objects.create(uuid=sip_id, currentpath=sip_dir)
        sip.transfer_id = transfer_id
        logger.debug("SIP object created: %s", sip.pk)

        package = cls(name, url, transfer, sip)

        params = (package, package_queue, workflow)
        future = executor.submit(Package.trigger_workflow, *params)
        future.add_done_callback(
            functools.partial(Package.trigger_workflow_done_callback, package.uuid)
        )

        return package

    @staticmethod
    def trigger_workflow(package, package_queue, workflow):
        logger.debug("Package %s: starting workflow processing", package.uuid)

        # It should be "2671aef1-653a-49bf-bc74-82572b64ace9".
        chain = workflow.get_initiator_chain()
        if chain is None:
            raise ValueError("Workflow initiator not found")

        job_chain = JobChain(package, chain, workflow)

        package_queue.schedule_job(next(job_chain))

    @staticmethod
    def trigger_workflow_done_callback(package_id, future):
        try:
            future.result()
        except Exception as err:
            logger.warning("Exception detected: %s", err, exc_info=True)
        else:
            logger.info("Package processing started (%s)", package_id)

    @property
    def uuid(self):
        return self.sip.pk

    @property
    def subid(self):
        if self.stage is Stage.INGEST:
            return self.sip.pk
        else:
            return self.transfer.pk

    @property
    def current_path(self):
        return self._current_path

    @current_path.setter
    def current_path(self, value):
        """The real (no shared dir vars) path to the package.
        """
        self._current_path = value.replace(
            r"%sharedPath%", _get_setting("SHARED_DIRECTORY")
        )

    @property
    def current_path_for_db(self):
        """The path to the package, as stored in the database.
        """
        return self.current_path.replace(
            _get_setting("SHARED_DIRECTORY"), r"%sharedPath%", 1
        )

    @property
    def context(self):
        """Returns a `PackageContext` for this package."""
        # This needs to be reloaded from the db every time, because new values
        # could have been added by a client script.
        # TODO: pass context changes back from client
        return PackageContext.load_from_db(self.subid)

    @property
    def unit_type(self):
        if self.stage is Stage.INGEST:
            return "unitSIP"
        else:
            return "unitTransfer"

    @property
    def unit_variable_type(self):
        if self.stage is Stage.INGEST:
            return "SIP"
        else:
            return "Transfer"

    @property
    def replacement_path_string(self):
        if self.stage is Stage.INGEST:
            return r"%SIPDirectory%"
        else:
            return r"%transferDirectory%"

    @property
    @auto_close_old_connections()
    def base_queryset(self):
        if self.stage is Stage.INGEST:
            return models.File.objects.filter(sip_id=self.sip.pk)
        else:
            return models.File.objects.filter(transfer_id=self.transfer.pk)

    @auto_close_old_connections()
    def set_variable(self, key, value, chain_link_id):
        """Sets a UnitVariable, which tracks choices made by users during processing.
        """
        # TODO: refactor this concept
        if not value:
            value = ""
        else:
            value = str(value)

        unit_var, created = models.UnitVariable.objects.update_or_create(
            unittype=self.unit_variable_type,
            unituuid=self.subid,
            variable=key,
            defaults=dict(variablevalue=value, microservicechainlink=chain_link_id),
        )
        if created:
            message = "New UnitVariable %s created for %s: %s (MSCL: %s)"
        else:
            message = "Existing UnitVariable %s for %s updated to %s (MSCL" " %s)"
        logger.debug(message, key, self.subid, value, chain_link_id)

    def start_ingest(self):
        """Signal this package so it becomes a SIP."""
        self.stage = Stage.INGEST

    @auto_close_old_connections()
    def reload(self):
        if self.stage is Stage.INGEST:
            sip = models.SIP.objects.get(uuid=self.sip.pk)
            self.current_path = sip.currentpath
            self.aip_filename = sip.aip_filename or ""
            self.sip_type = sip.sip_type
        else:
            transfer = models.Transfer.objects.get(uuid=self.transfer.pk)
            self.current_path = transfer.currentlocation
            self.processing_configuration = transfer.processing_configuration

    def get_replacement_mapping(self, filter_subdir_path=None):
        mapping = BASE_REPLACEMENTS.copy()
        mapping.update(
            {
                r"%SIPUUID%": str(self.sip.pk),
                r"%TransferUUID%": str(self.transfer.pk),
                r"%SIPName%": self.name,
                r"%SIPLogsDirectory%": os.path.join(self.current_path, "logs", ""),
                r"%SIPObjectsDirectory%": os.path.join(
                    self.current_path, "objects", ""
                ),
                r"%SIPDirectory%": self.current_path,
                r"%SIPDirectoryBasename%": os.path.basename(
                    os.path.abspath(self.current_path)
                ),
                r"%relativeLocation%": self.current_path_for_db,
            }
        )

        if self.stage is Stage.INGEST:
            mapping.update(
                {
                    r"%unitType%": self.unit_variable_type,
                    r"%AIPFilename%": self.aip_filename,
                    r"%SIPType%": self.sip_type,
                }
            )
        else:
            mapping.update(
                {
                    self.replacement_path_string: self.current_path,
                    r"%unitType%": self.unit_variable_type,
                    r"%processingConfiguration%": self.processing_configuration,
                    r"%URL%": self.url,
                }
            )

        return mapping

    def files(self, filter_subdir=None):
        """Generator that yields all files associated with the package or that
        should be associated with a package.
        """
        with auto_close_old_connections():
            queryset = self.base_queryset

            if filter_subdir:
                filter_path = "".join([self.replacement_path_string, filter_subdir])
                queryset = queryset.filter(currentlocation__startswith=filter_path)

            start_path = self.current_path
            if filter_subdir:
                start_path = start_path + filter_subdir

            files_returned_already = set()
            if queryset.exists():
                for file_obj in queryset.iterator():
                    file_obj_mapped = get_file_replacement_mapping(
                        file_obj, self.current_path
                    )
                    if not os.path.exists(file_obj_mapped.get("%inputFile%")):
                        continue
                    files_returned_already.add(file_obj_mapped.get("%inputFile%"))
                    yield file_obj_mapped

            for basedir, subdirs, files in os.walk(start_path):
                for file_name in files:
                    file_path = os.path.join(basedir, file_name)
                    if file_path not in files_returned_already:
                        yield {
                            r"%relativeLocation%": file_path,
                            r"%fileUUID%": "None",
                            r"%fileGrpUse%": "",
                        }


class PackageContext:
    """Package context tracks choices made previously while processing
    """

    def __init__(self, *items):
        self._data = collections.OrderedDict()
        for key, value in items:
            self._data[key] = value

    def __repr__(self):
        return "PackageContext({!r})".format(dict(list(self._data.items())))

    def __iter__(self):
        yield from self._data.items()

    def __len__(self):
        return len(self._data)

    def __contains__(self, key):
        return key in self._data

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __delitem__(self, key):
        del self._data[key]

    @classmethod
    @auto_close_old_connections()
    def load_from_db(cls, uuid):
        """
        Loads a context from the UnitVariable table.
        """
        context = cls()

        # TODO: we shouldn't need one UnitVariable per chain, with all the same values
        unit_vars_queryset = models.UnitVariable.objects.filter(
            unituuid=uuid, variable="replacementDict"
        )
        # Distinct helps here, at least
        unit_vars_queryset = unit_vars_queryset.values_list("variablevalue").distinct()
        for unit_var_value in unit_vars_queryset:
            # TODO: nope nope nope, fix eval usage
            try:
                unit_var = ast.literal_eval(unit_var_value[0])
            except (ValueError, SyntaxError):
                logger.exception(
                    "Failed to eval unit variable value %s", unit_var_value[0]
                )
            else:
                context.update(unit_var)

        return context

    def copy(self):
        clone = PackageContext()
        clone._data = self._data.copy()

        return clone

    def update(self, mapping):
        for key, value in mapping.items():
            self._data[key] = value


class PackageNotFoundError(Exception):
    pass


@dataclass
class PackageStatus:
    status: int = None
    job: str = None


@auto_close_old_connections()
def get_package_status(package_queue, package_id: str) -> PackageStatus:
    try:
        sip = models.SIP.objects.get(pk=package_id)
    except models.SIP.DoesNotExist:
        raise PackageNotFoundError

    def get_latest_job(unit_id):
        return (
            models.Job.objects.filter(sipuuid=unit_id)
            .order_by("-createdtime", "-createdtimedec")
            .first()
        )

    package = package_queue.active_packages.get(package_id)
    if package:
        # Reminder: package.subid can be in Transfer or Ingest.
        job = get_latest_job(package.subid)
        kwargs = dict(status=a3m_pb2.PROCESSING)
        if job:
            kwargs.update({"job": job.jobtype})
        return PackageStatus(**kwargs)

    # A3M-TODO: persist package-workflow status!
    # It'd be much easier if a workflow instance could keep the package
    # model(s) up to date.

    # We have an inactive package, look up the status in the database.
    job = get_latest_job(package_id)

    # It must be an error during Transfer when Ingest activity not recorded.
    if not job:
        transfer_id = sip.transfer_id
        if transfer_id is None:
            raise Exception(
                "Package status cannot be determined: transfer_id is undefined"
            )
        job = get_latest_job(sip.transfer_id)
        if job is None:
            raise Exception(
                "Package status cannot be determined: transfer records are unavailable"
            )

    if job.currentstep == models.Job.STATUS_AWAITING_DECISION:
        status = a3m_pb2.AWAITING_DECISION
    elif "failed" in job.microservicegroup.lower():
        status = a3m_pb2.FAILED
    elif "reject" in job.microservicegroup.lower():
        status = a3m_pb2.REJECTED
    elif job.jobtype == "a3m - Store AIP":
        status = a3m_pb2.COMPLETE
    else:
        raise Exception(
            f"Package status cannot be determined (job.currentstep={job.currentstep}, job.type={job.jobtype}, job.microservicegroup={job.microservicegroup})"
        )

    return PackageStatus(status=status, job=job.microservicegroup)
