import unittest
from unittest.mock import patch, Mock
import pyeapiasync.utils as utils
from collections.abc import Iterable

class TestUtils(unittest.IsolatedAsyncioTestCase):

    @patch('pyeapiasync.utils.import_module')
    async def test_load_module(self, mock_import_module):
        loaded_module = Mock(object='loaded_module')
        mock_import_module.return_value = loaded_module
        result = utils.load_module('test')
        self.assertEqual(result, loaded_module)

    @patch('pyeapiasync.utils.import_module')
    async def test_load_module_raises_import_error(self, mock_import_module):
        mock_import_module.return_value = None
        with self.assertRaises(ImportError):
            utils.load_module('test')

    async def test_make_iterable_from_string(self):
        result = utils.make_iterable('test')
        self.assertIsInstance(result, Iterable)
        self.assertEqual(len(result), 1)

    async def test_make_iterable_from_unicode(self):
        result = utils.make_iterable(u'test')
        self.assertIsInstance(result, Iterable)
        self.assertEqual(len(result), 1)

    async def test_make_iterable_from_iterable(self):
        result = utils.make_iterable(['test'])
        self.assertIsInstance(result, Iterable)
        self.assertEqual(len(result), 1)

    async def test_make_iterable_raises_type_error(self):
        with self.assertRaises(TypeError):
            utils.make_iterable(object())

    async def test_import_module(self):
        result = utils.import_module('pyeapiasync.api.vlansasync')
        self.assertIsNotNone(result)

    async def test_import_module_raises_import_error(self):
        with self.assertRaises(ImportError):
            utils.import_module('fake.module.test')

    async def test_expand_singles(self):
        vlans = '1,2,3'
        result = utils.expand_range(vlans)
        result = ','.join(result)
        self.assertTrue(vlans == result)

    async def test_expand_range(self):
        vlans = '1-15'
        expected = [str(x) for x in range(1, 16)]
        result = utils.expand_range(vlans)
        self.assertEqual(result, expected)

    async def test_expand_mixed(self):
        vlans = '1,3,5-7,9'
        result = utils.expand_range(vlans)
        self.assertEqual(result, ['1', '3', '5', '6', '7', '9'])

    async def test_collapse_singles(self):
        vlans = '1,3,5,7'
        result = utils.collapse_range(vlans)
        self.assertEqual(result, ['1', '3', '5', '7'])

    async def test_collapse_range(self):
        vlans = '1,2,3,4,5'
        result = utils.collapse_range(vlans)
        self.assertEqual(result, ['1-5'])

    async def test_collapse_mixed(self):
        vlans = '1,3,5,6,7,9'
        result = utils.collapse_range(vlans)
        self.assertEqual(result, ['1', '3', '5-7', '9'])

    @patch('pyeapiasync.utils._LOGGER')
    async def test_debug(self, mock_logger):
        utils.islocalconnection = Mock(return_value=True)
        utils.debug('test')
        mock_logger.debug.assert_called_with('test_utils.test_debug: test')
