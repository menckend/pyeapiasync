import unittest
import json
import aiohttp

from unittest.mock import Mock, patch, AsyncMock

import pyeapiasync.eapilibasync as eapilib


class TestEapiAsyncConnection(unittest.IsolatedAsyncioTestCase):

    async def test_execute_valid_response(self):
        response_dict = dict(jsonrpc='2.0', result=[], id=id(self))
        mock_send = AsyncMock(name='send')
        mock_send.return_value = response_dict

        instance = eapilib.EapiAsyncConnection()
        instance.send = mock_send

        result = await instance.execute(['command'])
        self.assertEqual(result, response_dict)

    async def test_execute_raises_type_error(self):
        instance = eapilib.EapiAsyncConnection()
        with self.assertRaises(TypeError):
            await instance.execute(None, encoding='invalid')

    async def test_execute_raises_connection_error(self):
        mock_send = Mock(name='send')
        mock_send.side_effect = eapilib.ConnectionError('test', 'test')

        instance = eapilib.EapiAsyncConnection()
        instance.send = mock_send

        with self.assertRaises(eapilib.ConnectionError):
            await instance.execute('test')

    async def test_execute_raises_command_error(self):
        mock_send = Mock(name='send')
        mock_send.side_effect = eapilib.CommandError('1000', 'test')

        instance = eapilib.EapiAsyncConnection()
        instance.send = mock_send

        with self.assertRaises(eapilib.CommandError):
            await instance.execute('test')

    async def test_create_socket_connection(self):
        instance = eapilib.SocketEapiAsyncConnection()
        self.assertIsInstance(instance, eapilib.EapiAsyncConnection)
        self.assertIsNotNone(str(instance.transport))

    @patch('pyeapiasync.eapilibasync.asyncio.open_unix_connection')
    async def test_socket_connection_create(self, mock_open_unix):
        # Create mock reader and writer
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        
        # Mock the connection
        mock_open_unix.return_value = (mock_reader, mock_writer)
        
        # Create instance and test connection
        instance = eapilib.SocketEapiAsyncConnection('/path/to/sock')
        await instance._connect()
        
        # Verify connection was attempted with correct path
        mock_open_unix.assert_called_once_with(path='/path/to/sock')
        
        # Verify connection state
        self.assertTrue(instance._connected)
        self.assertEqual(instance.reader, mock_reader)
        self.assertEqual(instance.writer, mock_writer)

    async def test_create_http_local_connection(self):
        instance = eapilib.HttpLocalEapiAsyncConnection()
        self.assertIsInstance(instance, eapilib.EapiAsyncConnection)
        self.assertIsNotNone(str(instance.transport))

    async def test_create_http_connection(self):
        instance = eapilib.HttpEapiAsyncConnection('localhost')
        self.assertIsInstance(instance, eapilib.EapiAsyncConnection)
        self.assertIsNotNone(str(instance.transport))

    async def test_create_https_connection(self):
        instance = eapilib.HttpsEapiAsyncConnection('localhost')
        self.assertIsInstance(instance, eapilib.EapiAsyncConnection)
        self.assertIsNotNone(str(instance.transport))

    async def test_send(self):
        response_dict = dict(jsonrpc='2.0', result=[{}], id=id(self))
        response_json = json.dumps(response_dict)

        mock_session = Mock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text.return_value = response_json
        mock_session.post.return_value = AsyncMock(__aenter__=AsyncMock(return_value=mock_response))

        instance = eapilib.EapiAsyncConnection()
        instance.url = "http://localhost/command-api"
        instance._session = mock_session
        instance.ssl_context = None
        
        result = await instance.send('test')
        self.assertEqual(result, response_dict)

    async def test_send_with_authentication(self):
        response_dict = dict(jsonrpc='2.0', result=[{}], id=id(self))
        response_json = json.dumps(response_dict)

        mock_session = Mock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text.return_value = response_json
        mock_session.post.return_value = AsyncMock(__aenter__=AsyncMock(return_value=mock_response))

        instance = eapilib.EapiAsyncConnection()
        instance.url = "http://localhost/command-api"
        instance._session = mock_session
        instance.ssl_context = None
        instance.authentication('username', 'password')
        
        result = await instance.send('test')
        self.assertEqual(result, response_dict)

    async def test_send_unauthorized_user(self):
        response_str = 'Unable to authenticate user: Bad username/password combination'
        error_string = f'Unauthorized. {response_str}'

        mock_session = Mock()
        mock_response = AsyncMock()
        mock_response.status = 401
        mock_response.reason = 'Unauthorized'
        mock_response.text.return_value = response_str
        mock_session.post.return_value = AsyncMock(__aenter__=AsyncMock(return_value=mock_response))

        instance = eapilib.EapiAsyncConnection()
        instance.url = "http://localhost/command-api"
        instance._session = mock_session
        instance.ssl_context = None
        instance.authentication('username', 'password')
        
        with self.assertRaises(eapilib.ConnectionError) as cm:
            await instance.send('test')
        self.assertEqual(cm.exception.message, error_string)

    async def test_send_raises_connection_error(self):
        mock_session = Mock()
        mock_session.post.side_effect = aiohttp.ClientError()

        instance = eapilib.EapiAsyncConnection()
        instance.url = "http://localhost/command-api"
        instance._session = mock_session
        instance.ssl_context = None

        with self.assertRaises(eapilib.ConnectionError) as cm:
            await instance.send('test')
        self.assertEqual(cm.exception.message, 'unable to connect to eAPI')

    async def test_send_raises_connection_socket_error(self):
        mock_session = Mock()
        mock_session.post.side_effect = OSError('timeout')

        instance = eapilib.EapiAsyncConnection()
        instance.url = "http://localhost/command-api"
        instance._session = mock_session
        instance.ssl_context = None

        with self.assertRaises(eapilib.ConnectionError) as cm:
            await instance.send('test')
        error_msg = 'Socket error during eAPI connection: timeout'
        self.assertEqual(cm.exception.message, error_msg)

    async def test_send_raises_command_error(self):
        error = dict(code=9999, message='test', data=[{'errors': ['test']}])
        response_dict = dict(jsonrpc='2.0', error=error, id=id(self))
        response_json = json.dumps(response_dict)

        mock_session = Mock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text.return_value = response_json
        mock_session.post.return_value = AsyncMock(__aenter__=AsyncMock(return_value=mock_response))

        instance = eapilib.EapiAsyncConnection()
        instance.url = "http://localhost/command-api"
        instance._session = mock_session
        instance.ssl_context = None

        with self.assertRaises(eapilib.CommandError) as cm:
            await instance.send('test')
        self.assertEqual(cm.exception.error_code, 9999)

    async def test_send_raises_autocomplete_command_error(self):
        message = "runCmds() got an unexpected keyword argument 'autoComplete'"
        error = dict(code=9999, message=message, data=[{'errors': ['test']}])
        response_dict = dict(jsonrpc='2.0', error=error, id=id(self))
        response_json = json.dumps(response_dict)

        mock_session = Mock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text.return_value = response_json
        mock_session.post.return_value = AsyncMock(__aenter__=AsyncMock(return_value=mock_response))

        instance = eapilib.EapiAsyncConnection()
        instance.url = "http://localhost/command-api"
        instance._session = mock_session
        instance.ssl_context = None

        with self.assertRaises(eapilib.CommandError) as cm:
            await instance.send('test')
        self.assertIn('autoComplete parameter is not supported', cm.exception.message)

    async def test_send_raises_expandaliases_command_error(self):
        message = "runCmds() got an unexpected keyword argument 'expandAliases'"
        error = dict(code=9999, message=message, data=[{'errors': ['test']}])
        response_dict = dict(jsonrpc='2.0', error=error, id=id(self))
        response_json = json.dumps(response_dict)

        mock_session = Mock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text.return_value = response_json
        mock_session.post.return_value = AsyncMock(__aenter__=AsyncMock(return_value=mock_response))

        instance = eapilib.EapiAsyncConnection()
        instance.url = "http://localhost/command-api"
        instance._session = mock_session
        instance.ssl_context = None

        with self.assertRaises(eapilib.CommandError) as cm:
            await instance.send('test')
        self.assertIn('expandAliases parameter is not supported', cm.exception.message)

    async def test_request_adds_autocomplete(self):
        instance = eapilib.EapiAsyncConnection()
        request = instance.request(['sh ver'], encoding='json',
                                   autoComplete=True)
        data = json.loads(request)
        self.assertIn('autoComplete', data['params'])

    async def test_request_adds_expandaliases(self):
        instance = eapilib.EapiAsyncConnection()
        request = instance.request(['test'], encoding='json',
                                   expandAliases=True)
        data = json.loads(request)
        self.assertIn('expandAliases', data['params'])

    async def test_request_ignores_unknown_param(self):
        instance = eapilib.EapiAsyncConnection()
        request = instance.request(['sh ver'], encoding='json',
                                   unknown=True)
        data = json.loads(request)
        self.assertNotIn('unknown', data['params'])


class TestCommandError(unittest.TestCase):

    def test_create_command_error(self):
        result = eapilib.CommandError(9999, 'test')
        self.assertIsInstance(result, eapilib.EapiError)

    def test_command_error_trace(self):
        commands = ['test command', 'test command', 'test command']
        output = [{}, 'test output']
        result = eapilib.CommandError(9999, 'test', commands=commands,
                                             output=output)
        self.assertIsNotNone(result.trace)
