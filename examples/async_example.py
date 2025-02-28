#!/usr/bin/env python
#
# Copyright (c) 2024, Arista Networks, Inc.
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

"""
Example script for using the async functionality in pyeapi
"""

import asyncio
import pyeapiasync
import sys


async def get_version(node):
    """Get the version of the device asynchronously"""
    version = await node.get_version()
    return version


async def get_running_config(node):
    """Get the running config of the device asynchronously"""
    config = await node.get_running_config()
    return config


async def run_commands(node, commands):
    """Run commands on the device asynchronously"""
    result = await node.enable(commands)
    return result


async def main():
    """Main function to demonstrate async functionality"""
    # Connect to the device
    try:
        # You can use connect_to_async to connect using a
        #   profile from eapi.conf
        # node = await pyeapi.connect_to_async('veos01')

        # Or connect directly with parameters
        node = await pyeapiasync.connect_async(
            transport='https',
            host='localhost',
            username='admin',
            password='',
            port=443,
            return_node=True
        )

        # Run multiple commands concurrently
        version_task = asyncio.create_task(get_version(node))
        config_task = asyncio.create_task(get_running_config(node))
        commands_task = asyncio.create_task(run_commands(node,
                                                         ['show version',
                                                          'show interfaces']))

        # Wait for all tasks to complete
        version = await version_task
        config = await config_task
        commands_result = await commands_task

        # Print results
        print(f"Version: {version}")
        print(f"Config length: {len(config)} characters")
        print(f"Commands result: {commands_result}")

        # Configure the device asynchronously
        config_result = await node.config(['hostname async-test'])
        print(f"Config result: {config_result}")

        # Get a section of the config asynchronously
        hostname_section = await node.section('hostname')
        print(f"Hostname section: {hostname_section}")

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
