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
import pyeapiasync.api.bgpasync as bgp
from unittest.mock import AsyncMock

sys.path.append(os.path.join(os.path.dirname(__file__), '../lib'))

from testlib import get_fixture, function
from testlib import EapiAsyncConfigUnitTest


class TestApiBgp(EapiAsyncConfigUnitTest):

    def __init__(self, *args, **kwargs):
        super(TestApiBgp, self).__init__(*args, **kwargs)
        self.instance = bgp.BgpAsync(None)
        self.config = open(get_fixture('running_config.bgp')).read()

    def setUp(self):
        super().setUp()
        self.node = AsyncMock()
        self.node.config = AsyncMock()
        self.node.config.return_value = 'router bgp 65000'

    async def test_get(self):
        self.instance.node = self.node
        result = await self.instance.get()
        keys = ['bgp_as', 'router_id', 'maximum_paths', 'maximum_ecmp_paths',
                'shutdown', 'neighbors', 'networks']
        self.assertEqual(sorted(keys), sorted(result.keys()))

    async def test_create(self):
        for bgpas in ['65000', 65000]:
            func = function('create', bgpas)
            cmds = ['router bgp %s' % bgpas]
            await self.eapi_positive_config_test(func, cmds)

    async def test_create_invalid_as(self):
        for bgpas in ['66000', 66000]:
            with self.assertRaises(ValueError):
                await self.instance.create(bgpas)

    async def test_delete(self):
        func = function('delete')
        cmds = ['no router bgp 65000']
        await self.eapi_positive_config_test(func, cmds)

    async def test_default(self):
        func = function('default')
        cmds = ['default router bgp 65000']
        await self.eapi_positive_config_test(func, cmds)

    async def test_add_network(self):
        func = function('add_network', '172.16.10.1', '24', 'test')
        cmds = ['router bgp 65000', 'network 172.16.10.1/24 route-map test']
        await self.eapi_positive_config_test(func, cmds)

        func = function('add_network', '', '24', 'test')
        await self.eapi_exception_config_test(func, ValueError)

        func = function('add_network', '172.16.10.1', '', 'test')
        await self.eapi_exception_config_test(func, ValueError)

    async def test_remove_network(self):
        func = function('remove_network', '172.16.10.1', '24', 'test')
        cmds = ['router bgp 65000', 'no network 172.16.10.1/24 route-map test']
        await self.eapi_positive_config_test(func, cmds)

        func = function('remove_network', '', '24', 'test')
        await self.eapi_exception_config_test(func, ValueError)

        func = function('remove_network', '172.16.10.1', '', 'test')
        await self.eapi_exception_config_test(func, ValueError)

    async def test_set_router_id(self):
        for state in ['config', 'negate', 'default']:
            rid = '1.1.1.1'
            if state == 'config':
                cmds = ['router bgp 65000', 'router-id 1.1.1.1']
                func = function('set_router_id', rid)
            elif state == 'negate':
                cmds = ['router bgp 65000', 'no router-id']
                func = function('set_router_id', None, False, True)
            elif state == 'default':
                cmds = ['router bgp 65000', 'default router-id']
                func = function('set_router_id', rid, True)
            await self.eapi_positive_config_test(func, cmds)

        cmds = ['router bgp 65000', 'no router-id']
        func = function('set_router_id', None)
        await self.eapi_positive_config_test(func, cmds)

    async def test_maximum_paths_just_max_path(self):
        for state in ['config', 'negate', 'default']:
            max_paths = 20
            if state == 'config':
                cmds = ['router bgp 65000', 'maximum-paths 20']
                func = function('set_maximum_paths', max_paths)
            elif state == 'negate':
                cmds = ['router bgp 65000', 'no maximum-paths']
                func = function('set_maximum_paths', disable=True)
            elif state == 'default':
                cmds = ['router bgp 65000', 'default maximum-paths']
                func = function('set_maximum_paths', default=True)
            await self.eapi_positive_config_test(func, cmds)

        cmds = ['router bgp 65000', 'no maximum-paths']
        func = function('set_maximum_paths', None)
        await self.eapi_positive_config_test(func, cmds)

    async def test_maximum_paths_max_path_and_ecmp(self):
        for state in ['config', 'negate', 'default']:
            max_paths = 20
            max_ecmp_path = 20
            if state == 'config':
                cmds = ['router bgp 65000', 'maximum-paths 20 ecmp 20']
                func = function('set_maximum_paths', max_paths, max_ecmp_path)
            elif state == 'negate':
                cmds = ['router bgp 65000', 'no maximum-paths']
                func = function('set_maximum_paths', disable=True)
            elif state == 'default':
                cmds = ['router bgp 65000', 'default maximum-paths']
                func = function('set_maximum_paths', default=True)
            await self.eapi_positive_config_test(func, cmds)

        func = function('set_maximum_paths', max_path=None, max_ecmp_path=20,
                        default=False, disable=False)
        await self.eapi_exception_config_test(func, TypeError)

    async def test_set_shutdown(self):
        for state in ['config', 'negate', 'default']:
            if state == 'config':
                cmds = ['router bgp 65000', 'shutdown']
                func = function('set_shutdown', default=False, disable=False)
            elif state == 'negate':
                cmds = ['router bgp 65000', 'no shutdown']
                func = function('set_shutdown', disable=True)
            elif state == 'default':
                cmds = ['router bgp 65000', 'default shutdown']
                func = function('set_shutdown', default=True)
            await self.eapi_positive_config_test(func, cmds)


