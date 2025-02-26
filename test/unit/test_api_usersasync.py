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

import pyeapi.api.usersasync

# Sample SSH key for testing
TEST_SSH_KEY = ('ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDKL1UtYLcK1E7w82Da/R+dB9QOwGgxD3AxWXeU'
                'WKPTKlXY+fnm34AOmZqJ4HqxwF9BrlV1/eCCsNZwdHyoZYeFYvIl+ZqGxe2m32ve2A15Xg0HQ7Ra'
                'EVCm6IY7FS7kc4nlnD/tFvTvShy/fzYQRAdM7ZfVtegW8sMSFJzBR/T/Y/sxI'
                '16Y/dQb8fC3la9T25XOrzsFrQiKRZmJGwg8d+0RLxpfMg0s/9ATwQKp6tPoLE'
                '4f3dKlAgSk5eENyVLA3RsypWADHpenHPcB7sa8D38e1TS+n+EUyAdb3Yov+5E'
                'SAbgLIJLd52Xv+FyYi0c2L49ByBjcRrupp4zfXn4DNRnEG4K6GcmswHuMEGZv'
                '5vjJ9OYaaaaaaa')


class TestApiUsersAsync(AsyncEapiConfigUnitTest):

    def __init__(self, *args, **kwargs):
        super(TestApiUsersAsync, self).__init__(*args, **kwargs)
        self.instance = pyeapi.api.usersasync.instance(None)
        self.config = open(get_fixture('running_config.text')).read()
        # Mock the config property to return the test config
        self.instance.get_block = unittest.mock.AsyncMock(return_value=self.config)
        self.instance.configure = unittest.mock.AsyncMock(return_value=True)
        self.instance.version_number = '4.22'  # Default version for tests

    def test_isprivilege_returns_false(self):
        # This is a static method, so no need for async
        result = pyeapi.api.usersasync.isprivilege('test')
        self.assertFalse(result)

    def test_instance(self):
        result = pyeapi.api.usersasync.instance(None)
        self.assertIsInstance(result, pyeapi.api.usersasync.UsersAsync)

    async def test_get(self):
        keys = ['nopassword', 'privilege', 'role', 'secret', 'format', 'sshkey']
        
        # Mock the _parse_username method to return a consistent structure
        self.instance._parse_username = unittest.mock.MagicMock(
            return_value={'test': {
                'nopassword': True, 'privilege': '1', 'role': '',
                'secret': '', 'format': '', 'sshkey': ''
            }})
        
        result = await self.instance.get('test')
        self.assertEqual(sorted(keys), sorted(result.keys()))

    async def test_getall(self):
        # Mock the users_re.findall to return a list of matches
        self.instance.users_re = unittest.mock.MagicMock()
        self.instance.users_re.findall = unittest.mock.MagicMock(
            return_value=[('test', '1', '', '', '', '', '')])
        
        # Mock the _parse_username method to return a consistent structure
        self.instance._parse_username = unittest.mock.MagicMock(
            return_value={'test': {
                'nopassword': True, 'privilege': '1', 'role': '',
                'secret': '', 'format': '', 'sshkey': ''
            }})
        
        result = await self.instance.getall()
        self.assertIsInstance(result, dict)

    async def test_create_with_nopassword(self):
        cmds = 'username test nopassword'
        func = async_function(self.instance.create, 'test', nopassword=True)
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_create_with_secret_cleartext(self):
        cmds = 'username test secret password'
        func = async_function(self.instance.create, 'test', secret='password')
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_create_with_secret_md5(self):
        cmds = 'username test secret 5 $1$X/upk0eL$85fzHLi.f/3HfufORBga2/'
        func = async_function(self.instance.create, 'test',
                           secret='$1$X/upk0eL$85fzHLi.f/3HfufORBga2/',
                           encryption='md5')
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_create_with_secret_nologin(self):
        cmds = 'username test secret $0$nologin'
        func = async_function(self.instance.create, 'test',
                           secret='$0$nologin')
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_create_with_secret_sha512(self):
        cmds = 'username test secret sha512 $6$Z.9sx8mTig/LuL2f$onLUBt26VzZPXWs0YVmGzp4RgZCHkr9iosyre9cyhNq740iW6sQe/rrKhOjV/HFQZtsUuMmnoHrPJdFowJXhA/'
        func = async_function(self.instance.create, 'test',
                           secret='$6$Z.9sx8mTig/LuL2f$onLUBt26VzZPXWs0YVmGzp4RgZCHkr9iosyre9cyhNq740iW6sQe/rrKhOjV/HFQZtsUuMmnoHrPJdFowJXhA/',
                           encryption='sha512')
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_create_with_missing_kwargs(self):
        with self.assertRaises(ValueError):
            await self.instance.create('test')

    async def test_create_with_invalid_secret_arg(self):
        with self.assertRaises(ValueError):
            await self.instance.create('test', secret='password', nopassword=True)

    async def test_delete(self):
        cmds = 'no username test'
        func = async_function(self.instance.delete, 'test')
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_delete_admin_exception(self):
        with self.assertRaises(ValueError):
            await self.instance.delete('admin')

    async def test_default(self):
        cmds = 'default username test'
        func = async_function(self.instance.default, 'test')
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_privilege(self):
        cmds = ['username test', 'privilege 10']
        func = async_function(self.instance.set_privilege, 'test', 10)
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_privilege_negate(self):
        cmds = ['username test', 'privilege 1']
        func = async_function(self.instance.set_privilege, 'test')
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_privilege_invalid_value(self):
        with self.assertRaises(ValueError):
            await self.instance.set_privilege('test', 'abc')

    async def test_set_role(self):
        cmds = ['username test', 'role network-admin']
        func = async_function(self.instance.set_role, 'test', 'network-admin')
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_role_negate(self):
        cmds = ['username test', 'no role']
        func = async_function(self.instance.set_role, 'test', disable=True)
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_role_default(self):
        cmds = ['username test', 'default role']
        func = async_function(self.instance.set_role, 'test', default=True)
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_sshkey_pre_4_23(self):
        # Test with EOS version < 4.23
        self.instance.version_number = '4.22'
        cmds = ['username test', 'sshkey %s' % TEST_SSH_KEY]
        func = async_function(self.instance.set_sshkey, 'test', TEST_SSH_KEY)
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_sshkey_post_4_23(self):
        # Test with EOS version >= 4.23
        self.instance.version_number = '4.23'
        cmds = ['username test', 'ssh-key %s' % TEST_SSH_KEY]
        func = async_function(self.instance.set_sshkey, 'test', TEST_SSH_KEY)
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_sshkey_with_empty_string(self):
        cmds = ['username test', 'no sshkey']
        func = async_function(self.instance.set_sshkey, 'test', '')
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_sshkey_with_None(self):
        cmds = ['username test', 'no sshkey']
        func = async_function(self.instance.set_sshkey, 'test', None)
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_sshkey_negate_pre_4_23(self):
        # Test with EOS version < 4.23
        self.instance.version_number = '4.22'
        cmds = ['username test', 'no sshkey']
        func = async_function(self.instance.set_sshkey, 'test', disable=True)
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_sshkey_negate_post_4_23(self):
        # Test with EOS version >= 4.23
        self.instance.version_number = '4.23'
        cmds = ['username test', 'no ssh-key']
        func = async_function(self.instance.set_sshkey, 'test', disable=True)
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_sshkey_default_pre_4_23(self):
        # Test with EOS version < 4.23
        self.instance.version_number = '4.22'
        cmds = ['username test', 'default sshkey']
        func = async_function(self.instance.set_sshkey, 'test', default=True)
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_sshkey_default_post_4_23(self):
        # Test with EOS version >= 4.23
        self.instance.version_number = '4.23'
        cmds = ['username test', 'default ssh-key']
        func = async_function(self.instance.set_sshkey, 'test', default=True)
        await self.async_eapi_positive_config_test(func, cmds)


if __name__ == '__main__':
    unittest.main()c