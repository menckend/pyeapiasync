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

from testlib import get_fixture, random_vlan, async_function
from testlib import AsyncEapiConfigUnitTest

import pyeapi.api.switchportsasync


class TestApiSwitchportsAsync(AsyncEapiConfigUnitTest):

    INTERFACES = ['Ethernet1', 'Ethernet1/1', 'Port-Channel1']

    def __init__(self, *args, **kwargs):
        super(TestApiSwitchportsAsync, self).__init__(*args, **kwargs)
        self.instance = pyeapi.api.switchportsasync.instance(None)
        self.config = open(get_fixture('running_config.text')).read()
        # Mock the get_block method to return test config
        self.instance.get_block = unittest.mock.AsyncMock(return_value=self.config)
        self.instance.configure = unittest.mock.AsyncMock(return_value=True)

    def test_instance(self):
        result = pyeapi.api.switchportsasync.instance(None)
        self.assertIsInstance(result, pyeapi.api.switchportsasync.SwitchportsAsync)

    async def test_get(self):
        result = await self.instance.get('Ethernet1')
        keys = ['name', 'mode', 'access_vlan', 'trunk_native_vlan',
                'trunk_allowed_vlans', 'trunk_groups']
        self.assertEqual(sorted(result.keys()), sorted(keys))
        self.instance.get_block.assert_called_once()

    async def test_getall(self):
        # Mock the node.enable method
        self.instance.node = unittest.mock.MagicMock()
        self.instance.node.enable = unittest.mock.AsyncMock(
            return_value=[{'result': {'interfaces': {
                'Ethernet1': {}, 'Ethernet2': {}, 'Ethernet3': {},
                'Ethernet4': {}, 'Ethernet5': {}, 'Ethernet6': {},
                'Ethernet7': {}, 'Ethernet8': {}, 'Port-Channel10': {}
            }}}])
            
        # Mock the get method to return consistently
        self.instance.get = unittest.mock.AsyncMock(return_value={
            'name': 'test', 'mode': 'access', 'access_vlan': '1',
            'trunk_native_vlan': '1', 'trunk_allowed_vlans': '1-4094',
            'trunk_groups': []
        })
            
        expected = sorted(['Port-Channel10',
                           'Ethernet1', 'Ethernet2',
                           'Ethernet3', 'Ethernet4',
                           'Ethernet5', 'Ethernet6',
                           'Ethernet7', 'Ethernet8'])
        result = await self.instance.getall()
        self.assertIsInstance(result, dict)
        self.assertEqual(sorted(result.keys()), expected)

    async def test_instance_functions(self):
        for name in ['create', 'delete', 'default']:
            if name == 'create':
                cmds = 'interface Ethernet1'
                func = async_function(self.instance.create, 'Ethernet1')
                await self.async_eapi_positive_config_test(func, cmds)
            elif name == 'delete':
                cmds = ['interface Ethernet1', 'no switchport']
                func = async_function(self.instance.delete, 'Ethernet1')
                await self.async_eapi_positive_config_test(func, cmds)
            elif name == 'default':
                cmds = 'default interface Ethernet1'
                func = async_function(self.instance.default, 'Ethernet1')
                await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_mode(self):
        for intf in self.INTERFACES:
            for mode in ['access', 'trunk']:
                cmds = ['interface %s' % intf, 'switchport mode %s' % mode]
                func = async_function(self.instance.set_mode, intf, mode)
                await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_mode_with_no_value(self):
        for intf in self.INTERFACES:
            cmds = ['interface %s' % intf, 'no switchport mode']
            func = async_function(self.instance.set_mode, intf, disable=True)
            await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_mode_with_default(self):
        for intf in self.INTERFACES:
            cmds = ['interface %s' % intf, 'default switchport mode']
            func = async_function(self.instance.set_mode, intf, default=True)
            await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_access_vlan(self):
        for intf in self.INTERFACES:
            vid = str(random_vlan())
            cmds = ['interface %s' % intf, 'switchport access vlan %s' % vid]
            func = async_function(self.instance.set_access_vlan, intf, vid)
            await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_access_vlan_with_no_value(self):
        for intf in self.INTERFACES:
            cmds = ['interface %s' % intf, 'no switchport access vlan']
            func = async_function(self.instance.set_access_vlan, intf, disable=True)
            await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_access_vlan_with_default(self):
        for intf in self.INTERFACES:
            cmds = ['interface %s' % intf, 'default switchport access vlan']
            func = async_function(self.instance.set_access_vlan, intf, default=True)
            await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_trunk_native_vlan(self):
        for intf in self.INTERFACES:
            vid = str(random_vlan())
            cmds = ['interface %s' % intf, 'switchport trunk native vlan %s' % vid]
            func = async_function(self.instance.set_trunk_native_vlan, intf, vid)
            await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_trunk_native_vlan_with_no_value(self):
        for intf in self.INTERFACES:
            cmds = ['interface %s' % intf, 'no switchport trunk native vlan']
            func = async_function(self.instance.set_trunk_native_vlan,
                              intf, disable=True)
            await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_trunk_native_vlan_with_default(self):
        for intf in self.INTERFACES:
            cmds = ['interface %s' % intf, 'default switchport trunk native vlan']
            func = async_function(self.instance.set_trunk_native_vlan,
                              intf, default=True)
            await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_trunk_allowed_vlans(self):
        for intf in self.INTERFACES:
            vid = '1,2,3-5,6,7'
            cmds = ['interface %s' % intf,
                    'switchport trunk allowed vlan %s' % vid]
            func = async_function(self.instance.set_trunk_allowed_vlans, intf, vid)
            await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_trunk_allowed_vlans_with_no_value(self):
        for intf in self.INTERFACES:
            cmds = ['interface %s' % intf, 'no switchport trunk allowed vlan']
            func = async_function(self.instance.set_trunk_allowed_vlans,
                              intf, disable=True)
            await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_trunk_allowed_vlans_with_default(self):
        for intf in self.INTERFACES:
            cmds = ['interface %s' % intf, 'default switchport trunk allowed vlan']
            func = async_function(self.instance.set_trunk_allowed_vlans,
                              intf, default=True)
            await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_trunk_groups(self):
        for intf in self.INTERFACES:
            value = ['test1', 'test2', 'test3']
            cmds = ['interface %s' % intf, 'no switchport trunk group']
            for name in value:
                cmds.append('switchport trunk group %s' % name)
            func = async_function(self.instance.set_trunk_groups, intf, value)
            await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_trunk_groups_with_empty_list(self):
        for intf in self.INTERFACES:
            cmds = ['interface %s' % intf, 'no switchport trunk group']
            func = async_function(self.instance.set_trunk_groups, intf, [])
            await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_trunk_groups_with_no_value(self):
        for intf in self.INTERFACES:
            cmds = ['interface %s' % intf, 'no switchport trunk group']
            func = async_function(self.instance.set_trunk_groups, intf, disable=True)
            await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_trunk_groups_with_default(self):
        for intf in self.INTERFACES:
            cmds = ['interface %s' % intf, 'default switchport trunk group']
            func = async_function(self.instance.set_trunk_groups, intf, default=True)
            await self.async_eapi_positive_config_test(func, cmds)

    async def test_add_trunk_group(self):
        for intf in self.INTERFACES:
            name = 'test'
            cmds = ['interface %s' % intf, 'switchport trunk group %s' % name]
            func = async_function(self.instance.add_trunk_group, intf, name)
            await self.async_eapi_positive_config_test(func, cmds)

    async def test_remove_trunk_group(self):
        for intf in self.INTERFACES:
            name = 'test'
            cmds = ['interface %s' % intf, 'no switchport trunk group %s' % name]
            func = async_function(self.instance.remove_trunk_group, intf, name)
            await self.async_eapi_positive_config_test(func, cmds)


if __name__ == '__main__':
    unittest.main()