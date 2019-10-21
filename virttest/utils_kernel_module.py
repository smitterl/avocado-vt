# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See LICENSE for more details.
#
# Copyright: Red Hat Inc. 2020
# Author: Sebastian Mitterle <smitterl@redhat.com>

"""
Handle Linux kernel modules
"""

import os
import logging

from avocado.utils import process
from avocado.core import exceptions

def load(module_name, force, params):
    """
    Convenience method that creates and instance KernelModuleHandler instance
    and calls load_module only if any action will is required.

    :param module_name: name of kernel module to be handled
    :param force: if to force load with params in any case, e.g. True
    :param params: Parameters to load with, e.g. 'key1=param1 key2=param2 ...'
    :return: instance if module was loaded
    """

    if params != "" or force:
        handler = KernelModuleHandler(module_name)
        handler.load_module(force, params)
        return handler
    return None


class KernelModuleHandler(object):
    """Class handling Linux kernel modules"""

    def __init__(self, module_name):
        """Create kernel module handler"""

        self._module_name = module_name
        self._was_loaded = None
        self._loaded_config = None
        self._config_backup = None
        self._backup_config()

    def load_module(self, force, params):
        """
        Load module with given parameters

        :param force: if to force load with params in any case, e.g. True
        :param params: Parameters to load with, e.g. 'key1=param1 key2=param2 ...'
        """

        current_config = self._get_serialized_config()
        if not force:
            do_not_load = False
            if current_config and all(x in current_config.split() for x in params.split()):
                logging.debug("Not reloading module. Current module configuration for %s"
                              " already contains all requested parameters."
                              " Requested: '%s'. Current: '%s'. Use force=True to force"
                              " loading.", self._module_name, params, current_config)
                do_not_load = True
            elif not self._was_loaded:
                logging.debug("Module %s isn't loaded. Use force=True to force"
                              " loading.", self._module_name)
                do_not_load = True
            if do_not_load:
                return

        cmd = ""
        if self._was_loaded:
            cmd += 'rmmod %s; ' % self._module_name
        cmd += 'modprobe %s %s' % (self._module_name, params)
        cmd = cmd.strip()
        logging.debug("Loading module: %s", cmd)
        status, output = process.getstatusoutput(cmd, shell=True,
                                                 ignore_status=True)
        if status:
            raise exceptions.TestError("Couldn't load module %s: %s" % (
                self._module_name, output
            ))
        self._loaded_config = params

    def restore(self):
        """Restore previous module state"""

        if self._loaded_config is not None:
            if not self._was_loaded:
                cmd = 'rmmod %s' % self._module_name
            else:
                cmd = 'rmmod %s; modprobe %s %s' % (self._module_name,
                                                    self._module_name,
                                                    self._config_backup)
            cmd = cmd.strip()
            logging.debug("Restoring module state: %s", cmd)
            status = process.system(cmd, shell=True,
                                    ignore_status=True)
            if status:
                raise exceptions.TestError("Couldn't restore module %s: %s" % (
                    self._module_name, self._config_backup))

    def _backup_config(self):
        """
        Check if self.module_name is loaded and read config

        """
        config = self._get_serialized_config()
        if config is not None:
            self._config_backup = config
            self._was_loaded = True
        else:
            self._was_loaded = False
        logging.debug("Backed up %s module state (was_loaded, params)"
                      "=(%s, %s)", self._module_name, self._was_loaded,
                      self._config_backup)

    def get_was_loaded(self):
        """ Read-only property """

        return self._was_loaded

    def get_config_backup(self):
        """ Read-only property """

        return self._config_backup

    def _get_serialized_config(self):
        """
        Get current module parameters

        :return: String holding module config 'param1=value1 param2=value2 ...', None if
         module not loaded
        """

        mod_params_path = '/sys/module/%s/parameters/' % self._module_name
        if not os.path.exists(mod_params_path):
            return None

        mod_params = {}
        params = os.listdir(mod_params_path)
        for param in params:
            with open(os.path.join(mod_params_path, param), 'r') as param_file:
                mod_params[param] = param_file.read().strip()
        return " ".join("%s=%s" % _ for _ in mod_params.items()) if mod_params else ""