class TestApiBgpNeighbor(EapiAsyncConfigUnitTest):

    def __init__(self, *args, **kwargs):
        super(TestApiBgpNeighbor, self).__init__(*args, **kwargs)
        self.instance = bgp.BgpNeighborsAsync(None)
        self.config = open(get_fixture('running_config.bgp')).read()

    def setUp(self):
        super().setUp()
        self.node = AsyncMock()
        self.node.config = AsyncMock()
        self.node.config.return_value = 'router bgp 65000'

    async def test_getall(self):
        self.instance.node = self.node
        result = await self.instance.getall()
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 3)

    async def test_get(self):
        self.instance.node = self.node
        result = await self.instance.get('test')
        keys = ['name', 'send_community', 'shutdown', 'description',
                'remote_as', 'next_hop_self', 'route_map_in', 'route_map_out',
                'peer_group']
        self.assertEqual(sorted(keys), sorted(result.keys()))

    async def test_delete(self):
        func = function('delete', 'test')
        cmds = ['router bgp 65000', 'no neighbor test']
        await self.eapi_positive_config_test(func, cmds)

    async def test_set_peer_group(self):
        for state in ['config', 'negate', 'default']:
            peer_group = 'test'
            name = '172.16.10.1'
            cmd = 'neighbor {} peer-group'.format(name)
            if state == 'config':
                cmds = ['router bgp 65000', '{} {}'.format(cmd, peer_group)]
                func = function('set_peer_group', name, peer_group)
            elif state == 'negate':
                cmds = ['router bgp 65000', 'no {}'.format(cmd)]
                func = function('set_peer_group', name, disable=True)
            elif state == 'default':
                cmds = ['router bgp 65000', 'default {}'.format(cmd)]
                func = function('set_peer_group', name, peer_group, default=True)
            await self.eapi_positive_config_test(func, cmds)

        cmds = ['router bgp 65000', 'no neighbor 172.16.10.1 peer-group']
        func = function('set_peer_group', '172.16.10.1', None)
        await self.eapi_positive_config_test(func, cmds)

    async def test_set_remote_as(self):
        for state in ['config', 'negate', 'default']:
            remote_as = '65000'
            name = 'test'
            cmd = 'neighbor {} remote-as'.format(name)
            if state == 'config':
                cmds = ['router bgp 65000', '{} {}'.format(cmd, remote_as)]
                func = function('set_remote_as', name, remote_as)
            elif state == 'negate':
                cmds = ['router bgp 65000', 'no {}'.format(cmd)]
                func = function('set_remote_as', name, disable=True)
            elif state == 'default':
                cmds = ['router bgp 65000', 'default {}'.format(cmd)]
                func = function('set_remote_as', name, remote_as, default=True)
            await self.eapi_positive_config_test(func, cmds)

        cmds = ['router bgp 65000', 'no neighbor test remote-as']
        func = function('set_remote_as', 'test', None)
        await self.eapi_positive_config_test(func, cmds)

    async def test_set_shutdown(self):
        for state in ['config', 'negate', 'default', 'false']:
            name = 'test'
            cmd = 'neighbor {}'.format(name)
            if state == 'config':
                cmds = ['router bgp 65000', '{} shutdown'.format(cmd)]
                func = function('set_shutdown', name, default=False, disable=False)
            elif state == 'negate':
                cmds = ['router bgp 65000', 'no {} shutdown'.format(cmd)]
                func = function('set_shutdown', name, disable=True)
            elif state == 'default':
                cmds = ['router bgp 65000', 'default {} shutdown'.format(cmd)]
                func = function('set_shutdown', name, default=True)
            elif state == 'false':
                cmds = ['router bgp 65000', 'no {} shutdown'.format(cmd)]
                func = function('set_shutdown', name, disable=True)
            await self.eapi_positive_config_test(func, cmds)

    async def test_set_send_community(self):
        for state in ['config', 'negate', 'default']:
            name = 'test'
            cmd = 'neighbor {}'.format(name)
            if state == 'config':
                cmds = ['router bgp 65000', '{} send-community'.format(cmd)]
                func = function('set_send_community', name, value=True)
            elif state == 'negate':
                cmds = ['router bgp 65000', 'no {} send-community'.format(cmd)]
                func = function('set_send_community', name, disable=True)
            elif state == 'default':
                cmds = ['router bgp 65000', 'default {} send-community'.format(cmd)]
                func = function('set_send_community', name, value=False, default=True)
            await self.eapi_positive_config_test(func, cmds)

        cmds = ['router bgp 65000', 'no neighbor test send-community']
        func = function('set_send_community', 'test', None)
        await self.eapi_positive_config_test(func, cmds)

    async def test_set_next_hop_self(self):
        for state in ['config', 'negate', 'default']:
            name = 'test'
            cmd = 'neighbor {}'.format(name)
            if state == 'config':
                cmds = ['router bgp 65000', '{} next-hop-self'.format(cmd)]
                func = function('set_next_hop_self', name, value=True)
            elif state == 'negate':
                cmds = ['router bgp 65000', 'no {} next-hop-self'.format(cmd)]
                func = function('set_next_hop_self', name, disable=True)
            elif state == 'default':
                cmds = ['router bgp 65000', 'default {} next-hop-self'.format(cmd)]
                func = function('set_next_hop_self', name, value=False, default=True)
            await self.eapi_positive_config_test(func, cmds)

        cmds = ['router bgp 65000', 'no neighbor test next-hop-self']
        func = function('set_next_hop_self', 'test', None)
        await self.eapi_positive_config_test(func, cmds)

    async def test_set_route_map_in(self):
        for state in ['config', 'negate', 'default']:
            route_map = 'TEST_RM'
            name = 'test'
            cmd = 'neighbor {} route-map'.format(name)
            if state == 'config':
                cmds = ['router bgp 65000', '{} {} in'.format(cmd, route_map)]
                func = function('set_route_map_in', name, value=route_map)
            elif state == 'negate':
                cmds = ['router bgp 65000', 'no {} in'.format(cmd)]
                func = function('set_route_map_in', name, disable=True)
            elif state == 'default':
                cmds = ['router bgp 65000', 'default {} in'.format(cmd)]
                func = function('set_route_map_in', name, value=route_map, default=True)
            await self.eapi_positive_config_test(func, cmds)

        cmds = ['router bgp 65000', 'no neighbor test route-map in']
        func = function('set_route_map_in', 'test', None)
        await self.eapi_positive_config_test(func, cmds)

    async def test_set_route_map_out(self):
        for state in ['config', 'negate', 'default']:
            route_map = 'TEST_RM'
            name = 'test'
            cmd = 'neighbor {} route-map'.format(name)
            if state == 'config':
                cmds = ['router bgp 65000', '{} {} out'.format(cmd, route_map)]
                func = function('set_route_map_out', name, value=route_map)
            elif state == 'negate':
                cmds = ['router bgp 65000', 'no {} out'.format(cmd)]
                func = function('set_route_map_out', name, disable=True)
            elif state == 'default':
                cmds = ['router bgp 65000', 'default {} out'.format(cmd)]
                func = function('set_route_map_out', name, value=route_map, default=True)
            await self.eapi_positive_config_test(func, cmds)

        cmds = ['router bgp 65000', 'no neighbor test route-map out']
        func = function('set_route_map_out', 'test', None)
        await self.eapi_positive_config_test(func, cmds)

    async def test_set_description(self):
        for state in ['config', 'negate', 'default']:
            value = 'this is a test'
            name = 'test'
            cmd = 'neighbor {} description'.format(name)
            if state == 'config':
                cmds = ['router bgp 65000', '{} {}'.format(cmd, value)]
                func = function('set_description', name, value=value)
            elif state == 'negate':
                cmds = ['router bgp 65000', 'no {}'.format(cmd)]
                func = function('set_description', name, disable=True)
            elif state == 'default':
                cmds = ['router bgp 65000', 'default {}'.format(cmd)]
                func = function('set_description', name, value=value, default=True)
            await self.eapi_positive_config_test(func, cmds)

        cmds = ['router bgp 65000', 'no neighbor test description']
        func = function('set_description', 'test', None)
        await self.eapi_positive_config_test(func, cmds)


if __name__ == '__main__':
    unittest.main()
