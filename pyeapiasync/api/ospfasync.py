#
# Copyright (c) 2016, Arista Networks, Inc.
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
"""Module for working with OSPF configuration in EOS asynchronously

This module provides an API for creating/modifying/deleting
OSPF configurations asynchronously

"""

import re
from pyeapiasync.api import EntityAsync
from pyeapiasync.utils import make_iterable


class OspfAsync(EntityAsync):
    """ The OspfAsync class implements global Ospf router configuration
     asynchronously
    """

    def __init__(self, *args, **kwargs):
        super(OspfAsync, self).__init__(*args, **kwargs)
        pass

    async def get(self, vrf=None):
        """Returns the OSPF routing configuration asynchronously

           Args:
                vrf (str): VRF name to return OSPF routing config for
           Returns:
               dict:
                    keys:
                         router_id (int): OSPF router-id

                         vrf (str): VRF of the OSPF process
                         networks (dict): All networks that
                         are advertised in OSPF

                         ospf_process_id (int): OSPF proc id

                         redistribution (dict): All protocols that
                         are configured to be redistributed in OSPF

                         shutdown (bool): Gives the current shutdown
                         off the process
        """
        match = '^router ospf .*'
        if vrf:
            match += ' vrf %s' % vrf
        config = await self.get_block(match)
        if not config:
            return None

        response = dict()
        response.update(self._parse_router_id(config))
        response.update(self._parse_vrf(config))
        response.update(self._parse_networks(config))
        response.update(self._parse_ospf_process_id(config))
        response.update(self._parse_redistribution(config))
        response.update(self._parse_shutdown(config))

        return response

    def _parse_ospf_process_id(self, config):
        """Parses config file for the OSPF proc ID

           Args:
               config(str):  Running configuration
           Returns:
               dict: key: ospf_process_id (int)
        """
        match = re.search(r'^router ospf (\d+)', config)
        return dict(ospf_process_id=int(match.group(1)))

    def _parse_vrf(self, config):
        """Parses config file for the OSPF vrf name

           Args:
               config(str):  Running configuration
           Returns:
               dict: key: ospf_vrf (str)
        """
        match = re.search(r'^router ospf \d+ vrf (\w+)', config)
        if match:
            return dict(vrf=match.group(1))
        return dict(vrf='default')

    def _parse_router_id(self, config):
        """Parses config file for the OSPF router ID

           Args:
               config(str):  Running configuration
           Returns:
               dict: key: router_id (str)
        """
        match = re.search(r'router-id ([^\s]+)', config)
        value = match.group(1) if match else None
        return dict(router_id=value)

    def _parse_networks(self, config):
        """Parses config file for the networks advertised
           by the OSPF process

           Args:
               config(str):  Running configuration
           Returns:
               list: dict:
                         keys: network (str)
                               netmask (str)
                               area (str)
        """

        networks = list()
        regexp = r'network (.+)/(\d+) area (\d+\.\d+\.\d+\.\d+)'
        matches = re.findall(regexp, config)
        for (network, netmask, area) in matches:
            networks.append(dict(network=network, netmask=netmask, area=area))
        return dict(networks=networks)

    def _parse_redistribution(self, config):
        """Parses config file for the OSPF router ID

           Args:
               config (str):  Running configuration
           Returns:
               list: dict:
                         keys: protocol (str)
                               route-map (optional) (str)
        """
        redistributions = list()
        regexp = r'redistribute .*'
        matches = re.findall(regexp, config)
        for line in matches:
            ospf_redist = line.split()
            if len(ospf_redist) == 2:
                # simple redist: eg 'redistribute bgp'
                protocol = ospf_redist[1]
                redistributions.append(dict(protocol=protocol))
            if len(ospf_redist) == 4:
                # complex redist eg 'redistribute bgp route-map NYSE-RP-MAP'
                protocol = ospf_redist[1]
                route_map_name = ospf_redist[3]
                redistributions.append(dict(protocol=protocol,
                                       route_map=route_map_name))
        return dict(redistributions=redistributions)

    def _parse_shutdown(self, config):
        """Parses config file for the OSPF router ID

           Args:
               config(str):  Running configuration
           Returns:
               dict: key: shutdown (bool)
        """

        value = 'no shutdown' in config
        return dict(shutdown=not value)

    async def set_shutdown(self):
        """Shutdowns the OSPF process asynchronously

           Args:
               None
           Returns:
              bool: True if the commands are completed successfully
        """

        cmd = 'shutdown'
        return await self.configure_ospf(cmd)

    async def set_no_shutdown(self):
        """Removes the shutdown property from the OSPF process
            asynchronously

           Args:
               None
           Returns:
              bool: True if the commands are completed successfully
        """

        cmd = 'no shutdown'
        return await self.configure_ospf(cmd)

    async def delete(self):
        """Removes the entire ospf process from the running configuration
            asynchronously

           Args:
               None
           Returns:
               bool: True if the command completed succssfully
        """
        config = await self.get()
        if not config:
            return True
        command = 'no router ospf {}'.format(config['ospf_process_id'])
        return await self.configure(command)

    async def create(self, ospf_process_id, vrf=None):
        """Creates a OSPF process in the specified VRF or the default VRF
            asynchronously.

           Args:
                ospf_process_id (str): The OSPF process Id value
                vrf (str): The VRF to apply this OSPF process to
           Returns:
                bool: True if the command completed successfully
           Exception:
                ValueError: If the ospf_process_id passed in less
                            than 0 or greater than 65536
        """
        value = int(ospf_process_id)
        if not 0 < value < 65536:
            raise ValueError('ospf as must be between 1 and 65535')
        command = 'router ospf {}'.format(ospf_process_id)
        if vrf:
            command += ' vrf %s' % vrf
        return await self.configure(command)

    async def configure_ospf(self, cmd):
        """Allows for a list of OSPF subcommands to be configured
            asynchronously"

           Args:
               cmd: (list or str): Subcommand to be entered
           Returns:
               bool: True if all the commands completed successfully
        """
        config = await self.get()
        cmds = ['router ospf {}'.format(config['ospf_process_id'])]
        cmds.extend(make_iterable(cmd))
        return await super(OspfAsync, self).configure(cmds)

    async def set_router_id(self, value=None, default=False, disable=False):
        """Controls the router id property for the OSPF Proccess asynchronously

           Args:
               value (str): The router-id value
               default (bool): Controls the use of the default keyword
               disable (bool): Controls the use of the no keyword
           Returns:
               bool: True if the commands are completed successfully
        """
        cmd = self.command_builder('router-id', value=value,
                                   default=default, disable=disable)
        return await self.configure_ospf(cmd)

    async def add_network(self, network, netmask, area=0):
        """Adds a network to be advertised by OSPF asynchronously

           Args:
               network (str):  The network to be advertised in dotted decimal
                               notation
               netmask (str):  The netmask to configure
               area (str):  The area the network belongs to.
                            By default this value is 0
           Returns:
               bool: True if the command completes successfully
           Exception:
               ValueError: This will get raised if network or netmask
                           are not passed to the method
        """
        if network == '' or netmask == '':
            raise ValueError('network and mask values '
                             'may not be empty')
        cmd = 'network {}/{} area {}'.format(network, netmask, area)
        return await self.configure_ospf(cmd)

    async def remove_network(self, network, netmask, area=0):
        """Removes a network advertisment by OSPF asynchronously

           Args:
               network (str):  The network to be removed in dotted decimal
                               notation
               netmask (str):  The netmask to configure
               area (str):  The area the network belongs to.
                            By default this value is 0
           Returns:
               bool: True if the command completes successfully
           Exception:
               ValueError: This will get raised if network or netmask
                           are not passed to the method
        """

        if network == '' or netmask == '':
            raise ValueError('network and mask values '
                             'may not be empty')
        cmd = 'no network {}/{} area {}'.format(network, netmask, area)
        return await self.configure_ospf(cmd)

    async def add_redistribution(self, protocol, route_map_name=None):
        """Adds a protocol redistribution to OSPF asynchronously

           Args:
               protocol (str):  protocol to redistribute
               route_map_name (str): route-map to be used to
                                     filter the protocols
           Returns:
               bool: True if the command completes successfully
           Exception:
               ValueError:  This will be raised if the protocol pass is not one
                            of the following: [rip, bgp, static, connected]
        """
        protocols = ['bgp', 'rip', 'static', 'connected']
        if protocol not in protocols:
            raise ValueError('redistributed protocol must be'
                             'bgp, connected, rip or static')
        if route_map_name is None:
            cmd = 'redistribute {}'.format(protocol)
        else:
            cmd = 'redistribute {} route-map {}'.format(protocol,
                                                        route_map_name)
        return await self.configure_ospf(cmd)

    async def remove_redistribution(self, protocol):
        """Removes a protocol redistribution to OSPF asynchronously

           Args:
               protocol (str):  protocol to redistribute
               route_map_name (str): route-map to be used to
                                     filter the protocols
           Returns:
               bool: True if the command completes successfully
           Exception:
               ValueError:  This will be raised if the protocol pass is not one
                            of the following: [rip, bgp, static, connected]
        """

        protocols = ['bgp', 'rip', 'static', 'connected']
        if protocol not in protocols:
            raise ValueError('redistributed protocol must be'
                             'bgp, connected, rip or static')
        cmd = 'no redistribute {}'.format(protocol)
        return await self.configure_ospf(cmd)


def instance(api):
    """Returns an instance of OspfAsync
    """
    return OspfAsync(api)
