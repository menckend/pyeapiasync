#!/usr/bin/env python
from __future__ import print_function
import pyeapiasync

pyeapiasync.load_config('nodes.conf')
node = pyeapiasync.connect_to('veos01')

output = node.enable('show version')

print(('My System MAC address is', output[0]['result']['systemMacAddress']))
