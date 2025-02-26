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

from testlib import get_fixture, async_function, random_int, random_string
from testlib import AsyncEapiConfigUnitTest
from random import choice

import pyeapi.api.staticrouteasync

# Define test data
IP_DESTS = ['1.1.1.0/24', '2.2.2.0/24']
NEXT_HOPS = [('Ethernet1', '1.1.1.1'), ('Ethernet2', '1.1.1.2'),
             ('Null0', None), ('44.44.44.0', None)]
DISTANCES = TAGS = ROUTE_NAMES = [None, True]


class TestApiStaticrouteAsync(AsyncEapiConfigUnitTest):

    def __init__(self, *args, **kwargs):
        super(TestApiStaticrouteAsync, self).__init__(*args, **kwargs)
        self.instance = pyeapi.api.staticrouteasync.StaticRouteAsync(None)
        self.config = open(get_fixture('running_config.text')).read()
        # Mock the get_block method to return test config
        self.instance.config = self.config

    def test_instance(self):
        result = pyeapi.api.staticrouteasync.instance(None)
        self.assertIsInstance(result, pyeapi.api.staticrouteasync.StaticRouteAsync)

    async def test_get(self):
        # Test retrieval of a specific static route entry
        # Assumes running_config.text file contains the following
        # ip route specifications, and that no additional routes
        # are specified.

        # ip route 0.0.0.0/0 192.68.1.254 1 tag 0
        # ip route 1.2.3.0/24 Ethernet1 1.1.1.1 1 tag 1 name test1
        # ip route 1.2.3.0/24 Ethernet1 1.1.1.1 10 tag 1 name test1
        # ip route 1.2.3.0/24 Ethernet1 10.1.1.1 20 tag 1 name test1

        # Get the route(s) for ip_dest 0.0.0.0/24
        ip_dest = '0.0.0.0/0'
        routes = {
            '192.68.1.254': {
                None: {
                    1: {
                        'route_name': None,
                        'tag': 0
                    }
                }
            }
        }

        # Mock the getall method to return a known structure
        self.instance.getall = unittest.mock.AsyncMock(
            return_value={ip_dest: routes})
        
        result = await self.instance.get(ip_dest)
        self.assertEqual(result, routes)

    async def test_getall(self):
        # Test retrieval of all static route entries
        # Assumes running_config.text file contains the following
        # ip route specifications, and that no additional routes
        # are specified.

        # ip route 0.0.0.0/0 192.68.1.254 1 tag 0
        # ip route 1.2.3.0/24 Ethernet1 1.1.1.1 1 tag 1 name test1
        # ip route 1.2.3.0/24 Ethernet1 1.1.1.1 10 tag 1 name test1
        # ip route 1.2.3.0/24 Ethernet1 10.1.1.1 20 tag 1 name test1

        # Mock the get_block method to return config with static routes
        self.instance.get_block = unittest.mock.AsyncMock()
        self.instance.get_block.return_value = """
ip route 0.0.0.0/0 192.68.1.254 1 tag 0
ip route 1.2.3.0/24 Ethernet1 1.1.1.1 1 tag 1 name test1
ip route 1.2.3.0/24 Ethernet1 1.1.1.1 10 tag 1 name test1
ip route 1.2.3.0/24 Ethernet1 10.1.1.1 20 tag 1 name test1
"""

        routes = {
            '0.0.0.0/0': {
                '192.68.1.254': {
                    None: {
                        1: {'route_name': None,
                            'tag': 0}
                    }
                }
            },
            '1.2.3.0/24': {
                'Ethernet1': {
                    '1.1.1.1': {
                        1: {
                            'route_name': 'test1',
                            'tag': 1},
                        10: {
                            'route_name': 'test1',
                            'tag': 1}
                    },
                    '10.1.1.1': {
                        20: {
                            'route_name': 'test1',
                            'tag': 1}
                    }
                }
            }
        }

        self.maxDiff = None
        result = await self.instance.getall()
        self.assertEqual(result, routes)

    async def test_create(self):
        # Test passing in a full set of parameters to 'create'
        # Some parameters may be not set: None
        self.instance.configure = unittest.mock.AsyncMock(return_value=True)
        
        for ip_dest in IP_DESTS:
            # Get the parameters for the call
            (next_hop, next_hop_ip) = choice(NEXT_HOPS)
            distance = choice(DISTANCES)
            if distance:
                distance = random_int(0, 255)
            tag = choice(TAGS)
            if tag:
                tag = random_int(0, 255)
            route_name = choice(ROUTE_NAMES)
            if route_name:
                route_name = random_string(minchar=4, maxchar=10)

            func = async_function(self.instance.create, ip_dest, next_hop,
                                next_hop_ip=next_hop_ip,
                                distance=distance,
                                tag=tag,
                                route_name=route_name)

            # Build the expected string for comparison
            # A value of None will default to an empty string, and
            # add the tag or name keywords where appropriate
            cmd_next_hop_ip = cmd_distance = cmd_tag = cmd_route_name = ''
            if next_hop_ip is not None:
                cmd_next_hop_ip = " %s" % next_hop_ip
            if distance is not None:
                cmd_distance = " %d" % distance
            if tag is not None:
                cmd_tag = " tag %d" % tag
            if route_name is not None:
                cmd_route_name = " name %s" % route_name
            cmds = "ip route %s %s%s%s%s%s" % \
                   (ip_dest, next_hop, cmd_next_hop_ip, cmd_distance,
                    cmd_tag, cmd_route_name)

            await self.async_eapi_positive_config_test(func, cmds)

    async def test_delete(self):
        # Test passing in a full set of parameters to 'delete'
        # Some parameters may be not set: None
        self.instance.configure = unittest.mock.AsyncMock(return_value=True)
        
        for ip_dest in IP_DESTS:
            (next_hop, next_hop_ip) = choice(NEXT_HOPS)
            distance = choice(DISTANCES)
            if distance:
                distance = random_int(0, 255)
            tag = choice(TAGS)
            if tag:
                tag = random_int(0, 255)
            route_name = choice(ROUTE_NAMES)
            if route_name:
                route_name = random_string(minchar=4, maxchar=10)

            func = async_function(self.instance.delete, ip_dest, next_hop,
                               next_hop_ip=next_hop_ip,
                               distance=distance,
                               tag=tag,
                               route_name=route_name)

            # Build the expected string for comparison
            # A value of None will default to an empty string, and
            # add the tag or name keywords where appropriate
            cmd_next_hop_ip = cmd_distance = cmd_tag = cmd_route_name = ''
            if next_hop_ip is not None:
                cmd_next_hop_ip = " %s" % next_hop_ip
            if distance is not None:
                cmd_distance = " %d" % distance
            if tag is not None:
                cmd_tag = " tag %d" % tag
            if route_name is not None:
                cmd_route_name = " name %s" % route_name
            cmds = "no ip route %s %s%s%s%s%s" % \
                   (ip_dest, next_hop, cmd_next_hop_ip, cmd_distance,
                    cmd_tag, cmd_route_name)

            await self.async_eapi_positive_config_test(func, cmds)

    async def test_default(self):
        # Test passing in a full set of parameters to 'default'
        # Some parameters may be not set: None
        self.instance.configure = unittest.mock.AsyncMock(return_value=True)
        
        for ip_dest in IP_DESTS:
            (next_hop, next_hop_ip) = choice(NEXT_HOPS)
            distance = choice(DISTANCES)
            if distance:
                distance = random_int(0, 255)
            tag = choice(TAGS)
            if tag:
                tag = random_int(0, 255)
            route_name = choice(ROUTE_NAMES)
            if route_name:
                route_name = random_string(minchar=4, maxchar=10)

            func = async_function(self.instance.default, ip_dest, next_hop,
                               next_hop_ip=next_hop_ip,
                               distance=distance,
                               tag=tag,
                               route_name=route_name)

            # Build the expected string for comparison
            # A value of None will default to an empty string, and
            # add the tag or name keywords where appropriate
            cmd_next_hop_ip = cmd_distance = cmd_tag = cmd_route_name = ''
            if next_hop_ip is not None:
                cmd_next_hop_ip = " %s" % next_hop_ip
            if distance is not None:
                cmd_distance = " %d" % distance
            if tag is not None:
                cmd_tag = " tag %d" % tag
            if route_name is not None:
                cmd_route_name = " name %s" % route_name
            cmds = "default ip route %s %s%s%s%s%s" % \
                   (ip_dest, next_hop, cmd_next_hop_ip, cmd_distance,
                    cmd_tag, cmd_route_name)

            await self.async_eapi_positive_config_test(func, cmds)

    async def test_set_tag(self):
        # Test passing in a new tag to the set_tag function
        self.instance.configure = unittest.mock.AsyncMock(return_value=True)
        
        ip_dest = '1.2.3.0/24'
        next_hop = 'Ethernet1'
        next_hop_ip = '1.1.1.1'
        distance = 10
        tag = '99'

        func = async_function(self.instance.set_tag, ip_dest, next_hop,
                           next_hop_ip=next_hop_ip,
                           distance=distance, tag=tag)

        cmd = "ip route %s %s %s %s tag %s" % \
            (ip_dest, next_hop, next_hop_ip, distance, tag)

        await self.async_eapi_positive_config_test(func, cmd)

    async def test_set_route_name(self):
        # Test passing in a new name to the set_route_name function
        self.instance.configure = unittest.mock.AsyncMock(return_value=True)
        
        ip_dest = '1.2.3.0/24'
        next_hop = 'Ethernet1'
        next_hop_ip = '1.1.1.1'
        distance = 10
        tag = '99'
        route_name = 'Test99'

        func = async_function(self.instance.set_route_name, ip_dest, next_hop,
                           next_hop_ip=next_hop_ip,
                           distance=distance, tag=tag,
                           route_name=route_name)

        cmd = "ip route %s %s %s %s tag %s name %s" % \
            (ip_dest, next_hop, next_hop_ip, distance, tag, route_name)

        await self.async_eapi_positive_config_test(func, cmd)


if __name__ == '__main__':
    unittest.main()