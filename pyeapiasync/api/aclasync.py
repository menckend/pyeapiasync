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
"""Module for working with EOS access control list resources asynchronously

This module provides an asynchronous implementation for configuring and
managing access control lists on Arista EOS nodes. Access control lists can be
specified as either 'standard' or 'extended' ACLs. This module provides the
following class implementations:

    * AclsAsync -- The top-level class used to manage both standard and
        extended access control lists in EOS asynchronously
    * StandardAclsAsync -- Class that manages the set of standard ACLs
        asynchronously
    * ExtendedAclsAsync -- Class that manages the set of extended ACLs
        asynchronously

"""
import re

from pyeapiasync.api import EntityCollectionAsync
from pyeapiasync.utils import ProxyCall
import netaddr


VALID_ACLS = frozenset(['standard', 'extended'])


def mask_to_prefixlen(mask):
    """Converts a subnet mask from dotted decimal to bit length

    Args:
        mask (str): The dotted decimal subnet mask to convert

    Returns:
        str: The subnet mask as a valid prefix length
    """
    mask = mask or '255.255.255.255'
    return netaddr.IPAddress(mask).netmask_bits()


def prefixlen_to_mask(prefixlen):
    """Converts a prefix length to a dotted decimal subnet mask

    Args:
        prefixlen (str): The prefix length value to convert

    Returns:
        str: The subt mask as a dotted decimal string
    """
    prefixlen = prefixlen or '32'
    addr = '0.0.0.0/%s' % prefixlen
    return str(netaddr.IPNetwork(addr).netmask)


class AclsAsync(EntityCollectionAsync):

    def __init__(self, node, *args, **kwargs):
        super(AclsAsync, self).__init__(node, *args, **kwargs)
        self._instances = dict()

    async def get(self, name):
        """Returns an ACL resource object asynchronously

        Args:
            name (str): The ACL name to retrieve from the running-config

        Returns:
            A Python dictionary object containing the ACL configuration
            or None if the ACL does not exist
        """
        return (await self.get_instance(name))[name]

    async def getall(self):
        """Returns all ACLs in a dict object asynchronously.

        Returns:
            A Python dictionary object containing all ACL
            configuration indexed by ACL name::
                {
                    "<ACL1 name>": {...},
                    "<ACL2 name>": {...}
                }
        """
        acl_re = re.compile(r'^ip access-list (?:(standard) )?(.+)$', re.M)
        config = await self.config
        response = {'standard': {}, 'extended': {}}
        for acl_type, name in acl_re.findall(config):
            acl = await self.get(name)
            if acl_type and acl_type == 'standard':
                response['standard'][name] = acl
            else:
                response['extended'][name] = acl
        return response

    def __getattr__(self, name):
        """Provides attribute access to the underlying ACL instance methods

        Args:
            name (str): The method name to call on the ACL instance

        Returns:
            A function wrapper that marshalls the request
        """
        return ProxyCall(self.marshall, name)

    async def marshall(self, name, *args, **kwargs):
        """Marshalls calls to instance methods asynchronously

        Args:
            name (str): The method name to call on the ACL instance
            *args: The arguments to pass to the method
            **kwargs: The keyword arguments to pass to the method

        Returns:
            The result of the method call

        Raises:
            AttributeError: If the method does not exist on the instance
        """
        acl_name = args[0]
        acl_instance = await self.get_instance(acl_name)
        if not hasattr(acl_instance, name):
            raise AttributeError("'%s' object has no attribute '%s'" %
                                 (acl_instance, name))
        method = getattr(acl_instance, name)
        return await method(*args, **kwargs)

    async def get_instance(self, name):
        """Returns an instance of the appropriate ACL class asynchronously

        This method will determine the ACL type and return the appropriate
        instance.

        Args:
            name (str): The name of the ACL to retrieve

        Returns:
            A dictionary containing the ACL instance indexed by name
        """
        if name in self._instances:
            return self._instances[name]
        acl_re = re.compile(r'^ip access-list (?:(standard) )?(%s)$' % name,
                            re.M)
        config = await self.config
        match = acl_re.search(config)
        if match:
            acl_type = match.group(1) or 'extended'
            return await self.create_instance(match.group(2), acl_type)
        return {name: None}

    async def create_instance(self, name, acl_type):
        """Creates a new ACL instance asynchronously

        Args:
            name (str): The name of the ACL
            acl_type (str): The type of ACL ('standard' or 'extended')

        Returns:
            The ACL instance
        """
        if acl_type not in VALID_ACLS:
            acl_type = 'standard'
        acl_instance = ACL_CLASS_MAP.get(acl_type)
        self._instances[name] = acl_instance(self.node)
        return self._instances[name]

    async def create(self, name, type='standard'):
        """Creates a new ACL in the running configuration asynchronously

        Args:
            name (str): The name of the ACL to create
            type (str): The type of ACL to create, either 'standard'
                or 'extended'

        Returns:
            True if the operation was successful otherwise False
        """
        acl_instance = await self.create_instance(name, type)
        return await acl_instance.create(name)


