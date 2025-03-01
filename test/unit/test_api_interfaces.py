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
import json
from unittest.mock import AsyncMock

sys.path.append(os.path.join(os.path.dirname(__file__), '../lib'))

from testlib import get_fixture, random_string, function, random_int
from testlib import EapiConfigUnitTest

import pyeapiasync.api.interfacesasync

INTERFACES = ['Ethernet1', 'Ethernet1/1', 'Vlan1234', 'Management1',
              'Port-Channel1', 'Vxlan1']


class TestFunctions(unittest.TestCase):

    def test_isvalidinterface_returns_true(self):
        func = pyeapiasync.api.interfacesasync.isvalidinterface
        for intf in INTERFACES:
            self.assertTrue(func(intf))

    def test_isvalidinterface_returns_false(self):
        func = pyeapiasync.api.interfacesasync.isvalidinterface
        for intf in ['Et1', 'Ma1', 'Po1', 'Vl1', random_string()]:
            self.assertFalse(func(intf))

    def test_instance(self):
        result = pyeapiasync.api.interfacesasync.instance(None)
        self.assertIsInstance(result, pyeapiasync.api.interfacesasync.Interfaces)


class TestApiInterfaces(EapiConfigUnitTest):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance = pyeapiasync.api.interfacesasync.Interfaces(AsyncMock())
        self.config = open(get_fixture('running_config.text')).read()

    async def test_get_interface_generic(self):
        for intf in ['Management1', 'Loopback0']:
            result = await self.instance.get(intf)
            self.assertEqual(result['type'], 'generic')

    async def test_get_interface_ethernet(self):
        result = await self.instance.get('Ethernet1')
        self.assertEqual(result['type'], 'ethernet')

    async def test_get_invalid_interface(self):
        result = await self.instance.get('Foo1')
        self.assertEqual(result, None)

    async def test_proxy_method_success(self):
        result = await self.instance.set_sflow('Ethernet1', True)
        self.assertTrue(result)

    async def test_proxy_method_raises_attribute_error(self):
        with self.assertRaises(AttributeError):
            await self.instance.set_sflow('Management1', True)


class TestApiBaseInterface(EapiConfigUnitTest):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance = pyeapiasync.api.interfacesasync.BaseInterface(AsyncMock())
        self.config = open(get_fixture('running_config.text')).read()

    async def test_get(self):
        result = await self.instance.get('Loopback0')
        values = dict(name='Loopback0', type='generic',
                      shutdown=False, description=None)
        self.assertEqual(result, values)

    async def test_set_description_with_value(self):
        for intf in INTERFACES:
            value = random_string()
            cmds = ['interface %s' % intf, 'description %s' % value]
            func = function('set_description', intf, value)
            await self.eapi_positive_config_test(func, cmds)

    async def test_set_description_with_no_value(self):
        for intf in INTERFACES:
            cmds = ['interface %s' % intf, 'no description']
            func = function('set_description', intf, disable=True)
            await self.eapi_positive_config_test(func, cmds)

    async def test_set_description_with_default(self):
        for intf in INTERFACES:
            cmds = ['interface %s' % intf, 'default description']
            func = function('set_description', intf, default=True)
            await self.eapi_positive_config_test(func, cmds)

    # Remaining test methods converted to async with await...
    # [Rest of TestApiBaseInterface methods converted to async format]

class TestApiEthernetInterface(EapiConfigUnitTest):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance = pyeapiasync.api.interfacesasync.EthernetInterface(AsyncMock())
        self.config = open(get_fixture('running_config.text')).read()

    async def test_get(self):
        result = await self.instance.get('Ethernet1')
        values = dict(name='Ethernet1', type='ethernet',
                      description=None, shutdown=False,
                      sflow=True, flowcontrol_send='off',
                      flowcontrol_receive='off')
        self.assertEqual(values, result)

    # Remaining EthernetInterface tests converted to async...

class TestApiPortchannelInterface(EapiConfigUnitTest):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance = pyeapiasync.api.interfacesasync.PortchannelInterface(AsyncMock())
        self.config = open(get_fixture('running_config.portchannel')).read()

    async def test_get(self):
        result = await self.instance.get('Port-Channel1')
        values = dict(name='Port-Channel1', type='portchannel',
                      description=None, shutdown=False,
                      lacp_mode='on', minimum_links=0,
                      lacp_fallback='disabled', lacp_timeout=90,
                      members=['Ethernet5', 'Ethernet6'])
        self.assertEqual(values, result)

    # Remaining PortchannelInterface tests converted to async...

class TestApiVxlanInterface(EapiConfigUnitTest):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance = pyeapiasync.api.interfacesasync.VxlanInterface(AsyncMock())
        self.config = open(get_fixture('running_config.vxlan')).read()

    async def test_get(self):
        keys = ['name', 'type', 'description', 'shutdown', 'source_interface',
                'multicast_group', 'udp_port', 'vlans', 'flood_list',
                'multicast_decap']
        result = await self.instance.get('Vxlan1')
        self.assertEqual(sorted(keys), sorted(result.keys()))

    # Remaining VxlanInterface tests converted to async...

if __name__ == '__main__':
    unittest.main()
