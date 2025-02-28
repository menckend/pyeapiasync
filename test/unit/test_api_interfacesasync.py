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
import asyncio

sys.path.append(os.path.join(os.path.dirname(__file__), '../lib'))

from testlib import get_fixture, random_string, async_function, random_int
from testlib import AsyncEapiConfigUnitTest

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
        self.assertIsInstance(result, pyeapiasync.api.interfacesasync.InterfacesAsync)


class TestApiInterfacesAsync(AsyncEapiConfigUnitTest):

    def setUp(self):
        super().setUp()
        self.instance = pyeapiasync.api.interfacesasync.InterfacesAsync(None)
        self.config = open(get_fixture('running_config.text')).read()
        # Mock the get_config method to return test config
        self.instance.get_block = unittest.mock.AsyncMock(return_value=self.config)
        self.instance.configure = unittest.mock.AsyncMock(return_value=True)

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
        # Mock the get_instance method to return a mock interface
        mock_interface = unittest.mock.MagicMock()
        mock_interface.set_sflow = unittest.mock.AsyncMock(return_value=True)
        self.instance.get_instance = unittest.mock.AsyncMock(
            return_value=mock_interface)
        
        result = await self.instance.set_sflow('Ethernet1', True)
        self.assertTrue(result)
        mock_interface.set_sflow.assert_called_with('Ethernet1', True)

    async def test_proxy_method_raises_attribute_error(self):
        # Mock the get_instance method to return a mock interface
        mock_interface = unittest.mock.MagicMock()
        mock_interface.set_sflow = None
        self.instance.get_instance = unittest.mock.AsyncMock(
            return_value=mock_interface)
        
        with self.assertRaises(AttributeError):
            await self.instance.set_sflow('Management1', True)

    async def test_getall(self):
        interfaces = ['Ethernet1', 'Management1', 'Loopback0', 
                      'Port-Channel1', 'Vlan1']
        # Mock the node.enable method
        mock_response = [{'interfaces': {intf: {} for intf in interfaces}}]
        self.instance.node = unittest.mock.MagicMock()
        self.instance.node.enable = unittest.mock.AsyncMock(
            return_value=mock_response)
        
        result = await self.instance.getall()
        self.assertIsInstance(result, dict)
        for intf in interfaces:
            self.assertIn(intf, result)

    async def test_create_raises_not_implemented_error_for_ethernet(self):
        with self.assertRaises(NotImplementedError):
            await self.instance.create('Ethernet1')

    async def test_create_creates_logical_interface(self):
        # Mock the get method to return None for non-existent interface
        self.instance.get = unittest.mock.AsyncMock(return_value=None)
        
        await self.instance.create('Loopback0')
        self.instance.configure.assert_called_with(['interface Loopback0'])

    async def test_delete_raises_not_implemented_error_for_ethernet(self):
        with self.assertRaises(NotImplementedError):
            await self.instance.delete('Ethernet1')

    async def test_delete_deletes_logical_interface(self):
        await self.instance.delete('Loopback0')
        self.instance.configure.assert_called_with(['no interface Loopback0'])

    async def test_default(self):
        await self.instance.default('Ethernet1')
        self.instance.configure.assert_called_with(['default interface Ethernet1'])


