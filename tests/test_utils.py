#!/usr/bin/env python3
###############################################################################
# Copyright 2019-2020 CERN. See the COPYRIGHT file at the top-level directory
# of this distribution. For licensing information, see the COPYING file at
# the top-level directory of this distribution.
###############################################################################

import contextlib
import difflib
import json
import unittest
from hepbenchmarksuite import utils
import sys
import pytest

def test_print_results():
    """Test the print results from utils."""
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


@pytest.mark.parametrize('url', ["httpps://brokenlink1", "httpss://brokenlink2", "brokenlink3.com"])
def test_failed_download(url):
    """Test the download failure."""
    assert utils.download_file(url, "test") == 1

# TODO once a publicly available hepscore url is published
#def test_success_download():


if __name__ == '__main__':
    unittest.main(verbosity=2)
