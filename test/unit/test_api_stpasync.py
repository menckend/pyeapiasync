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

from testlib import get_fixture, random_string, async_function
from testlib import AsyncEapiConfigUnitTest

import pyeapi.api.stpasync


def get_running_config():
    return get_fixture('running_config.text')


class TestApiStpAsync(AsyncEapiConfigUnitTest):

    def __init__(self, *args, **kwargs):
        super(TestApiStpAsync, self).__init__(*args, **kwargs)
        self.instance = pyeapi.api.stpasync.StpAsync(None)
        self.config = open(get_running_config()).read()
        # Mock the get_block method to return test config
        self.instance.get_block = unittest.mock.AsyncMock(return_value=self.config)
        self.instance.configure = unittest.mock.AsyncMock(return_value=True)

    def test_instance(self):
        result = pyeapi.api.stpasync.instance(None)
        self.assertIsInstance(result, pyeapi.api.stpasync.StpAsync)

    def test_interfaces(self):
        result = self.instance.interfaces
        self.assertIsInstance(result, pyeapi.api.stpasync.StpInterfacesAsync)

    def test_instances(self):
        result = self.instance.instances
        self.assertIsInstance(result, pyeapi.api.stpasync.StpInstancesAsync)

    async def test_set_mode_with_value(self):
        for value in ['mstp', 'none']:
            cmds = 'spanning-tree mode %s' % value
            func = async_function(self.instance.set_mode, value)
            await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_mode_with_default(self):
        cmds = 'default spanning-tree mode'
        func = async_function(self.instance.set_mode, default=True)
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_mode_with_disable(self):
        cmds = 'no spanning-tree mode'
        func = async_function(self.instance.set_mode, disable=True)
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_mode_invalid_value_raises_value_error(self):
        value = random_string()
        with self.assertRaises(ValueError):
            await self.instance.set_mode(value)


class TestApiStpInterfacesAsync(AsyncEapiConfigUnitTest):

    INTERFACES = ['Ethernet1', 'Ethernet1/1', 'Port-Channel1']

    def __init__(self, *args, **kwargs):
        super(TestApiStpInterfacesAsync, self).__init__(*args, **kwargs)
        self.instance = pyeapi.api.stpasync.StpInterfacesAsync(None)
        self.config = open(get_running_config()).read()
        # Mock the get_block method to return test config
        self.instance.get_block = unittest.mock.AsyncMock(return_value=self.config)
        self.instance.configure = unittest.mock.AsyncMock(return_value=True)
        self.instance.node = unittest.mock.MagicMock()
        self.instance.node.enable = unittest.mock.AsyncMock(
            return_value=[{'result': {'interfaces': {}}}])

    async def test_getall(self):
        result = await self.instance.getall()
        self.assertIsInstance(result, dict)

    async def test_set_portfast_type_with_value(self):
        for intf in self.INTERFACES:
            for value in ['edge', 'network', 'normal']:
                cmds = ['interface %s' % intf]
                cmds.append('spanning-tree portfast %s' % value)
                if value == 'edge':
                    cmds.append('spanning-tree portfast auto')
                func = async_function(self.instance.set_portfast_type, intf, value)
                await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_portfast_type_with_no_value(self):
        for intf in self.INTERFACES:
            cmds = ['interface %s' % intf, 'spanning-tree portfast normal']
            func = async_function(self.instance.set_portfast_type, intf)
            await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_portfast_type_invalid_value_raises_value_error(self):
        for intf in self.INTERFACES:
            value = random_string()
            with self.assertRaises(ValueError):
                await self.instance.set_portfast_type(intf, value)

    async def test_set_portfast_type_invalid_intf_raises_value_error(self):
        intf = random_string()
        with self.assertRaises(ValueError):
            await self.instance.set_portfast_type(intf)

    async def test_set_bpduguard_with_value(self):
        for intf in self.INTERFACES:
            for value in [True, False]:
                cmds = ['interface %s' % intf]
                config_val = 'enable' if value else 'disable'
                cmds.append('spanning-tree bpduguard %s' % config_val)
                func = async_function(self.instance.set_bpduguard, intf, value)
                await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_bpduguard_with_no_value(self):
        for intf in self.INTERFACES:
            cmds = ['interface %s' % intf, 'spanning-tree bpduguard disable']
            func = async_function(self.instance.set_bpduguard, intf)
            await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_bpduguard_with_default(self):
        for intf in self.INTERFACES:
            cmds = ['interface %s' % intf, 'default spanning-tree bpduguard']
            func = async_function(self.instance.set_bpduguard, intf, default=True)
            await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_bpduguard_with_disable(self):
        for intf in self.INTERFACES:
            cmds = ['interface %s' % intf, 'no spanning-tree bpduguard']
            func = async_function(self.instance.set_bpduguard, intf, disable=True)
            await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_bpduguard_invalid_intf_raises_value_error(self):
        intf = random_string()
        with self.assertRaises(ValueError):
            await self.instance.set_bpduguard(intf)

    async def test_set_portfast_with_value(self):
        for intf in self.INTERFACES:
            for value in [True, False]:
                cmds = ['interface %s' % intf]
                config_val = '' if value else 'no'
                cmds.append('%s spanning-tree portfast' % config_val)
                func = async_function(self.instance.set_portfast, intf, value)
                await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_portfast_with_no_value(self):
        for intf in self.INTERFACES:
            cmds = ['interface %s' % intf, 'no spanning-tree portfast']
            func = async_function(self.instance.set_portfast, intf)
            await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_portfast_with_default(self):
        for intf in self.INTERFACES:
            cmds = ['interface %s' % intf, 'default spanning-tree portfast']
            func = async_function(self.instance.set_portfast, intf, default=True)
            await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_portfast_with_disable(self):
        for intf in self.INTERFACES:
            cmds = ['interface %s' % intf, 'no spanning-tree portfast']
            func = async_function(self.instance.set_portfast, intf, disable=True)
            await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_portfast_invalid_intf_raises_value_error(self):
        intf = random_string()
        with self.assertRaises(ValueError):
            await self.instance.set_portfast(intf)


if __name__ == '__main__':
    unittest.main()