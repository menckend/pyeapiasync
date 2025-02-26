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

from testlib import get_fixture, async_function
from testlib import AsyncEapiConfigUnitTest

import pyeapi.api.aclasync


class TestApiAclAsyncFunctions(unittest.TestCase):
    """Tests for non-async functions in the aclasync module"""
    def test_mask_to_prefixlen(self):
        result = pyeapi.api.aclasync.mask_to_prefixlen('255.255.255.0')
        self.assertEqual(result, 24)


class TestApiAclsAsync(AsyncEapiConfigUnitTest):

    def setUp(self):
        super().setUp()
        self.instance = pyeapi.api.aclasync.AclsAsync(None)
        self.config = open(get_fixture('running_config.text')).read()
        # Mock the config property to return the test config
        self.instance.config = self.config

    def test_instance(self):
        result = pyeapi.api.aclasync.instance(None)
        self.assertIsInstance(result, pyeapi.api.aclasync.AclsAsync)

    async def test_getall(self):
        result = await self.instance.getall()
        self.assertIsInstance(result, dict)
        self.assertIn('exttest', result['extended'])
        self.assertIn('test', result['standard'])

    async def test_get_not_configured(self):
        self.assertIsNone(await self.instance.get('unconfigured'))

    async def test_get(self):
        result = await self.instance.get('test')
        keys = ['name', 'type', 'entries']
        self.assertEqual(sorted(keys), sorted(result.keys()))

    async def test_get_instance(self):
        result = await self.instance.get_instance('test')
        self.assertIsInstance(result, pyeapi.api.aclasync.StandardAclsAsync)
        self.instance._instances['test'] = result
        result = await self.instance.get_instance('exttest')
        self.assertIsInstance(result, pyeapi.api.aclasync.ExtendedAclsAsync)
        result = await self.instance.get_instance('unconfigured')
        self.assertIsInstance(result, dict)
        self.assertIsNone(result['unconfigured'])
        result = await self.instance.get_instance('test')
        self.assertIsInstance(result, pyeapi.api.aclasync.StandardAclsAsync)
        self.assertEqual(len(self.instance._instances), 2)

    async def test_create_instance_standard(self):
        result = await self.instance.create_instance('test', 'standard')
        self.assertIsInstance(result, pyeapi.api.aclasync.StandardAclsAsync)
        self.assertEqual(len(self.instance._instances), 1)

    async def test_create_instance_extended(self):
        result = await self.instance.create_instance('exttest', 'extended')
        self.assertIsInstance(result, pyeapi.api.aclasync.ExtendedAclsAsync)
        self.assertEqual(len(self.instance._instances), 1)

    async def test_create_standard(self):
        cmds = 'ip access-list standard test'
        func = async_function(self.instance.create, 'test')
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_create_extended(self):
        cmds = 'ip access-list exttest'
        func = async_function(self.instance.create, 'exttest', 'extended')
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_create_unknown_type_creates_standard(self):
        cmds = 'ip access-list standard test'
        func = async_function(self.instance.create, 'test', 'unknown')
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_marshall_method_success(self):
        # This tests the marshall method by proxying a call to remove_entry
        # We'll need to mock the get_instance method to return a mock object
        # with a remove_entry method
        mock_instance = unittest.mock.MagicMock()
        mock_instance.remove_entry.return_value = asyncio.Future()
        mock_instance.remove_entry.return_value.set_result(True)
        
        self.instance.get_instance = unittest.mock.AsyncMock(
            return_value={'test': mock_instance})
        
        result = await self.instance.remove_entry('test', '10')
        self.assertTrue(result)
        mock_instance.remove_entry.assert_called_with('test', '10')

    async def test_marshall_method_raises_attribute_error(self):
        # This tests that marshall raises AttributeError for non-existent methods
        mock_instance = unittest.mock.MagicMock()
        mock_instance.nonmethod = None
        
        self.instance.get_instance = unittest.mock.AsyncMock(
            return_value={'test': mock_instance})
        
        with self.assertRaises(AttributeError):
            await self.instance.nonmethod('test', '10')


