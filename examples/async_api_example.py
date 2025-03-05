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
Example script for using the async API modules in pyeapi
"""

import asyncio
import sys
import pyeapiasync


async def get_vlans(node):
    """Get all VLANs from the device asynchronously"""
    all_vlans = await node.api['vlansasync'].getall()
    return all_vlans


async def create_vlan(node, vlan_id, vlan_name):
    """Create a new VLAN on the device asynchronously"""
    vlans = node.api['vlansasync']

    # Create the VLAN
    result = await vlans.create(vlan_id)
    if not result:
        print(f"Failed to create VLAN {vlan_id}")
        return False

    # Set the VLAN name
    result = await vlans.set_name(vlan_id, vlan_name)
    if not result:
        print(f"Failed to set name for VLAN {vlan_id}")
        return False

    return True


async def delete_vlan(node, vlan_id):
    """Delete a VLAN from the device asynchronously"""
    result = await node.api['vlansasync'].delete(vlan_id)
    return result


async def main():
    """Main function to demonstrate async API functionality"""
    # Connect to the device
    try:
        # You can use connect_to_async to connect using a profile
        #   from eapi.conf
        # node = await pyeapiasync.connect_to_async('veos01')

        # Or connect directly with parameters
        node = await pyeapiasync.connect_async(
            transport='https',
            host='localhost',
            username='admin',
            password='',
            port=443,
            return_node=True
        )

        # Load the API modules
        node.api_autoload()

        # Get all VLANs
        print("Getting all VLANs...")
        vlans = await get_vlans(node)
        print(f"Current VLANs: {vlans}")

        # Create a new VLAN
        vlan_id = '100'
        vlan_name = 'Test_VLAN_100'
        print("Creating VLAN...")
        result = await create_vlan(node, vlan_id, vlan_name)
        if result:
            print(f"Successfully created VLAN {vlan_id}")

        # Get the VLANs again to see the new VLAN
        print("Getting all VLANs after creation...")
        vlans = await get_vlans(node)
        print(f"Updated VLANs: {vlans}")

        # Delete the VLAN
        print(f"Deleting VLAN {vlan_id}...")
        result = await delete_vlan(node, vlan_id)
        if result:
            print(f"Successfully deleted VLAN {vlan_id}")

        # Get the VLANs again to confirm deletion
        print("Getting all VLANs after deletion...")
        vlans = await get_vlans(node)
        print(f"Final VLANs: {vlans}")

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