class TestApiBaseInterfaceAsync(AsyncEapiConfigUnitTest):

    def setUp(self):
        super().setUp()
        self.instance = pyeapiasync.api.interfacesasync.BaseInterfaceAsync(None)
        self.config = open(get_fixture('running_config.text')).read()
        # Mock the get_config method to return test config
        self.instance.get_block = unittest.mock.AsyncMock(return_value=self.config)
        self.instance.configure = unittest.mock.AsyncMock(return_value=True)

    async def test_get(self):
        result = await self.instance.get('Loopback0')
        values = dict(name='Loopback0', type='generic',
                      shutdown=False, description=None)
        self.assertEqual(result, values)

    async def test_set_description_with_value(self):
        for intf in INTERFACES:
            value = random_string()
            await self.instance.set_description(intf, value)
            self.instance.configure.assert_called_with(
                ['interface %s' % intf, 'description %s' % value])

    async def test_set_description_with_no_value(self):
        for intf in INTERFACES:
            await self.instance.set_description(intf, disable=True)
            self.instance.configure.assert_called_with(
                ['interface %s' % intf, 'no description'])

    async def test_set_description_with_default(self):
        for intf in INTERFACES:
            await self.instance.set_description(intf, default=True)
            self.instance.configure.assert_called_with(
                ['interface %s' % intf, 'default description'])

    async def test_set_shutdown(self):
        for intf in INTERFACES:
            await self.instance.set_shutdown(intf, default=False, disable=False)
            self.instance.configure.assert_called_with(
                ['interface %s' % intf, 'shutdown'])

    async def test_set_shutdown_with_disable(self):
        for intf in INTERFACES:
            await self.instance.set_shutdown(intf)
            self.instance.configure.assert_called_with(
                ['interface %s' % intf, 'no shutdown'])

    async def test_set_shutdown_with_default(self):
        for intf in INTERFACES:
            await self.instance.set_shutdown(intf, default=True)
            self.instance.configure.assert_called_with(
                ['interface %s' % intf, 'default shutdown'])

    async def test_set_encapsulation_non_subintf(self):
        with self.assertRaises(NotImplementedError):
            await self.instance.set_encapsulation('Ethernet1', 1)

    async def test_set_encapsulation_non_supported_intf(self):
        with self.assertRaises(NotImplementedError):
            await self.instance.set_encapsulation('Vlan1234', 1)

    async def test_set_encapsulation_ethernet_subintf(self):
        await self.instance.set_encapsulation('Ethernet1.1', 1)
        self.instance.configure.assert_called_with(
            ['interface Ethernet1.1', 'encapsulation dot1q vlan 1'])

    async def test_set_encapsulation_portchannel_subintf_disable(self):
        await self.instance.set_encapsulation('Port-Channel1.1', 1, disable=True)
        self.instance.configure.assert_called_with(
            ['interface Port-Channel1.1', 'no encapsulation dot1q vlan'])

    async def test_set_encapsulation_ethernet_subintf_default(self):
        await self.instance.set_encapsulation('Ethernet1.1', 1, default=True)
        self.instance.configure.assert_called_with(
            ['interface Ethernet1.1', 'default encapsulation dot1q vlan'])


class TestApiEthernetInterfaceAsync(AsyncEapiConfigUnitTest):

    def setUp(self):
        super().setUp()
        self.instance = pyeapiasync.api.interfacesasync.EthernetInterfaceAsync(None)
        self.config = open(get_fixture('running_config.text')).read()
        # Mock the get_config method to return test config
        self.instance.get_block = unittest.mock.AsyncMock(return_value=self.config)
        self.instance.configure = unittest.mock.AsyncMock(return_value=True)

    async def test_get(self):
        result = await self.instance.get('Ethernet1')
        self.assertEqual(result['type'], 'ethernet')
        self.assertEqual(result['name'], 'Ethernet1')
        self.assertEqual(result['sflow'], True)
        self.assertEqual(result['flowcontrol_send'], 'off')
        self.assertEqual(result['flowcontrol_receive'], 'off')

    async def test_set_flowcontrol_with_values(self):
        for state in ['on', 'off']:
            await self.instance.set_flowcontrol_send('Ethernet1', state)
            self.instance.configure.assert_called_with(
                ['interface Ethernet1', 'flowcontrol send %s' % state])
            
            await self.instance.set_flowcontrol_receive('Ethernet1', state)
            self.instance.configure.assert_called_with(
                ['interface Ethernet1', 'flowcontrol receive %s' % state])

    async def test_set_flowcontrol_with_invalid_value_raises_value_error(self):
        with self.assertRaises(ValueError):
            await self.instance.set_flowcontrol_send('Ethernet1', 'invalid')
        with self.assertRaises(ValueError):
            await self.instance.set_flowcontrol_receive('Ethernet1', 'invalid')

    async def test_set_flowcontrol_with_default(self):
        await self.instance.set_flowcontrol_send('Ethernet1', default=True)
        self.instance.configure.assert_called_with(
            ['interface Ethernet1', 'default flowcontrol send'])
            
        await self.instance.set_flowcontrol_receive('Ethernet1', default=True)
        self.instance.configure.assert_called_with(
            ['interface Ethernet1', 'default flowcontrol receive'])

    async def test_set_flowcontrol_with_disable(self):
        await self.instance.set_flowcontrol_send('Ethernet1', disable=True)
        self.instance.configure.assert_called_with(
            ['interface Ethernet1', 'no flowcontrol send'])
            
        await self.instance.set_flowcontrol_receive('Ethernet1', disable=True)
        self.instance.configure.assert_called_with(
            ['interface Ethernet1', 'no flowcontrol receive'])

    async def test_set_sflow_with_default(self):
        await self.instance.set_sflow('Ethernet1', default=True)
        self.instance.configure.assert_called_with(
            ['interface Ethernet1', 'default sflow enable'])

    async def test_set_sflow_with_disable(self):
        await self.instance.set_sflow('Ethernet1', disable=True)
        self.instance.configure.assert_called_with(
            ['interface Ethernet1', 'no sflow enable'])

    async def test_set_sflow_with_enable(self):
        await self.instance.set_sflow('Ethernet1', True)
        self.instance.configure.assert_called_with(
            ['interface Ethernet1', 'sflow enable'])
        
        await self.instance.set_sflow('Ethernet1', False)
        self.instance.configure.assert_called_with(
            ['interface Ethernet1', 'no sflow enable'])


