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
import pyeapiasync.api.usersasync

class TestApiUsers(EapiAsyncConfigUnitTest):
    def __init__(self, *args, **kwargs):
        super(TestApiUsers, self).__init__(*args, **kwargs)
        self.instance = pyeapiasync.api.usersasync.instance(None)
        self.config = open(get_fixture('running_config.text')).read()
    
    def test_isprivilege_returns_false(self):
        result = pyeapiasync.api.usersasync.isprivilege('test')
        self.assertFalse(result)
    
    async def test_get(self):
        keys = ['nopassword', 'privilege', 'role', 'secret', 'format', 'sshkey']
        result = await self.instance.get('test')
        self.assertEqual(sorted(keys), sorted(result.keys()))
    
    async def test_getall(self):
        result = await self.instance.getall()
        self.assertIsInstance(result, dict)
    
    async def test_create_with_nopassword(self):
        cmds = 'username test nopassword'
        func = function('create', 'test', nopassword=True)
        await self.eapi_positive_config_test(func, cmds)
    
    async def test_create_with_secret_cleartext(self):
        cmds = 'username test secret 0 pass'
        func = function('create', 'test', secret='pass')
        await self.eapi_positive_config_test(func, cmds)
    
    async def test_create_with_secret_md5(self):
        cmds = 'username test secret 5 pass'
        func = function('create', 'test', secret='pass', encryption='md5')
        await self.eapi_positive_config_test(func, cmds)
    
    async def test_create_with_secret_nologin(self):
        cmds = 'username test secret *'
        func = function('create', 'test', secret='', encryption='nologin')
        await self.eapi_positive_config_test(func, cmds)
    
    async def test_create_with_secret_sha512(self):
        cmds = 'username test secret sha512 pass'
        func = function('create', 'test', secret='pass', encryption='sha512')
        await self.eapi_positive_config_test(func, cmds)
    
    async def test_create_with_missing_kwargs(self):
        with self.assertRaises(TypeError):
            await self.instance.create('test')
    
    async def test_create_with_invalid_secret_arg(self):
        with self.assertRaises(TypeError):
            await self.instance.create_with_secret('test', 'test', 'test')
    
    async def test_delete(self):
        with self.assertRaises(TypeError):
            await self.instance.delete('admin')
    
    async def test_delete_admin_exception(self):
        cmds = 'no username test'
        func = function('delete', 'test')
        await self.eapi_positive_config_test(func, cmds)
    
    async def test_default(self):
        cmds = 'default username test'
        func = function('default', 'test')
        await self.eapi_positive_config_test(func, cmds)
    
    async def test_set_privilege(self):
        cmds = 'username test privilege 8'
        func = function('set_privilege', 'test', 8)
        await self.eapi_positive_config_test(func, cmds)
    
    async def test_set_privilege_negate(self):
        cmds = 'username test privilege 1'
        func = function('set_privilege', 'test')
        await self.eapi_positive_config_test(func, cmds)
    
    async def test_set_privilege_invalid_value(self):
        with self.assertRaises(TypeError):
            await self.instance.set_privilege('test', 16)
    
    async def test_set_role(self):
        cmds = 'username test role ops'
        func = function('set_role', 'test', value='ops')
        await self.eapi_positive_config_test(func, cmds)
    
    async def test_set_role_negate(self):
        cmds = 'no username test role'
        func = function('set_role', 'test', disable=True)
        await self.eapi_positive_config_test(func, cmds)
    
    async def test_set_role_default(self):
        cmds = 'default username test role'
        func = function('set_role', 'test', default=True)
        await self.eapi_positive_config_test(func, cmds)
    
    async def test_set_sshkey(self):
        cmds = 'username test sshkey newkey'
        func = function('set_sshkey', 'test', value='newkey')
        await self.eapi_positive_config_test(func, cmds)
    
    async def test_set_sshkey_negate(self):
        cmds = 'no username test sshkey'
        func = function('set_sshkey', 'test', disable=True)
        await self.eapi_positive_config_test(func, cmds)
    
    async def test_set_sshkey_default(self):
        cmds = 'default username test sshkey'
        func = function('set_sshkey', 'test', default=True)
        await self.eapi_positive_config_test(func, cmds)

if __name__ == '__main__':
    unittest.main()
