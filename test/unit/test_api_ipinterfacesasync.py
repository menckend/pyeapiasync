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
from testlib import AsyncEapiConfigUnitTest, async_function

import pyeapi.api.ipinterfacesasync


class TestApiIpinterfacesAsync(AsyncEapiConfigUnitTest):

    INTERFACES = ['Ethernet1', 'Ethernet1/1', 'Vlan1234', 'Management1',
                  'Port-Channel1']

    def setUp(self):
        super().setUp()
        self.instance = pyeapi.api.ipinterfacesasync.instance(None)
        self.config = open(get_fixture('running_config.text')).read()
        # Mock the get_block method to return test config
        self.instance.get_block = unittest.mock.AsyncMock(return_value=self.config)
        self.instance.configure = unittest.mock.AsyncMock(return_value=True)

    async def test_get(self):
        result = await self.instance.get('Loopback0')
        values = dict(name='Loopback0', address='1.1.1.1/32', mtu=1500)
        self.assertEqual(result, values)
        
        # test interface with secondary ip
        result = await self.instance.get('Loopback2')
        values = dict(name='Loopback2', address='2.2.2.2/32',
                     secondary=['3.255.255.1/24', '4.255.255.1/24'], mtu=None)
        self.assertEqual(result, values)

    async def test_getall(self):
        # Mock node.enable to return a list of interfaces
        self.instance.node = unittest.mock.MagicMock()
        self.instance.node.enable = unittest.mock.AsyncMock(
            return_value=[{'result': {'interfaces': {
                'Ethernet1': {'interfaceAddress': {'primaryIp': {'address': '1.1.1.1', 'maskLen': 24}}},
                'Management1': {'interfaceAddress': {'primaryIp': {'address': '192.168.1.1', 'maskLen': 24}}},
                'Loopback0': {'interfaceAddress': {'primaryIp': {'address': '2.2.2.2', 'maskLen': 32}}}
            }}}])
        
        result = await self.instance.getall()
        self.assertIsInstance(result, dict)
        for interface in ['Ethernet1', 'Management1', 'Loopback0']:
            self.assertIn(interface, result)

        # Mock to return empty interfaces dict
        self.instance.node.enable = unittest.mock.AsyncMock(
            return_value=[{'result': {'interfaces': {}}}])
        result = await self.instance.getall()
        self.assertEqual(result, {})

    async def test_instance_functions(self):
        # Test the instance function
        instance = pyeapi.api.ipinterfacesasync.instance(None)
        self.assertIsInstance(instance, pyeapi.api.ipinterfacesasync.IpinterfacesAsync)

        # Test create and delete
        for intf in self.INTERFACES:
            # Test create
            await self.instance.create(intf)
            self.instance.configure.assert_called_with(['interface %s' % intf, 'no switchport'])
            
            # Test delete
            await self.instance.delete(intf)
            self.instance.configure.assert_called_with(['interface %s' % intf, 'no ip address'])

    async def test_set_address_with_value(self):
        for intf in self.INTERFACES:
            value = '%s/24' % random_string(1, 50)
            await self.instance.set_address(intf, value)
            self.instance.configure.assert_called_with(['interface %s' % intf, 'ip address %s' % value])

    async def test_set_address_with_no_value(self):
        for intf in self.INTERFACES:
            await self.instance.set_address(intf, disable=True)
            self.instance.configure.assert_called_with(['interface %s' % intf, 'no ip address'])

    async def test_set_address_with_default(self):
        for intf in self.INTERFACES:
            await self.instance.set_address(intf, default=True)
            self.instance.configure.assert_called_with(['interface %s' % intf, 'default ip address'])

    async def test_set_address_invalid_value_raises_value_error(self):
        value = '1.1.1.1'
        with self.assertRaises(ValueError):
            await self.instance.set_address('Vlan1234', value)

    async def test_set_mtu_with_values(self):
        for intf in self.INTERFACES:
            value = random_int(68, 65535)
            await self.instance.set_mtu(intf, value)
            self.instance.configure.assert_called_with(['interface %s' % intf, 'mtu %s' % value])

    async def test_set_mtu_with_no_value(self):
        for intf in self.INTERFACES:
            await self.instance.set_mtu(intf, disable=True)
            self.instance.configure.assert_called_with(['interface %s' % intf, 'no mtu'])

    async def test_set_mtu_default(self):
        for intf in self.INTERFACES:
            await self.instance.set_mtu(intf, default=True)
            self.instance.configure.assert_called_with(['interface %s' % intf, 'default mtu'])

    async def test_set_mtu_invalid_value_raises_value_error(self):
        for value in [0, 67, 65536, random_string()]:
            with self.assertRaises(ValueError):
                await self.instance.set_mtu('Vlan1234', value)

    async def test_set_mtu_valid_string_value(self):
        await self.instance.set_mtu('Vlan1234', '1500')
        self.instance.configure.assert_called_with(['interface Vlan1234', 'mtu 1500'])

    async def test_add_secondary_address(self):
        for intf in self.INTERFACES:
            value = '%s/24' % random_string(1, 50)
            await self.instance.add_secondary(intf, value)
            self.instance.configure.assert_called_with(['interface %s' % intf, 'ip address %s secondary' % value])

    async def test_add_secondary_invalid_value_raises_value_error(self):
        value = '1.1.1.1'
        with self.assertRaises(ValueError):
            await self.instance.add_secondary('Vlan1234', value)

    async def test_remove_secondary_address(self):
        for intf in self.INTERFACES:
            value = '%s/24' % random_string(1, 50)
            await self.instance.remove_secondary(intf, value)
            self.instance.configure.assert_called_with(['interface %s' % intf, 'no ip address %s secondary' % value])

    async def test_remove_secondary_all(self):
        for intf in self.INTERFACES:
            await self.instance.remove_secondary(intf, 'all')
            self.instance.configure.assert_called_with(['interface %s' % intf, 'no ip address secondary'])


if __name__ == '__main__':
    unittest.main()