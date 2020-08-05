#!/usr/bin/python3
###############################################################################
# Copyright 2019-2020 CERN. See the COPYRIGHT file at the top-level directory
# of this distribution. For licensing information, see the COPYING file at
# the top-level directory of this distribution.
###############################################################################

import argparse
from datetime import datetime
import logging
import os
import unittest
from unittest import mock
from hepbenchmarksuite.plugins.extractor import Extractor
from hepbenchmarksuite import send_queue


class TestHWExtractor(unittest.TestCase):
    """********************************************************
                *** HEP-BENCHMARK-SUITE ***

    Testing the extraction of Hardware Metadata.

   *********************************************************"""

    def test_command_success(self):
        """
        Test if the execution of a command is successfull.
        """

        hw = Extractor()
        result = hw.exec_cmd('echo 1')
        self.assertEqual(result, '1')

    def test_command_failure(self):
        """
        Test if the execution of a command fails.
        """

        hw = Extractor()
        result = hw.exec_cmd('echofail 1')
        self.assertEqual(result, 'not_available')

    def test_parser_bios(self):
        """
        Test the parser for a BIOS output.
        """

        hw = Extractor()

        with open('tests/data/BIOS.sample', 'r') as bios_file:
            bios_text = bios_file.read()

        parser = hw.get_parser(bios_text)

        self.assertEqual(parser('Version'),
                         'SE5C600.86B.02.01.0002.082220131453',
                         'BIOS parser mismatch!')
        self.assertEqual(parser('Vendor'), 'Intel Corp.',
                         'BIOS parser mismatch!')
        self.assertEqual(parser('Release Date'), '08/22/2013',
                         'BIOS parser mismatch!')

    def test_parser_cpu(self):
        """
        Test the parser for a BIOS output.
        """

        hw = Extractor()

        with open('tests/data/CPU.sample', 'r') as cpu_file:
            cpu_text = cpu_file.read()

        CPU_OK = {
            "Architecture": "x86_64",
            "CPU_Model": "Intel(R) Xeon(R) CPU E5-2695 v2 @ 2.40GHz",
            "CPU_Family": "6",
            "CPU": "48",
            "Online_CPUs_list": "0-47",
            "Threads_per_core": "2",
            "Cores_per_socket": "12",
            "Sockets": "2",
            "Vendor_ID": "GenuineIntel",
            "Stepping": "4",
            "CPU_Max_Speed_MHz": "3200.0000",
            "CPU_Min_Speed_MHz": "1200.0000",
            "BogoMIPS": "4788.43",
            "L2_cache": "256K",
            "L3_cache": "30720K",
            "NUMA_node0_CPUs": "0-11,24-35",
            "NUMA_node1_CPUs": "12-23,36-47",
        }

        cpu_output = hw.get_cpu_parser(cpu_text)

        self.assertEqual(cpu_output, CPU_OK, "CPU parser mismatch!")

    def test_parser_memory(self):
        """
        Test the parser for a memory output.
        """

        hw = Extractor()

        with open('tests/data/MEM.sample', 'r') as mem_file:
            mem_text = mem_file.read()

        mem_output = hw.get_mem_parser(mem_text)

        MEM_OK = {
            "dimm1": "8192 MB DDR3 | Nanya | NT8GC72C4NG0NL-CG",
            "dimm2": "8192 MB DDR3 | Nanya | NT8GC72C4NG0NL-CG",
            "dimm3": "8192 MB DDR3 | Nanya | NT8GC72C4NG0NL-CG",
            "dimm4": "8192 MB DDR3 | Nanya | NT8GC72C4NG0NL-CG",
            "dimm5": "8192 MB DDR3 | Nanya | NT8GC72C4NG0NL-CG",
            "dimm6": "8192 MB DDR3 | Nanya | NT8GC72C4NG0NL-CG",
            "dimm7": "8192 MB DDR3 | Nanya | NT8GC72C4NG0NL-CG",
            "dimm8": "8192 MB DDR3 | Nanya | NT8GC72C4NG0NL-CG"
        }

        self.assertEqual(mem_output, MEM_OK, "Memory parser mismatch!")

    def test_parser_storage(self):
        """
        Test the parser for a storage output.
        """

        hw = Extractor()

        with open('tests/data/STORAGE.sample', 'r') as storage_file:
            storage_text = storage_file.read()

        storage_output = hw.get_storage_parser(storage_text)

        STORAGE_OK = {
            "disk1": "/dev/sda | INTEL SSDSC2CW24 | 223GiB (240GB)",
            "disk2": "/dev/sdb | INTEL SSDSC2CW24 | 223GiB (240GB)",
            "disk3": "/dev/sdc | INTEL SSDSC2CW24 | 223GiB (240GB)"
        }

        self.assertEqual(storage_output, STORAGE_OK,
                         "Storage parser mismatch!")


class TestAMQ(unittest.TestCase):
    """AMQ send_queue functionality"""

    def setUp(self, message):
        """Create json with timestamp and random string"""

        # get CI environment args.
        # TODO(someone): fix for testing outside CI
        USER = os.getenv('QUEUE_USERNAME')
        PASSWORD = os.getenv('QUEUE_PASSWORD')
        SERVER = os.getenv('QUEUE_HOST')
        PORT = 61113
        TOPIC = os.getenv('QUEUE_NAME')
        CERT = os.getenv('CERT_FILE')
        KEY = os.getenv('KEY_FILE')
        TESTDIR = os.getcwd()
        print(TESTDIR)
        with open(TESTDIR+"/data/result_profile_template.json", "r") as t:
            lines = t.readlines()

        def genJSON(message){
            timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
            self.assertTrue(isinstance(message, str),
                            'Message is not a string')
            with open(TESTDIR+"/data/result_profile.json", "w") as profile:
                for line in lines:
                    line = re.sub(r'_INSERTTIMESTAMP_', timestamp, line)
                    line = re.sub(r'_INSERTFREETEXT_', self.message, line)
                    profile.write(line)
        }

    def test_generate_json(self):
        """Test if the json creation is successfull."""

        open_mock = mock.mock_open()
        with mock.patch("main.open", open_mock, create=True):
            genJSON("test amq user-password")
        open_mock.assert_called_with(TESTDIR+"/data/result_profile.json", "w")
        open_mock.return_value.write.assert_called_once_with("test amq user-password")
        self.assertTrue(os.path.isfile(TESTDIR+"/data/result_profile.json"))

    @mock.patch('argparse.ArgumentParser.parse_args',
                return_value=argparse.Namespace(
                    port=PORT,
                    server=SERVER,
                    username=USER,
                    password=PASSWORD,
                    topic=TOPIC,
                    key=None,
                    cert=None,
                    file=TESTDIR+"/data/result_profile.json"
                ))
    def test_AMQ_commandline(mock_args):
        """Pass command line arguments to send_queue via mock"""
        self.args = send_queue.main()
        self.assertEqual(self.args, mock_args)

    def test_AMQ_call(self):
        """Pass config object to send_queue"""
        test_connection = {
            'port': PORT,
            'server': SERVER,
            'topic': TOPIC,
            'username': USER
            'password': PASSWORD
        }
        send_queue.send_message(TESTDIR+"/data/result_profile.json",
                                test_connection)
        self.assertLogs()

    def test_bad_UN_PW(self):

    def test_missing_topic(self):
    def test_wrong_topic(self):
    def test_wrong_cert(self):
    def 


    def tearDown(self):
        events.append("tearDown")


if __name__ == '__main__':
    unittest.main(verbosity=2)
