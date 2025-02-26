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

import pyeapi.api.mlagasync


class TestApiMlagAsync(AsyncEapiConfigUnitTest):

    def setUp(self):
        super().setUp()
        self.instance = pyeapi.api.mlagasync.instance(None)
        self.config = open(get_fixture('running_config.text')).read()
        # Mock the get_block method to return test config
        self.instance.get_block = unittest.mock.AsyncMock(return_value=self.config)
        self.instance.configure = unittest.mock.AsyncMock(return_value=True)

    async def test_get(self):
        result = await self.instance.get()

        keys = ['config', 'interfaces']

        intfkeys = ['mlag_id']
        interfaces = result['interfaces']['Port-Channel10']

        cfgkeys = ['domain_id', 'local_interface', 'peer_address',
                   'peer_link', 'shutdown']

        self.assertEqual(sorted(keys), sorted(result.keys()))
        self.assertEqual(sorted(cfgkeys), sorted(result['config'].keys()))
        self.assertEqual(sorted(intfkeys), sorted(interfaces.keys()))

    async def test_set_domain_id(self):
        for state in ['config', 'negate', 'default']:
            if state == 'config':
                cmds = ['mlag configuration', 'domain-id test']
                func = async_function(self.instance.set_domain_id, 'test')
                await self.async_eapi_positive_config_test(func, cmds)
            elif state == 'negate':
                cmds = ['mlag configuration', 'no domain-id']
                func = async_function(self.instance.set_domain_id, disable=True)
                await self.async_eapi_positive_config_test(func, cmds)
            elif state == 'default':
                cmds = ['mlag configuration', 'default domain-id']
                func = async_function(self.instance.set_domain_id, default=True)
                await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_local_interface(self):
        for state in ['config', 'negate', 'default']:
            if state == 'config':
                cmds = ['mlag configuration', 'local-interface Vlan1234']
                func = async_function(self.instance.set_local_interface, 'Vlan1234')
                await self.async_eapi_positive_config_test(func, cmds)
            elif state == 'negate':
                cmds = ['mlag configuration', 'no local-interface']
                func = async_function(self.instance.set_local_interface, disable=True)
                await self.async_eapi_positive_config_test(func, cmds)
            elif state == 'default':
                cmds = ['mlag configuration', 'default local-interface']
                func = async_function(self.instance.set_local_interface, default=True)
                await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_peer_address(self):
        for state in ['config', 'negate', 'default']:
            if state == 'config':
                cmds = ['mlag configuration', 'peer-address 1.2.3.4']
                func = async_function(self.instance.set_peer_address, '1.2.3.4')
                await self.async_eapi_positive_config_test(func, cmds)
            elif state == 'negate':
                cmds = ['mlag configuration', 'no peer-address']
                func = async_function(self.instance.set_peer_address, disable=True)
                await self.async_eapi_positive_config_test(func, cmds)
            elif state == 'default':
                cmds = ['mlag configuration', 'default peer-address']
                func = async_function(self.instance.set_peer_address, default=True)
                await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_peer_link(self):
        for state in ['config', 'negate', 'default']:
            if state == 'config':
                cmds = ['mlag configuration', 'peer-link Ethernet1']
                func = async_function(self.instance.set_peer_link, 'Ethernet1')
                await self.async_eapi_positive_config_test(func, cmds)
            elif state == 'negate':
                cmds = ['mlag configuration', 'no peer-link']
                func = async_function(self.instance.set_peer_link, disable=True)
                await self.async_eapi_positive_config_test(func, cmds)
            elif state == 'default':
                cmds = ['mlag configuration', 'default peer-link']
                func = async_function(self.instance.set_peer_link, default=True)
                await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_shutdown(self):
        for enable, value in [(None, True), (False, False), (True, True)]:
            if enable is None:
                cmds = ['mlag configuration', 'shutdown']
                func = async_function(self.instance.set_shutdown)
                await self.async_eapi_positive_config_test(func, cmds)
            else:
                cmd = 'shutdown' if enable else 'no shutdown'
                cmds = ['mlag configuration', cmd]
                func = async_function(self.instance.set_shutdown, value)
                await self.async_eapi_positive_config_test(func, cmds)

        # Test default case
        cmds = ['mlag configuration', 'default shutdown']
        func = async_function(self.instance.set_shutdown, default=True)
        await self.async_eapi_positive_config_test(func, cmds)

        # Test disable case (should result in 'no shutdown')
        cmds = ['mlag configuration', 'no shutdown']
        func = async_function(self.instance.set_shutdown, disable=True)
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_mlag_id(self):
        for state in ['config', 'negate', 'default']:
            if state == 'config':
                cmds = ['interface Ethernet1', 'mlag 1']
                func = async_function(self.instance.set_mlag_id, 'Ethernet1', '1')
                await self.async_eapi_positive_config_test(func, cmds)
            elif state == 'negate':
                cmds = ['interface Ethernet1', 'no mlag']
                func = async_function(self.instance.set_mlag_id, 'Ethernet1', disable=True)
                await self.async_eapi_positive_config_test(func, cmds)
            elif state == 'default':
                cmds = ['interface Ethernet1', 'default mlag']
                func = async_function(self.instance.set_mlag_id, 'Ethernet1', value='1',
                                     default=True)
                await self.async_eapi_positive_config_test(func, cmds)


if __name__ == '__main__':
    unittest.main()