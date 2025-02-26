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

import pyeapi.api.ntpasync


class TestApiNtpAsync(AsyncEapiConfigUnitTest):

    def __init__(self, *args, **kwargs):
        super(TestApiNtpAsync, self).__init__(*args, **kwargs)
        self.instance = pyeapi.api.ntpasync.NtpAsync(None)
        self.config = open(get_fixture('running_config.text')).read()
        # Mock the get_block method to return test config
        self.instance.get_block = unittest.mock.AsyncMock(return_value=self.config)
        self.instance.configure = unittest.mock.AsyncMock(return_value=True)

    def test_instance(self):
        result = pyeapi.api.ntpasync.instance(None)
        self.assertIsInstance(result, pyeapi.api.ntpasync.NtpAsync)

    async def test_get(self):
        result = await self.instance.get()
        ntp = {'servers': [{'1.2.3.4': 'prefer'},
                           {'10.20.30.40': None},
                           {'11.22.33.44': None},
                           {'123.33.22.11': 'prefer'},
                           {'123.44.55.66': None},
                           {'192.168.1.32': 'iburst'}],
               'source_interface': 'Loopback1'}
        keys = ['source_interface', 'servers']
        self.assertEqual(sorted(keys), sorted(result.keys()))
        self.assertEqual(ntp['source_interface'], result['source_interface'])
        self.assertIsNotNone(result['servers'])

    async def test_create(self):
        func = async_function(self.instance.create, 'Ethernet2')
        await self.async_eapi_positive_config_test(func, 'ntp source Ethernet2')

    async def test_delete(self):
        # Test with version < 4.23
        self.instance.version_number = '4.22'
        func = async_function(self.instance.delete)
        await self.async_eapi_positive_config_test(func, 'no ntp source')

        # Test with version >= 4.23
        self.instance.version_number = '4.23'
        func = async_function(self.instance.delete)
        await self.async_eapi_positive_config_test(func, 'no ntp local-interface')

    async def test_default(self):
        # Test with version < 4.23
        self.instance.version_number = '4.22'
        func = async_function(self.instance.default)
        await self.async_eapi_positive_config_test(func, 'default ntp source')

        # Test with version >= 4.23
        self.instance.version_number = '4.23'
        func = async_function(self.instance.default)
        await self.async_eapi_positive_config_test(func, 'default ntp local-interface')

    async def test_set_source_interface(self):
        # Test with version < 4.23
        self.instance.version_number = '4.22'
        func = async_function(self.instance.set_source_interface, 'Vlan50')
        await self.async_eapi_positive_config_test(func, 'ntp source Vlan50')

        # Test with version >= 4.23
        self.instance.version_number = '4.23'
        func = async_function(self.instance.set_source_interface, 'Vlan50')
        await self.async_eapi_positive_config_test(func, 'ntp local-interface Vlan50')

    async def test_add_server(self):
        func = async_function(self.instance.add_server, '1.1.1.1')
        await self.async_eapi_positive_config_test(func, 'ntp server 1.1.1.1')

    async def test_add_server_prefer(self):
        func = async_function(self.instance.add_server, '1.1.1.1', prefer=True)
        await self.async_eapi_positive_config_test(func, 'ntp server 1.1.1.1 prefer')

    async def test_add_server_invalid(self):
        # Test with empty string
        with self.assertRaises(ValueError):
            await self.instance.add_server('')

        # Test with space
        with self.assertRaises(ValueError):
            await self.instance.add_server(' ')

        # Test with None
        with self.assertRaises(ValueError):
            await self.instance.add_server(None)

    async def test_remove_server(self):
        func = async_function(self.instance.remove_server, '1.1.1.1')
        await self.async_eapi_positive_config_test(func, 'no ntp server 1.1.1.1')

    async def test_remove_all_servers(self):
        func = async_function(self.instance.remove_all_servers)
        await self.async_eapi_positive_config_test(func, 'no ntp')


if __name__ == '__main__':
    unittest.main()