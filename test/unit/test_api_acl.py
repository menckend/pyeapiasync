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
import asyncio
sys.path.append(os.path.join(os.path.dirname(__file__), '../lib'))
from testlib import get_fixture, function, async_function
from testlib import EapiAsyncConfigUnitTest
import pyeapiasync.api.aclasync as aclasync
from unittest.mock import AsyncMock

class TestApiAclFunctions(unittest.TestCase):

    def test_mask_to_prefixlen(self):
        result = aclasync.mask_to_prefixlen('255.255.255.0')
        self.assertEqual(result, 24)

    def test_prefixlen_to_mask(self):
        result = aclasync.prefixlen_to_mask('24')
        self.assertEqual(result, '255.255.255.0')


class TestApiAcls(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.node = AsyncMock()
        self.node.get_running_config = AsyncMock()
        self.instance = aclasync.instance(self.node)

    async def test_instance(self):
        result = aclasync.instance(None)
        self.assertIsInstance(result, aclasync.AclsAsync)

    async def test_getall(self):
        self.node.get_running_config.return_value = get_fixture('running_config.text')
        result = await self.instance.getall()
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result['standard']), 0)
        self.assertEqual(len(result['extended']), 0)

    async def test_get_not_configured(self):
        self.node.get_running_config.return_value = get_fixture('running_config.text')
        self.assertIsNone(await self.instance.get('unconfigured'))

    async def test_get(self):
        self.node.get_running_config.return_value = get_fixture('running_config.text')
        result = await self.instance.get('test')
        self.assertIsNone(result)

    async def test_get_instance(self):
        self.node.get_running_config.return_value = get_fixture('running_config.text')
        result = await self.instance.get_instance('test')
        self.assertEqual(result, {'test': None})

    async def test_create_standard(self):
        self.node.config = AsyncMock()
        func = lambda: self.instance.create('test')
        cmds = 'ip access-list standard test'
        await self.eapi_positive_config_test(func, cmds)

    async def test_create_extended(self):
        self.node.config = AsyncMock()
        func = lambda: self.instance.create('test', 'extended')
        cmds = 'ip access-list test'
        await self.eapi_positive_config_test(func, cmds)

    async def test_create_unknown_type_creates_standard(self):
        self.node.config = AsyncMock()
        func = lambda: self.instance.create('test', 'bogus')
        cmds = 'ip access-list standard test'
        await self.eapi_positive_config_test(func, cmds)

    async def test_proxy_method_success(self):
        # Set up running config mock to return actual fixture data
        with open(get_fixture('running_config.text'), 'r') as f:
            self.node.get_running_config.return_value = f.read()
        
        self.node.config = AsyncMock()
        self.node.config.return_value = True
        
        # Create a standard ACL instance first
        await self.instance.create('test', 'standard')
        
        # Now try to remove an entry
        await self.instance.remove_entry('test', '10')
        
        # Verify both calls were made as expected
        self.assertEqual(self.node.config.call_count, 2)
        self.node.config.assert_has_calls([
            unittest.mock.call(['ip access-list standard test']),
            unittest.mock.call(['ip access-list standard test', 'no 10', 'exit'])
        ])

    async def test_proxy_method_raises_attribute_error(self):
        # Set up running config mock to return actual fixture data
        with open(get_fixture('running_config.text'), 'r') as f:
            self.node.get_running_config.return_value = f.read()
            
        with self.assertRaises(AttributeError):
            await self.instance.nonmethod('test', '10')

    async def eapi_positive_config_test(self, func, *args):
        self.node.config.return_value = True
        result = await func()
        self.assertTrue(result)
        self.node.config.assert_called_once_with(list(args))
        await asyncio.sleep(0)

class TestApiStandardAcls(EapiAsyncConfigUnitTest):

    def __init__(self, *args, **kwargs):
        super(TestApiStandardAcls, self).__init__(*args, **kwargs)
        self.instance = aclasync.StandardAclsAsync(None)
        self.config = open(get_fixture('running_config.text')).read()

    async def test_get(self):
        result = await self.instance.get('test')
        keys = ['name', 'type', 'entries']
        self.assertEqual(sorted(keys), sorted(result.keys()))
        self.assertEqual(result['type'], 'standard')
        await asyncio.sleep(0)

    async def test_get_not_configured(self):
        self.assertIsNone(await self.instance.get('unconfigured'))
        await asyncio.sleep(0)

    async def test_acl_functions(self):
        self.node.config = AsyncMock()
        expected_calls = []
        
        # Test each ACL function individually
        for name in ['create', 'delete', 'default']:
            if name == 'create':
                cmds = ['ip access-list standard test']
            elif name == 'delete':
                cmds = ['no ip access-list standard test']
            elif name == 'default':
                cmds = ['default ip access-list standard test']
                
            func = function(name, 'test')
            self.node.config.return_value = True
            method = getattr(self.instance, func.name)
            self.assertTrue(await method(*func.args, **func.kwargs))
            expected_calls.append(unittest.mock.call(cmds))
            
        self.node.config.assert_has_calls(expected_calls)

    async def test_update_entry(self):
        cmds = ['ip access-list standard test', 'no 10',
                '10 permit 0.0.0.0/32 log', 'exit']
        func = function('update_entry', 'test', '10', 'permit', '0.0.0.0',
                        '32', True)
        await self.eapi_positive_config_test(func, cmds)
       # await asyncio.sleep(0)

    async def test_update_entry_no_log(self):
        cmds = ['ip access-list standard test', 'no 10',
                '10 permit 0.0.0.0/32', 'exit']
        func = function('update_entry', 'test', '10', 'permit', '0.0.0.0',
                        '32')
        await self.eapi_positive_config_test(func, cmds)

    async def test_remove_entry(self):
        cmds = ['ip access-list standard test', 'no 10', 'exit']
        func = function('remove_entry', 'test', '10')
        await self.eapi_positive_config_test(func, cmds)

    async def test_add_entry(self):
        cmds = ['ip access-list standard test', 'permit 0.0.0.0/32 log',
                'exit']
        func = function('add_entry', 'test', 'permit', '0.0.0.0',
                        '32', True)
        await self.eapi_positive_config_test(func, cmds)

    async def test_add_entry_no_log(self):
        cmds = ['ip access-list standard test', 'permit 0.0.0.0/32',
                'exit']
        func = function('add_entry', 'test', 'permit', '0.0.0.0',
                        '32')
        await self.eapi_positive_config_test(func, cmds)

    async def test_add_entry_with_seqno(self):
        cmds = ['ip access-list standard test', '30 permit 0.0.0.0/32 log',
                'exit']
        func = function('add_entry', 'test', 'permit', '0.0.0.0',
                        '32', True, 30)
        await self.eapi_positive_config_test(func, cmds)


