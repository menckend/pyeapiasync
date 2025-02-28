#
# Copyright (c) 2015, Arista Networks, Inc.
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
import sys
import unittest

sys.path.append(os.path.join(os.path.dirname(__file__), '../lib'))

import pyeapiasync.api.vrrpasync

from testlib import get_fixture

# Test constants
upd_intf = 'Vlan50'
upd_vrid = 10
upd_cmd = 'interface %s' % upd_intf
known_vrrps = {
    'Ethernet1': {
        10: {'priority': 175,
             'timers_advertise': 1,
             'mac_addr_adv_interval': 30,
             'preempt': True,
             'preempt_delay_min': 0,
             'preempt_delay_reload': 0,
             'delay_reload': 0,
             'primary_ip': '10.10.6.10',
             'secondary_ip': [],
             'description': 'vrrp 10 on Ethernet1',
             'enable': True,
             'track': [],
             'bfd_ip': '',
             'ip_version': 2}
    },
    'Port-Channel10': {
        10: {'priority': 150,
             'timers_advertise': 1,
             'mac_addr_adv_interval': 30,
             'preempt': True,
             'preempt_delay_min': 0,
             'preempt_delay_reload': 0,
             'delay_reload': 0,
             'primary_ip': '10.10.5.10',
             'secondary_ip': ['10.10.5.20'],
             'description': 'vrrp 10 on Port-Channel10',
             'enable': True,
             'track': [],
             'bfd_ip': '',
             'ip_version': 2}
    },
    'Vlan50': {
        10: {'priority': 200,
             'timers_advertise': 3,
             'mac_addr_adv_interval': 30,
             'preempt': True,
             'preempt_delay_min': 0,
             'preempt_delay_reload': 0,
             'delay_reload': 0,
             'primary_ip': '10.10.4.10',
             'secondary_ip': ['10.10.4.21', '10.10.4.22',
                              '10.10.4.23', '10.10.4.24'],
             'description': '',
             'enable': True,
             'track': [
                 {'name': 'Ethernet1', 'action': 'decrement', 'amount': 10},
                 {'name': 'Ethernet1', 'action': 'shutdown'},
                 {'name': 'Ethernet2', 'action': 'decrement', 'amount': 50},
                 {'name': 'Ethernet2', 'action': 'shutdown'},
                 {'name': 'Ethernet11', 'action': 'decrement', 'amount': 75},
                 {'name': 'Ethernet11', 'action': 'shutdown'},
             ],
             'bfd_ip': '',
             'ip_version': 2},
        20: {'priority': 100,
             'timers_advertise': 5,
             'mac_addr_adv_interval': 30,
             'preempt': False,
             'preempt_delay_min': 0,
             'preempt_delay_reload': 0,
             'delay_reload': 0,
             'primary_ip': '10.10.4.20',
             'secondary_ip': [],
             'description': '',
             'enable': False,
             'track': [
                 {'name': 'Ethernet1', 'action': 'shutdown'},
                 {'name': 'Ethernet2', 'action': 'decrement', 'amount': 1},
                 {'name': 'Ethernet2', 'action': 'shutdown'},
             ],
             'bfd_ip': '',
             'ip_version': 2},
        30: {'priority': 50,
             'timers_advertise': 1,
             'mac_addr_adv_interval': 30,
             'preempt': True,
             'preempt_delay_min': 0,
             'preempt_delay_reload': 0,
             'delay_reload': 0,
             'primary_ip': '10.10.4.30',
             'secondary_ip': [],
             'description': '',
             'enable': True,
             'track': [],
             'bfd_ip': '10.10.4.33',
             'ip_version': 2}
    }
}