class StandardAclsAsync(EntityCollectionAsync):

    entry_re = re.compile(r'(\d+)'
                          r'(?: ([p|d]\w+))'
                          r'(?: (any))?'
                          r'(?: (host))?'
                          r'(?: ([0-9]+(?:\.[0-9]+){3}))?'
                          r'(?:/([0-9]{1,2}))?'
                          r'(?: ([0-9]+(?:\.[0-9]+){3}))?'
                          r'(?: (log))?')

    async def get(self, name):
        """Returns a standard ACL resource object asynchronously

        Args:
            name (str): The ACL name to retrieve from the running-config

        Returns:
            A Python dictionary object containing the ACL configuration
            or None if the ACL does not exist
        """
        config = await self.get_block('ip access-list standard %s' % name)
        if not config:
            return None
        resource = dict(name=name, type='standard')
        resource.update(self._parse_entries(config))
        return resource

    def _parse_entries(self, config):
        """Parses the ACL configuration and returns a dictionary of entries

        Args:
            config (str): The ACL configuration block

        Returns:
            A dictionary of entries indexed by sequence number
        """
        entries = dict()
        pattern = r'\d+ [p|d].*$'
        for item in re.finditer(pattern, config, re.M):
            match = self.entry_re.match(item.group(0))
            groups = match.groups()
            seq = groups[0]
            act = groups[1]
            ip = groups[4]
            mlen = groups[5]
            mask = groups[6]
            log = groups[7]
            entry = dict()
            entry['action'] = act
            entry['srcaddr'] = ip or '0.0.0.0'
            if mlen:
                entry['srclen'] = mlen
            else:
                if mask:
                    mask_len = mask_to_prefixlen(mask)
                else:
                    mask_len = '32'
                entry['srclen'] = mask_len
            if log is not None:
                entry['log'] = True
            else:
                entry['log'] = False
            entries[seq] = entry
        return dict(entries=entries)

    async def create(self, name):
        """Creates a new standard ACL in the running configuration asynchronously

        Args:
            name (str): The name of the ACL to create

        Returns:
            True if the operation was successful otherwise False
        """
        return await self.configure('ip access-list standard %s' % name)

    async def delete(self, name):
        """Deletes a standard ACL from the running configuration asynchronously

        Args:
            name (str): The name of the ACL to delete

        Returns:
            True if the operation was successful otherwise False
        """
        return await self.configure('no ip access-list standard %s' % name)

    async def default(self, name):
        """Defaults a standard ACL in the running configuration asynchronously

        Args:
            name (str): The name of the ACL to default

        Returns:
            True if the operation was successful otherwise False
        """
        return await self.configure('default ip access-list standard %s'
                                    % name)

    async def update_entry(self, name, seqno, action, addr, prefixlen,
                           log=False):
        """Updates an entry in the standard ACL asynchronously

        Args:
            name (str): The name of the ACL
            seqno (str): The sequence number of the entry
            action (str): The action to take, either 'permit' or 'deny'
            addr (str): The source IP address
            prefixlen (str): The prefix length or subnet mask
            log (bool): Whether to enable logging for this entry

        Returns:
            True if the operation was successful otherwise False
        """
        cmds = ['ip access-list standard %s' % name]
        cmds.append('no %s' % seqno)
        entry = '%s %s %s/%s' % (seqno, action, addr, prefixlen)
        if log:
            entry += ' log'
        cmds.append(entry)
        return await self.configure(cmds)

    async def add_entry(self, name, action, addr, prefixlen, log=False,
                        seqno=None):
        """Adds an entry to a standard ACL asynchronously

        Args:
            name (str): The name of the ACL
            action (str): The action to take, either 'permit' or 'deny'
            addr (str): The source IP address
            prefixlen (str): The prefix length or subnet mask
            log (bool): Whether to enable logging for this entry
            seqno (str): Optional sequence number for the entry

        Returns:
            True if the operation was successful otherwise False
        """
        cmds = ['ip access-list standard %s' % name]
        entry = '%s %s/%s' % (action, addr, prefixlen)
        if seqno is not None:
            entry = '%s %s' % (seqno, entry)
        if log:
            entry += ' log'
        cmds.append(entry)
        cmds.append('exit')
        return await self.configure(cmds)

    async def remove_entry(self, name, seqno):
        """Removes an entry from a standard ACL asynchronously

        Args:
            name (str): The name of the ACL
            seqno (str): The sequence number of the entry to remove

        Returns:
            True if the operation was successful otherwise False
        """
        cmds = ['ip access-list standard %s' % name, 'no %s' % seqno, 'exit']
        return await self.configure(cmds)


