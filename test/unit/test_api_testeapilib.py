import unittest
import json

from unittest.mock import Mock, patch

import pyeapiasync.eapilibasync


class TestEapiAsyncConnection(unittest.IsolatedAsyncioTestCase):

    async def test_execute_valid_response(self):
        response_dict = dict(jsonrpc='2.0', result=[], id=id(self))
        mock_send = Mock(name='send')
        mock_send.return_value = json.dumps(response_dict)

        instance = pyeapiasync.eapilibasync.EapiAsyncConnection()
        instance.send = mock_send

        result = await instance.execute(['command'])
        self.assertEqual(json.loads(result), response_dict)

    async def test_execute_raises_type_error(self):
        instance = pyeapiasync.eapilibasync.EapiAsyncConnection()
        with self.assertRaises(TypeError):
            await instance.execute(None, encoding='invalid')

    async def test_execute_raises_connection_error(self):
        mock_send = Mock(name='send')
        mock_send.side_effect = pyeapiasync.eapilibasync.ConnectionError('test', 'test')

        instance = pyeapiasync.eapilibasync.EapiAsyncConnection()
        instance.send = mock_send

        with self.assertRaises(pyeapiasync.eapilibasync.ConnectionError):
            await instance.execute('test')

    async def test_execute_raises_command_error(self):
        mock_send = Mock(name='send')
        mock_send.side_effect = pyeapiasync.eapilibasync.CommandError('1000', 'test')

        instance = pyeapiasync.eapilibasync.EapiAsyncConnection()
        instance.send = mock_send

        with self.assertRaises(pyeapiasync.eapilibasync.CommandError):
            await instance.execute('test')

    async def test_create_socket_connection(self):
        instance = pyeapiasync.eapilibasync.SocketEapiAsyncConnection()
        self.assertIsInstance(instance, pyeapiasync.eapilibasync.EapiAsyncConnection)
        self.assertIsNotNone(str(instance.transport))

    @patch('pyeapiasync.eapilibasync.socket')
    async def test_socket_connection_create(self, mock_socket):
        instance = pyeapiasync.eapilibasync.SocketConnection('/path/to/sock')
        await instance.connect()
        mock_socket.socket.return_value.connect.assert_called_with('/path/to/sock')

    async def test_create_http_local_connection(self):
        instance = pyeapiasync.eapilibasync.HttpLocalEapiAsyncConnection()
        self.assertIsInstance(instance, pyeapiasync.eapilibasync.EapiAsyncConnection)
        self.assertIsNotNone(str(instance.transport))

    async def test_create_http_connection(self):
        instance = pyeapiasync.eapilibasync.HttpEapiAsyncConnection('localhost')
        self.assertIsInstance(instance, pyeapiasync.eapilibasync.EapiAsyncConnection)
        self.assertIsNotNone(str(instance.transport))

    async def test_create_https_connection(self):
        instance = pyeapiasync.eapilibasync.HttpsEapiAsyncConnection('localhost')
        self.assertIsInstance(instance, pyeapiasync.eapilibasync.EapiAsyncConnection)
        self.assertIsNotNone(str(instance.transport))

    async def test_send(self):
        response_dict = dict(jsonrpc='2.0', result=[{}], id=id(self))
        response_json = json.dumps(response_dict)

        mock_transport = Mock(name='transport')
        mockcfg = {'getresponse.return_value.read.return_value': response_json}
        mock_transport.configure_mock(**mockcfg)

        instance = pyeapiasync.eapilibasync.EapiAsyncConnection()
        instance.transport = mock_transport
        await instance.send('test')
        # HTTP requests to be processed by EAPI should always go to
        # the /command-api endpoint regardless of using TCP/IP or unix-socket
        # for the transport. Unix-socket implementation maps localhost to the
        # unix-socket - /var/run/command-api.sock
        mock_transport.putrequest.assert_called_once_with('POST',
                                                          '/command-api')
        self.assertTrue(mock_transport.close.called)

    async def test_send_with_authentication(self):
        response_dict = dict(jsonrpc='2.0', result=[{}], id=id(self))
        response_json = json.dumps(response_dict)

        mock_transport = Mock(name='transport')
        mockcfg = {'getresponse.return_value.read.return_value': response_json}
        mock_transport.configure_mock(**mockcfg)

        instance = pyeapiasync.eapilibasync.EapiAsyncConnection()
        instance.authentication('username', 'password')
        instance.transport = mock_transport
        await instance.send('test')

        self.assertTrue(mock_transport.close.called)

    async def test_send_unauthorized_user(self):
        error_string = ('Unauthorized. Unable to authenticate user: Bad'
                        ' username/password combination')
        response_str = ('Unable to authenticate user: Bad username/password'
                        ' combination')
        mock_transport = Mock(name='transport')
        mockcfg = {'getresponse.return_value.read.return_value': response_str,
                   'getresponse.return_value.status': 401,
                   'getresponse.return_value.reason': 'Unauthorized'}
        mock_transport.configure_mock(**mockcfg)

        instance = pyeapiasync.eapilibasync.EapiAsyncConnection()
        instance.authentication('username', 'password')
        instance.transport = mock_transport
        try:
            await instance.send('test')
        except pyeapiasync.eapilibasync.ConnectionError as err:
            self.assertEqual(err.message, error_string)

    async def test_send_raises_connection_error(self):
        mock_transport = Mock(name='transport')
        mockcfg = {'getresponse.return_value.read.side_effect': ValueError}
        mock_transport.configure_mock(**mockcfg)

        instance = pyeapiasync.eapilibasync.EapiAsyncConnection()
        instance.transport = mock_transport
        try:
            await instance.send('test')
        except pyeapiasync.eapilibasync.ConnectionError as err:
            self.assertEqual(err.message, 'unable to connect to eAPI')

    async def test_send_raises_connection_socket_error(self):
        mock_transport = Mock(name='transport')
        mockcfg = {'getresponse.return_value.read.side_effect':
                   OSError('timeout')}
        mock_transport.configure_mock(**mockcfg)

        instance = pyeapiasync.eapilibasync.EapiAsyncConnection()
        instance.transport = mock_transport
        try:
            await instance.send('test')
        except pyeapiasync.eapilibasync.ConnectionError as err:
            error_msg = 'Socket error during eAPI connection: timeout'
            self.assertEqual(err.message, error_msg)

    async def test_send_raises_command_error(self):
        error = dict(code=9999, message='test', data=[{'errors': ['test']}])
        response_dict = dict(jsonrpc='2.0', error=error, id=id(self))
        response_json = json.dumps(response_dict)

        mock_transport = Mock(name='transport')
        mockcfg = {'getresponse.return_value.read.return_value': response_json}
        mock_transport.configure_mock(**mockcfg)

        instance = pyeapiasync.eapilibasync.EapiAsyncConnection()
        instance.transport = mock_transport

        with self.assertRaises(pyeapiasync.eapilibasync.CommandError):
            await instance.send('test')

    async def test_send_raises_autocomplete_command_error(self):
        message = "runCmds() got an unexpected keyword argument 'autoComplete'"
        error = dict(code=9999, message=message, data=[{'errors': ['test']}])
        response_dict = dict(jsonrpc='2.0', error=error, id=id(self))
        response_json = json.dumps(response_dict)

        mock_transport = Mock(name='transport')
        mockcfg = {'getresponse.return_value.read.return_value': response_json}
        mock_transport.configure_mock(**mockcfg)

        instance = pyeapiasync.eapilibasync.EapiAsyncConnection()
        instance.transport = mock_transport

        try:
            await instance.send('test')
        except pyeapiasync.eapilibasync.CommandError as error:
            match = ("autoComplete parameter is not supported in this version"
                     " of EOS.")
            self.assertIn(match, error.message)

    async def test_send_raises_expandaliases_command_error(self):
        message = "runCmds() got an unexpected keyword argument" \
                  " 'expandAliases'"
        error = dict(code=9999, message=message, data=[{'errors': ['test']}])
        response_dict = dict(jsonrpc='2.0', error=error, id=id(self))
        response_json = json.dumps(response_dict)

        mock_transport = Mock(name='transport')
        mockcfg = {'getresponse.return_value.read.return_value': response_json}
        mock_transport.configure_mock(**mockcfg)

        instance = pyeapiasync.eapilibasync.EapiAsyncConnection()
        instance.transport = mock_transport

        try:
            await instance.send('test')
        except pyeapiasync.eapilibasync.CommandError as error:
            match = ("expandAliases parameter is not supported in this version"
                     " of EOS.")
            self.assertIn(match, error.message)

    async def test_request_adds_autocomplete(self):
        instance = pyeapiasync.eapilibasync.EapiAsyncConnection()
        request = instance.request(['sh ver'], encoding='json',
                                  autoComplete=True)
        data = json.loads(request)
        self.assertIn('autoComplete', data['params'])

    async def test_request_adds_expandaliases(self):
        instance = pyeapiasync.eapilibasync.EapiAsyncConnection()
        request = instance.request(['test'], encoding='json',
                                  expandAliases=True)
        data = json.loads(request)
        self.assertIn('expandAliases', data['params'])

    async def test_request_ignores_unknown_param(self):
        instance = pyeapiasync.eapilibasync.EapiAsyncConnection()
        request = instance.request(['sh ver'], encoding='json',
                                  unknown=True)
        data = json.loads(request)
        self.assertNotIn('unknown', data['params'])


class TestCommandError(unittest.TestCase):

    def test_create_command_error(self):
        result = pyeapiasync.eapilibasync.CommandError(9999, 'test')
        self.assertIsInstance(result, pyeapiasync.eapilibasync.EapiError)

    def test_command_error_trace(self):
        commands = ['test command', 'test command', 'test command']
        output = [{}, 'test output']
        result = pyeapiasync.eapilibasync.CommandError(9999, 'test', commands=commands,
                                             output=output)
        self.assertIsNotNone(result.trace)