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
"""Provides asynchronous wrapper for eAPI calls

This module provides an asynchronous connection to eAPI by wrapping eAPI calls
in an instance of AsyncConnection. The connection module provides an easy
implementation for sending and receiving calls over eAPI using asyncio and
aiohttp.
"""

# import socket
import base64
import logging
import ssl
import re
# import asyncio
import aiohttp

try:
    import ujson as json
except ImportError:
    try:
        import rapidjson as json
    except ImportError:
        import json

from pyeapi.utils import make_iterable
from pyeapi.eapilib import (
    CommandError, ConnectionError, DEFAULT_HTTP_PORT, DEFAULT_HTTPS_PORT,
    DEFAULT_HTTP_LOCAL_PORT, DEFAULT_HTTP_PATH,
    DEFAULT_UNIX_SOCKET  # ,EapiError, DEFAULT_HTTPS_LOCAL_PORT
)

_LOGGER = logging.getLogger(__name__)


class EapiAsyncConnection(object):
    """Creates an asynchronous connection to eAPI for sending and receiving
    eAPI requests

    The EapiAsyncConnection object provides an implementation for sending and
    receiving eAPI requests and responses asynchronously using asyncio and
    aiohttp.
    """

    def __init__(self):
        self.transport = None
        self.error = None
        self.socket_error = None
        self._auth = None
        self._session = None

    def __str__(self):
        return 'EapiAsyncConnection(transport=%s)' % str(self.transport)

    def __repr__(self):
        return 'EapiAsyncConnection(transport=%s)' % repr(self.transport)

    def authentication(self, username, password):
        """Configures the user authentication for eAPI

        This method configures the username and password combination to use
        for authenticating to eAPI.

        Args:
            username (str): The username to use to authenticate the eAPI
                connection with
            password (str): The password in clear text to use to authenticate
                the eAPI connection with
        """
        _auth_text = '{}:{}'.format(username, password)
        _auth_bin = base64.encodebytes(_auth_text.encode())
        _auth = _auth_bin.decode().replace('\n', '')
        self._auth = ("Authorization", "Basic %s" % _auth)

        _LOGGER.debug('Authentication string is: {}:***'.format(username))

    def request(self, commands, encoding=None, reqid=None, **kwargs):
        """Generates an eAPI request object

        This method will take a list of EOS commands and generate a valid
        eAPI request object form them.  The eAPI request object is then
        JSON encoding and returned to the caller.

        eAPI Request Object

        .. code-block:: json

            {
                "jsonrpc": "2.0",
                "method": "runCmds",
                "params": {
                    "version": 1,
                    "cmds": [
                        <commands>
                    ],
                    "format": [json, text],
                }
                "id": <reqid>
            }

        Args:
            commands (list): A list of commands to include in the eAPI
                request object
            encoding (string): The encoding method passed as the `format`
                parameter in the eAPI request
            reqid (string): A custom value to assign to the request ID
                field.  This value is automatically generated if not passed
            **kwargs: Additional keyword arguments for expanded eAPI
                functionality. Only supported eAPI params are used in building
                the request

        Returns:
            A JSON encoding request structure that can be send over eAPI
        """
        commands = make_iterable(commands)
        reqid = id(self) if reqid is None else reqid
        params = {'version': 1, 'cmds': commands, 'format': encoding}
        streaming = False
        if 'apiVersion' in kwargs:
            params['version'] = kwargs['apiVersion']
        if 'autoComplete' in kwargs:
            params['autoComplete'] = kwargs['autoComplete']
        if 'expandAliases' in kwargs:
            params['expandAliases'] = kwargs['expandAliases']
        if 'streaming' in kwargs:
            streaming = kwargs['streaming']
        return json.dumps({'jsonrpc': '2.0', 'method': 'runCmds',
                           'params': params, 'id': str(reqid),
                           'streaming': streaming})

    async def _sanitize_request(self, data):
        """remove user-sensitive input from data response"""
        try:
            data_json = json.loads(data)
            match = self._find_sub_json(
                data_json, {'cmd': 'enable', 'input': ()})
            if match:
                match.entry[match.idx]['input'] = '<removed>'
                return json.dumps(data_json)
        except ValueError:
            pass
        return data

    def _find_sub_json(self, jsn, sbj, instance=0):
        """finds a subset (sbj) in json. `sbj` must be a subset and json must
        not be atomic. Wildcard(s) in `sbj` can be specified with tuple type.
        A json label cannot be wildcarded. A single wildcard represent a single
        json entry. E.g.:

            _find_sub_json( jsn, { 'foo': () } )

        Returned value is a Match class with attributes:
        - entry: an iterable containing a matching `sbj`
        - idx: index or key pointing to the match in the iterable
        If no match found None is returned - that way is possible to get a
        reference to the sought json and modify it, e.g:

            match = _find_sub_json( jsn, { 'foo':(), 'bar': [123, (), ()] } )
            if match:
                match.entry[ match.idx ][ 'foo' ] = 'bar'

        It's also possible to specify an occurrence of the match via `instance`
        parameter - by default a first found match is returned"""
        class Match():
            def __init__(self, entry, idx):
                self.entry = entry
                self.idx = idx

        def is_iterable(val):
            return True if isinstance(val, (list, dict)) else False

        def is_atomic(val):
            return not is_iterable(val)

        def is_match(jsn, sbj):
            if isinstance(sbj, tuple):              # sbj is a wildcard
                return True
            if is_atomic(sbj):
                return False if is_iterable(jsn) else sbj == jsn
            if type(jsn) is not type(sbj) or len(jsn) != len(sbj):
                return False
            for left, right in zip(
                    sorted(jsn.items() if isinstance(jsn, dict)
                           else enumerate(jsn)),
                    sorted(sbj.items() if isinstance(sbj, dict)
                           else enumerate(sbj))):
                if left[0] != right[0]:
                    return False
                if not is_match(left[1], right[1]):
                    return False
            return True

        if is_atomic(jsn):
            return None
        instance = [instance] if isinstance(instance, int) else instance
        for key, val in jsn.items() if isinstance(jsn,
                                                  dict) else enumerate(jsn):
            if is_match(val, sbj):
                if instance[0] > 0:
                    instance[0] -= 1
                else:
                    return Match(jsn, key)
            if is_iterable(val):
                match = self._find_sub_json(val, sbj, instance)
                if match:
                    return match
        return None

    def _parse_error_message(self, message):
        """Parses the eAPI failure response message

        This method accepts an eAPI failure message and parses the necesary
        parts in order to generate a CommandError.

        Args:
            message (str): The error message to parse

        Returns:
            tuple: A tuple that consists of the following:
                * code: The error code specified in the failure message
                * message: The error text specified in the failure message
                * error: The error text from the command that generated the
                    error (the last command that ran)
                * output: A list of all output from all commands
        """
        msg = message['error']['message']
        code = message['error']['code']

        err = None
        out = None

        if 'data' in message['error']:
            err = []
            for dct in message['error']['data']:
                err.extend(
                    ['%s: %s' % (k, repr(v)) for k, v in dct.items()])
            err = ', '.join(err)
            out = message['error']['data']

        return code, msg, err, out

    async def send(self, data):
        """Sends the eAPI request to the destination node asynchronously

        This method is responsible for sending an eAPI request to the
        destination node and returning a response based on the eAPI response
        object.  eAPI responds to request messages with either a success
        message or failure message.

        Args:
            data (string): The data to be included in the body of the eAPI
                request object

        Returns:
            A decoded response.  The response object is deserialized from
                JSON and returned as a standard Python dictionary object

        Raises:
            CommandError if an eAPI failure response object is returned from
                the node.   The CommandError exception includes the error
                code and error message from the eAPI response.
        """
        try:
            sanitized_data = await self._sanitize_request(data)
            _LOGGER.debug('Request content: {}'.format(sanitized_data))

            headers = {'Content-Type': 'application/json-rpc'}
            if self._auth:
                headers[self._auth[0]] = self._auth[1]

            async with self._session.post(
                    self.url,
                    data=data,
                    headers=headers,
                    ssl=self.ssl_context) as response:

                response_content = await response.text()
                _LOGGER.debug('Response: status:{status}'.format(
                    status=response.status))
                _LOGGER.debug('Response content: {}'.format(response_content))

                if response.status == 401:
                    raise ConnectionError(str(self),
                                          f'{response.reason}. ' +
                                          '{response_content}')

                decoded = json.loads(response_content)
                _LOGGER.debug('eapi_response: %s' % decoded)

                if 'error' in decoded:
                    (code, msg, err, out) = self._parse_error_message(decoded)
                    pattern = "unexpected keyword argument '(.*)'"
                    match = re.search(pattern, msg)
                    if match:
                        auto_msg = ('%s parameter is not supported in this'
                                    ' version of EOS.' % match.group(1))
                        _LOGGER.error(auto_msg)
                        msg = msg + '. ' + auto_msg
                    raise CommandError(code, msg, command_error=err,
                                       output=out)

                return decoded

        except aiohttp.ClientError as exc:
            _LOGGER.exception(exc)
            self.socket_error = exc
            self.error = exc
            error_msg = 'Socket error during eAPI connection: %s' % str(exc)
            raise ConnectionError(str(self), error_msg)
        except ValueError as exc:
            _LOGGER.exception(exc)
            self.socket_error = None
            self.error = exc
            raise ConnectionError(str(self), 'unable to connect to eAPI')

    async def execute(self, commands, encoding='json', **kwargs):
        """Executes the list of commands on the destination node asynchronously

        This method takes a list of commands and sends them to the
        destination node, returning the results.  The execute method handles
        putting the destination node in enable mode and will pass the
        enable password, if required.

        Args:
            commands (list): A list of commands to execute on the remote node
            encoding (string): The encoding to send along with the request
                message to the destination node.  Valid values include 'json'
                or 'text'.  This argument will influence the response object
                encoding
            **kwargs: Arbitrary keyword arguments

        Returns:
            A decoded response message as a native Python dictionary object
            that has been deserialized from JSON.

        Raises:
            CommandError:  A CommandError is raised that includes the error
                code, error message along with the list of commands that were
                sent to the node.  The exception instance is also stored in
                the error property and is availble until the next request is
                sent
        """
        if encoding not in ('json', 'text'):
            raise TypeError('encoding must be one of [json, text]')

        try:
            self.error = None
            request = self.request(commands, encoding=encoding, **kwargs)
            response = await self.send(request)
            return response

        except (ConnectionError, CommandError, TypeError) as exc:
            exc.commands = commands
            self.error = exc
            raise


