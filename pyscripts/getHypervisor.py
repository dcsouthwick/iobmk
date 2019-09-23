#!/usr/bin/env python

import SOAPpy
import socket

import argparse
import time
import os
import logging
import sys

logging.basicConfig(stream=sys.stdout,level=logging.INFO)
logger = logging.getLogger('[getHypervisor]')

if __name__ == '__main__':
    """ Script  to extractfrom LandDB the  name of hte physica node where the VM is running"""

    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("--endpoint", required=True, default='', help="soap endpoint")
        parser.add_argument("--namespace", required=True, default='', help="network service")
        parser.add_argument("--user", required=True, default='', help="username")
        parser.add_argument("--passwd", required=True, default='', help="password")
        parser.add_argument("--host", default=socket.gethostname().replace(".cern.ch",""), help="hostname")
        args = parser.parse_args()
        
        SOAPserver=SOAPpy.SOAPProxy(args.endpoint, namespace=args.namespace)
        #Get the auth token
        atoken=SOAPserver.getAuthToken(args.user,args.passwd,"NICE")
        #Build the auth header
        authStruct=SOAPpy.structType(data = {"token" :atoken})
        authStruct._ns1=("ns1","urn:NetworkService")
        authHeader=SOAPpy.headerType(data = {"Auth":authStruct})
        SOAPserver.header=authHeader
        print SOAPserver.vmGetInfo(args.host).VMParent
    except Exception as e:
        print "foo"
        raise e
