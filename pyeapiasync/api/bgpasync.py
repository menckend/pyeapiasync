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
"""API module for Bgp asynchronous operations

This module provides an asynchronous implementation for configuring and
managing BGP routing on Arista EOS nodes. It provides the following
class implementations:

    * BgpAsync -- Configures global BGP router configuration asynchronously
    * BgpNeighborsAsync -- Configures BGP neighbors asynchronously

"""

import re
from collections import namedtuple
import netaddr

from pyeapiasync.api import EntityAsync, EntityCollectionAsync
from pyeapiasync.utils import make_iterable

Network = namedtuple('Network', 'prefix length route_map')


class BgpAsync(EntityAsync):
    """The BgpAsync class implements global BGP router configuration
    asynchronously

    This class provides a configuration resource for BGP settings
    including router-id, AS number, maximum paths, and network advertisements.
    """

    def __init__(self, *args, **kwargs):
        super(BgpAsync, self).__init__(*args, **kwargs)
        self._neighbors = None

    @property
    def neighbors(self):
        """Returns an instance of BgpNeighborsAsync

        Returns:
            An instance of BgpNeighborsAsync
        """
        if self._neighbors is not None:
            return self._neighbors
        self._neighbors = BgpNeighborsAsync(self.node)
        return self._neighbors

    async def get(self):
        """Returns the bgp routing configuration as a dict object
            asynchronously

        Returns:
            dict: A dictionary object of BGP attributes including:
                * bgp_as (int): The BGP autonomous system number
                * router_id (str): The BGP router ID
                * maximum_paths (int): The maximum paths value
                * maximum_ecmp_paths (int): The maximum ECMP paths value
                * shutdown (bool): Shutdown state of BGP process
                * networks (list): List of network advertisements
                * neighbors (dict): Dictionary of BGP neighbors

        Returns None if BGP is not configured.
        """
        config = await self.get_block('^router bgp .*')
        if not config:
            return None
        response = dict()
        response.update(self._parse_bgp_as(config))
        response.update(self._parse_router_id(config))
        response.update(self._parse_max_paths(config))
        response.update(self._parse_shutdown(config))
        response.update(self._parse_networks(config))
        response['neighbors'] = await self.neighbors.getall()
        return response

    def _parse_bgp_as(self, config):
        """Parses the BGP autonomous system number from the config

        Args:
            config (str): The BGP configuration block

        Returns:
            dict: Dictionary containing the BGP AS number
        """
        as_num = re.search(r'(?<=^router bgp ).*', config).group(0)
        return {'bgp_as': int(as_num) if as_num.isnumeric() else as_num}

    def _parse_router_id(self, config):
        """Parses the BGP router-id from the config

        Args:
            config (str): The BGP configuration block

        Returns:
            dict: Dictionary containing the router-id
        """
        match = re.search(r'router-id ([^\s]+)', config)
        value = match.group(1) if match else None
        return dict(router_id=value)

    def _parse_max_paths(self, config):
        """Parses the BGP maximum paths settings from the config

        Args:
            config (str): The BGP configuration block

        Returns:
            dict: Dictionary containing maximum_paths and maximum_ecmp_paths
        """
        match = re.search(r'maximum-paths\s+(\d+)\s+ecmp\s+(\d+)', config)
        paths = int(match.group(1)) if match else None
        ecmp_paths = int(match.group(2)) if match else None
        return dict(maximum_paths=paths, maximum_ecmp_paths=ecmp_paths)

    def _parse_shutdown(self, config):
        """Parses the BGP shutdown state from the config

        Args:
            config (str): The BGP configuration block

        Returns:
            dict: Dictionary containing shutdown state boolean
        """
        value = 'no shutdown' in config
        return dict(shutdown=not value)

    def _parse_networks(self, config):
        """Parses BGP network advertisements from the config

        Args:
            config (str): The BGP configuration block

        Returns:
            dict: Dictionary containing list of network advertisements
        """
        networks = list()
        regexp = r'network (.+)/(\d+)(?: route-map (\w+))*'
        matches = re.findall(regexp, config)
        for (prefix, mask, rmap) in matches:
            rmap = None if rmap == '' else rmap
            networks.append(dict(prefix=prefix, masklen=mask, route_map=rmap))
        return dict(networks=networks)

    async def configure_bgp(self, cmd):
        """Configures the BGP process with the specified command asynchronously

        Args:
            cmd (str or list): The command(s) to send to the node in BGP
                context

        Returns:
            bool: True if the commands completed successfully otherwise False
        """
        config = await self.get()
        cmds = ['router bgp {}'.format(config['bgp_as'])]
        cmds.extend(make_iterable(cmd))
        return await super(BgpAsync, self).configure(cmds)

    async def create(self, bgp_as):
        """Creates a new BGP process with the specified AS asynchronously

        Args:
            bgp_as (int or str): The BGP autonomous system number

        Returns:
            bool: True if the command completed successfully otherwise False

        Raises:
            ValueError: If the bgp_as value is not valid (1-65535)
        """
        value = int(bgp_as)
        if not 0 < value < 65536:
            raise ValueError('bgp as must be between 1 and 65535')
        command = 'router bgp {}'.format(bgp_as)
        return await self.configure(command)

    async def delete(self):
        """Deletes the BGP process from the configuration asynchronously

        Returns:
            bool: True if the command completed successfully otherwise False
        """
        config = await self.get()
        if not config:
            return True
        command = 'no router bgp {}'.format(config['bgp_as'])
        return await self.configure(command)

    async def default(self):
        """Defaults the BGP process configuration asynchronously

        Returns:
            bool: True if the command completed successfully otherwise False
        """
        config = await self.get()
        if not config:
            return True
        command = 'default router bgp {}'.format(config['bgp_as'])
        return await self.configure(command)

    async def set_router_id(self, value=None, default=False, disable=False):
        """Configures the BGP router-id asynchronously

        Args:
            value (str): The router-id value (IPv4 format)
            default (bool): If True, defaults the router-id
            disable (bool): If True, removes the router-id configuration

        Returns:
            bool: True if the command completed successfully otherwise False
        """
        cmd = self.command_builder('router-id', value=value,
                                   default=default, disable=disable)
        return await self.configure_bgp(cmd)

    async def set_maximum_paths(self, max_path=None, max_ecmp_path=None,
                                default=False, disable=False):
        """Configures the BGP maximum paths settings asynchronously

        Args:
            max_path (int): The maximum paths value
            max_ecmp_path (int): The maximum ECMP paths value
            default (bool): If True, defaults the maximum paths settings
            disable (bool): If True, removes the maximum paths configuration

        Returns:
            bool: True if the command completed successfully otherwise False

        Raises:
            TypeError: If max_ecmp_path is specified without max_path
        """
        if not max_path and max_ecmp_path:
            raise TypeError('Cannot use maximum_ecmp_paths without '
                            'providing max_path')
        value = None
        if max_path:
            value = '{}'.format(max_path)
            if max_ecmp_path:
                value += ' ecmp {}'.format(max_ecmp_path)
        cmd = self.command_builder('maximum-paths', value=value,
                                   default=default, disable=disable)
        return await self.configure_bgp(cmd)

    async def set_shutdown(self, default=False, disable=True):
        """Sets the BGP shutdown state asynchronously

        Args:
            default (bool): If True, sets the shutdown state to default
            disable (bool): If True, disables the shutdown state

        Returns:
            bool: True if the command completed successfully otherwise False
        """
        # Default setting for BGP shutdown is disable=True,
        # meaning 'no shutdown'.
        # If both default and disable are false, BGP shutdown will
        # effectively be enabled.
        cmd = self.command_builder('shutdown', value=True, default=default,
                                   disable=disable)
        return await self.configure_bgp(cmd)

    async def add_network(self, prefix, length, route_map=None):
        """Adds a network advertisement to the BGP process asynchronously

        Args:
            prefix (str): The network prefix to advertise
            length (int): The network prefix length
            route_map (str): The route-map to apply to the network

        Returns:
            bool: True if the command completed successfully otherwise False

        Raises:
            ValueError: If prefix or length values are empty
        """
        if prefix == '' or length == '':
            raise ValueError('network prefix and length values '
                             'may not be empty')
        cmd = 'network {}/{}'.format(prefix, length)
        if route_map:
            cmd += ' route-map {}'.format(route_map)
        return await self.configure_bgp(cmd)

    async def remove_network(self, prefix, masklen, route_map=None):
        """Removes a network advertisement from the BGP process asynchronously

        Args:
            prefix (str): The network prefix to remove
            masklen (int): The network prefix length
            route_map (str): The route-map to apply to the network

        Returns:
            bool: True if the command completed successfully otherwise False

        Raises:
            ValueError: If prefix or masklen values are empty
        """
        if prefix == '' or masklen == '':
            raise ValueError('network prefix and length values '
                             'may not be empty')
        cmd = 'no network {}/{}'.format(prefix, masklen)
        if route_map:
            cmd += ' route-map {}'.format(route_map)
        return await self.configure_bgp(cmd)


