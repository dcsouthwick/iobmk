#!/usr/bin/python3
"""********************************************************
                *** HEP-BENCHMARK-SUITE ***
This script allows you to quickly fetch hardware metatadata.

This tool is part of the CERN HEP-BENCHMARK-SUITE.

In case of issues, bugs, suggestions, etc. please contact:
            hep-benchmarks-support@cern.ch

Author:  Miguel F. Medeiros
*********************************************************"""

from hwmetadata.extractor import Extractor
import logging
import sys

# Configure logging
logger         = logging.getLogger()
LOG_FORMAT     = logging.Formatter('%(levelname)s  %(asctime)s [%(name)s]  %(message)s',  datefmt='%Y-%m-%d %H:%M:%S')
LOG_HANDLER    = logging.StreamHandler(stream=sys.stdout)
LOG_LEVEL      = logging.DEBUG

# Add handlers for logging
logger.setLevel(LOG_LEVEL)
LOG_HANDLER.setFormatter(LOG_FORMAT)
logger.addHandler(LOG_HANDLER)

# Collect data
hw=Extractor()
hw.collect()

# Print the output to stdout and save metadata to json file
hw.dump(stdout=True, outfile='hw.json')

# hw.export() returns a dict which can be used for other python integrations.
print(hw.export())