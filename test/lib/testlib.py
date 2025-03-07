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

import os
import random
import string
import unittest
import asyncio
import unittest.async_case
from unittest.mock import AsyncMock
from pyeapiasync.utils import CliVariants
from pyeapiasync.clientasync import AsyncNode
from collections import namedtuple


def get_fixtures_path():
    return os.path.join(os.path.dirname(__file__), '../fixtures')


def get_fixture(filename):
    return os.path.join(get_fixtures_path(), filename)


def random_string(minchar=1, maxchar=50):
    return ''.join(random.choice(string.ascii_uppercase + string.digits)
                   for _ in range(random.randint(minchar, maxchar)))


def random_vlan():
    return random.randint(1, 4094)


def random_int(minvalue, maxvalue):
    return random.randint(minvalue, maxvalue)


Function = namedtuple('Function', 'name args kwargs')


def function(name, *args, **kwargs):
    return Function(name, args, kwargs)


class EapiAsyncConfigUnitTest(unittest.async_case.IsolatedAsyncioTestCase):
    def __init__(self, *args, **kwargs):
        self.instance = None
        self.config = None
        super(EapiAsyncConfigUnitTest, self).__init__(*args, **kwargs)

    async def asyncSetUp(self):
        self.node = AsyncNode(None)
        self.node._version_number = '4.17.1.1'
        self.node._running_config = self.config
        self.mock_config = AsyncMock(name='node.config')
        self.node.config = self.mock_config
        self.mock_enable = AsyncMock(name='node.enable')
        self.node.enable = self.mock_enable
        self.assertIsNotNone(self.instance)
        self.instance.node = self.node
        await asyncio.sleep(0)

#    async def eapi_config_test(self, func, cmds=None):
#        func, fargs, fkwargs = func
#        func = getattr(self.instance, func)

#        await asyncio.sleep(0)
#        if cmds is not None:
#            lcmds = len([cmds]) if isinstance(cmds, str) else len(cmds)
#            self.mock_config.return_value = [{} for i in range(0, lcmds)]

#        result = func(*fargs, **fkwargs)

#        if cmds is not None:
            # if config was called with CliVariants, then create all possible
            # cli combinations with CliVariants and see if cmds is one of them
#            called_args = list(self.node.config.call_args)[0][0]
#            variants = [x for x in called_args if isinstance(x, CliVariants)]
#            if not variants:
#                self.node.config.assert_called_with(cmds)
#                await asyncio.sleep(0)
#                return result
            # process all variants
#            cli_variants = CliVariants.expand(called_args)
#            self.assertIn(cmds, cli_variants)
#        else:
#            self.assertEqual(self.node.config.call_count, 0)
#        await asyncio.sleep(0)
#        return result

    async def eapi_config_test(self, func, cmds=None, *args, **kwargs):
        func, fargs, fkwargs = func
        func = getattr(self.instance, func)

        if cmds is not None:
            lcmds = len([cmds]) if isinstance(cmds, str) else len(cmds)
            self.mock_config.return_value = [{} for i in range(0, lcmds)]

        result = func(*fargs, **fkwargs)

        if cmds is not None:
            # if config was called with CliVariants, then create all possible
            # cli combinations with CliVariants and see if cmds is one of them
            called_args = list( self.node.config.call_args )[ 0 ][ 0 ]
            variants = [ x for x in called_args if isinstance(x, CliVariants) ]
            if not variants:
                self.node.config.assert_called_with(cmds)
                return result
            # process all variants
            cli_variants = CliVariants.expand( called_args )
            self.assertIn( cmds, cli_variants )
        else:
            self.assertEqual(self.node.config.call_count, 0)

        return result








#    async def eapi_positive_config_test(self, func, cmds=None):
#        self.mock_config.return_value = True
#        result = self.eapi_config_test(func, cmds)
#        self.assertTrue(result)
#        eapi_config_test


    async def eapi_positive_config_test(self, func, cmds=None, *args, **kwargs):
        result = self.eapi_config_test(func, cmds, *args, **kwargs)
        self.assertTrue(result)
        await asyncio.sleep(0)  


    def eapi_negative_config_test(self, func, cmds=None):
        self.mock_config.return_value = False
        result = self.eapi_config_test(func, cmds)
        self.assertFalse(result)

    def eapi_exception_config_test(self, func, exc):
        with self.assertRaises(exc):
            self.eapi_config_test(func)

    def eapi_positive_config_with_input_test(self, func, cmds=None):
        self.mock_config.return_value = True
        result = self.eapi_config_test(func, cmds)
        self.assertTrue(result)
