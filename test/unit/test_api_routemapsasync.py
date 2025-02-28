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

from testlib import get_fixture, async_function, random_string
from testlib import AsyncEapiConfigUnitTest

import pyeapiasync.api.routemapsasync


class TestApiRoutemapsAsync(AsyncEapiConfigUnitTest):

    def __init__(self, *args, **kwargs):
        super(TestApiRoutemapsAsync, self).__init__(*args, **kwargs)
        self.instance = pyeapiasync.api.routemapsasync.RoutemapsAsync(None)
        self.config = open(get_fixture('running_config.routemaps')).read()
        # Mock the config property to return the test config
        self.instance.get_block = unittest.mock.AsyncMock()
        self.instance.get_block.return_value = self.config
        self.instance.configure = unittest.mock.AsyncMock(return_value=True)

    def test_instance(self):
        result = pyeapiasync.api.routemapsasync.instance(None)
        self.assertIsInstance(result, pyeapiasync.api.routemapsasync.RoutemapsAsync)

    async def test_get(self):
        # Mock _parse_entries to return a fixed structure
        self.instance._parse_entries = unittest.mock.AsyncMock(
            return_value={'deny': {30: {'continue': 200, 'description': None, 
                                       'match': ['as 2000', 'source-protocol ospf', 'interface Ethernet2'],
                                       'set': []}},
                          'permit': {10: {'continue': 100, 'description': None,
                                         'match': ['interface Ethernet1'],
                                         'set': ['tag 50']}}})
                                         
        result = await self.instance.get('TEST')
        keys = ['deny', 'permit']
        self.assertEqual(sorted(keys), sorted(result.keys()))

    async def test_get_not_configured(self):
        # Mock _parse_entries to return empty dict
        self.instance._parse_entries = unittest.mock.AsyncMock(return_value={})
        
        result = await self.instance.get('blah')
        self.assertIsNone(result)

    async def test_getall(self):
        # Mock the config property and findall to return list of routemaps
        self.instance.config = self.config
        
        # Mock the get method to return a fixed structure for each routemap
        self.instance.get = unittest.mock.AsyncMock()
        self.instance.get.return_value = {'permit': {10: {'continue': None, 'description': None,
                                                        'match': [], 'set': []}}}
                                                        
        result = await self.instance.getall()
        self.assertIsInstance(result, dict)
        self.instance.get.assert_called()

    async def test_routemaps_functions(self):
        for name in ['create', 'delete', 'default']:
            if name == 'create':
                cmds = 'route-map new permit 100'
                func = async_function(self.instance.create, 'new', 'permit', 100)
            elif name == 'delete':
                cmds = 'no route-map new permit 100'
                func = async_function(self.instance.delete, 'new', 'permit', 100)
            elif name == 'default':
                cmds = 'default route-map new permit 100'
                func = async_function(self.instance.default, 'new', 'permit', 100)
                
            await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_set_statement_clean(self):
        cmds = ['route-map new permit 100', 'set weight 100']
        func = async_function(self.instance.set_set_statements, 'new', 'permit', 100,
                           ['weight 100'])
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_set_statement_remove_extraneous(self):
        # Review fixtures/running_config.routemaps to see the default
        # running-config that is the basis for this test
        cmds = ['route-map TEST permit 10', 'no set tag 50',
                'route-map TEST permit 10', 'set weight 100']
        func = async_function(self.instance.set_set_statements, 'TEST', 'permit', 10,
                           ['weight 100'])
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_match_statement_clean(self):
        cmds = ['route-map new permit 200', 'match as 100']
        func = async_function(self.instance.set_match_statements, 'new', 'permit', 200,
                           ['as 100'])
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_match_statement_remove_extraneous(self):
        # Review fixtures/running_config.routemaps to see the default
        # running-config that is the basis for this test
        cmds = ['route-map TEST permit 10', 'no match interface Ethernet1',
                'route-map TEST permit 10', 'match as 1000']
        func = async_function(self.instance.set_match_statements, 'TEST', 'permit', 10,
                           ['as 1000'])
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_continue(self):
        cmds = ['route-map TEST permit 10', 'continue 100']
        func = async_function(self.instance.set_continue, 'TEST', 'permit', 10, 100)
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_continue_with_invalid_integer(self):
        with self.assertRaises(ValueError):
            await self.instance.set_continue('TEST', 'permit', 10, -1)

    async def test_set_continue_with_invalid_string(self):
        with self.assertRaises(ValueError):
            await self.instance.set_continue('TEST', 'permit', 10, 'abc')

    async def test_set_continue_to_default(self):
        cmds = ['route-map TEST permit 10', 'default continue']
        func = async_function(self.instance.set_continue, 'TEST', 'permit', 10, 
                           default=True)
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_negate_continue(self):
        cmds = ['route-map TEST permit 10', 'no continue']
        func = async_function(self.instance.set_continue, 'TEST', 'permit', 10, 
                           disable=True)
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_description_with_value(self):
        value = random_string()
        cmds = ['route-map TEST permit 10', 'description %s' % value]
        func = async_function(self.instance.set_description, 'TEST', 'permit', 10, 
                           value)
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_negate_description(self):
        cmds = ['route-map TEST permit 10', 'no description']
        func = async_function(self.instance.set_description, 'TEST', 'permit', 10, 
                           disable=True)
        await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_description_with_default(self):
        cmds = ['route-map TEST permit 10', 'default description']
        func = async_function(self.instance.set_description, 'TEST', 'permit', 10, 
                           default=True)
        await self.async_eapi_positive_config_test(func, cmds)


if __name__ == '__main__':
    unittest.main()