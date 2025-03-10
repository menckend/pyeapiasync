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
"""Module for managing the NTP configuration in EOS asynchronously

This module provides an API for configuring NTP resources using
EOS and eAPI asynchronously.

Arguments:
    name (string): The interface port that specifies the NTP source.
"""

import re

from pyeapiasync.api import EntityAsync


class NtpAsync(EntityAsync):
    """The NtpAsync class implements global NTP router
    configuration asynchronously
    """

    def __init__(self, *args, **kwargs):
        super(NtpAsync, self).__init__(*args, **kwargs)

    async def get(self):
        """Returns the current NTP configuration asynchronously

        The NtpAsync resource returns the following:

            * source_interface (str): The interface port that specifies
                                      NTP server
            * servers (list): A list of the NTP servers that have been
                              assigned to the node. Each entry in the
                              list is a key/value pair of the name of
                              the server as the key and None or 'prefer'
                              as the value if the server is preferred.

        Returns:
            A Python dictionary object of key/value pairs that
            represents the current NTP configuration of the node::

                {
                    "source_interface": "Loopback0",
                    "servers": [
                        {"1.1.1.1": None},
                        {"1.1.1.2": "prefer"},
                        {"1.1.1.3": "prefer"},
                        {"1.1.1.4": None},
                    ]
                }
        """
        config = await self.config
        if not config:
            return None
        version = await self.get_version_number()
        response = dict()
        response.update(self._parse_source_interface(config, version))
        response.update(self._parse_servers(config))
        return response

    def _parse_source_interface(self, config, version):
        if version >= "4.23":
            match = re.search(r"^ntp local-interface (\S+)", config, re.M)
        else:
            match = re.search(r"^ntp source (\S+)", config, re.M)
        value = match.group(1) if match else None
        return dict(source_interface=value)

    def _parse_servers(self, config):
        matches = re.findall(r"ntp server (\S+) ?(prefer)?", config, re.M)
        value = []
        for match in matches:
            server = match[0]
            prefer = match[1] if match[1] == 'prefer' else None
            value.append({server: prefer})
        return dict(servers=value)

    async def create(self, name):
        """Instantiate the NTP by setting the source interface asynchronously.

        Args:
            name (string): The interface port that specifies the NTP source.

        Returns:
            True if the operation succeeds, otherwise False.
        """
        return await self.set_source_interface(name)

    async def delete(self):
        """Delete the NTP source entry from the node asynchronously.

        Returns:
            True if the operation succeeds, otherwise False.
        """
        if self.version_number >= '4.23':
            cmd = self.command_builder('ntp local-interface', disable=True)
        else:
            cmd = self.command_builder('ntp source', disable=True)
        return await self.configure(cmd)

    async def default(self):
        """Default the NTP source entry from the node asynchronously.

        Returns:
            True if the operation succeeds, otherwise False.
        """
        if self.version_number >= '4.23':
            cmd = self.command_builder('ntp local-interface', default=True)
        else:
            cmd = self.command_builder('ntp source', default=True)
        return await self.configure(cmd)

    async def set_source_interface(self, name):
        """Assign the NTP source on the node asynchronously

        Args:
            name (string): The interface port that specifies the NTP source.

        Returns:
            True if the operation succeeds, otherwise False.
        """
        if self.version_number >= '4.23':
            cmd = self.command_builder('ntp local-interface', value=name)
        else:
            cmd = self.command_builder('ntp source', value=name)
        return await self.configure(cmd)

    async def add_server(self, name, prefer=False):
        """Add or update an NTP server entry to the node config asynchronously

        Args:
            name (string): The IP address or FQDN of the NTP server.
            prefer (bool): Sets the NTP server entry as preferred if True.

        Returns:
            True if the operation succeeds, otherwise False.
        """
        if not name or re.match(r"^\s+$", name):
            raise ValueError('ntp server name must be specified')
        if prefer:
            name = '%s prefer' % name
        cmd = self.command_builder('ntp server', value=name)
        return await self.configure(cmd)

    async def remove_server(self, name):
        """Remove an NTP server entry from the node config asynchronously

        Args:
            name (string): The IP address or FQDN of the NTP server.

        Returns:
            True if the operation succeeds, otherwise False.
        """
        cmd = self.command_builder('no ntp server', value=name)
        return await self.configure(cmd)

    async def remove_all_servers(self):
        """Remove all NTP server entries from the node config asynchronously

        Returns:
            True if the operation succeeds, otherwise False.
        """
        # 'no ntp' removes all server entries.
        # For command_builder, disable command 'ntp' gives the desired command
        cmd = self.command_builder('ntp', disable=True)
        return await self.configure(cmd)


    def instance(node):
        """Returns an instance of NtpAsync

        This method will create and return an instance of the NtpAsync object
        passing the value of node to the object. The instance method is required
        for the resource to be autoloaded by the AsyncNode object

        Args:
            node (AsyncNode): The node argument passes an instance of
                AsyncNode to the resource

        Returns:
            An instance of NtpAsync
        """
        return NtpAsync(node)
