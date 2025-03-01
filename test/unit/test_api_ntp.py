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
import sys
import os
import unittest

sys.path.append(os.path.join(os.path.dirname(__file__), '../lib'))

from testlib import get_fixture, function
from testlib import EapiAsyncConfigUnitTest
from pyeapiasync.api.ntpasync import NtpAsync


class TestApiNtpAsync(EapiAsyncConfigUnitTest):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance = NtpAsync.instance(None)
        self.config = open(get_fixture('running_config.text')).read()

    def test_instance(self):
        result = NtpAsync.instance(None)
        self.assertIsInstance(result, NtpAsync)

    async def test_get(self):
        result = await self.instance.get()
        ntp = {'servers': [{'1.2.3.4': 'prefer'},
                           {'10.20.30.40': None},
                           {'11.22.33.44': None},
                           {'123.33.22.11': 'prefer'},
                           {'123.44.55.66': None},
                           {'joe': None}],
               'source_interface': 'Loopback1'}
        keys = ['source_interface', 'servers']
        self.assertEqual(sorted(keys), sorted(result.keys()))
        self.assertEqual(ntp['source_interface'], result['source_interface'])
        self.assertIsNotNone(result['servers'])

    async def test_create(self):
        cmd = 'ntp source Ethernet2'
        func = function('create', 'Ethernet2')
        await self.eapi_async_positive_config_test(func, cmd)

    async def test_delete(self):
        cmd = 'no ntp source'
        func = function('delete')
        await self.eapi_async_positive_config_test(func, cmd)

    async def test_default(self):
        cmd = 'default ntp source'
        func = function('default')
        await self.eapi_async_positive_config_test(func, cmd)

    async def test_set_source_interface(self):
        cmd = 'ntp source Vlan50'
        func = function('set_source_interface', 'Vlan50')
        await self.eapi_async_positive_config_test(func, cmd)

    async def test_add_server(self):
        cmd = 'ntp server 1.1.1.1'
        func = function('add_server', '1.1.1.1')
        await self.eapi_async_positive_config_test(func, cmd)

    async def test_add_server_prefer(self):
        cmd = 'ntp server 1.1.1.1 prefer'
        func = function('add_server', '1.1.1.1', prefer=True)
        await self.eapi_async_positive_config_test(func, cmd)

    async def test_add_server_invalid(self):
        func = function('add_server', '', prefer=True)
        await self.eapi_async_exception_config_test(func, ValueError)

        func = function('add_server', ' ', prefer=True)
        await self.eapi_async_exception_config_test(func, ValueError)

    async def test_remove_server(self):
        cmd = 'no ntp server 1.1.1.1'
        func = function('remove_server', '1.1.1.1')
        await self.eapi_async_positive_config_test(func, cmd)

    async def test_remove_all_servers(self):
        cmd = 'no ntp'
        func = function('remove_all_servers')
        await self.eapi_async_positive_config_test(func, cmd)


if __name__ == '__main__':
    unittest.main()
