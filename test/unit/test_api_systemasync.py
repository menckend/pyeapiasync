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
#   documentation and/or othser materials provided with the distribution.
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

import pyeapiasync.api.systemasync


class TestApiSystemAsync(AsyncEapiConfigUnitTest):

    def __init__(self, *args, **kwargs):
        super(TestApiSystemAsync, self).__init__(*args, **kwargs)
        self.instance = pyeapiasync.api.systemasync.SystemAsync(None)
        self.config = open(get_fixture('running_config.text')).read()
        # Mock the get_block method to return test config
        self.instance.get_block = unittest.mock.AsyncMock(return_value=self.config)
        self.instance.configure = unittest.mock.AsyncMock(return_value=True)
        self.instance.error = unittest.mock.MagicMock()

    def test_instance(self):
        result = pyeapiasync.api.systemasync.instance(None)
        self.assertIsInstance(result, pyeapiasync.api.systemasync.SystemAsync)

    async def test_get(self):
        # Mock get_block to return a specific configuration
        sample_config = """
hostname test
ip routing
!
banner motd
Testing Banner MOTD
EOF
!
banner login
Testing Banner Login
EOF
!
"""
        self.instance.get_block = unittest.mock.AsyncMock(return_value=sample_config)
        
        result = await self.instance.get()
        keys = ['hostname', 'iprouting', 'banner_motd', 'banner_login']
        self.assertEqual(sorted(keys), sorted(result.keys()))
        self.assertEqual(result['hostname'], 'test')
        self.assertEqual(result['iprouting'], True)
        self.assertEqual(result['banner_motd'], 'Testing Banner MOTD')
        self.assertEqual(result['banner_login'], 'Testing Banner Login')

    async def test_get_check_hostname(self):
        # Mock get_block to return a specific hostname
        sample_config = "hostname teststring\n"
        self.instance.get_block = unittest.mock.AsyncMock(return_value=sample_config)
        
        result = await self.instance.get()
        self.assertEqual(result['hostname'], 'teststring')

    async def test_get_with_period(self):
        # Mock get_block to return a hostname with periods
        sample_config = "hostname host.domain.net\n"
        self.instance.get_block = unittest.mock.AsyncMock(return_value=sample_config)
        
        result = await self.instance.get()
        self.assertEqual(result['hostname'], 'host.domain.net')

    async def test_get_check_banners(self):
        # Mock get_block to return specific banner configuration
        sample_config = """
banner motd
Testing Banner MOTD
EOF
!
banner login
Testing Banner Login
EOF
!
"""
        self.instance.get_block = unittest.mock.AsyncMock(return_value=sample_config)
        
        result = await self.instance.get()
        self.assertEqual(result['banner_motd'], 'Testing Banner MOTD')
        self.assertEqual(result['banner_login'], 'Testing Banner Login')

    async def test_get_banner_with_EOF(self):
        # Mock get_block to return banner content that contains "EOF" (edge case)
        sample_config = """
banner motd
Testing Banner MOTD with EOF in the middle
EOF
!
"""
        self.instance.get_block = unittest.mock.AsyncMock(return_value=sample_config)
        
        result = await self.instance.get()
        self.assertEqual(result['banner_motd'], 'Testing Banner MOTD with EOF in the middle')

    async def test_set_hostname_with_value(self):
        value = random_string()
        cmds = 'hostname %s' % value
        func = async_function(self.instance.set_hostname, value)
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_hostname_with_no_value(self):
        cmds = 'no hostname'
        func = async_function(self.instance.set_hostname, disable=True)
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_hostname_with_default(self):
        cmds = 'default hostname'
        func = async_function(self.instance.set_hostname, default=True)
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_hostname_default_over_value(self):
        # Test that default takes precedence over a specified value
        value = random_string()
        cmds = 'default hostname'
        func = async_function(self.instance.set_hostname, value, default=True)
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_hostname_with_period(self):
        value = 'host.domain.net'
        cmds = 'hostname %s' % value
        func = async_function(self.instance.set_hostname, value)
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_iprouting_to_true(self):
        cmds = 'ip routing'
        func = async_function(self.instance.set_iprouting, True)
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_iprouting_to_false(self):
        cmds = 'no ip routing'
        func = async_function(self.instance.set_iprouting, False)
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_iprouting_to_no(self):
        cmds = 'no ip routing'
        func = async_function(self.instance.set_iprouting, disable=True)
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_iprouting_to_default(self):
        cmds = 'default ip routing'
        func = async_function(self.instance.set_iprouting, default=True)
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_banner_motd(self):
        text = random_string()
        cmds = ['banner motd', text, 'EOF']
        func = async_function(self.instance.set_banner_motd, text)
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_banner_motd_donkey(self):
        text = random_string()
        cmds = ['banner motd donkey', text, 'donkey']
        func = async_function(self.instance.set_banner_motd, text, delim='donkey')
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_banner_motd_default(self):
        cmds = 'default banner motd'
        func = async_function(self.instance.set_banner_motd, default=True)
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_banner_motd_disable(self):
        cmds = 'no banner motd'
        func = async_function(self.instance.set_banner_motd, disable=True)
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_banner_login(self):
        text = random_string()
        cmds = ['banner login', text, 'EOF']
        func = async_function(self.instance.set_banner_login, text)
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_banner_login_donkey(self):
        text = random_string()
        cmds = ['banner login donkey', text, 'donkey']
        func = async_function(self.instance.set_banner_login, text, delim='donkey')
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_banner_login_default(self):
        cmds = 'default banner login'
        func = async_function(self.instance.set_banner_login, default=True)
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_banner_login_disable(self):
        cmds = 'no banner login'
        func = async_function(self.instance.set_banner_login, disable=True)
        await self.async_eapi_positive_config_test(func, cmds)


if __name__ == '__main__':
    unittest.main()