class TestApiExtendedAcls(EapiAsyncConfigUnitTest):

    def __init__(self, *args, **kwargs):
        super(TestApiExtendedAcls, self).__init__(*args, **kwargs)
        self.instance = aclasync.ExtendedAclsAsync(None)
        self.config = open(get_fixture('running_config.text')).read()

    async def test_get(self):
        result = await self.instance.get('exttest')
        keys = ['name', 'type', 'entries']
        self.assertEqual(sorted(keys), sorted(result.keys()))
        self.assertEqual(result['type'], 'extended')
        self.assertIn('entries', result)
        self.assertIn('50', result['entries'])
        entry = dict(action='permit', dstaddr='1.1.1.2', dstlen=None,
                     dstport=None, other=None, protocol='ip', srcaddr='any',
                     srclen=None, srcport=None)
        self.assertEqual(entry, result['entries']['50'])
        self.assertIn('70', result['entries'])
        entry = dict(action='permit', dstaddr='3.3.3.3', dstlen=None,
                     dstport='lt ipp', protocol='tcp', srcaddr='8.8.8.0',
                     other='urg ttl eq 24 fragments tracked log',
                     srclen='24', srcport='neq irc')
        self.assertEqual(entry, result['entries']['70'])
        await asyncio.sleep(0)

    async def test_get_not_configured(self):
        self.assertIsNone(await self.instance.get('unconfigured'))
        await asyncio.sleep(0)

    async def test_acl_functions(self):
        self.node.config = AsyncMock()
        expected_calls = []
        
        # Test each ACL function individually
        for name in ['create', 'delete', 'default']:
            if name == 'create':
                cmds = ['ip access-list exttest']
            elif name == 'delete':
                cmds = ['no ip access-list exttest']
            elif name == 'default':
                cmds = ['default ip access-list exttest']
                
            func = function(name, 'exttest')
            self.node.config.return_value = True
            method = getattr(self.instance, func.name)
            self.assertTrue(await method(*func.args, **func.kwargs))
            expected_calls.append(unittest.mock.call(cmds))
            
        self.node.config.assert_has_calls(expected_calls)
        await asyncio.sleep(0)

    async def test_update_entry(self):
        cmds = ['ip access-list exttest', 'no 10',
                '10 permit ip 0.0.0.0/32 1.1.1.1/32 log', 'exit']
        func = function('update_entry', 'exttest', '10', 'permit', 'ip',
                        '0.0.0.0', '32', '1.1.1.1', '32', True)
        await self.eapi_positive_config_test(func, cmds)

    async def test_update_entry_no_log(self):
        cmds = ['ip access-list exttest', 'no 10',
                '10 permit ip 0.0.0.0/32 1.1.1.1/32', 'exit']
        func = function('update_entry', 'exttest', '10', 'permit', 'ip',
                        '0.0.0.0', '32', '1.1.1.1', '32')
        await self.eapi_positive_config_test(func, cmds)

    async def test_remove_entry(self):
        cmds = ['ip access-list exttest', 'no 10', 'exit']
        func = function('remove_entry', 'exttest', '10')
        await self.eapi_positive_config_test(func, cmds)

    async def test_add_entry(self):
        cmds = ['ip access-list exttest',
                'permit ip 0.0.0.0/32 1.1.1.1/32 log', 'exit']
        func = function('add_entry', 'exttest', 'permit', 'ip', '0.0.0.0',
                        '32', '1.1.1.1', '32', True)
        await self.eapi_positive_config_test(func, cmds)

    async def test_add_entry_no_log(self):
        cmds = ['ip access-list exttest', 'permit ip 0.0.0.0/32 1.1.1.1/32',
                'exit']
        func = function('add_entry', 'exttest', 'permit', 'ip', '0.0.0.0',
                        '32', '1.1.1.1', '32')
        await self.eapi_positive_config_test(func, cmds)

    async def test_add_entry_with_seqno(self):
        cmds = ['ip access-list exttest',
                '30 permit ip 0.0.0.0/32 1.1.1.1/32 log', 'exit']
        func = function('add_entry', 'exttest', 'permit', 'ip', '0.0.0.0',
                        '32', '1.1.1.1', '32', True, 30)
        await self.eapi_positive_config_test(func, cmds)


if __name__ == '__main__':
    unittest.main()
