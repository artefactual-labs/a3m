# -*- coding: utf-8 -*-
"""Package management."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import abc
import ast
import collections
import logging
import os
from uuid import UUID
from uuid import uuid4

import scandir
from django.conf import settings
from django.utils import six

from a3m.archivematicaFunctions import strToUnicode
from a3m.main import models
from a3m.server.db import auto_close_old_connections
from a3m.server.jobs import JobChain
from a3m.server.utils import uuid_from_path


logger = logging.getLogger("archivematica.mcp.server.packages")


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
    future = executor.submit(_trigger_worflow, *params)
    future.add_done_callback(_trigger_workflow_done_callback)

    return transfer


def _trigger_workflow_done_callback(future):
    try:
        future.result()
    except Exception as err:
        logger.warning("Exception detected: %s", err, exc_info=True)


def _trigger_worflow(transfer, name, url, workflow, package_queue):
    logger.debug("Package %s: starting workflow processing", transfer.pk)
    standard_workflow_chain = "6953950b-c101-4f4c-a0c3-0cd0684afe5e"
    standard_workflow_link = "045c43ae-d6cf-44f7-97d6-c8a602748565"
    unit = Transfer(url, transfer.pk)
    job_chain = JobChain(
        unit,
        workflow.get_chain(standard_workflow_chain),
        workflow,
        starting_link=workflow.get_link(standard_workflow_link),
    )

    # TODO: changes in workflow
    # - new chain with a link that
    #   - 1. downloads the file/direcotry
    #   - 2. performs identification
    #   - 3. decide new chain dynamically: standard / zippedDirectory / baggitDirectory / baggitZippedDirectory
    # - remove tranfser types maildir, dspace, trim

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


@six.add_metaclass(abc.ABCMeta)
class Package(object):
    """A `Package` can be a Transfer, a SIP, or a DIP.
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
        return basename.replace("-" + six.text_type(self.uuid), "")

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
                r"%SIPUUID%": six.text_type(self.uuid),
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

            for basedir, subdirs, files in scandir.walk(start_path):
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
            value = six.text_type(value)

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


class SIPDIP(Package):
    """SIPDIP captures behavior shared between SIP- and DIP-type packages that
    share the same model in Archivematica.
    """

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


class DIP(SIPDIP):
    REPLACEMENT_PATH_STRING = r"%SIPDirectory%"
    UNIT_VARIABLE_TYPE = "DIP"
    JOB_UNIT_TYPE = "unitDIP"

    def reload(self):
        # reload is a no-op for DIPs
        pass

    def get_replacement_mapping(self, filter_subdir_path=None):
        mapping = super(DIP, self).get_replacement_mapping(
            filter_subdir_path=filter_subdir_path
        )
        mapping[r"%unitType%"] = "DIP"

        if filter_subdir_path:
            relative_location = filter_subdir_path.replace(
                _get_setting("SHARED_DIRECTORY"), r"%sharedPath%", 1
            )
            mapping[r"%relativeLocation%"] = relative_location

        return mapping


class Transfer(Package):
    REPLACEMENT_PATH_STRING = r"%transferDirectory%"
    UNIT_VARIABLE_TYPE = "Transfer"
    JOB_UNIT_TYPE = "unitTransfer"

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

        return cls(path, transfer_obj.uuid)

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
        mapping = super(Transfer, self).get_replacement_mapping(
            filter_subdir_path=filter_subdir_path
        )

        mapping.update(
            {
                self.REPLACEMENT_PATH_STRING: self.current_path,
                r"%unitType%": "Transfer",
                r"%processingConfiguration%": self.processing_configuration,
            }
        )

        return mapping


class SIP(SIPDIP):
    REPLACEMENT_PATH_STRING = r"%SIPDirectory%"
    UNIT_VARIABLE_TYPE = "SIP"
    JOB_UNIT_TYPE = "unitSIP"

    def __init__(self, *args, **kwargs):
        super(SIP, self).__init__(*args, **kwargs)

        self.aip_filename = None
        self.sip_type = None

    @auto_close_old_connections()
    def reload(self):
        sip = models.SIP.objects.get(uuid=self.uuid)
        self.current_path = sip.currentpath
        self.aip_filename = sip.aip_filename or ""
        self.sip_type = sip.sip_type

    def get_replacement_mapping(self, filter_subdir_path=None):
        mapping = super(SIP, self).get_replacement_mapping(
            filter_subdir_path=filter_subdir_path
        )

        mapping.update(
            {
                r"%unitType%": "SIP",
                r"%AIPFilename%": self.aip_filename,
                r"%SIPType%": self.sip_type,
            }
        )

        return mapping


class PackageContext(object):
    """Package context tracks choices made previously while processing
    """

    def __init__(self, *items):
        self._data = collections.OrderedDict()
        for key, value in items:
            self._data[key] = value

    def __repr__(self):
        return "PackageContext({!r})".format(dict(list(self._data.items())))

    def __iter__(self):
        for key, value in six.iteritems(self._data):
            yield key, value

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