class HttpLocalEapiAsyncConnection(EapiAsyncConnection):
    def __init__(self, port=None, path=None, timeout=60, **kwargs):
        super(HttpLocalEapiAsyncConnection, self).__init__()
        port = port or DEFAULT_HTTP_LOCAL_PORT
        path = path or DEFAULT_HTTP_PATH
        self.url = f"http://localhost:{port}{path}"
        self.ssl_context = None
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=timeout))

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._session.close()


class HttpEapiAsyncConnection(EapiAsyncConnection):
    def __init__(self, host, port=None, path=None, username=None,
                 password=None, timeout=60, **kwargs):
        super(HttpEapiAsyncConnection, self).__init__()
        port = port or DEFAULT_HTTP_PORT
        path = path or DEFAULT_HTTP_PATH
        self.url = f"http://{host}:{port}{path}"
        self.ssl_context = None
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=timeout))
        if username and password:
            self.authentication(username, password)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._session.close()


class HttpsEapiAsyncConnection(EapiAsyncConnection):
    def __init__(self, host, port=None, path=None, username=None,
                 password=None, context=None, timeout=60, **kwargs):
        super(HttpsEapiAsyncConnection, self).__init__()
        port = port or DEFAULT_HTTPS_PORT
        path = path or DEFAULT_HTTP_PATH
        self.url = f"https://{host}:{port}{path}"

        enforce_verification = kwargs.get('enforce_verification')
        # after fix #236 (allowing passing ssl context), this parameter
        # is deprecated - will be release noted and removed in the respective
        # release versions

        if context is None and not enforce_verification:
            self.ssl_context = self.disable_certificate_verification()
        else:
            self.ssl_context = context

        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=timeout))
        if username and password:
            self.authentication(username, password)

    def disable_certificate_verification(self):
        # SSL/TLS certificate verification is enabled by default in latest
        # Python releases and causes self-signed certificates generated
        # on EOS to fail validation (unless explicitly imported).
        # Disable the SSL/TLS certificate verification for now.
        # Use the approach in PEP476 to disable certificate validation.
        # TODO:
        # ************************** WARNING *****************************
        # This behaviour is considered a *security risk*, so use it
        # temporary until a proper fix is implemented.
        if hasattr(ssl, '_create_unverified_context'):
            return ssl._create_unverified_context()
        return None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._session.close()


