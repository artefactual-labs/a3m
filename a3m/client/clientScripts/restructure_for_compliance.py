# This file is part of Archivematica.
#
# Copyright 2010-2013 Artefactual Systems Inc. <http://artefactual.com>
#
# Archivematica is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Archivematica is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.  If not, see <http://www.gnu.org/licenses/>.
import logging
import os
import shutil

from django.db import transaction

from a3m.archivematicaFunctions import create_structured_directory
from a3m.archivematicaFunctions import OPTIONAL_FILES
from a3m.archivematicaFunctions import REQUIRED_DIRECTORIES


logger = logging.getLogger(__name__)


def _move_file(job, src, dst, exit_on_error=True):
    logger.debug("Moving %s to %s", src, dst)
    try:
        shutil.move(src, dst)
    except OSError:
        job.pyprint("Could not move", src)
        if exit_on_error:
            raise


def restructure_transfer(job, unit_path):
    # Create required directories
    create_structured_directory(unit_path)

    # Move everything else to the objects directory
    for item in os.listdir(unit_path):
        src = os.path.join(unit_path, item)
        dst = os.path.join(unit_path, "objects", ".")
        if os.path.isdir(src) and item not in REQUIRED_DIRECTORIES:
            _move_file(job, src, dst)
        elif os.path.isfile(src) and item not in OPTIONAL_FILES:
            _move_file(job, src, dst)


def call(jobs):
    with transaction.atomic():
        for job in jobs:
            with job.JobContext(logger=logger):
                try:
                    sip_path = job.args[1]
                    restructure_transfer(job, sip_path)
                except OSError as err:
                    job.pyprint(repr(err))
                    job.set_status(1)
