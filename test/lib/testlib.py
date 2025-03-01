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

from unittest.mock import AsyncMock
from pyeapiasync.utils import CliVariants
from pyeapiasync.clientasync import Node
from collections import namedtuple

Function = namedtuple('Function', 'name args kwargs')

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

def function(name, *args, **kwargs):
    return Function(name, args, kwargs)


class EapiAsyncConfigUnitTest(unittest.IsolatedAsyncioTestCase):
    def __init__(self, *args, **kwargs):
        self.instance = None
        self.config = None
        super().__init__(*args, **kwargs)

    async def asyncSetUp(self):
        self.node = Node(None)
        self.node._version_number = '4.17.1.1'
        self.node._running_config = self.config

        self.mock_config = AsyncMock(name='node.config_async')
        self.node.config_async = self.mock_config

        self.mock_enable = AsyncMock(name='node.enable_async')
        self.node.enable_async = self.mock_enable

        self.assertIsNotNone(self.instance)
        self.instance.node = self.node

    async def eapi_config_test(self, func, cmds=None, *args, **kwargs):
        func, fargs, fkwargs = func
        func = getattr(self.instance, func)

        if cmds is not None:
            lcmds = len([cmds]) if isinstance(cmds, str) else len(cmds)
            self.mock_config.return_value = [{} for i in range(0, lcmds)]

        result = await func(*fargs, **fkwargs)

        if cmds is not None:
            # if config was called with CliVariants, then create all possible
            # cli combinations with CliVariants and see if cmds is one of them
            called_args = list(self.mock_config.call_args)[0][0]
            variants = [x for x in called_args if isinstance(x, CliVariants)]
            if not variants:
                self.mock_config.assert_called_with(cmds)
                return result
            # process all variants
            cli_variants = CliVariants.expand( called_args )
            self.assertIn( cmds, cli_variants )
        else:
            self.assertEqual(self.mock_config.call_count, 0)

        return result

    async def eapi_positive_config_test(self, func, cmds=None, *args, **kwargs):
        result = await self.eapi_config_test(func, cmds, *args, **kwargs)
        self.assertTrue(result)

    async def eapi_negative_config_test(self, func, cmds=None, *args, **kwargs):
        result = await self.eapi_config_test(func, cmds, *args, **kwargs)
        self.assertFalse(result)

    async def eapi_exception_config_test(self, func, exc, *args, **kwargs):
        with self.assertRaises(exc):
            await self.eapi_config_test(func, *args, **kwargs)

    async def eapi_positive_config_with_input_test(self, func, cmds=None,
                                             *args, **kwargs):
        result = await self.eapi_config_test(func, cmds, *args, **kwargs)
        self.assertTrue(result)