class BgpNeighborsAsync(EntityCollectionAsync):
    """The BgpNeighborsAsync class implements BGP neighbor configuration
        asynchronously

    This class provides a configuration resource for BGP neighbors including
    peer groups, remote AS settings, descriptions, and route policy
    configuration.
    """

    async def get(self, name):
        """Returns the neighbor configuration for the specified neighbor
            asynchronously

        Args:
            name (str): The neighbor name or IP address

        Returns:
            dict: A dictionary object of BGP neighbor attributes including:
                * name (str): The BGP neighbor name
                * peer_group (str): The peer group name if configured
                * remote_as (str): The remote AS number
                * send_community (bool): Whether send-community is enabled
                * shutdown (bool): Whether the neighbor is shutdown
                * description (str): The neighbor description
                * next_hop_self (bool): Whether next-hop-self is enabled
                * route_map_in (str): The inbound route-map name
                * route_map_out (str): The outbound route-map name
        """
        config = await self.get_block('^router bgp .*')
        response = dict(name=name)
        response.update(self._parse_peer_group(config, name))
        response.update(self._parse_remote_as(config, name))
        response.update(self._parse_send_community(config, name))
        response.update(self._parse_shutdown(config, name))
        response.update(self._parse_description(config, name))
        response.update(self._parse_next_hop_self(config, name))
        response.update(self._parse_route_map_in(config, name))
        response.update(self._parse_route_map_out(config, name))
        return response

    async def getall(self):
        """Returns all configured neighbors asynchronously

        Returns:
            dict: A dictionary of all BGP neighbors indexed by name
                or None if BGP is not configured
        """
        config = await self.get_block('^router bgp .*')
        if not config:
            return None

        collection = dict()
        for neighbor in re.findall(r'neighbor ([^\s]+)', config):
            collection[neighbor] = await self.get(neighbor)
        return collection

    def _parse_peer_group(self, config, name):
        """Parses the peer group configuration for the neighbor

        Args:
            config (str): The BGP configuration block
            name (str): The neighbor name

        Returns:
            dict: Dictionary containing the peer_group value
        """
        if self.version_number >= '4.23':
            regexp = r'neighbor {} peer group ([^\s]+)'.format(name)
        else:
            regexp = r'neighbor {} peer-group ([^\s]+)'.format(name)
        match = re.search(regexp, config)
        value = match.group(1) if match else None
        return dict(peer_group=value)

    def _parse_remote_as(self, config, name):
        """Parses the remote-as configuration for the neighbor

        Args:
            config (str): The BGP configuration block
            name (str): The neighbor name

        Returns:
            dict: Dictionary containing the remote_as value
        """
        remote_as_re = rf'(?<=neighbor {name} remote-as ).*'
        match = re.search(remote_as_re, config)
        return {'remote_as': match.group(0) if match else None}

    def _parse_send_community(self, config, name):
        """Parses the send-community configuration for the neighbor

        Args:
            config (str): The BGP configuration block
            name (str): The neighbor name

        Returns:
            dict: Dictionary containing the send_community boolean
        """
        exp = 'no neighbor {} send-community'.format(name)
        value = exp in config
        return dict(send_community=not value)

    def _parse_shutdown(self, config, name):
        """Parses the shutdown configuration for the neighbor

        Args:
            config (str): The BGP configuration block
            name (str): The neighbor name

        Returns:
            dict: Dictionary containing the shutdown boolean
        """
        regexp = r'(?<!no )neighbor {} shutdown'.format(name)
        match = re.search(regexp, config, re.M)
        value = True if match else False
        return dict(shutdown=value)

    def _parse_description(self, config, name):
        """Parses the description configuration for the neighbor

        Args:
            config (str): The BGP configuration block
            name (str): The neighbor name

        Returns:
            dict: Dictionary containing the description string
        """
        regexp = r'neighbor {} description (.*)$'.format(name)
        match = re.search(regexp, config, re.M)
        value = match.group(1) if match else None
        return dict(description=value)

    def _parse_next_hop_self(self, config, name):
        """Parses the next-hop-self configuration for the neighbor

        Args:
            config (str): The BGP configuration block
            name (str): The neighbor name

        Returns:
            dict: Dictionary containing the next_hop_self boolean
        """
        exp = 'no neighbor {} next-hop-self'.format(name)
        value = exp in config
        return dict(next_hop_self=not value)

    def _parse_route_map_in(self, config, name):
        """Parses the inbound route-map configuration for the neighbor

        Args:
            config (str): The BGP configuration block
            name (str): The neighbor name

        Returns:
            dict: Dictionary containing the route_map_in value
        """
        regexp = r'neighbor {} route-map ([^\s]+) in'.format(name)
        match = re.search(regexp, config, re.M)
        value = match.group(1) if match else None
        return dict(route_map_in=value)

    def _parse_route_map_out(self, config, name):
        """Parses the outbound route-map configuration for the neighbor

        Args:
            config (str): The BGP configuration block
            name (str): The neighbor name

        Returns:
            dict: Dictionary containing the route_map_out value
        """
        regexp = r'neighbor {} route-map ([^\s]+) out'.format(name)
        match = re.search(regexp, config, re.M)
        value = match.group(1) if match else None
        return dict(route_map_out=value)

    def ispeergroup(self, name):
        """Determines if the name is a peer group or IP address

        Args:
            name (str): The neighbor name to check

        Returns:
            bool: True if name is a peer group, False if IP address
        """
        try:
            netaddr.IPAddress(name)
            return False
        except netaddr.core.AddrFormatError:
            return True

    async def create(self, name):
        """Creates a new BGP neighbor asynchronously

        Args:
            name (str): The neighbor name or IP address

        Returns:
            bool: True if the command completed successfully otherwise False
        """
        return await self.set_shutdown(name, default=False, disable=False)

    async def delete(self, name):
        """Deletes a BGP neighbor configuration asynchronously

        Args:
            name (str): The neighbor name or IP address

        Returns:
            bool: True if the command completed successfully otherwise False
        """
        response = await self.configure('no neighbor {}'.format(name))
        if not response:
            if self.version_number >= '4.23':
                response = await self.configure('no neighbor {} '
                                                'peer group'.format(name))
            else:
                response = await self.configure('no neighbor {} '
                                                'peer-group'.format(name))
        return response

    async def configure(self, cmd):
        """Configures the BGP neighbor with the specified command
            asynchronously

        Args:
            cmd (str or list): The command(s) to send to the node in BGP
                context

        Returns:
            bool: True if the commands completed successfully otherwise False

        Raises:
            ValueError: If BGP is not configured
        """
        config = await self.config
        match = re.search(r'router bgp (\d+)', config)
        if not match:
            raise ValueError('bgp is not configured')
        cmds = ['router bgp {}'.format(match.group(1)), cmd]
        return await super(BgpNeighborsAsync, self).configure(cmds)

    def command_builder(self, name, cmd, value, default, disable):
        """Builds a BGP neighbor command string

        Args:
            name (str): The neighbor name or IP address
            cmd (str): The command to build
            value (str): The value to set
            default (bool): Whether to default the command
            disable (bool): Whether to disable the command

        Returns:
            str: The built command string
        """
        string = 'neighbor {} {}'.format(name, cmd)
        return super(BgpNeighborsAsync, self).command_builder(
            string, value, default, disable)

    async def set_peer_group(self, name, value=None, default=False,
                             disable=False):
        """Sets the peer group for a BGP neighbor asynchronously

        Args:
            name (str): The neighbor name or IP address
            value (str): The peer group name to set
            default (bool): If True, defaults the peer group setting
            disable (bool): If True, removes the peer group configuration

        Returns:
            bool: True if the command completed successfully otherwise False
        """
        if not self.ispeergroup(name):
            if self.version_number >= '4.23':
                cmd = self.command_builder(name, 'peer group', value, default,
                                           disable)
            else:
                cmd = self.command_builder(name, 'peer-group', value, default,
                                           disable)
            return await self.configure(cmd)
        return False

    async def set_remote_as(self, name, value=None, default=False,
                            disable=False):
        """Sets the remote-as for a BGP neighbor asynchronously

        Args:
            name (str): The neighbor name or IP address
            value (str): The remote AS number to set
            default (bool): If True, defaults the remote-as setting
            disable (bool): If True, removes the remote-as configuration

        Returns:
            bool: True if the command completed successfully otherwise False
        """
        cmd = self.command_builder(name, 'remote-as', value, default, disable)
        return await self.configure(cmd)

    async def set_shutdown(self, name, default=False, disable=True):
        """Sets the shutdown state for a BGP neighbor asynchronously

        Args:
            name (str): The neighbor name or IP address
            default (bool): If True, defaults the shutdown setting
            disable (bool): If True (default), configures 'no shutdown'

        Returns:
            bool: True if the command completed successfully otherwise False
        """
        # Default setting for BGP neighbor shutdown is
        # disable=True, meaning 'no shutdown'
        # If both default and disable are false, BGP neighbor shutdown will
        # effectively be enabled.
        cmd = self.command_builder(name, 'shutdown', True, default, disable)
        return await self.configure(cmd)

    async def set_send_community(self, name, value=None, default=False,
                                 disable=False):
        """Sets the send-community state for a BGP neighbor asynchronously

        Args:
            name (str): The neighbor name or IP address
            value (str): The send-community value to set
            default (bool): If True, defaults the send-community setting
            disable (bool): If True, configures 'no send-community'

        Returns:
            bool: True if the command completed successfully otherwise False
        """
        cmd = self.command_builder(name, 'send-community', value, default,
                                   disable)
        return await self.configure(cmd)

    async def set_next_hop_self(self, name, value=None, default=False,
                                disable=False):
        """Sets the next-hop-self state for a BGP neighbor asynchronously

        Args:
            name (str): The neighbor name or IP address
            value (str): The next-hop-self value to set
            default (bool): If True, defaults the next-hop-self setting
            disable (bool): If True, configures 'no next-hop-self'

        Returns:
            bool: True if the command completed successfully otherwise False
        """
        cmd = self.command_builder(name, 'next-hop-self', value, default,
                                   disable)
        return await self.configure(cmd)

    async def set_route_map_in(self, name, value=None, default=False,
                               disable=False):
        """Sets the inbound route-map for a BGP neighbor asynchronously

        Args:
            name (str): The neighbor name or IP address
            value (str): The route-map name to set
            default (bool): If True, defaults the route-map setting
            disable (bool): If True, removes the route-map configuration

        Returns:
            bool: True if the command completed successfully otherwise False
        """
        cmd = self.command_builder(name, 'route-map', value, default, disable)
        cmd += ' in'
        return await self.configure(cmd)

    async def set_route_map_out(self, name, value=None, default=False,
                                disable=False):
        """Sets the outbound route-map for a BGP neighbor asynchronously

        Args:
            name (str): The neighbor name or IP address
            value (str): The route-map name to set
            default (bool): If True, defaults the route-map setting
            disable (bool): If True, removes the route-map configuration

        Returns:
            bool: True if the command completed successfully otherwise False
        """
        cmd = self.command_builder(name, 'route-map', value, default, disable)
        cmd += ' out'
        return await self.configure(cmd)

    async def set_description(self, name, value=None, default=False,
                              disable=False):
        """Sets the description for a BGP neighbor asynchronously

        Args:
            name (str): The neighbor name or IP address
            value (str): The description to set
            default (bool): If True, defaults the description setting
            disable (bool): If True, removes the description configuration

        Returns:
            bool: True if the command completed successfully otherwise False
        """
        cmd = self.command_builder(name, 'description', value, default,
                                   disable)
        return await self.configure(cmd)


def instance(node):
    """Returns an instance of BgpAsync

    This method will create and return an instance of the BgpAsync object
    passing the value of node to the object. The instance method is required
    for the resource to be autoloaded by the AsyncNode object

    Args:
        node (AsyncNode): The node argument passes an instance of
            AsyncNode to the resource

    Returns:
        An instance of BgpAsync
    """
    return BgpAsync(node)