class ExtendedAclsAsync(EntityCollectionAsync):

    entry_re = re.compile(r'(\d+)'
                          r'(?: ([p|d]\w+))'
                          r'(?: (\w+|\d+))'
                          r'(?: ([a|h]\w+))?'
                          r'(?: ([0-9]+(?:\.[0-9]+){3}))?'
                          r'(?:/([0-9]{1,2}))?'
                          r'(?: ((?:eq|gt|lt|neq|range) [\w-]+))?'
                          r'(?: ([a|h]\w+))?'
                          r'(?: ([0-9]+(?:\.[0-9]+){3}))?'
                          r'(?:/([0-9]{1,2}))?'
                          r'(?: ([0-9]+(?:\.[0-9]+){3}))?'
                          r'(?: ((?:eq|gt|lt|neq|range) [\w-]+))?'
                          r'(?: (.+))?')

    async def get(self, name):
        """Returns an extended ACL resource object asynchronously

        Args:
            name (str): The ACL name to retrieve from the running-config

        Returns:
            A Python dictionary object containing the ACL configuration
            or None if the ACL does not exist
        """
        config = await self.get_block('ip access-list %s' % name)
        if not config:
            return None
        resource = dict(name=name, type='extended')
        resource.update(self._parse_entries(config))
        return resource

    def _parse_entries(self, config):
        """Parses the ACL configuration and returns a dictionary of entries

        Args:
            config (str): The ACL configuration block

        Returns:
            A dictionary of entries indexed by sequence number
        """
        entries = dict()
        pattern = r'\d+ [p|d].*$'
        for item in re.finditer(pattern, config, re.M):
            match = self.entry_re.match(item.group(0))
            if match:
                entry = dict()
                entry['action'] = match.group(2)
                entry['protocol'] = match.group(3)
                entry['srcaddr'] = match.group(5) or 'any'
                entry['srclen'] = match.group(6)
                entry['srcport'] = match.group(7)
                entry['dstaddr'] = match.group(9) or 'any'
                entry['dstlen'] = match.group(10)
                entry['dstport'] = match.group(12)
                entry['other'] = match.group(13)
                entries[match.group(1)] = entry
        return dict(entries=entries)

    async def create(self, name):
        """Creates a new extended ACL in the running configuration asynchronously

        Args:
            name (str): The name of the ACL to create

        Returns:
            True if the operation was successful otherwise False
        """
        return await self.configure('ip access-list %s' % name)

    async def delete(self, name):
        """Deletes an extended ACL from the running configuration asynchronously

        Args:
            name (str): The name of the ACL to delete

        Returns:
            True if the operation was successful otherwise False
        """
        return await self.configure('no ip access-list %s' % name)

    async def default(self, name):
        """Defaults an extended ACL in the running configuration asynchronously

        Args:
            name (str): The name of the ACL to default

        Returns:
            True if the operation was successful otherwise False
        """
        return await self.configure('default ip access-list %s' % name)

    async def update_entry(self, name, seqno, action, protocol, srcaddr,
                           srcprefixlen, dstaddr, dstprefixlen, log=False):
        """Updates an entry in the extended ACL asynchronously

        Args:
            name (str): The name of the ACL
            seqno (str): The sequence number of the entry
            action (str): The action to take, either 'permit' or 'deny'
            protocol (str): The protocol name or number
            srcaddr (str): The source IP address
            srcprefixlen (str): The source prefix length
            dstaddr (str): The destination IP address
            dstprefixlen (str): The destination prefix length
            log (bool): Whether to enable logging for this entry

        Returns:
            True if the operation was successful otherwise False
        """
        cmds = ['ip access-list %s' % name]
        cmds.append('no %s' % seqno)
        entry = '%s %s %s %s/%s %s/%s' % (seqno, action, protocol, srcaddr,
                                          srcprefixlen, dstaddr, dstprefixlen)
        if log:
            entry += ' log'
        cmds.append(entry)
        cmds.append('exit')
        return await self.configure(cmds)

    async def add_entry(self, name, action, protocol, srcaddr, srcprefixlen,
                        dstaddr, dstprefixlen, log=False, seqno=None):
        """Adds an entry to an extended ACL asynchronously

        Args:
            name (str): The name of the ACL
            action (str): The action to take, either 'permit' or 'deny'
            protocol (str): The protocol name or number
            srcaddr (str): The source IP address
            srcprefixlen (str): The source prefix length
            dstaddr (str): The destination IP address
            dstprefixlen (str): The destination prefix length
            log (bool): Whether to enable logging for this entry
            seqno (str): Optional sequence number for the entry

        Returns:
            True if the operation was successful otherwise False
        """
        cmds = ['ip access-list %s' % name]
        entry = '%s %s %s/%s %s/%s' % (action, protocol, srcaddr,
                                       srcprefixlen, dstaddr, dstprefixlen)
        if seqno is not None:
            entry = '%s %s' % (seqno, entry)
        if log:
            entry += ' log'
        cmds.append(entry)
        cmds.append('exit')
        return await self.configure(cmds)

    async def remove_entry(self, name, seqno):
        """Removes an entry from an extended ACL asynchronously

        Args:
            name (str): The name of the ACL
            seqno (str): The sequence number of the entry to remove

        Returns:
            True if the operation was successful otherwise False
        """
        cmds = ['ip access-list %s' % name, 'no %s' % seqno, 'exit']
        return await self.configure(cmds)


ACL_CLASS_MAP = {'standard': StandardAclsAsync, 'extended': ExtendedAclsAsync}


def instance(node):
    """Returns an instance of AclsAsync

    This method will create and return an instance of the AclsAsync object
    passing the value of node to the object. The instance method is required
    for the resource to be autoloaded by the AsyncNode object

    Args:
        node (AsyncNode): The node argument passes an instance of
            AsyncNode to the resource

    Returns:
        An instance of AclsAsync
    """
    return AclsAsync(node)
