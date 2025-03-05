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
import os
import unittest

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../lib'))

from testlib import get_fixture, function, random_int, random_string
from testlib import EapiAsyncConfigUnitTest
from pyeapiasync.api.ipinterfacesasync import IpInterfacesAsync


class TestApiIpInterfacesAsync(EapiAsyncConfigUnitTest):

    INTERFACES = ['Ethernet1', 'Ethernet1/1', 'Vlan1234', 'Management1',
                  'Port-Channel1']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance = IpInterfacesAsync.instance(None)
        self.config = open(get_fixture('running_config.text')).read()

    async def test_get(self):
        result = await self.instance.get('Loopback0')
        values = dict(name='Loopback0', address='1.1.1.1/32', mtu=1500)
        self.assertEqual(result, values)
        # Test interface with secondary ip
        result = await self.instance.get('Loopback2')
        values = dict(name='Loopback2', address='2.2.2.2/32',
                      secondary=['3.255.255.1/24', '4.255.255.1/24'], mtu=None)
        self.assertEqual(result, values)

    async def test_getall(self):
        result = await self.instance.getall()
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 4)

    async def test_instance_functions(self):
        for intf in self.INTERFACES:
            for name in ['create', 'delete']:
                if name == 'create':
                    cmds = [f'interface {intf}', 'no switchport']
                elif name == 'delete':
                    cmds = [f'interface {intf}', 'no ip address', 'switchport']
                func = function(name, intf)
                await self.eapi_async_positive_config_test(func, cmds)

    async def test_set_address_with_value(self):
        for intf in self.INTERFACES:
            value = '1.2.3.4/5'
            cmds = [f'interface {intf}', f'ip address {value}']
            func = function('set_address', intf, value)
            await self.eapi_async_positive_config_test(func, cmds)

    async def test_set_address_with_no_value(self):
        for intf in self.INTERFACES:
            cmds = [f'interface {intf}', 'no ip address']
            func = function('set_address', intf, disable=True)
            await self.eapi_async_positive_config_test(func, cmds)

    async def test_set_address_with_default(self):
        for intf in self.INTERFACES:
            cmds = [f'interface {intf}', 'default ip address']
            func = function('set_address', intf, default=True)
            await self.eapi_async_positive_config_test(func, cmds)

    async def test_set_mtu_with_values(self):
        for intf in self.INTERFACES:
            for value in [68, 65535, random_int(68, 65535)]:
                cmds = [f'interface {intf}', f'mtu {value}']
                func = function('set_mtu', intf, value)
                await self.eapi_async_positive_config_test(func, cmds)

    async def test_set_mtu_with_no_value(self):
        for intf in self.INTERFACES:
            cmds = [f'interface {intf}', 'no mtu']
            func = function('set_mtu', intf, disable=True)
            await self.eapi_async_positive_config_test(func, cmds)

    async def test_set_mtu_default(self):
        for intf in self.INTERFACES:
            cmds = [f'interface {intf}', 'default mtu']
            func = function('set_mtu', intf, default=True)
            await self.eapi_async_positive_config_test(func, cmds)


if __name__ == '__main__':
    unittest.main()