class TestApiStandardAclsAsync(AsyncEapiConfigUnitTest):

    def setUp(self):
        super().setUp()
        self.instance = pyeapi.api.aclasync.StandardAclsAsync(None)
        self.config = open(get_fixture('running_config.text')).read()
        # Mock the get_block method to return the appropriate config section
        self.instance.get_block = unittest.mock.AsyncMock()
        self.instance.get_block.return_value = (
            'ip access-list standard test\n'
            '10 permit 0.0.0.0/32 log\n'
            '20 deny 1.1.1.1/24\n'
        )
        self.instance.configure = unittest.mock.AsyncMock(return_value=True)

    async def test_get(self):
        result = await self.instance.get('test')
        keys = ['name', 'type', 'entries']
        self.assertEqual(sorted(keys), sorted(result.keys()))
        self.assertEqual(result['type'], 'standard')
        self.instance.get_block.assert_called_with('ip access-list standard test')

    async def test_get_not_configured(self):
        self.instance.get_block.return_value = ''
        self.assertIsNone(await self.instance.get('unconfigured'))
        self.instance.get_block.assert_called_with('ip access-list standard unconfigured')

    async def test_acl_functions_create(self):
        await self.instance.create('test')
        self.instance.configure.assert_called_with('ip access-list standard test')

    async def test_acl_functions_delete(self):
        await self.instance.delete('test')
        self.instance.configure.assert_called_with('no ip access-list standard test')

    async def test_acl_functions_default(self):
        await self.instance.default('test')
        self.instance.configure.assert_called_with('default ip access-list standard test')

    async def test_update_entry(self):
        cmds = ['ip access-list standard test', 'no 10',
                '10 permit 0.0.0.0/32 log']
        await self.instance.update_entry('test', '10', 'permit', '0.0.0.0',
                                       '32', True)
        self.instance.configure.assert_called_with(cmds)

    async def test_update_entry_no_log(self):
        cmds = ['ip access-list standard test', 'no 10',
                '10 permit 0.0.0.0/32']
        await self.instance.update_entry('test', '10', 'permit', '0.0.0.0',
                                       '32')
        self.instance.configure.assert_called_with(cmds)

    async def test_remove_entry(self):
        cmds = ['ip access-list standard test', 'no 10', 'exit']
        await self.instance.remove_entry('test', '10')
        self.instance.configure.assert_called_with(cmds)

    async def test_add_entry(self):
        cmds = ['ip access-list standard test', 'permit 0.0.0.0/32 log',
                'exit']
        await self.instance.add_entry('test', 'permit', '0.0.0.0',
                                    '32', True)
        self.instance.configure.assert_called_with(cmds)

    async def test_add_entry_no_log(self):
        cmds = ['ip access-list standard test', 'permit 0.0.0.0/32',
                'exit']
        await self.instance.add_entry('test', 'permit', '0.0.0.0',
                                    '32')
        self.instance.configure.assert_called_with(cmds)

    async def test_add_entry_with_seqno(self):
        cmds = ['ip access-list standard test', '30 permit 0.0.0.0/32 log',
                'exit']
        await self.instance.add_entry('test', 'permit', '0.0.0.0',
                                    '32', True, 30)
        self.instance.configure.assert_called_with(cmds)

    def test_parse_entries(self):
        config = ('ip access-list standard test\n'
                  '10 permit 0.0.0.0/32 log\n'
                  '20 deny 1.1.1.1 255.255.255.0\n')
        result = self.instance._parse_entries(config)
        self.assertIn('entries', result)
        self.assertIn('10', result['entries'])
        self.assertIn('20', result['entries'])
        entry = result['entries']['10']
        self.assertEqual(entry['action'], 'permit')
        self.assertEqual(entry['srcaddr'], '0.0.0.0')
        self.assertEqual(entry['srclen'], '32')
        self.assertTrue(entry['log'])
        entry = result['entries']['20']
        self.assertEqual(entry['action'], 'deny')
        self.assertEqual(entry['srcaddr'], '1.1.1.1')
        self.assertEqual(entry['srclen'], '24')
        self.assertFalse(entry['log'])


