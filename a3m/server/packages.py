"""Package management."""
import abc
import ast
import collections
import logging
import os
from uuid import UUID
from uuid import uuid4

from django.conf import settings

from a3m.archivematicaFunctions import strToUnicode
from a3m.main import models
from a3m.server.db import auto_close_old_connections
from a3m.server.jobs import JobChain
from a3m.server.rpc import a3m_pb2
from a3m.server.utils import uuid_from_path


logger = logging.getLogger(__name__)


StartingPoint = collections.namedtuple("StartingPoint", "watched_dir chain link")


def _get_setting(name):
    """Retrieve a Django setting decoded as a unicode string."""
    return strToUnicode(getattr(settings, name))


BASE_REPLACEMENTS = {
    r"%tmpDirectory%": os.path.join(_get_setting("SHARED_DIRECTORY"), "tmp", ""),
    r"%processingDirectory%": _get_setting("PROCESSING_DIRECTORY"),
    r"%watchDirectoryPath%": _get_setting("WATCH_DIRECTORY"),
    r"%rejectedDirectory%": _get_setting("REJECTED_DIRECTORY"),
}


@auto_close_old_connections()
def create_package(package_queue, executor, workflow, name, url):
    """Launch transfer and return its object immediately."""
    if not name:
        raise ValueError("No transfer name provided.")
    if not url:
        raise ValueError("No url provided.")

    transfer = models.Transfer.objects.create(uuid=uuid4())
    transfer.set_processing_configuration("automated")
    logger.debug("Transfer object created: %s", transfer.pk)

    params = (transfer, name, url, workflow, package_queue)
    future = executor.submit(_trigger_workflow, *params)
    future.add_done_callback(_trigger_workflow_done_callback)

    return transfer


def _trigger_workflow_done_callback(future):
    try:
        future.result()
    except Exception as err:
        logger.warning("Exception detected: %s", err, exc_info=True)


def _trigger_workflow(transfer, name, url, workflow, package_queue):
    logger.debug("Package %s: starting workflow processing", transfer.pk)
    chain_id = "2671aef1-653a-49bf-bc74-82572b64ace9"
    link_id = "8e3e2bf8-a543-43f9-bb2a-c3df01f112df"

    unit = Transfer("", transfer.pk, url)

    job_chain = JobChain(
        unit,
        workflow.get_chain(chain_id),
        workflow,
        starting_link=workflow.get_link(link_id),
    )

    package_queue.schedule_job(next(job_chain))


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


