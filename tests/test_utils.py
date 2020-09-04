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
import contextlib
import difflib
import json
import sys


class TestHepscore(unittest.TestCase):
    """Test extra utility methods"""

    def setUp(self):
        self.conf = {'global': {'mode': 'singularity', 'rundir': '/tmp'}}

    @patch.dict(utils.sys.modules, {'hepscore': None})
    def test_hepscore_import(self):
        """Test hepscore missing reports failure"""
        ret = utils.run_hepscore(self.conf)
        self.assertEqual(ret, -1)

    @patch.object(HEPscore, 'run', return_value=-1)
    def test_hepscore_loadconf(self, mock_hepscore):
        test_conf = self.conf.copy()
        ret = utils.run_hepscore(test_conf)
        mock_hepscore.assert_called()
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

    @patch.object(HEPscore, 'run', return_value=-1)
    def test_hepscore_override_conf(self, mock_hepscore):
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


def test_print_results():
    """Test the print results from utils"""

    # Temporary file
    TEMP_FILE = 'result_dump'

    # Create a context to redirect the stdout output
    # from utils.print_results_from_file to a file
    # that can be later accessed for comparison
    with open(TEMP_FILE, 'w') as tmp_file:
        with contextlib.redirect_stdout(tmp_file):
            utils.print_results_from_file('tests/data/result_profile_sample.json')

    # Open a valid print results sample file
    with open('tests/data/valid_print_results_sample', 'r') as print_sample:
        # Open the file with the output generated from previous call
        with open(TEMP_FILE, "r") as gen_out:
            sample_output = print_sample.readlines()
            utils_output  = gen_out.readlines()

            # Compare differences between sample print message
            # and the one resulting from utils print function
            diff = difflib.Differ().compare(sample_output, utils_output)

            # Dump the printout for easier identification of issues
            sys.stdout.writelines(diff)

            assert sample_output == utils_output



if __name__ == '__main__':
    unittest.main(verbosity=2)