class TestApiExtendedAclsAsync(AsyncEapiConfigUnitTest):

    def setUp(self):
        super().setUp()
        self.instance = pyeapi.api.aclasync.ExtendedAclsAsync(None)
        self.config = open(get_fixture('running_config.text')).read()
        # Mock the get_block method to return the appropriate config section
        self.instance.get_block = unittest.mock.AsyncMock()
        self.instance.get_block.return_value = (
            'ip access-list exttest\n'
            '50 permit ip any 1.1.1.2\n'
            '70 permit tcp 8.8.8.0/24 neq irc 3.3.3.3 lt ipp '
            'urg ttl eq 24 fragments tracked log\n'
        )
        self.instance.configure = unittest.mock.AsyncMock(return_value=True)

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
        self.instance.get_block.assert_called_with('ip access-list exttest')

    async def test_get_not_configured(self):
        self.instance.get_block.return_value = ''
        self.assertIsNone(await self.instance.get('unconfigured'))
        self.instance.get_block.assert_called_with('ip access-list unconfigured')

    async def test_acl_functions_create(self):
        await self.instance.create('exttest')
        self.instance.configure.assert_called_with('ip access-list exttest')

    async def test_acl_functions_delete(self):
        await self.instance.delete('exttest')
        self.instance.configure.assert_called_with('no ip access-list exttest')

    async def test_acl_functions_default(self):
        await self.instance.default('exttest')
        self.instance.configure.assert_called_with('default ip access-list exttest')

    async def test_update_entry(self):
        cmds = ['ip access-list exttest', 'no 10',
                '10 permit ip 0.0.0.0/32 1.1.1.1/32 log', 'exit']
        await self.instance.update_entry('exttest', '10', 'permit', 'ip',
                                       '0.0.0.0', '32', '1.1.1.1', '32', True)
        self.instance.configure.assert_called_with(cmds)

    async def test_update_entry_no_log(self):
        cmds = ['ip access-list exttest', 'no 10',
                '10 permit ip 0.0.0.0/32 1.1.1.1/32', 'exit']
        await self.instance.update_entry('exttest', '10', 'permit', 'ip',
                                       '0.0.0.0', '32', '1.1.1.1', '32')
        self.instance.configure.assert_called_with(cmds)

    async def test_remove_entry(self):
        cmds = ['ip access-list exttest', 'no 10', 'exit']
        await self.instance.remove_entry('exttest', '10')
        self.instance.configure.assert_called_with(cmds)

    async def test_add_entry(self):
        cmds = ['ip access-list exttest',
                'permit ip 0.0.0.0/32 1.1.1.1/32 log', 'exit']
        await self.instance.add_entry('exttest', 'permit', 'ip', '0.0.0.0',
                                    '32', '1.1.1.1', '32', True)
        self.instance.configure.assert_called_with(cmds)

    async def test_add_entry_no_log(self):
        cmds = ['ip access-list exttest', 'permit ip 0.0.0.0/32 1.1.1.1/32',
                'exit']
        await self.instance.add_entry('exttest', 'permit', 'ip', '0.0.0.0',
                                    '32', '1.1.1.1', '32')
        self.instance.configure.assert_called_with(cmds)

    async def test_add_entry_with_seqno(self):
        cmds = ['ip access-list exttest',
                '30 permit ip 0.0.0.0/32 1.1.1.1/32 log', 'exit']
        await self.instance.add_entry('exttest', 'permit', 'ip', '0.0.0.0',
                                    '32', '1.1.1.1', '32', True, 30)
        self.instance.configure.assert_called_with(cmds)

    def test_parse_entries(self):
        config = ('ip access-list exttest\n'
                  '50 permit ip any 1.1.1.2\n'
                  '70 permit tcp 8.8.8.0/24 neq irc 3.3.3.3 lt ipp '
                  'urg ttl eq 24 fragments tracked log\n')
        result = self.instance._parse_entries(config)
        self.assertIn('entries', result)
        self.assertIn('50', result['entries'])
        self.assertIn('70', result['entries'])
        entry = result['entries']['50']
        self.assertEqual(entry['action'], 'permit')
        self.assertEqual(entry['protocol'], 'ip')
        self.assertEqual(entry['srcaddr'], 'any')
        self.assertEqual(entry['dstaddr'], '1.1.1.2')
        entry = result['entries']['70']
        self.assertEqual(entry['action'], 'permit')
        self.assertEqual(entry['protocol'], 'tcp')
        self.assertEqual(entry['srcaddr'], '8.8.8.0')
        self.assertEqual(entry['srclen'], '24')
        self.assertEqual(entry['srcport'], 'neq irc')
        self.assertEqual(entry['dstaddr'], '3.3.3.3')
        self.assertEqual(entry['dstport'], 'lt ipp')
        self.assertEqual(entry['other'], 'urg ttl eq 24 fragments tracked log')


if __name__ == '__main__':
    unittest.main()