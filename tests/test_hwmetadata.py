###############################################################################
# Copyright 2019-2020 CERN. See the COPYRIGHT file at the top-level directory
# of this distribution. For licensing information, see the COPYING file at
# the top-level directory of this distribution.
###############################################################################

#!/usr/bin/python3

import unittest
from hepbenchmarksuite.plugins.extractor import Extractor

class TestHWExtractor(unittest.TestCase):
    """********************************************************
                *** HEP-BENCHMARK-SUITE ***
    This class allows you to test the extract Hardware Metadata.

    This tool is part of the CERN HEP-BENCHMARK-SUITE.

    In case of issues, bugs, suggestions, etc. please contact:
                hep-benchmarks-support@cern.ch

    Author:  Miguel F. Medeiros
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

        self.assertEqual(parser('Version'), 'SE5C600.86B.02.01.0002.082220131453', 'BIOS parser mismatch!')
        self.assertEqual(parser('Vendor'), 'Intel Corp.', 'BIOS parser mismatch!')
        self.assertEqual(parser('Release Date'), '08/22/2013',  'BIOS parser mismatch!')

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

        self.assertEqual(storage_output, STORAGE_OK, "Storage parser mismatch!")

if __name__ == '__main__':
    unittest.main(verbosity=2)
