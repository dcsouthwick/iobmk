#!/usr/bin/env python3

import sys
import shlex
from subprocess import run, Popen, PIPE, STDOUT

def exec_cmd(cmd_str, env=None):
    """Execute a command string and returns its output.

    Args:
      cmd_str: A string with the command to execute.

    Returns:
      A string with the output.
    """
    print("Excuting command: '{}'".format(cmd_str))

    if "|" in cmd_str:
        cmds = cmd_str.split('|')
    else:
        cmds = [cmd_str]

    p = dict()
    try:
        for i, cmd in enumerate(cmds):
            if i == 0:
                p[i] = Popen(shlex.split(cmd), encoding='utf-8', stdout=PIPE, stderr=STDOUT)
            else:
                p[i] = Popen(shlex.split(cmd), encoding='utf-8', stdin=p[i - 1].stdout, stdout=PIPE, stderr=STDOUT)
        
        stdout=''
        line = p[len(cmds) - 1].stdout.readline()
        while line:
            sys.stdout.write(line)
            stdout += line
        #stdout, _ = p[len(cmds) - 1].communicate()
        returncode = p[len(cmds) - 1].wait()
        stdout
    except FileNotFoundError as e:
        returncode = 1
        stderr = e
        pass
    # Check for errors
    if returncode != 0:
        stdout = "not_available"
    else:
        stdout = stdout.rstrip()
        #stdout = stdout.decode('utf-8').rstrip()

    return stdout, returncode

while True:
    print(exec_cmd(input("CMD to run: ")))