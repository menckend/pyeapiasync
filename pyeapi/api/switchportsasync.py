#
# Copyright (c) 2014, Arista Networks, Inc.
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
"""Module for working with logical layer 2 switchports in EOS asynchronously

This module provides an API for working with logical layer 2 interfaces
(switchports) in EOS asynchronously. Switchports are interfaces built on top of
physical Ethernet and bundled Port-Channel interfaces.

"""

import re

from pyeapi.api import EntityCollectionAsync
from pyeapi.utils import make_iterable


class SwitchportsAsync(EntityCollectionAsync):
    """The SwitchportsAsync class provides a configuration resource for swichports asynchronously

    Logical layer 2 interfaces built on top of physical Ethernet and bundled
    Port-Channel interfaces can be configured and managed with an instance
    of SwitchportsAsync. The SwitchportsAsync class is a resource collection and
    supports get and getall methods. The SwitchportsAsync class is derived from
    the EntityCollectionAsync class

    """

    async def get(self, name):
        """Returns a dictionary object that represents a switchport asynchronously

        The Switchport resource returns the following:

            * name (str): The name of the interface
            * mode (str): The switchport mode value
            * access_vlan (str): The switchport access vlan value
            * trunk_native_vlan (str): The switchport trunk native vlan vlaue
            * trunk_allowed_vlans (str): The trunk allowed vlans value
            * trunk_groups (list): The list of trunk groups configured

        Args:
            name (string): The interface identifier to get.  Note: Switchports
                are only supported on Ethernet and Port-Channel interfaces

        Returns:
            dict: A Python dictionary object of key/value pairs that represent
                the switchport configuration for the interface specified  If
                the specified argument is not a switchport then None
                is returned
        """
        config = await self.get_block('interface %s' % name)
        if 'no switchport\n' in config:
            return

        resource = dict(name=name)
        resource.update(self._parse_mode(config))
        resource.update(self._parse_access_vlan(config))
        resource.update(self._parse_trunk_native_vlan(config))
        resource.update(self._parse_trunk_allowed_vlans(config))
        resource.update(self._parse_trunk_groups(config))
        return resource

    def _parse_mode(self, config):
        """Scans the specified config and parses the switchport mode value

        Args:
            config (str): The interface configuration block to scan

        Returns:
            dict: A Python dict object with the value of switchport mode.
                The dict returned is intended to be merged into the resource
                dict
        """
        value = re.search(r'switchport mode (\w+)', config, re.M)
        return dict(mode=value.group(1))

    def _parse_trunk_groups(self, config):
        """Scans the specified config and parses the trunk group values

        Args:
            config (str): The interface configuraiton blcok

        Returns:
            A dict object with the trunk group values that can be merged
                into the resource dict
        """
        values = re.findall(r'switchport trunk group ([^\s]+)', config, re.M)
        return dict(trunk_groups=values)

    def _parse_access_vlan(self, config):
        """Scans the specified config and parse the access-vlan value
        Args:
            config (str): The interface configuration block to scan

        Returns:
            dict: A Python dict object with the value of switchport access
                value.  The dict returned is intended to be merged into the
                resource dict
        """
        value = re.search(r'switchport access vlan (\d+)', config)
        return dict(access_vlan=value.group(1) if value else None)

    def _parse_trunk_native_vlan(self, config):
        """Scans the specified config and parse the trunk native vlan value

        Args:
            config (str): The interface configuration block to scan

        Returns:
            dict: A Python dict object with the value of switchport trunk
                native vlan value.  The dict returned is intended to be
                merged into the resource dict
        """
        match = re.search(r'switchport trunk native vlan (\d+)', config)
        return dict(trunk_native_vlan=match.group(1))

    def _parse_trunk_allowed_vlans(self, config):
        """Scans the specified config and parse the trunk allowed vlans value

        Args:
            config (str): The interface configuration block to scan

        Returns:
            dict: A Python dict object with the value of switchport trunk
                allowed vlans value.  The dict returned is intended to be
                merged into the resource dict
        """
        match = re.search(r'switchport trunk allowed vlan (.+)$', config, re.M)
        return dict(trunk_allowed_vlans=match.group(1))

    async def getall(self):
        """Returns a dict object to all Switchports asynchronously

        This method will return all of the configured switchports as a
        dictionary object keyed by the interface identifier.

        Returns:
            A Python dictionary object that represents all configured
                switchports in the current running configuration
        """
        interfaces_re = re.compile(r'(?<=^interface\s)([Et|Po][^.\s]+)$', re.M)
        config = await self.config

        response = dict()
        for name in interfaces_re.findall(config):
            interface = await self.get(name)
            if interface:
                response[name] = interface
        return response

    async def create(self, name):
        """Creates a new logical layer 2 interface asynchronously

        This method will create a new switchport for the interface specified
        in the arguments (name).  If the logical switchport already exists
        then this command will have no effect

        Args:
            name (string): The interface identifier to create the logical
                layer 2 switchport for.  The name must be the full interface
                name and not an abbreviated interface name (eg Ethernet1, not
                Et1)

        Returns:
            True if the create operation succeeds otherwise False.  If the
                interface specified in args is already a switchport then this
                method will have no effect but will still return True
        """
        commands = ['interface %s' % name, 'no ip address',
                    'switchport']
        return await self.configure(commands)

    async def delete(self, name):
        """Deletes the logical layer 2 interface asynchronously

        This method will delete the logical switchport for the interface
        specified in the arguments.  If the interface doe not have a logical
        layer 2 interface defined, then this method will have no effect.

        Args:
            name (string): The interface identifier to create the logical
                layer 2 switchport for.  The name must be the full interface
                name and not an abbreviated interface name (eg Ethernet1, not
                Et1)

        Returns:
            True if the create operation succeeds otherwise False.  If the
                interface specified in args is already a switchport then this
                method will have no effect but will still return True
        """
        commands = ['interface %s' % name, 'no switchport']
        return await self.configure(commands)

    async def default(self, name):
        """Defaults the configuration of the switchport interface asynchronously

        This method will default the configuration state of the logical
        layer 2 interface.

        Args:
            name (string): The interface identifier to create the logical
                layer 2 switchport for.  The name must be the full interface
                name and not an abbreviated interface name (eg Ethernet1, not
                Et1)

        Returns:
            True if the create operation succeeds otherwise False.  If the
                interface specified in args is already a switchport then this
                method will have no effect but will still return True
        """
        commands = ['interface %s' % name, 'no ip address',
                    'default switchport']
        return await self.configure(commands)

    async def set_mode(self, name, value=None, default=False, disable=False):
        """Configures the switchport mode asynchronously

        Args:
            name (string): The interface identifier to create the logical
                layer 2 switchport for.  The name must be the full interface
                name and not an abbreviated interface name (eg Ethernet1, not
                Et1)

            value (string): The value to set the mode to.  Accepted values
                for this argument are access or trunk

            default (bool): Configures the mode parameter to its default
                value using the EOS CLI

            disable (bool): Negate the mode parameter using the EOS CLI

        Returns:
            True if the create operation succeeds otherwise False.
        """
        string = 'switchport mode'
        command = self.command_builder(string, value=value, default=default,
                                       disable=disable)
        return await self.configure_interface(name, command)

    async def set_access_vlan(self, name, value=None, default=False, disable=False):
        """Configures the switchport access vlan asynchronously

        Args:
            name (string): The interface identifier to create the logical
                layer 2 switchport for.  The name must be the full interface
                name and not an abbreviated interface name (eg Ethernet1, not
                Et1)

            value (string): The value to set the access vlan to.  The value
                must be a valid VLAN ID in the range of 1 to 4094.

            default (bool): Configures the access vlan parameter to its default
                value using the EOS CLI

            disable (bool): Negate the access vlan parameter using the EOS CLI

        Returns:
            True if the create operation succeeds otherwise False.
        """
        string = 'switchport access vlan'
        command = self.command_builder(string, value=value, default=default,
                                       disable=disable)
        return await self.configure_interface(name, command)

    async def set_trunk_native_vlan(self, name, value=None, default=False,
                                   disable=False):
        """Configures the switchport trunk native vlan value asynchronously

        Args:
            name (string): The interface identifier to create the logical
                layer 2 switchport for.  The name must be the full interface
                name and not an abbreviated interface name (eg Ethernet1, not
                Et1)

            value (string): The value to set the trunk nativevlan to.  The
                value must be a valid VLAN ID in the range of 1 to 4094.

            default (bool): Configures the access vlan parameter to its default
                value using the EOS CLI

            disable (bool): Negate the access vlan parameter using the EOS CLI

        Returns:
            True if the create operation succeeds otherwise False.
        """
        string = 'switchport trunk native vlan'
        command = self.command_builder(string, value=value, default=default,
                                       disable=disable)
        return await self.configure_interface(name, command)

    async def set_trunk_allowed_vlans(self, name, value=None, default=False,
                                     disable=False):
        """Configures the switchport trunk allowed vlans value asynchronously

        Args:
            name (string): The interface identifier to create the logical
                layer 2 switchport for.  The name must be the full interface
                name and not an abbreviated interface name (eg Ethernet1, not
                Et1)

            value (string): The value to set the trunk allowed vlans to.  The
                value must be a valid VLAN ID in the range of 1 to 4094.

            default (bool): Configures the access vlan parameter to its default
                value using the EOS CLI

            disable (bool): Negate the access vlan parameter using the EOS CLI

        Returns:
            True if the create operation succeeds otherwise False.
        """
        string = 'switchport trunk allowed vlan'
        command = self.command_builder(string, value=value, default=default,
                                       disable=disable)
        return await self.configure_interface(name, command)

    async def set_trunk_groups(self, intf, value=None, default=False, disable=False):
        """Configures the switchport trunk group value asynchronously

        Args:
            intf (str): The interface identifier to configure.
            value (str): The set of values to configure the trunk group
            default (bool): Configures the trunk group default value
            disable (bool): Negates all trunk group settings

        Returns:
            True if the config operation succeeds otherwise False
        """
        if default:
            cmd = 'default switchport trunk group'
            return await self.configure_interface(intf, cmd)

        if disable:
            cmd = 'no switchport trunk group'
            return await self.configure_interface(intf, cmd)

        current_value = (await self.get(intf))['trunk_groups']
        failure = False

        value = make_iterable(value)

        for name in set(value).difference(current_value):
            if not await self.add_trunk_group(intf, name):
                failure = True

        for name in set(current_value).difference(value):
            if not await self.remove_trunk_group(intf, name):
                failure = True

        return not failure

    async def add_trunk_group(self, intf, value):
        """Adds the specified trunk group to the interface asynchronously

        Args:
            intf (str): The interface name to apply the trunk group to
            value (str): The trunk group value to apply to the interface

        Returns:
            True if the operation as successfully applied otherwise false
        """
        string = 'switchport trunk group {}'.format(value)
        return await self.configure_interface(intf, string)

    async def remove_trunk_group(self, intf, value):
        """Removes a specified trunk group to the interface asynchronously

        Args:
            intf (str): The interface name to remove the trunk group from
            value (str): The trunk group value

        Returns:
            True if the operation as successfully applied otherwise false
        """
        string = 'no switchport trunk group {}'.format(value)
        return await self.configure_interface(intf, string)


def instance(node):
    """Returns an instance of SwitchportsAsync

    This method will create and return an instance of the SwitchportsAsync object
    passing the value of node to the instance.  The module method is
    required for the resource to be autoloaded by the Node object

    Args:
        node (Node): The node argument provides an instance of Node to the
            resource
    """
    return SwitchportsAsync(node)
