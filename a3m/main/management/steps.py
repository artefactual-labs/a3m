# -*- coding: utf-8 -*-
# This file is part of Archivematica.
#
# Copyright 2010-2016 Artefactual Systems Inc. <http://artefactual.com>
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
from __future__ import absolute_import

import logging
import uuid

from django.conf import settings as django_settings
from django.contrib.auth import get_user_model

from a3m.main.models import Agent, DashboardSetting
from a3m.helpers import get_setting, set_setting
import a3m.storageService as storage_service
from a3m.version import get_version


logger = logging.getLogger("archivematica.dashboard")


def create_super_user(username, email, password, key):
    UserModel = get_user_model()
    # Create the new super user if it doesn't already exist
    try:
        UserModel._default_manager.get(**{UserModel.USERNAME_FIELD: username})
    except UserModel.DoesNotExist:
        # User doesn't exist, create it
        UserModel._default_manager.db_manager("default").create_superuser(
            username, email, password
        )


def set_agent_code(agent_code, pk):
    archivematica_agent = Agent.objects.get(pk=pk)
    archivematica_agent.identifiervalue = agent_code
    archivematica_agent.save()


def setup_pipeline(org_name, org_identifier, site_url):
    dashboard_uuid = get_setting("dashboard_uuid")
    # Setup pipeline only if dashboard_uuid doesn't already exists
    if dashboard_uuid:
        return

    # Assign UUID to Dashboard
    dashboard_uuid = str(uuid.uuid4())
    set_setting("dashboard_uuid", dashboard_uuid)

    # Update Archivematica version in DB
    set_agent_code("Archivematica-" + get_version(), pk=1)

    if org_name != "" or org_identifier != "":
        agent = get_agent()
        agent.name = org_name
        agent.identifiertype = "repository code"
        agent.identifiervalue = org_identifier
        agent.save()

    if site_url:
        set_setting("site_url", site_url)


def setup_pipeline_in_ss(use_default_config=False):
    # Check if pipeline is already registered on SS
    dashboard_uuid = get_setting("dashboard_uuid")
    try:
        storage_service.get_pipeline(dashboard_uuid)
    except Exception:
        logger.warning("SS inaccessible or pipeline not registered.")
    else:
        # If pipeline is already registered on SS, then exit
        logger.warning("This pipeline is already configured on SS.")
        return

    if not use_default_config:
        # Storage service manually set up, just register Pipeline if
        # possible. Do not provide additional information about the shared
        # path, or API, as this is probably being set up in the storage
        # service manually.
        storage_service.create_pipeline()
        return

    # Retrieve remote name
    try:
        setting = DashboardSetting.objects.get(name="site_url")
    except DashboardSetting.DoesNotExist:
        remote_name = None
    else:
        remote_name = setting.value

    # Create pipeline, tell it to use default setup
    storage_service.create_pipeline(
        create_default_locations=True,
        shared_path=django_settings.SHARED_DIRECTORY,
        remote_name=remote_name,
    )


def get_agent():
    return Agent.objects.get(pk=2)
