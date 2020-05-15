###############################################################################
# Copyright 2019-2020 CERN. See the COPYRIGHT file at the top-level directory
# of this distribution. For licensing information, see the COPYING file at
# the top-level directory of this distribution.
###############################################################################

import subprocess
import json
import logging
import sys
import re
import time
import os

_log = logging.getLogger(__name__)

class Extractor(object):
  """********************************************************
                *** HEP-BENCHMARK-SUITE ***
    This class allows you to extract Hardware Metadata.

    This tool depends on some system tools and will check for
    their existence. For a complete data dump, it is recommend
    to run as priviledge user.

   *********************************************************"""

  def __init__(self):
    """Initialize setup"""

    self.data = {}
    self.pkg  = {}

    # Check if the script is run as root user; needed to extract full data.

    if os.geteuid() != 0:
      _log.info("you should run this program as super-user for a complete output.")
      self._permission = False
    else:
      self._permission = True
      #sys.exit(1)

    # Check if the required tools to extract the data are installed.
    # If the tools are not present, the output will be limited on certain fields.
    # The dict self.pkg enforces the switching of outputs.

    req_packages = ['lshw', 'ipmitool', 'dmidecode']

    for rp in req_packages:
      cmd = subprocess.Popen("rpm -q {}".format(rp), shell=True, executable='/bin/bash',  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      cmd_reply, cmd_error = cmd.communicate()

      if cmd.returncode != 0:
        _log.error("Package is not installed: {}".format(cmd_reply))
        self.pkg[rp] = False
      else:
        _log.debug("Package installed: {}".format(cmd_reply.decode('utf-8').rstrip()))
        self.pkg[rp] = True

    _log.debug("Installed packages: {}".format(self.pkg))

  def exec_cmd(self, cmd_str):
    """ Accepts command string and returns output. """

    _log.debug("Excuting command: {}".format(cmd_str))

    cmd = subprocess.Popen(cmd_str, shell=True, executable='/bin/bash',  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    cmd_reply, cmd_error = cmd.communicate()

    # Check for errors
    if cmd.returncode != 0:
      cmd_reply = "not_available"
      _log.error(cmd_error)

    else:
      # Convert bytes to text and remove \n
      try:
        cmd_reply = cmd_reply.decode('utf-8').rstrip()
      except UnicodeDecodeError:
        _log.error("Failed to decode to utf-8.")

    return cmd_reply

  def collect_base(self):
    """ Collect base information of the system. """

    BASE = {
      'Hostname'       : "hostname -f",
    }

    # Extract and save data
    self._extract(BASE)

  def collect_SW(self):
    """ Collect Software specific metadata. """

    _log.info("Collecting SW information.")

    SW_CMD = {
      'os_version'     : "cat /etc/redhat-release",
      'kernel_version' : "uname -r",
      'gcc_version'    : "gcc --version | head -n1",
      'glibc_version'  : "yum list installed | grep glibc.x86_64 | awk '{print $2}'",
    }

    SW = {
      "python_version" : sys.version.split()[0],
    }

    # Execute commands and append result to a dict
    for key, val in SW_CMD.items():
      SW[key] = self.exec_cmd(val)

    return SW

  def collect_cpu(self):
    """ Collect all relevant CPU information. """

    _log.info("Collecting CPU information.")

    # Get the parsing result from lscpu
    CPU = self.get_cpu_parser(self.exec_cmd("lscpu"))

    # Update with additional data
    CPU.update ({
      'Power_Policy'       : self.exec_cmd("cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor | sort | uniq"),
      'Power_Driver'       : self.exec_cmd("cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_driver   | sort | uniq"),
      'Microcode'          : self.exec_cmd("grep microcode /proc/cpuinfo | uniq | awk 'NR==1{print $3}'"),
      'SMT_Enabled?'       : bool(self.exec_cmd("cat /sys/devices/system/cpu/smt/active"))
    })

    return CPU

  def get_cpu_parser(self, cmd_output):
    """ Collect all CPU data from lscpu. """

    parse_lscpu = self.get_parser(cmd_output, "lscpu")

    CPU = {
            'Architecture'       : parse_lscpu("Architecture"),
            'CPU_Model'          : parse_lscpu("Model name"),
            'CPU_Family'         : parse_lscpu("CPU family"),
            'CPU'                : parse_lscpu("CPU\(s\)"),
            'Online_CPUs_list'   : parse_lscpu("On-line CPU\(s\) list"),
            'Threads_per_core'   : parse_lscpu("Thread\(s\) per core"),
            'Cores_per_socket'   : parse_lscpu("Core\(s\) per socket"),
            'Sockets'            : parse_lscpu("Socket\(s\)"),
            'Vendor_ID'          : parse_lscpu("Vendor ID"),
            'Stepping'           : parse_lscpu("Stepping"),
            'CPU_Max_Speed_MHz'  : parse_lscpu("CPU max MHz"),
            'CPU_Min_Speed_MHz'  : parse_lscpu("CPU min MHz"),
            'BogoMIPS'           : parse_lscpu("BogoMIPS"),
            'L2_cache'           : parse_lscpu("L2 cache"),
            'L3_cache'           : parse_lscpu("L3 cache"),
            'NUMA_node0_CPUs'    : parse_lscpu("NUMA node0 CPU\(s\)"),
            'NUMA_node1_CPUs'    : parse_lscpu("NUMA node1 CPU\(s\)"),
    }
    return CPU

  def collect_bios(self):
    """ Collect all relevant BIOS information. """

    _log.info("Collecting BIOS information.")

    # get common parser
    if self.pkg['dmidecode'] and self._permission:
      parse_bios = self.get_parser(self.exec_cmd("dmidecode -t bios"), "bios")
    else:
      parse_bios = lambda x : "not_available"

    BIOS = {
      'Vendor'        : parse_bios("Vendor"),
      'Version'       : parse_bios("Version"),
      'Release_data'  : parse_bios("Release Date"),
    }

    return BIOS

  def collect_system(self):
    """ Collect relevant BIOS information. """

    _log.info("Collecting system information.")

    # get common parser
    if self.pkg['dmidecode'] and self._permission:
      parse_system = self.get_parser(self.exec_cmd("dmidecode -t system"), "system")
    else:
      parse_system = lambda x : "not_available"

    if self.pkg['ipmitool'] and self._permission:
      parse_BMC_FRU = self.get_parser(self.exec_cmd("ipmitool fru"), "BMC")
    else:
      parse_BMC_FRU = lambda x : "not_available"

    SYSTEM = {
      'Manufacturer'      : parse_system("Manufacturer"),
      'Product_Name'      : parse_system("Product Name"),
      'Version'           : parse_system("Version"),
      'Product_Serial'    : parse_BMC_FRU("Product Serial"),
      'Product_Asset_Tag' : parse_BMC_FRU("Product Asset Tag")
    }

    return SYSTEM

  def collect_memory(self):
    """ Collect system memory. """

    _log.info("Collecting system memory.")

    if self.pkg['dmidecode'] and self._permission:
      # Execute command and get output to parse
      cmd_output = self.exec_cmd("dmidecode -t 17")

      # Get memory parser for memory listing
      MEM = self.get_mem_parser(cmd_output)

    else:
      MEM = {}

    MEM.update ({
     'Mem_Total'     : self.exec_cmd("free | awk 'NR==2{print $2}'"),
     'Mem_Available' : self.exec_cmd("free | awk 'NR==2{print $7}'"),
     'Mem_Swap'      : self.exec_cmd("free | awk 'NR==3{print $2}'")
   })

    return MEM

  def get_mem_parser(self, cmd_output):
    """ Memory parser for dmidecode. """

    # Regex for matches
    regSize = re.compile(r'(?P<Field>Size:\s*\s)(?P<value>(?!No Module Installed).*\S)')
    regPart = re.compile(r'(?P<Field>Part Number:\s*\s)(?P<value>(?!NO DIMM).*\S)')
    regMan  = re.compile(r'(?P<Field>Manufacturer:\s*\s)(?P<value>(?!NO DIMM).*\S)')
    regType = re.compile(r'(?P<Field>Type:\s*\s)(?P<value>(?!Unknown).*\S)')


    # Return iterators containing matches
    result_Size = re.finditer(regSize, cmd_output)
    result_Part = re.finditer(regPart, cmd_output)
    result_Man  = re.finditer(regMan,  cmd_output)
    result_Type = re.finditer(regType, cmd_output)

    n=1
    MEM = {}

    # Loop at same time each iterator
    for size, part, man, typ in zip(result_Size, result_Part, result_Man, result_Type):
      #print(n,":",size.group('value'), typ.group('value'),"|" , man.group('value'), "|" , part.group('value'))
      MEM["dimm"+str(n)] = "{0} {1} | {2} | {3}".format(size.group('value'),typ.group('value'), man.group('value'), part.group('value'))
      n+=1

    return MEM

  def collect_storage(self):
    """ Collect system memory """

    _log.info("Collecting system storage.")

    if self.pkg['lshw'] and self._permission:

      # Execute command and get output to parse
      cmd_output = self.exec_cmd("lshw -c disk")

      # Get storage parser
      STORAGE = self.get_storage_parser(cmd_output)

    else:
      STORAGE = {}

    return STORAGE

  def get_storage_parser(self, cmd_output):
    """ Storage parser for lshw -c disk. """

    # Regex for matches
    regLogic   = re.compile(r'(?P<Field>logical name:\s*\s)(?P<value>.*)')
    regProduct = re.compile(r'(?P<Field>product:\s*\s)(?P<value>.*)')
    regSize    = re.compile(r'(?P<Field>size:\s*\s)(?P<value>.*)')

    # Return iterators containing matches
    result_logic   = re.finditer(regLogic,   cmd_output)
    result_product = re.finditer(regProduct, cmd_output)
    result_size    = re.finditer(regSize,    cmd_output)

    n=1
    STORAGE = {}
    for log, prod, siz in zip(result_logic, result_product, result_size):
      STORAGE["disk"+str(n)] = "{0} | {1} | {2}".format(log.group('value'), prod.group('value'), siz.group('value'))
      n+=1

    return STORAGE

  def get_parser(self, cmd_output, reg="common"):
    """ Common regex parser. """

    def parser(pattern):
      """ Parser function """
      # Different regex for parsing different outputs
      if reg == "BMC":
        exp = '(?P<Field>{}\s*:\s)(?P<Value>.*)'.format(pattern)
      else:
        exp = '(?P<Field>{}:\s*\s)(?P<Value>.*)'.format(pattern)

      # Search pattern in output
      result = re.search(exp , cmd_output)
      try:
        _log.debug("Parsing = {} | Field = {} | Value = {}".format(reg, pattern, result.group('Value')))
        return result.group('Value')

      except AttributeError:
        _log.debug("Parsing = {} | Field = {} | Value = {}".format(reg, pattern, "None"))
        return "not_available"

    return parser

  def collect(self):
    """ Collect all metadata. """

    _log.info("Collecting the full metadata information.")

    self.collect_base()
    self._save("SW", self.collect_SW())
    self._save("HW", self.collect_HW())

  def collect_HW(self):
    """ Collect Hardware specific metadata. """

    _log.info("Collecting HW information.")

    HW = {
      "CPU"     : self.collect_cpu(),
      "BIOS"    : self.collect_bios(),
      "SYSTEM"  : self.collect_system(),
      "MEMORY"  : self.collect_memory(),
      "STORAGE" : self.collect_storage()
    }
    return HW

  def dump(self, stdout=False, outfile=False):
    """ Dump data to stdout and json file. """
    meta_data = json.dumps(self.data, indent=4)

    if stdout:
      print(meta_data)

    # Dump json data to file
    if outfile != False:
      with open(outfile, 'w') as json_file:
        json.dump(self.data, json_file, indent=4, sort_keys=True)

  def export(self):
    """ Export collected data as a dict """

    return self.data

  def _extract(self, cmd_dict):
    """ Extract the data given a dict with commands """
    data = {}
    for key, val in cmd_dict.items():
      self.data[key] = self.exec_cmd(val)

    return data

  def _save(self, tag, new_data):
    """ Save a given dict to the final data dict """
    self.data[tag] = new_data