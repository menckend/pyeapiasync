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
import sys
import os
import unittest
import asyncio

sys.path.append(os.path.join(os.path.dirname(__file__), '../lib'))

from testlib import get_fixture, async_function
from testlib import AsyncEapiConfigUnitTest

import pyeapi.api.bgpasync


class TestApiBgpAsync(AsyncEapiConfigUnitTest):

    def setUp(self):
        super().setUp()
        self.instance = pyeapi.api.bgpasync.instance(None)
        self.config = open(get_fixture('running_config.bgp')).read()
        # Mock the config property to return the test config
        self.instance.get_block = unittest.mock.AsyncMock(return_value=self.config)
        self.instance.configure = unittest.mock.AsyncMock(return_value=True)

    def test_instance(self):
        result = pyeapi.api.bgpasync.instance(None)
        self.assertIsInstance(result, pyeapi.api.bgpasync.BgpAsync)

    async def test_get(self):
        # Mock neighbors.getall to return an empty dict
        self.instance.neighbors.getall = unittest.mock.AsyncMock(return_value={})
        
        result = await self.instance.get()
        keys = ['bgp_as', 'router_id', 'maximum_paths', 'maximum_ecmp_paths',
                'shutdown', 'neighbors', 'networks']
        self.assertEqual(sorted(keys), sorted(result.keys()))
        self.instance.get_block.assert_called_with('^router bgp .*')

    async def test_create(self):
        for bgp_as in ['65000', 65000]:
            await self.instance.create(bgp_as)
            cmds = 'router bgp {}'.format(bgp_as)
            self.instance.configure.assert_called_with(cmds)

    async def test_create_invalid_as(self):
        for bgp_as in ['66000', 66000]:
            with self.assertRaises(ValueError):
                await self.instance.create(bgp_as)

    async def test_delete(self):
        # Mock the get method to return a config with bgp_as = 65000
        self.instance.get = unittest.mock.AsyncMock(return_value={'bgp_as': 65000})
        
        await self.instance.delete()
        cmds = 'no router bgp 65000'
        self.instance.configure.assert_called_with(cmds)

    async def test_default(self):
        # Mock the get method to return a config with bgp_as = 65000
        self.instance.get = unittest.mock.AsyncMock(return_value={'bgp_as': 65000})
        
        await self.instance.default()
        cmds = 'default router bgp 65000'
        self.instance.configure.assert_called_with(cmds)

    async def test_add_network(self):
        # Mock the configure_bgp method and get method
        self.instance.get = unittest.mock.AsyncMock(return_value={'bgp_as': 65000})
        self.instance.configure = unittest.mock.AsyncMock(return_value=True)
        
        await self.instance.add_network('172.16.10.1', '24', 'test')
        cmds = ['router bgp 65000', 'network 172.16.10.1/24 route-map test']
        self.instance.configure.assert_called_with(cmds)

        with self.assertRaises(ValueError):
            await self.instance.add_network('', '24', 'test')

        with self.assertRaises(ValueError):
            await self.instance.add_network('172.16.10.1', '', 'test')

    async def test_remove_network(self):
        # Mock the configure_bgp method and get method
        self.instance.get = unittest.mock.AsyncMock(return_value={'bgp_as': 65000})
        self.instance.configure = unittest.mock.AsyncMock(return_value=True)
        
        await self.instance.remove_network('172.16.10.1', '24', 'test')
        cmds = ['router bgp 65000', 'no network 172.16.10.1/24 route-map test']
        self.instance.configure.assert_called_with(cmds)

        with self.assertRaises(ValueError):
            await self.instance.remove_network('', '24', 'test')

        with self.assertRaises(ValueError):
            await self.instance.remove_network('172.16.10.1', '', 'test')

    async def test_set_router_id(self):
        # Mock the configure_bgp method
        self.instance.configure_bgp = unittest.mock.AsyncMock(return_value=True)
        
        for state in ['config', 'negate', 'default']:
            rid = '1.1.1.1'
            if state == 'config':
                await self.instance.set_router_id(rid)
                self.instance.configure_bgp.assert_called_with('router-id 1.1.1.1')
            elif state == 'negate':
                await self.instance.set_router_id(None, False, True)
                self.instance.configure_bgp.assert_called_with('no router-id')
            elif state == 'default':
                await self.instance.set_router_id(rid, True)
                self.instance.configure_bgp.assert_called_with('default router-id')

        # Test with None value (no disable, no default)
        await self.instance.set_router_id(None)
        self.instance.configure_bgp.assert_called_with('no router-id')

    async def test_maximum_paths_just_max_path(self):
        # Mock the configure_bgp method
        self.instance.configure_bgp = unittest.mock.AsyncMock(return_value=True)
        
        for state in ['config', 'negate', 'default']:
            max_paths = 20
            if state == 'config':
                await self.instance.set_maximum_paths(max_paths)
                self.instance.configure_bgp.assert_called_with('maximum-paths 20')
            elif state == 'negate':
                await self.instance.set_maximum_paths(disable=True)
                self.instance.configure_bgp.assert_called_with('no maximum-paths')
            elif state == 'default':
                await self.instance.set_maximum_paths(default=True)
                self.instance.configure_bgp.assert_called_with('default maximum-paths')

        # Test with None value (no disable, no default)
        await self.instance.set_maximum_paths(None)
        self.instance.configure_bgp.assert_called_with('no maximum-paths')

    async def test_maximum_paths_max_path_and_ecmp(self):
        # Mock the configure_bgp method
        self.instance.configure_bgp = unittest.mock.AsyncMock(return_value=True)
        
        for state in ['config', 'negate', 'default']:
            max_paths = 20
            max_ecmp_path = 20
            if state == 'config':
                await self.instance.set_maximum_paths(max_paths, max_ecmp_path)
                self.instance.configure_bgp.assert_called_with('maximum-paths 20 ecmp 20')
            elif state == 'negate':
                await self.instance.set_maximum_paths(disable=True)
                self.instance.configure_bgp.assert_called_with('no maximum-paths')
            elif state == 'default':
                await self.instance.set_maximum_paths(default=True)
                self.instance.configure_bgp.assert_called_with('default maximum-paths')

        with self.assertRaises(TypeError):
            await self.instance.set_maximum_paths(max_path=None, max_ecmp_path=20)

    async def test_set_shutdown(self):
        # Mock the configure_bgp method
        self.instance.configure_bgp = unittest.mock.AsyncMock(return_value=True)
        
        for state in ['config', 'negate', 'default']:
            if state == 'config':
                await self.instance.set_shutdown(default=False, disable=False)
                self.instance.configure_bgp.assert_called_with('shutdown')
            elif state == 'negate':
                await self.instance.set_shutdown(disable=True)
                self.instance.configure_bgp.assert_called_with('no shutdown')
            elif state == 'default':
                await self.instance.set_shutdown(default=True)
                self.instance.configure_bgp.assert_called_with('default shutdown')


