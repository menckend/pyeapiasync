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

sys.path.append(os.path.join(os.path.dirname(__file__), '../lib'))

from testlib import get_fixture, async_function
from testlib import AsyncEapiConfigUnitTest

import pyeapi.api.ospfasync


class TestApiOspfAsync(AsyncEapiConfigUnitTest):

    def __init__(self, *args, **kwargs):
        super(TestApiOspfAsync, self).__init__(*args, **kwargs)
        self.instance = pyeapi.api.ospfasync.instance(None)
        self.config = open(get_fixture('running_config.ospf')).read()
        # Mock the get_block method to return test config
        self.instance.get_block = unittest.mock.AsyncMock(return_value=self.config)
        self.instance.configure = unittest.mock.AsyncMock(return_value=True)

    def test_instance(self):
        result = pyeapi.api.ospfasync.instance(None)
        self.assertIsInstance(result, pyeapi.api.ospfasync.OspfAsync)

    async def test_get_no_vrf(self):
        result = await self.instance.get()
        keys = ['networks', 'ospf_process_id', 'vrf', 'redistributions',
                'router_id', 'shutdown']
        self.assertEqual(sorted(keys), sorted(result.keys()))
        self.assertEqual(result['vrf'], 'default')

    async def test_get_with_vrf(self):
        result = await self.instance.get(vrf='test')
        keys = ['networks', 'ospf_process_id', 'vrf', 'redistributions',
                'router_id', 'shutdown']
        self.assertEqual(sorted(keys), sorted(result.keys()))
        self.assertEqual(result['vrf'], 'test')

    async def test_create(self):
        for ospf_id in ['65000', 65000]:
            func = async_function(self.instance.create, ospf_id)
            cmds = 'router ospf {}'.format(ospf_id)
            await self.async_eapi_positive_config_test(func, cmds)

    async def test_create_with_vrf(self):
        for ospf_id in ['65000', 65000]:
            vrf_name = 'test'
            func = async_function(self.instance.create, ospf_id, vrf_name)
            cmds = 'router ospf {} vrf {}'.format(ospf_id, vrf_name)
            await self.async_eapi_positive_config_test(func, cmds)

    async def test_create_invalid_id(self):
        for ospf_id in ['66000', 66000]:
            with self.assertRaises(ValueError):
                await self.instance.create(ospf_id)

    async def test_delete(self):
        # Mock get to return a specific config
        self.instance.get = unittest.mock.AsyncMock(
            return_value={'ospf_process_id': 65000})
        
        func = async_function(self.instance.delete)
        cmds = 'no router ospf 65000'
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_add_network(self):
        func = async_function(self.instance.add_network, '172.16.10.0', '24', '0')
        cmds = ['router ospf 65000', 'network 172.16.10.0/24 area 0']
        await self.async_eapi_positive_config_test(func, cmds)

        with self.assertRaises(ValueError):
            await self.instance.add_network('', '24', '0')

        with self.assertRaises(ValueError):
            await self.instance.add_network('172.16.10.0', '', '0')

    async def test_remove_network(self):
        func = async_function(self.instance.remove_network, '172.16.10.0', '24', '0')
        cmds = ['router ospf 65000', 'no network 172.16.10.0/24 area 0']
        await self.async_eapi_positive_config_test(func, cmds)

        with self.assertRaises(ValueError):
            await self.instance.remove_network('', '24', '0')

        with self.assertRaises(ValueError):
            await self.instance.remove_network('172.16.10.0', '', '0')

    async def test_set_router_id(self):
        for state in ['config', 'negate', 'default']:
            rid = '1.1.1.1'
            if state == 'config':
                cmds = ['router ospf 65000', 'router-id 1.1.1.1']
                func = async_function(self.instance.set_router_id, rid)
                await self.async_eapi_positive_config_test(func, cmds)
            elif state == 'negate':
                cmds = ['router ospf 65000', 'no router-id']
                func = async_function(self.instance.set_router_id, disable=True)
                await self.async_eapi_positive_config_test(func, cmds)
            elif state == 'default':
                cmds = ['router ospf 65000', 'default router-id']
                func = async_function(self.instance.set_router_id, rid, True)
                await self.async_eapi_positive_config_test(func, cmds)

        cmds = ['router ospf 65000', 'no router-id']
        func = async_function(self.instance.set_router_id)
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_shutdown(self):
        cmds = ['router ospf 65000', 'shutdown']
        func = async_function(self.instance.set_shutdown)
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_no_shutdown(self):
        cmds = ['router ospf 65000', 'no shutdown']
        func = async_function(self.instance.set_no_shutdown)
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_add_redistribution_no_route_map(self):
        for protocol in ['bgp', 'rip', 'static', 'connected']:
            cmds = ['router ospf 65000', 'redistribute {}'.format(protocol)]
            func = async_function(self.instance.add_redistribution, protocol)
            await self.async_eapi_positive_config_test(func, cmds)
            
        with self.assertRaises(ValueError):
            await self.instance.add_redistribution('no-proto')

    async def test_add_redistribution_with_route_map(self):
        for protocol in ['bgp', 'rip', 'static', 'connected']:
            cmds = ['router ospf 65000', 'redistribute {} route-map test'.format(protocol)]
            func = async_function(self.instance.add_redistribution, protocol, 'test')
            await self.async_eapi_positive_config_test(func, cmds)
            
        with self.assertRaises(ValueError):
            await self.instance.add_redistribution('no-proto', 'test')

    async def test_delete_redistribution_no_route_map(self):
        for protocol in ['bgp', 'rip', 'static', 'connected']:
            cmds = ['router ospf 65000', 'no redistribute {}'.format(protocol)]
            func = async_function(self.instance.remove_redistribution, protocol)
            await self.async_eapi_positive_config_test(func, cmds)
            
        with self.assertRaises(ValueError):
            await self.instance.remove_redistribution('no-proto')


class TestApiNegOspfAsync(AsyncEapiConfigUnitTest):

    def __init__(self, *args, **kwargs):
        super(TestApiNegOspfAsync, self).__init__(*args, **kwargs)
        self.instance = pyeapi.api.ospfasync.instance(None)
        self.config = open(get_fixture('running_config.bgp')).read()
        # Mock the get_block method to return test config
        self.instance.get_block = unittest.mock.AsyncMock(return_value=self.config)

    async def test_no_get(self):
        result = await self.instance.get()
        self.assertEqual(None, result)

    async def test_no_delete(self):
        result = await self.instance.delete()
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()