class TestApiVxlanInterfaceAsync(AsyncEapiConfigUnitTest):

    def setUp(self):
        super().setUp()
        self.instance = pyeapiasync.api.interfacesasync.VxlanInterfaceAsync(None)
        self.config = open(get_fixture('running_config.text')).read()
        # Mock the get_config method to return test config
        self.instance.get_block = unittest.mock.AsyncMock(return_value=self.config)
        self.instance.configure = unittest.mock.AsyncMock(return_value=True)

    async def test_get(self):
        self.instance.get_block = unittest.mock.AsyncMock(
            return_value='interface Vxlan1\n   vxlan source-interface Loopback0\n   '
                         'vxlan udp-port 4789\n   vxlan vlan 10 vni 10\n   '
                         'vxlan flood vtep 1.1.1.1')
                         
        result = await self.instance.get('Vxlan1')
        self.assertEqual(result['name'], 'Vxlan1')
        self.assertEqual(result['type'], 'vxlan')
        self.assertEqual(result['source_interface'], 'Loopback0')
        self.assertEqual(result['udp_port'], 4789)
        self.assertEqual(result['vlans'][10]['vni'], 10)
        self.assertIn('1.1.1.1', result['flood_list'])

    async def test_set_source_interface(self):
        for state in ['config', 'negate', 'default']:
            source_intf = 'Loopback0'
            
            if state == 'config':
                await self.instance.set_source_interface('Vxlan1', source_intf)
                self.instance.configure.assert_called_with(
                    ['interface Vxlan1', 'vxlan source-interface Loopback0'])
            elif state == 'negate':
                await self.instance.set_source_interface('Vxlan1', disable=True)
                self.instance.configure.assert_called_with(
                    ['interface Vxlan1', 'no vxlan source-interface'])
            elif state == 'default':
                await self.instance.set_source_interface('Vxlan1', default=True)
                self.instance.configure.assert_called_with(
                    ['interface Vxlan1', 'default vxlan source-interface'])

    async def test_set_multicast_group(self):
        for state in ['config', 'negate', 'default']:
            mcast_grp = '239.10.10.10'
            
            if state == 'config':
                await self.instance.set_multicast_group('Vxlan1', mcast_grp)
                self.instance.configure.assert_called_with(
                    ['interface Vxlan1', 'vxlan multicast-group 239.10.10.10'])
            elif state == 'negate':
                await self.instance.set_multicast_group('Vxlan1', disable=True)
                self.instance.configure.assert_called_with(
                    ['interface Vxlan1', 'no vxlan multicast-group'])
            elif state == 'default':
                await self.instance.set_multicast_group('Vxlan1', default=True)
                self.instance.configure.assert_called_with(
                    ['interface Vxlan1', 'default vxlan multicast-group'])

    async def test_set_udp_port(self):
        for state in ['config', 'negate', 'default']:
            port = '4789' if state == 'default' else '1024'
            
            if state == 'config':
                await self.instance.set_udp_port('Vxlan1', port)
                self.instance.configure.assert_called_with(
                    ['interface Vxlan1', 'vxlan udp-port 1024'])
            elif state == 'negate':
                await self.instance.set_udp_port('Vxlan1', disable=True)
                self.instance.configure.assert_called_with(
                    ['interface Vxlan1', 'vxlan udp-port 4789'])
            elif state == 'default':
                await self.instance.set_udp_port('Vxlan1', default=True)
                self.instance.configure.assert_called_with(
                    ['interface Vxlan1', 'vxlan udp-port 4789'])

    async def test_add_vtep(self):
        await self.instance.add_vtep('Vxlan1', '1.1.1.1')
        self.instance.configure.assert_called_with(
            ['interface Vxlan1', 'vxlan flood vtep 1.1.1.1'])

    async def test_add_vtep_to_vlan(self):
        await self.instance.add_vtep('Vxlan1', '1.1.1.1', vlan='10')
        self.instance.configure.assert_called_with(
            ['interface Vxlan1', 'vxlan vlan 10 flood vtep 1.1.1.1'])

    async def test_remove_vtep(self):
        await self.instance.remove_vtep('Vxlan1', '1.1.1.1')
        self.instance.configure.assert_called_with(
            ['interface Vxlan1', 'no vxlan flood vtep 1.1.1.1'])

    async def test_remove_vtep_from_vlan(self):
        await self.instance.remove_vtep('Vxlan1', '1.1.1.1', vlan='10')
        self.instance.configure.assert_called_with(
            ['interface Vxlan1', 'no vxlan vlan 10 flood vtep 1.1.1.1'])

    async def test_update_vlan(self):
        await self.instance.update_vlan('Vxlan1', 10, 10)
        self.instance.configure.assert_called_with(
            ['interface Vxlan1', 'vxlan vlan 10 vni 10'])

    async def test_remove_vlan(self):
        await self.instance.remove_vlan('Vxlan1', 10)
        self.instance.configure.assert_called_with(
            ['interface Vxlan1', 'no vxlan vlan 10'])


