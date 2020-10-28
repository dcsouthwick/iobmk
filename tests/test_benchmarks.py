#!/usr/bin/env python3
###############################################################################
# Copyright 2019-2020 CERN. See the COPYRIGHT file at the top-level directory
# of this distribution. For licensing information, see the COPYING file at
# the top-level directory of this distribution.
###############################################################################

import unittest
from unittest.mock import patch, mock_open, MagicMock
from hepbenchmarksuite import utils
from hepscore import HEPscore


class TestHepscore(unittest.TestCase):
    """Test extra utility methods."""

    def setUp(self):
        self.conf = {'global': {'mode': 'singularity', 'rundir': '/tmp'}}

    @patch.dict(utils.sys.modules, {'hepscore': None})
    def test_hepscore_import(self):
        """Test hepscore missing reports failure."""
        ret = utils.run_hepscore(self.conf)
        self.assertEqual(ret, -1)

    @patch.object(HEPscore, 'write_output')
    @patch.object(HEPscore, 'run', return_value=-1)
    def test_hepscore_loadconf(self, mock_hepscore, mock_writer):
        test_conf = self.conf.copy()
        ret = utils.run_hepscore(test_conf)
        mock_hepscore.assert_called()
        mock_writer.assert_called()
        self.assertIn('hepscore_benchmark', test_conf)
        self.assertEqual(ret, -1)
        self.assertEqual('singularity', test_conf['hepscore_benchmark']['settings']['container_exec'])

    @patch.object(utils, 'files', side_effect=Exception('Boom!'))
    def test_hepscore_loadconf_failure(self, mock_files):
        test_conf = self.conf.copy()
        self.assertNotIn('hepscore_benchmark', test_conf)
        with self.assertLogs('hepbenchmarksuite.utils', level='ERROR') as log:
            ret = utils.run_hepscore(test_conf)
            self.assertEqual(ret, -1)
            self.assertIn('Unable to load default config yaml', *log.output)

    @patch.object(HEPscore, 'write_output')
    @patch.object(HEPscore, 'run', return_value=-1)
    def test_hepscore_override_conf(self, mock_hepscore, mock_writer):
        test_conf = self.conf.copy()
        test_conf.update({'hepscore_benchmark': {'settings': {}}})
        with self.assertRaises(SystemExit):
            utils.run_hepscore(test_conf)

    @patch.object(HEPscore, 'write_output')
    @patch.object(HEPscore, 'gen_score')
    @patch.object(HEPscore, 'run', return_value=1)
    def test_hepscore_genscore(self, mock_hepscore, mock_gen, mock_write):
        test_conf = self.conf.copy()

        ret = utils.run_hepscore(test_conf)
        self.assertEqual(ret, 1)
        mock_gen.assert_called()
        mock_write.assert_called_once_with('json', '/tmp/HEPSCORE/hepscore_result.json')

if __name__ == '__main__':
    unittest.main(verbosity=2)
