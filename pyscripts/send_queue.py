#
#  Copyright (c) CERN 2016
#
#  Author: Cristovao Cordeiro
# 

try:
    import stomp
except ImportError:
    import sys
    sys.path.append('/cvmfs/sft.cern.ch/lcg/releases/LCG_85swan2/stomppy/3.1.3/x86_64-centos7-gcc49-opt/lib/python2.7/site-packages/')
    import stomp
except:
    print "Couldn't import stomp"
    raise
import argparse
import time
import os
import logging
import sys

logging.basicConfig(stream=sys.stdout,level=logging.INFO)
logger = logging.getLogger('[send_queue]')


class MyListener(stomp.ConnectionListener):
    def __init__(self, conn):
        self.conn = conn
        self.status=True
        self.message=''

    def on_error(self, headers, message):
         logger.error('received an error \n%s' % message)
         self.status=False
         self.message=message
         
    def on_message(self, headers, message):
         logger.info('received a message "%s"' % message)

def send_message(resdoc, args, stomp_mversion):

    if args.key_file != '' and args.cert_file != '':
        ssl_flag = True
        logger.info("AMQ SSL: certificate based authentication")
    elif args.username != '' and args.password != '':
        ssl_flag=False
        logger.info("AMQ Plain: user-password based authentication")
    else:
        raise IOError("The input arguments do not include a valid pair of authentication (certificate, key) or (user,password)")

    conn = stomp.Connection(host_and_ports=[(args.server, int(args.port))], use_ssl=ssl_flag, \
        ssl_key_file=args.key_file, ssl_cert_file=args.cert_file, ssl_version=3)
    
    mylistener = MyListener(conn)
    conn.set_listener('mylistener', mylistener)

    conn.start()
    if ssl_flag:
        conn.connect(wait=True)
    else:
        conn.connect(login=args.username, passcode=args.password, wait=True)

    time.sleep(5)  #This nees to stay before the check of the status, in order to get it

    if stomp_mversion == 3:
        conn.send(resdoc, destination=args.name)
    else:
        conn.send(body=resdoc, destination=args.name)

    time.sleep(5)  #This nees to stay before the check of the status, in order to get it

    if conn.get_listener('mylistener').status == False:
        raise Exception("Error occurred %s" % conn.get_listener('mylistener').message)
    conn.disconnect()


if __name__ == '__main__':
    stomp_mversion = stomp.__version__[0]

    
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port"     ,required=True, default='', help="Queue port")
    parser.add_argument("-s", "--server"   ,required=True, default='', help="Queue host")
    parser.add_argument("-u", "--username" ,nargs='?', default='', help="Queue username")
    parser.add_argument("-w", "--password" ,nargs='?', default='', help="Queue password")
    parser.add_argument("-n", "--name"     ,required=True, default='', help="Queue name")
    parser.add_argument("-k", "--key_file" ,nargs='?', default='', help="AMQ authentication key")
    parser.add_argument("-c", "--cert_file",nargs='?', default='', help="AMQ authentication certificate")
    parser.add_argument("-f", "--file"     ,required=True, help="File to send")
    args = parser.parse_args()

    if os.path.isfile(args.file) == False:
        raise IOError("The result input file %s does not exist" %args.file)

    resdoc = open(args.file,'r').read()

    logger.info("Sending results to AMQ topic")
    send_message(resdoc, args, stomp_mversion)
    logger.info("Results sent to AMQ topic")
    