class TestApiBgpNeighborAsync(AsyncEapiConfigUnitTest):

    def setUp(self):
        super().setUp()
        self.instance = pyeapi.api.bgpasync.BgpNeighborsAsync(None)
        self.config = open(get_fixture('running_config.bgp')).read()
        # Mock the get_block and configure methods
        self.instance.get_block = unittest.mock.AsyncMock(return_value=self.config)
        self.instance.configure = unittest.mock.AsyncMock(return_value=True)
        # Mock the config property to return the test config
        self.instance.config = unittest.mock.AsyncMock(return_value=self.config)

    async def test_getall(self):
        # Mock the get method to return a simple neighbor config
        self.instance.get = unittest.mock.AsyncMock(return_value={
            'name': 'test',
            'send_community': True,
            'shutdown': False
        })
        
        result = await self.instance.getall()
        self.assertIsInstance(result, dict)
        self.instance.get_block.assert_called_with('^router bgp .*')

    async def test_get(self):
        result = await self.instance.get('test')
        keys = ['name', 'send_community', 'shutdown', 'description',
                'remote_as', 'next_hop_self', 'route_map_in', 'route_map_out',
                'peer_group']
        self.assertEqual(sorted(keys), sorted(result.keys()))
        self.instance.get_block.assert_called_with('^router bgp .*')

    async def test_delete(self):
        await self.instance.delete('test')
        self.instance.configure.assert_called_with('no neighbor test')

    def test_ispeergroup(self):
        # Test with IP address
        result = self.instance.ispeergroup('192.168.1.1')
        self.assertFalse(result)
        
        # Test with non-IP string
        result = self.instance.ispeergroup('peer-group-name')
        self.assertTrue(result)

    async def test_set_peer_group(self):
        # Mock the required methods
        self.instance.ispeergroup = unittest.mock.MagicMock(return_value=False)
        self.instance.command_builder = unittest.mock.MagicMock()
        self.instance.version_number = '4.20'
        
        for state in ['config', 'negate', 'default']:
            peer_group = 'test'
            name = '172.16.10.1'
            
            if state == 'config':
                self.instance.command_builder.return_value = 'neighbor 172.16.10.1 peer-group test'
                await self.instance.set_peer_group(name, peer_group)
                self.instance.command_builder.assert_called_with(name, 'peer-group', peer_group, False, False)
            elif state == 'negate':
                self.instance.command_builder.return_value = 'no neighbor 172.16.10.1 peer-group'
                await self.instance.set_peer_group(name, disable=True)
                self.instance.command_builder.assert_called_with(name, 'peer-group', None, False, True)
            elif state == 'default':
                self.instance.command_builder.return_value = 'default neighbor 172.16.10.1 peer-group'
                await self.instance.set_peer_group(name, peer_group, default=True)
                self.instance.command_builder.assert_called_with(name, 'peer-group', peer_group, True, False)

        # Test with version 4.23+
        self.instance.version_number = '4.23'
        self.instance.command_builder.return_value = 'neighbor 172.16.10.1 peer group test'
        await self.instance.set_peer_group('172.16.10.1', 'test')
        self.instance.command_builder.assert_called_with('172.16.10.1', 'peer group', 'test', False, False)

        # Test with a peer group name (should return False)
        self.instance.ispeergroup.return_value = True
        result = await self.instance.set_peer_group('peer-group-name', 'test')
        self.assertFalse(result)

    async def test_set_remote_as(self):
        # Mock the command_builder method
        self.instance.command_builder = unittest.mock.MagicMock()
        
        for state in ['config', 'negate', 'default']:
            remote_as = '65000'
            name = 'test'
            
            if state == 'config':
                self.instance.command_builder.return_value = 'neighbor test remote-as 65000'
                await self.instance.set_remote_as(name, remote_as)
                self.instance.command_builder.assert_called_with(name, 'remote-as', remote_as, False, False)
            elif state == 'negate':
                self.instance.command_builder.return_value = 'no neighbor test remote-as'
                await self.instance.set_remote_as(name, disable=True)
                self.instance.command_builder.assert_called_with(name, 'remote-as', None, False, True)
            elif state == 'default':
                self.instance.command_builder.return_value = 'default neighbor test remote-as'
                await self.instance.set_remote_as(name, remote_as, default=True)
                self.instance.command_builder.assert_called_with(name, 'remote-as', remote_as, True, False)

    async def test_set_shutdown(self):
        # Mock the command_builder method
        self.instance.command_builder = unittest.mock.MagicMock()
        
        for state in ['config', 'negate', 'default', 'false']:
            name = 'test'
            
            if state == 'config':
                self.instance.command_builder.return_value = 'neighbor test shutdown'
                await self.instance.set_shutdown(name, default=False, disable=False)
                self.instance.command_builder.assert_called_with(name, 'shutdown', True, False, False)
            elif state == 'negate':
                self.instance.command_builder.return_value = 'no neighbor test shutdown'
                await self.instance.set_shutdown(name, disable=True)
                self.instance.command_builder.assert_called_with(name, 'shutdown', True, False, True)
            elif state == 'default':
                self.instance.command_builder.return_value = 'default neighbor test shutdown'
                await self.instance.set_shutdown(name, default=True)
                self.instance.command_builder.assert_called_with(name, 'shutdown', True, True, False)
            elif state == 'false':
                self.instance.command_builder.return_value = 'no neighbor test shutdown'
                await self.instance.set_shutdown(name, disable=True)
                self.instance.command_builder.assert_called_with(name, 'shutdown', True, False, True)

    async def test_set_send_community(self):
        # Mock the command_builder method
        self.instance.command_builder = unittest.mock.MagicMock()
        
        for state in ['config', 'negate', 'default']:
            name = 'test'
            
            if state == 'config':
                self.instance.command_builder.return_value = 'neighbor test send-community'
                await self.instance.set_send_community(name, value=True)
                self.instance.command_builder.assert_called_with(name, 'send-community', True, False, False)
            elif state == 'negate':
                self.instance.command_builder.return_value = 'no neighbor test send-community'
                await self.instance.set_send_community(name, disable=True)
                self.instance.command_builder.assert_called_with(name, 'send-community', None, False, True)
            elif state == 'default':
                self.instance.command_builder.return_value = 'default neighbor test send-community'
                await self.instance.set_send_community(name, value=False, default=True)
                self.instance.command_builder.assert_called_with(name, 'send-community', False, True, False)

    async def test_set_next_hop_self(self):
        # Mock the command_builder method
        self.instance.command_builder = unittest.mock.MagicMock()
        
        for state in ['config', 'negate', 'default']:
            name = 'test'
            
            if state == 'config':
                self.instance.command_builder.return_value = 'neighbor test next-hop-self'
                await self.instance.set_next_hop_self(name, value=True)
                self.instance.command_builder.assert_called_with(name, 'next-hop-self', True, False, False)
            elif state == 'negate':
                self.instance.command_builder.return_value = 'no neighbor test next-hop-self'
                await self.instance.set_next_hop_self(name, disable=True)
                self.instance.command_builder.assert_called_with(name, 'next-hop-self', None, False, True)
            elif state == 'default':
                self.instance.command_builder.return_value = 'default neighbor test next-hop-self'
                await self.instance.set_next_hop_self(name, value=False, default=True)
                self.instance.command_builder.assert_called_with(name, 'next-hop-self', False, True, False)

    async def test_set_route_map_in(self):
        # Mock the command_builder method
        self.instance.command_builder = unittest.mock.MagicMock()
        
        for state in ['config', 'negate', 'default']:
            route_map = 'TEST_RM'
            name = 'test'
            
            if state == 'config':
                self.instance.command_builder.return_value = 'neighbor test route-map TEST_RM'
                await self.instance.set_route_map_in(name, value=route_map)
                self.instance.command_builder.assert_called_with(name, 'route-map', route_map, False, False)
            elif state == 'negate':
                self.instance.command_builder.return_value = 'no neighbor test route-map'
                await self.instance.set_route_map_in(name, disable=True)
                self.instance.command_builder.assert_called_with(name, 'route-map', None, False, True)
            elif state == 'default':
                self.instance.command_builder.return_value = 'default neighbor test route-map'
                await self.instance.set_route_map_in(name, value=route_map, default=True)
                self.instance.command_builder.assert_called_with(name, 'route-map', route_map, True, False)
            
            # Verify the ' in' suffix was added to the command
            self.instance.configure.assert_called_with('neighbor test route-map{} in'.format(
                f' {route_map}' if state == 'config' else ''))

    async def test_set_route_map_out(self):
        # Mock the command_builder method
        self.instance.command_builder = unittest.mock.MagicMock()
        
        for state in ['config', 'negate', 'default']:
            route_map = 'TEST_RM'
            name = 'test'
            
            if state == 'config':
                self.instance.command_builder.return_value = 'neighbor test route-map TEST_RM'
                await self.instance.set_route_map_out(name, value=route_map)
                self.instance.command_builder.assert_called_with(name, 'route-map', route_map, False, False)
            elif state == 'negate':
                self.instance.command_builder.return_value = 'no neighbor test route-map'
                await self.instance.set_route_map_out(name, disable=True)
                self.instance.command_builder.assert_called_with(name, 'route-map', None, False, True)
            elif state == 'default':
                self.instance.command_builder.return_value = 'default neighbor test route-map'
                await self.instance.set_route_map_out(name, value=route_map, default=True)
                self.instance.command_builder.assert_called_with(name, 'route-map', route_map, True, False)
            
            # Verify the ' out' suffix was added to the command
            self.instance.configure.assert_called_with('neighbor test route-map{} out'.format(
                f' {route_map}' if state == 'config' else ''))

    async def test_set_description(self):
        # Mock the command_builder method
        self.instance.command_builder = unittest.mock.MagicMock()
        
        for state in ['config', 'negate', 'default']:
            value = 'this is a test'
            name = 'test'
            
            if state == 'config':
                self.instance.command_builder.return_value = 'neighbor test description this is a test'
                await self.instance.set_description(name, value=value)
                self.instance.command_builder.assert_called_with(name, 'description', value, False, False)
            elif state == 'negate':
                self.instance.command_builder.return_value = 'no neighbor test description'
                await self.instance.set_description(name, disable=True)
                self.instance.command_builder.assert_called_with(name, 'description', None, False, True)
            elif state == 'default':
                self.instance.command_builder.return_value = 'default neighbor test description'
                await self.instance.set_description(name, value=value, default=True)
                self.instance.command_builder.assert_called_with(name, 'description', value, True, False)


if __name__ == '__main__':
    unittest.main()