class TestApiVrrpAsync(unittest.IsolatedAsyncioTestCase):

    maxDiff = None

    async def asyncSetUp(self):
        self.instance = pyeapiasync.api.vrrpasync.VrrpAsync(None)
        self.config = open(get_fixture('running_config.vrrp')).read()
        self.instance.config = self.config

    async def test_instance(self):
        result = pyeapiasync.api.vrrpasync.instance(None)
        self.assertIsInstance(result, pyeapiasync.api.vrrpasync.VrrpAsync)

    async def test_get(self):
        # Request various sets of vrrp configurations
        for interface in known_vrrps:
            result = await self.instance.get(interface)
            self.assertIsInstance(result, dict)
            self.assertEqual(result, known_vrrps[interface])

    async def test_get_non_existent_interface(self):
        # Request vrrp configuration for an interface that is not defined
        result = await self.instance.get('Vlan2000')
        self.assertIsNone(result)

    async def test_getall(self):
        result = await self.instance.getall()
        self.assertIsInstance(result, dict)
        self.assertEqual(result, known_vrrps)

    async def test_create(self):
        interface = 'Vlan50'
        vrid = 10
        config = {
            'primary_ip': '10.10.4.10',
            'priority': 200,
            'description': '',
            'secondary_ip': ['10.10.4.21', '10.10.4.22', '10.10.4.23', '10.10.4.24'],
            'ip_version': 2,
            'enable': True,
            'timers_advertise': 3,
            'mac_addr_adv_interval': 30,
            'preempt': True,
            'preempt_delay_min': 0,
            'preempt_delay_reload': 0,
            'delay_reload': 0,
            'track': [
                {'name': 'Ethernet1', 'action': 'decrement', 'amount': 10},
                {'name': 'Ethernet1', 'action': 'shutdown'},
                {'name': 'Ethernet2', 'action': 'decrement', 'amount': 50},
                {'name': 'Ethernet2', 'action': 'shutdown'},
                {'name': 'Ethernet11', 'action': 'decrement', 'amount': 75},
                {'name': 'Ethernet11', 'action': 'shutdown'},
            ],
            'bfd_ip': '',
        }
        # Mock the configure_interface method for testing
        self.instance.configure_interface = unittest.mock.AsyncMock(return_value=True)
        result = await self.instance.create(interface, vrid, **config)
        self.assertTrue(result)

    async def test_delete(self):
        interface = 'Vlan50'
        vrid = 10
        # Mock the configure_interface method for testing
        self.instance.configure_interface = unittest.mock.AsyncMock(return_value=True)
        result = await self.instance.delete(interface, vrid)
        self.assertTrue(result)
        self.instance.configure_interface.assert_called_once_with(interface, 'no vrrp 10')

    async def test_default(self):
        interface = 'Vlan50'
        vrid = 10
        # Mock the configure_interface method for testing
        self.instance.configure_interface = unittest.mock.AsyncMock(return_value=True)
        result = await self.instance.default(interface, vrid)
        self.assertTrue(result)
        self.instance.configure_interface.assert_called_once_with(interface, 'default vrrp 10')

    async def test_set_enable(self):
        interface = 'Vlan50'
        vrid = 10
        # Mock the version_number property
        self.instance.version_number = '4.20.0'
        # Mock the configure_interface method for testing
        self.instance.configure_interface = unittest.mock.AsyncMock(return_value=True)
        result = await self.instance.set_enable(interface, vrid, value=True)
        self.assertTrue(result)
        self.instance.configure_interface.assert_called_once_with(interface, 'no vrrp 10 shutdown')

    async def test_set_primary_ip(self):
        interface = 'Vlan50'
        vrid = 10
        ip = '10.10.4.10'
        # Mock the version_number property
        self.instance.version_number = '4.20.0'
        # Mock the configure_interface method for testing
        self.instance.configure_interface = unittest.mock.AsyncMock(return_value=True)
        result = await self.instance.set_primary_ip(interface, vrid, value=ip)
        self.assertTrue(result)

    async def test_set_priority(self):
        interface = 'Vlan50'
        vrid = 10
        priority = 200
        # Mock the version_number property
        self.instance.version_number = '4.20.0'
        # Mock the configure_interface method for testing
        self.instance.configure_interface = unittest.mock.AsyncMock(return_value=True)
        result = await self.instance.set_priority(interface, vrid, value=priority)
        self.assertTrue(result)

    async def test_set_description(self):
        interface = 'Vlan50'
        vrid = 10
        description = 'Test VRRP Description'
        # Mock the version_number property
        self.instance.version_number = '4.20.0'
        # Mock the configure_interface method for testing
        self.instance.configure_interface = unittest.mock.AsyncMock(return_value=True)
        result = await self.instance.set_description(interface, vrid, value=description)
        self.assertTrue(result)

    async def test_set_ip_version(self):
        interface = 'Vlan50'
        vrid = 10
        version = 3
        # Mock the version_number property
        self.instance.version_number = '4.20.0'
        # Mock the configure_interface method for testing
        self.instance.configure_interface = unittest.mock.AsyncMock(return_value=True)
        result = await self.instance.set_ip_version(interface, vrid, value=version)
        self.assertTrue(result)

    async def test_set_secondary_ips(self):
        interface = 'Vlan50'
        vrid = 10
        ips = ['10.10.4.21', '10.10.4.22']
        # Mock required methods for testing
        self.instance.version_number = '4.20.0'
        self.instance.get = unittest.mock.AsyncMock(return_value={
            vrid: {'secondary_ip': ['10.10.4.23']}
        })
        self.instance.configure_interface = unittest.mock.AsyncMock(return_value=True)
        result = await self.instance.set_secondary_ips(interface, vrid, ips)
        self.assertTrue(result)

    async def test_set_timers_advertise(self):
        interface = 'Vlan50'
        vrid = 10
        timer = 3
        # Mock the version_number property
        self.instance.version_number = '4.20.0'
        # Mock the configure_interface method for testing
        self.instance.configure_interface = unittest.mock.AsyncMock(return_value=True)
        result = await self.instance.set_timers_advertise(interface, vrid, value=timer)
        self.assertTrue(result)

    async def test_set_mac_addr_adv_interval(self):
        interface = 'Vlan50'
        vrid = 10
        interval = 30
        # Mock the configure_interface method for testing
        self.instance.configure_interface = unittest.mock.AsyncMock(return_value=True)
        result = await self.instance.set_mac_addr_adv_interval(interface, vrid, value=interval)
        self.assertTrue(result)

    async def test_set_preempt(self):
        interface = 'Vlan50'
        vrid = 10
        # Mock the configure_interface method for testing
        self.instance.configure_interface = unittest.mock.AsyncMock(return_value=True)
        result = await self.instance.set_preempt(interface, vrid, value=True)
        self.assertTrue(result)

    async def test_set_preempt_delay_min(self):
        interface = 'Vlan50'
        vrid = 10
        delay = 10
        # Mock the configure_interface method for testing
        self.instance.configure_interface = unittest.mock.AsyncMock(return_value=True)
        result = await self.instance.set_preempt_delay_min(interface, vrid, value=delay)
        self.assertTrue(result)

    async def test_set_preempt_delay_reload(self):
        interface = 'Vlan50'
        vrid = 10
        delay = 10
        # Mock the configure_interface method for testing
        self.instance.configure_interface = unittest.mock.AsyncMock(return_value=True)
        result = await self.instance.set_preempt_delay_reload(interface, vrid, value=delay)
        self.assertTrue(result)

    async def test_set_delay_reload(self):
        interface = 'Vlan50'
        vrid = 10
        delay = 10
        # Mock the version_number property
        self.instance.version_number = '4.20.0'
        # Mock the configure_interface method for testing
        self.instance.configure_interface = unittest.mock.AsyncMock(return_value=True)
        result = await self.instance.set_delay_reload(interface, vrid, value=delay)
        self.assertTrue(result)

    async def test_set_tracks(self):
        interface = 'Vlan50'
        vrid = 10
        tracks = [
            {'name': 'Ethernet1', 'action': 'shutdown'},
            {'name': 'Ethernet2', 'action': 'decrement', 'amount': 10}
        ]
        # Mock required methods for testing
        self.instance.version_number = '4.20.0'
        self.instance.get = unittest.mock.AsyncMock(return_value={
            vrid: {'track': []}
        })
        self.instance.configure_interface = unittest.mock.AsyncMock(return_value=True)
        result = await self.instance.set_tracks(interface, vrid, tracks)
        self.assertTrue(result)

    async def test_set_bfd_ip(self):
        interface = 'Vlan50'
        vrid = 10
        bfd_ip = '10.10.4.33'
        # Mock the configure_interface method for testing
        self.instance.configure_interface = unittest.mock.AsyncMock(return_value=True)
        result = await self.instance.set_bfd_ip(interface, vrid, value=bfd_ip)
        self.assertTrue(result)

    async def test_vrconf_format(self):
        config = {
            'primary_ip': '10.10.4.10',
            'priority': 200,
            'description': '',
            'secondary_ip': ['10.10.4.21', '10.10.4.22'],
            'ip_version': 2,
            'enable': True,
            'timers_advertise': 3,
            'mac_addr_adv_interval': 30,
            'preempt': True,
            'preempt_delay_min': 0,
            'preempt_delay_reload': 0,
            'delay_reload': 0,
            'track': [
                {'name': 'Ethernet1', 'action': 'shutdown'},
                {'name': 'Ethernet2', 'action': 'decrement', 'amount': 10}
            ],
            'bfd_ip': '',
        }
        result = self.instance.vrconf_format(config)
        self.assertEqual(result['primary_ip'], '10.10.4.10')
        self.assertEqual(result['secondary_ip'], sorted(['10.10.4.21', '10.10.4.22']))
        

if __name__ == '__main__':
    unittest.main()
