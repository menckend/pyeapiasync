#
# Copyright (c) 2015, Arista Networks, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#   Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
#   Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
#
#   Neither the name of Arista Networks nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL ARISTA NETWORKS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
"""Module for working with the global system in EOS asynchronously

This module provides an API for working with the global system settings
in EOS asynchronously. It provides the following class implementations:

    * SystemAsync -- Configures global system settings asynchronously

SystemAsync Attributes:
    hostname (string): The hostname of the node as configured in the
        running-configuration.

"""

import re

from pyeapi.api import EntityAsync


class SystemAsync(EntityAsync):
    """The SystemAsync class implements global config for the node asynchronously

    Global configuration settings include those thaat identify the node
    and provide node level configuration such as hostname
    """

    async def get(self):
        """Returns the system configuration abstraction asynchronously

        The SystemAsync resource returns the following:

            * hostname (str): The hostname value

        Returns:
            dict: Represents the node's system configuration
        """
        config = await self.config
        resource = dict()
        resource.update(self._parse_hostname(config))
        resource.update(self._parse_iprouting(config))
        resource.update(self._parse_banners(config))

        return resource

    def _parse_hostname(self, config):
        """Parses the global config and returns the hostname value

        Args:
            config (str): The running configuration

        Returns:
            dict: The configured value for hostname.  The returned dict
                object is intended to be merged into the resource dict
        """
        value = 'localhost'
        match = re.search(r'^hostname ([^\s]+)$', config, re.M)
        if match:
            value = match.group(1)
        return dict(hostname=value)

    def _parse_iprouting(self, config):
        """Parses the global config and returns the ip routing value

        Args:
            config (str): The running configuration

        Returns:
            dict: The configure value for ip routing.  The returned dict
                object is intendd to be merged into the resource dict
        """
        value = 'no ip routing' not in config
        return dict(iprouting=value)

    def _parse_banners(self, config):
        """Parses the global config and returns the value for both motd
            and login banners.

        Args:
            config (str): The running configuration

        Returns:
           dict: The configure value for modtd and login banners. If the
                  banner is not set it will return a value of None for that
                  key. The returned dict object is intendd to be merged
                  into the resource dict
        """
        motd_value = login_value = None
        matches = re.findall(r'^banner\s+(login|motd)\s?$\n(.*?)$\nEOF$\n',
                             config, re.DOTALL | re.M)
        for match in matches:
            if match[0].strip() == "motd":
                motd_value = match[1]
            elif match[0].strip() == "login":
                login_value = match[1]

        return dict(banner_motd=motd_value, banner_login=login_value)

    async def set_hostname(self, value=None, default=False, disable=False):
        """Configures the global system hostname setting asynchronously

        EosVersion:
            4.13.7M

        Args:
            value (str): The hostname value
            default (bool): Controls use of the default keyword
            disable (bool): Controls the use of the no keyword

        Returns:
            bool: True if the commands are completed successfully
        """
        cmd = self.command_builder('hostname', value=value, default=default,
                                   disable=disable)
        return await self.configure(cmd)

    async def set_iprouting(self, value=None, default=False, disable=False):
        """Configures the state of global ip routing asynchronously

        EosVersion:
            4.13.7M

        Args:
            value(bool): True if ip routing should be enabled or False if
                ip routing should be disabled
            default (bool): Controls the use of the default keyword
            disable (bool): Controls the use of the no keyword

        Returns:
            bool: True if the commands completed successfully otherwise False
        """
        if value is False:
            disable = True
        cmd = self.command_builder('ip routing', value=value, default=default,
                                   disable=disable)
        return await self.configure(cmd)

    async def set_banner(self, banner_type, value=None, default=False,
                        disable=False):
        """Configures system banners asynchronously

        Args:
            banner_type(str): banner to be changed (likely login or motd)
            value(str): value to set for the banner
            default (bool): Controls the use of the default keyword
            disable (bool): Controls the use of the no keyword`

        Returns:
            bool: True if the commands completed successfully otherwise False
        """

        command_string = "banner %s" % banner_type
        if default is True or disable is True:
            cmd = self.command_builder(command_string, value=None,
                                       default=default, disable=disable)
            return await self.configure(cmd)
        else:
            if not value.endswith("\n"):
                value = value + "\n"
            command_input = dict(cmd=command_string, input=value)
            return await self.configure([command_input])


def instance(api):
    """Returns an instance of SystemAsync
    """
    return SystemAsync(api)