class HttpsEapiCertAsyncConnection(EapiAsyncConnection):
    def __init__(self, host, port=None, path=None, key_file=None,
                 cert_file=None, ca_file=None, timeout=60, **kwargs):
        if key_file is None or cert_file is None:
            raise ValueError("For https_cert connections both a key_file and "
                             "cert_file are required. A ca_file is also "
                             "recommended")
        super(HttpsEapiCertAsyncConnection, self).__init__()
        port = port or DEFAULT_HTTPS_PORT
        path = path or DEFAULT_HTTP_PATH
        self.url = f"https://{host}:{port}{path}"

        # Create SSL context with client certificates
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.load_cert_chain(cert_file, key_file)
        if ca_file:
            self.ssl_context.load_verify_locations(ca_file)

        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=timeout))

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._session.close()


class SessionApiAsyncConnection(object):
    async def authentication(self, username, password):
        try:
            data = json.dumps({"username": username, "password": password})
            login_url = self.url.replace('/command-api', '/login')

            headers = {'Content-Type': 'application/json'}
            async with self._session.post(
                    login_url,
                    data=data,
                    headers=headers,
                    ssl=self.ssl_context) as resp:

                if resp.status != 200:
                    response_text = await resp.text()
                    raise ConnectionError(str(self),
                                          f'{resp.reason}. {response_text}')

                # Get the session cookie
                cookies = resp.cookies
                cookie_str = '; '.join([f'{name}={value}'
                                        for name, value in cookies.items()])
                self._auth = ("Cookie", cookie_str)

        except aiohttp.ClientError as exc:
            _LOGGER.exception(exc)
            self.socket_error = exc
            self.error = exc
            error_msg = f'Socket error during eAPI authentication: {exc}'
            raise ConnectionError(str(self), error_msg)
        except ValueError as exc:
            _LOGGER.exception(exc)
            self.socket_error = None
            self.error = exc
            raise ConnectionError(str(self), 'unable to connect to eAPI')


class HttpEapiSessionAsyncConnection(SessionApiAsyncConnection,
                                     HttpEapiAsyncConnection):
    pass


class HttpsEapiSessionAsyncConnection(SessionApiAsyncConnection,
                                      HttpsEapiAsyncConnection):
    pass


# Socket connection is more complex to implement with asyncio
# This is a placeholder for future implementation
class SocketEapiAsyncConnection(EapiAsyncConnection):
    def __init__(self, path=None, timeout=60, **kwargs):
        super(SocketEapiAsyncConnection, self).__init__()
        self.path = path or DEFAULT_UNIX_SOCKET
        self.timeout = timeout
        raise NotImplementedError("Async socket connection not yet \
                                  implemented")