class Package(metaclass=abc.ABCMeta):
    """A `Package` can be a Transfer or a SIP.
    """

    def __init__(self, current_path, uuid):
        self._current_path = current_path.replace(
            r"%sharedPath%", _get_setting("SHARED_DIRECTORY")
        )
        if uuid and not isinstance(uuid, UUID):
            uuid = UUID(uuid)
        self.uuid = uuid

    def __repr__(self):
        return '{class_name}("{current_path}", {uuid})'.format(
            class_name=self.__class__.__name__,
            uuid=self.uuid,
            current_path=self.current_path,
        )

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
    def package_name(self):
        basename = os.path.basename(self.current_path.rstrip("/"))
        return basename.replace("-" + str(self.uuid), "")

    @property
    @auto_close_old_connections()
    def base_queryset(self):
        return models.File.objects.filter(sip_id=self.uuid)

    @property
    def context(self):
        """Returns a `PackageContext` for this package.
        """
        # This needs to be reloaded from the db every time, because new values
        # could have been added by a client script.
        # TODO: pass context changes back from client
        return PackageContext.load_from_db(self.uuid)

    @abc.abstractmethod
    def reload(self):
        pass

    def get_replacement_mapping(self, filter_subdir_path=None):
        mapping = BASE_REPLACEMENTS.copy()
        mapping.update(
            {
                r"%SIPUUID%": str(self.uuid),
                r"%SIPName%": self.package_name,
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

        return mapping

    def files(
        self, filter_filename_start=None, filter_filename_end=None, filter_subdir=None
    ):
        """Generator that yields all files associated with the package or that
        should be associated with a package.
        """
        with auto_close_old_connections():
            queryset = self.base_queryset

            if filter_filename_start:
                # TODO: regex filter
                raise NotImplementedError("filter_filename_start is not implemented")
            if filter_filename_end:
                queryset = queryset.filter(
                    currentlocation__endswith=filter_filename_end
                )
            if filter_subdir:
                filter_path = "".join([self.REPLACEMENT_PATH_STRING, filter_subdir])
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
                    if (
                        filter_filename_start
                        and not file_name.startswith(filter_filename_start)
                    ) or (
                        filter_filename_end
                        and not file_name.endswith(filter_filename_end)
                    ):
                        continue
                    file_path = os.path.join(basedir, file_name)
                    if file_path not in files_returned_already:
                        yield {
                            r"%relativeLocation%": file_path,
                            r"%fileUUID%": "None",
                            r"%fileGrpUse%": "",
                        }

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
            unittype=self.UNIT_VARIABLE_TYPE,
            unituuid=self.uuid,
            variable=key,
            defaults=dict(variablevalue=value, microservicechainlink=chain_link_id),
        )
        if created:
            message = "New UnitVariable %s created for %s: %s (MSCL: %s)"
        else:
            message = "Existing UnitVariable %s for %s updated to %s (MSCL" " %s)"

        logger.info(message, key, self.uuid, value, chain_link_id)


class Transfer(Package):
    REPLACEMENT_PATH_STRING = r"%transferDirectory%"
    UNIT_VARIABLE_TYPE = "Transfer"
    JOB_UNIT_TYPE = "unitTransfer"

    def __init__(self, current_path, uuid, url):
        super().__init__(current_path, uuid)
        self.url = url or ""

    @classmethod
    @auto_close_old_connections()
    def get_or_create_from_db_by_path(cls, path):
        """Matches a directory to a database Transfer by its appended UUID, or path."""
        path = path.replace(_get_setting("SHARED_DIRECTORY"), r"%sharedPath%", 1)

        transfer_uuid = uuid_from_path(path)
        created = True
        if transfer_uuid:
            transfer_obj, created = models.Transfer.objects.get_or_create(
                uuid=transfer_uuid, defaults={"currentlocation": path}
            )
            # TODO: we thought this path was unused but some tests have proved
            # us wrong (see issue #1141) - needs to be investigated.
            if not created and transfer_obj.currentlocation != path:
                transfer_obj.currentlocation = path
                transfer_obj.save()
        else:
            try:
                transfer_obj = models.Transfer.objects.get(currentlocation=path)
                created = False
            except models.Transfer.DoesNotExist:
                transfer_obj = models.Transfer.objects.create(
                    uuid=uuid4(), currentlocation=path
                )
        logger.info(
            "Transfer %s %s (%s)",
            transfer_obj.uuid,
            "created" if created else "updated",
            path,
        )

        return cls(path, transfer_obj.uuid, None)

    @property
    @auto_close_old_connections()
    def base_queryset(self):
        return models.File.objects.filter(transfer_id=self.uuid)

    @auto_close_old_connections()
    def reload(self):
        transfer = models.Transfer.objects.get(uuid=self.uuid)
        self.current_path = transfer.currentlocation
        self.processing_configuration = transfer.processing_configuration

    def get_replacement_mapping(self, filter_subdir_path=None):
        mapping = super().get_replacement_mapping(filter_subdir_path=filter_subdir_path)

        mapping.update(
            {
                self.REPLACEMENT_PATH_STRING: self.current_path,
                r"%unitType%": "Transfer",
                r"%processingConfiguration%": self.processing_configuration,
                r"%URL%": self.url,
            }
        )

        return mapping


class SIP(Package):
    REPLACEMENT_PATH_STRING = r"%SIPDirectory%"
    UNIT_VARIABLE_TYPE = "SIP"
    JOB_UNIT_TYPE = "unitSIP"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.aip_filename = None
        self.sip_type = None

    @auto_close_old_connections()
    def reload(self):
        sip = models.SIP.objects.get(uuid=self.uuid)
        self.current_path = sip.currentpath
        self.aip_filename = sip.aip_filename or ""
        self.sip_type = sip.sip_type

    def get_replacement_mapping(self, filter_subdir_path=None):
        mapping = super().get_replacement_mapping(filter_subdir_path=filter_subdir_path)

        mapping.update(
            {
                r"%unitType%": "SIP",
                r"%AIPFilename%": self.aip_filename,
                r"%SIPType%": self.sip_type,
            }
        )

        return mapping

    @classmethod
    @auto_close_old_connections()
    def get_or_create_from_db_by_path(cls, path):
        """Matches a directory to a database SIP by its appended UUID, or path."""
        path = path.replace(_get_setting("SHARED_DIRECTORY"), r"%sharedPath%", 1)
        package_type = cls.UNIT_VARIABLE_TYPE
        sip_uuid = uuid_from_path(path)
        created = True
        if sip_uuid:
            sip_obj, created = models.SIP.objects.get_or_create(
                uuid=sip_uuid,
                defaults={
                    "sip_type": package_type,
                    "currentpath": path,
                    "diruuids": False,
                },
            )
            # TODO: we thought this path was unused but some tests have proved
            # us wrong (see issue #1141) - needs to be investigated.
            if package_type == "SIP" and (not created and sip_obj.currentpath != path):
                sip_obj.currentpath = path
                sip_obj.save()
        else:
            try:
                sip_obj = models.SIP.objects.get(currentpath=path)
                created = False
            except models.SIP.DoesNotExist:
                sip_obj = models.SIP.objects.create(
                    uuid=uuid4(),
                    currentpath=path,
                    sip_type=package_type,
                    diruuids=False,
                )
        logger.info(
            "%s %s %s (%s)",
            package_type,
            sip_obj.uuid,
            "created" if created else "updated",
            path,
        )
        return cls(path, sip_obj.uuid)


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


@auto_close_old_connections()
def get_package_status(package_id):
    try:
        models.Transfer.objects.get(pk=package_id)
    except models.Transfer.DoesNotExist:
        raise PackageNotFoundError

    # A3M-TODO: it may raise if the transfer was just submitted and there
    # are zero jobs recorded.
    return get_unit_status(package_id, "unitTransfer")


def get_unit_status(unit_uuid, unit_type):
    """Get status for a SIP or Transfer.

    Returns a dict with status info. Keys will always include 'status' and
    'microservice', and may include 'sip_uuid'.

    SIP UUID is populated only if the unit_type was unitTransfer and status is
    COMPLETE. Otherwise, it is None.

    :param str unit_uuid: UUID of the SIP or Transfer
    :param str unit_type: unitSIP or unitTransfer
    :return: Dict with status info.
    """
    status = None
    ret = {}

    # Get jobs for the current unit ordered by created time.
    unit_jobs = (
        models.Job.objects.filter(sipuuid=unit_uuid)
        .filter(unittype=unit_type)
        .order_by("-createdtime", "-createdtimedec")
    )

    # Tentatively choose the job with the latest created time to be the
    # current/last for the unit.
    job = unit_jobs[0]

    ret["microservice"] = job.jobtype

    if job.currentstep == models.Job.STATUS_AWAITING_DECISION:
        status = a3m_pb2.AWAITING_DECISION
    elif "failed" in job.microservicegroup.lower():
        status = a3m_pb2.FAILED
    elif "reject" in job.microservicegroup.lower():
        status = a3m_pb2.REJECTED
    elif job.jobtype == "Verify AIP":
        status = a3m_pb2.COMPLETE
    elif unit_type == "unitTransfer" and (
        models.Job.objects.filter(sipuuid=unit_uuid)
        .filter(jobtype="Create SIP from transfer objects")
        .exists()
    ):
        # Get SIP UUID
        sips = (
            models.File.objects.filter(transfer_id=unit_uuid, sip__isnull=False)
            .values("sip")
            .distinct()
        )
        if not sips:
            raise Exception("SIP not found")
        #  A3M-TODO: we're returning the status of the SIP but instead we
        # could try to hide the transfer from the user.
        return get_unit_status(sips[0]["sip"], "unitSIP")
    else:
        status = a3m_pb2.PROCESSING

    # The job with the latest created time is not always the last/current
    # (Ref. https://github.com/archivematica/Issues/issues/262)
    # As a workaround for SIPs, in case the job with latest created time
    # is not the one that closes the chain, check if there could be a job
    # that does so
    # (a better fix would be to try to use microchain links related tables
    # to obtain the actual last/current job, but this adds too much complexity)
    if unit_type == "unitSIP" and status == a3m_pb2.PROCESSING:
        for x in unit_jobs:
            if x.jobtype == "Verify AIP":
                status = a3m_pb2.COMPLETE
                break

    return status, ret