class TestApiPortChannelInterfaceAsync(AsyncEapiConfigUnitTest):

    def setUp(self):
        super().setUp()
        self.instance = pyeapiasync.api.interfacesasync.PortChannelInterfaceAsync(None)
        self.config = open(get_fixture('running_config.text')).read()
        # Mock the get_config method to return test config
        self.instance.get_block = unittest.mock.AsyncMock(return_value=self.config)
        self.instance.configure = unittest.mock.AsyncMock(return_value=True)

    async def test_get(self):
        self.instance.get_block = unittest.mock.AsyncMock(
            return_value='interface Port-Channel1\n   mtu 9000\n   '
                         'channel-group 1 mode active\n   '
                         'port-channel min-links 2\n')
                         
        result = await self.instance.get('Port-Channel1')
        self.assertEqual(result['name'], 'Port-Channel1')
        self.assertEqual(result['type'], 'portchannel')
        self.assertEqual(result['lacp_mode'], 'active')
        self.assertEqual(result['minimum_links'], 2)

    async def test_set_members(self):
        # Mock node.enable to return a list of interfaces
        self.instance.node = unittest.mock.MagicMock()
        self.instance.node.enable = unittest.mock.AsyncMock(
            return_value=[{'result': {'interfaceDescriptions': 
                          {'Ethernet1': {}, 'Ethernet2': {}}}}])
        
        await self.instance.set_members('Port-Channel1', ['Ethernet1', 'Ethernet2'])
        # Should configure both interfaces
        calls = [
            unittest.mock.call(['interface Ethernet1', 'channel-group 1 mode on']),
            unittest.mock.call(['interface Ethernet2', 'channel-group 1 mode on']),
        ]
        self.instance.configure.assert_has_calls(calls)

    async def test_set_members_with_mode(self):
        # Mock node.enable to return a list of interfaces
        self.instance.node = unittest.mock.MagicMock()
        self.instance.node.enable = unittest.mock.AsyncMock(
            return_value=[{'result': {'interfaceDescriptions': 
                          {'Ethernet1': {}, 'Ethernet2': {}}}}])
        
        await self.instance.set_members('Port-Channel1', ['Ethernet1', 'Ethernet2'], mode='active')
        # Should configure both interfaces
        calls = [
            unittest.mock.call(['interface Ethernet1', 'channel-group 1 mode active']),
            unittest.mock.call(['interface Ethernet2', 'channel-group 1 mode active']),
        ]
        self.instance.configure.assert_has_calls(calls)

    async def test_set_lacp_mode(self):
        for mode in ['active', 'passive', 'on']:
            await self.instance.set_lacp_mode('Port-Channel1', mode)
            # Should find member interfaces and configure them
            self.instance.configure.assert_called_with(
                ['interface Port-Channel1', 'port-channel lacp fallback static'])

    async def test_set_lacp_mode_invalid_value_raises_value_error(self):
        with self.assertRaises(ValueError):
            await self.instance.set_lacp_mode('Port-Channel1', 'invalid')

    async def test_set_minimum_links(self):
        value = random_int(1, 8)
        await self.instance.set_minimum_links('Port-Channel1', value)
        self.instance.configure.assert_called_with(
            ['interface Port-Channel1', 'port-channel min-links %s' % value])

    async def test_set_minimum_links_invalid_value_raises_value_error(self):
        for value in [0, 9, 'string']:
            with self.assertRaises(ValueError):
                await self.instance.set_minimum_links('Port-Channel1', value)


if __name__ == '__main__':
    unittest.main()