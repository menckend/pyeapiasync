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
import importlib

sys.path.append(os.path.join(os.path.dirname(__file__), '../lib'))

from unittest.mock import Mock, patch, call, AsyncMock
from testlib import get_fixture, random_string, random_int

import pyeapiasync.clientasync as client

DEFAULT_CONFIG = {'connection:localhost': dict(transport='socket')}


class TestNode(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.connection = AsyncMock()
        self.node = client.AsyncNode(self.connection)

    async def test_get_version_properties_match_version_number_no_match_model(self):
        self.node.enable = AsyncMock()
        version = '4.17.1.1F-3512479.41711F (engineering build)'
        self.node.enable.return_value = [{'result': {'version': version,
                                                     'modelName': 'vEOS'}}]
        await self.node._get_version_properties()
        self.assertEqual(self.node._version_number, '4.17.1.1')
        self.assertEqual(self.node._model, 'vEOS')

    async def test_get_version_properties_no_match_version_number_match_model(self):
        self.node.enable = AsyncMock()
        version = 'special-4.17.1.1F-3512479.41711F (engineering build)'
        model = 'DCS-7260QX-64-F'
        self.node.enable.return_value = [{'result': {'version': version,
                                                     'modelName': model}}]
        await self.node._get_version_properties()
        self.assertEqual(self.node._version_number, version)
        self.assertEqual(self.node._model, '7260')

    async def test_version_properties_populate(self):
        self.node.enable = AsyncMock()
        version = '4.17.1.1F-3512479.41711F (engineering build)'
        self.node.enable.return_value = [{'result': {'version': version,
                                                     'modelName': 'vEOS'}}]
        version_number = await self.node.version_number
        self.assertEqual(version_number, '4.17.1.1')
        version_str = await self.node.version
        self.assertEqual(version_str, version)
        model = await self.node.model
        self.assertEqual(model, 'vEOS')

    async def test_enable_with_single_command(self):
        command = random_string()
        response = ['enable', command]

        self.connection.execute.return_value = {'result': list(response)}
        result = await self.node.enable(command)

        expected_commands = ['enable', command]
        self.connection.execute.assert_called_once_with(expected_commands, 'json')
        self.assertEqual(command, result[0]['result'])

    async def test_enable_with_single_unicode_command(self):
        command = random_string()
        command = u'%s' % command
        response = ['enable', command]

        self.connection.execute.return_value = {'result': list(response)}
        result = await self.node.enable(command)

        expected_commands = ['enable', command]
        self.connection.execute.assert_called_once_with(expected_commands, 'json')
        self.assertEqual(command, result[0]['result'])

    async def test_enable_with_single_extended_command(self):
        command = {'cmd': 'show cvx', 'revision': 2}
        response = ['enable', command]

        self.connection.execute.return_value = {'result': list(response)}
        result = await self.node.enable(command)

        expected_commands = ['enable', command]
        self.connection.execute.assert_called_once_with(expected_commands, 'json')
        self.assertEqual(command, result[0]['result'])

    async def test_no_enable_with_single_command(self):
        command = random_string()
        response = [command]

        self.connection.execute.return_value = {'result': list(response)}
        result = await self.node.enable(command, send_enable=False)

        self.connection.execute.assert_called_once_with([command], 'json')
        self.assertEqual(command, result[0]['result'])

    async def test_enable_with_multiple_commands(self):
        commands = list()
        for i in range(0, random_int(2, 5)):
            commands.append(random_string())

        def execute_response(cmds, *args):
            return {'result': [x for x in cmds]}

        self.connection.execute.side_effect = execute_response

        responses = await self.node.enable(commands)
        expected_calls = [call(['enable', cmd], 'json') for cmd in commands]
        self.assertEqual(self.connection.execute.mock_calls, expected_calls)

        for index, response in enumerate(responses):
            self.assertEqual(commands[index], response['result'])

    async def test_enable_with_multiple_unicode_commands(self):
        commands = list()
        for i in range(0, random_int(2, 5)):
            commands.append(u'%s' % random_string())

        def execute_response(cmds, *args):
            return {'result': [x for x in cmds]}

        self.connection.execute.side_effect = execute_response

        responses = await self.node.enable(commands)

        expected_calls = [call(['enable', cmd], 'json') for cmd in commands]
        self.assertEqual(self.connection.execute.mock_calls, expected_calls)

        for index, response in enumerate(responses):
            self.assertEqual(commands[index], response['result'])

    async def test_config_with_single_command(self):
        command = random_string()
        self.node.run_commands = AsyncMock(return_value=[{}, {}])
        result = await self.node.config(command)
        self.assertEqual(result, [{}])

    async def test_config_with_multiple_commands(self):
        commands = [random_string(), random_string()]
        self.node.run_commands = AsyncMock(return_value=[{}, {}, {}])
        result = await self.node.config(commands)
        self.assertEqual(result, [{}, {}])

    async def test_config_with_single_multiline(self):
        command = ('banner login MULTILINE:This is a new banner\n'
                   'with different lines!!!')

        self.node.run_commands = AsyncMock(return_value=[{}, {}])
        result = await self.node.config(command)
        self.assertEqual(result, [{}])

    async def test_config_with_multiple_multilines(self):
        commands = [random_string(),
                    ('banner login MULTILINE:This is a new banner\n'
                     'with different lines!!!'),
                    random_string()]

        self.node.run_commands = AsyncMock(return_value=[{}, {}, {}, {}])
        result = await self.node.config(commands)
        self.assertEqual(result, [{}, {}, {}])

    async def test_get_config(self):
        config = [dict(output='test\nconfig')]
        self.node.run_commands = AsyncMock(return_value=config)
        result = await self.node.get_config()
        self.assertIsInstance(result, list)

    async def test_get_config_as_string(self):
        config = [dict(output='test\nconfig')]
        self.node.run_commands = AsyncMock(return_value=config)
        result = await self.node.get_config(as_string=True)
        self.assertIsInstance(result, str)

    async def test_get_config_raises_type_error(self):
        with self.assertRaises(TypeError):
            await self.node.get_config('invalid-config')

    async def test_api_autoload(self):
        self.node.api_autoload()
        self.assertIsNotNone(self.node.api)
        self.assertIsInstance(self.node.api, dict)

    async def test_enable_authentication(self):
        self.node.enable_authentication('test')
        self.assertEqual(self.node._enablepwd, 'test')

    async def test_enable_with_config_statement(self):
        cmds = ['show version', 'configure', 'hostname foo']
        with self.assertRaises(TypeError):
            await self.node.enable(cmds)


class TestClient(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        if 'EAPI_CONF' in os.environ:
            del os.environ['EAPI_CONF']
        importlib.reload(client)

    @patch('pyeapiasync.clientasync.make_connection_async')
    async def test_connect_types(self, connection):
        transports = list(client.TRANSPORTS.keys())
        kwargs = dict(host='localhost', username='admin', password='',
                      port=None, key_file=None, cert_file=None,
                      ca_file=None, timeout=60, context=None)

        for transport in transports:
            await client.connect_async(transport)
            connection.assert_called_with(transport, **kwargs)

    async def test_make_connection_raises_typeerror(self):
        with self.assertRaises(TypeError):
            await client.make_connection_async('invalid')

    async def test_node_str_returns(self):
        node = client.AsyncNode(None)
        self.assertIsNotNone(str(node))

    async def test_node_repr_returns(self):
        node = client.AsyncNode(None)
        self.assertIsNotNone(repr(node))

    async def test_node_hasattr_connection(self):
        node = client.AsyncNode(None)
        self.assertTrue(hasattr(node, 'connection'))

    @patch('pyeapiasync.clientasync.AsyncNode.get_config')
    async def test_node_calls_running_config_with_all_by_default(self, get_config_mock):
        node = client.AsyncNode(None)
        get_config_mock.return_value = 'config'
        config = await node.running_config
        get_config_mock.assert_called_once_with(params='all', as_string=True)
        self.assertEqual(config, 'config')

    @patch('pyeapiasync.clientasync.AsyncNode.get_config')
    async def test_node_calls_running_config_without_params_if_config_defaults_false(
            self, get_config_mock):
        node = client.AsyncNode(None, config_defaults=False)
        get_config_mock.return_value = 'config'
        config = await node.running_config
        get_config_mock.assert_called_once_with(params=None, as_string=True)
        self.assertEqual(config, 'config')

    async def test_node_returns_running_config(self):
        node = client.AsyncNode(None)
        get_config_mock = AsyncMock(name='get_config')
        config_file = open(get_fixture('running_config.text'))
        config = config_file.read()
        config_file.close()
        get_config_mock.return_value = config
        node.get_config = get_config_mock
        result = await node.running_config
        self.assertIsInstance(result, str)

    async def test_node_returns_startup_config(self):
        node = client.AsyncNode(None)
        get_config_mock = AsyncMock(name='get_config')
        config_file = open(get_fixture('running_config.text'))
        config = config_file.read()
        config_file.close()
        get_config_mock.return_value = config
        node.get_config = get_config_mock
        result = await node.startup_config
        self.assertIsInstance(result, str)

    async def test_node_returns_cached_startup_config(self):
        node = client.AsyncNode(None)
        config_file = open(get_fixture('running_config.text'))
        config = config_file.read()
        config_file.close()
        node._startup_config = config
        result = await node.startup_config
        self.assertEqual(result, config)

    async def test_node_returns_version(self):
        node = client.AsyncNode(None)
        version = '4.17.1.1F-3512479.41711F (engineering build)'
        node.enable = AsyncMock()
        node.enable.return_value = [{'result': {'version': version,
                                                'modelName': 'vEOS'}}]
        result = await node.version
        self.assertIsInstance(result, str)
        self.assertEqual(result, version)

    async def test_node_returns_cached_version(self):
        node = client.AsyncNode(None)
        node._version = '4.16.7R'
        result = await node.version
        self.assertEqual(result, '4.16.7R')

    async def test_node_returns_version_number(self):
        node = client.AsyncNode(None)
        version = '4.17.1.1F-3512479.41711F (engineering build)'
        node.enable = AsyncMock()
        node.enable.return_value = [{'result': {'version': version,
                                                'modelName': 'vEOS'}}]
        result = await node.version_number
        self.assertIsInstance(result, str)
        self.assertEqual(result, '4.17.1.1')

    async def test_node_returns_cached_version_number(self):
        node = client.AsyncNode(None)
        node._version_number = '4.16.7'
        result = await node.version_number
        self.assertEqual(result, '4.16.7')

    async def test_node_returns_model(self):
        node = client.AsyncNode(None)
        version = '4.17.1.1F-3512479.41711F (engineering build)'
        model = 'DCS-7260QX-64-F'
        node.enable = AsyncMock()
        node.enable.return_value = [{'result': {'version': version,
                                                'modelName': model}}]
        result = await node.model
        self.assertIsInstance(result, str)
        self.assertEqual(result, '7260')

    async def test_node_returns_cached_model(self):
        node = client.AsyncNode(None)
        node._model = '7777'
        result = await node.model
        self.assertEqual(result, '7777')

    async def test_connect_default_type(self):
        transport = AsyncMock()
        transport.return_value = AsyncMock()
        with patch.dict(client.TRANSPORTS, {'https': transport}):
            connection = await client.connect_async()
            kwargs = dict(host='localhost', username='admin', password='',
                          port=None, key_file=None, cert_file=None,
                          ca_file=None, timeout=60, context=None)
            transport.assert_called_once_with(**kwargs)
