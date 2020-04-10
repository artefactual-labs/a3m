# -*- coding: utf-8 -*-

from __future__ import absolute_import

from a3m.main import models


def get_setting(setting, default=""):
    try:
        setting = models.DashboardSetting.objects.get(name=setting)
        return setting.value
    except:
        return default


def set_setting(setting, value=""):
    try:
        setting_data = models.DashboardSetting.objects.get(name=setting)
    except:
        setting_data = models.DashboardSetting.objects.create()
        setting_data.name = setting
    # ``DashboardSetting.value`` is a string-based field. The empty string is
    # the way to represent the lack of data, therefore NULL values are avoided.
    if value is None:
        value = ""
    setting_data.value = value
    setting_data.save()
