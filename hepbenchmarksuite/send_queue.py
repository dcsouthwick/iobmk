###############################################################################
# Copyright 2019-2020 CERN. See the COPYRIGHT file at the top-level directory
# of this distribution. For licensing information, see the COPYING file at
# the top-level directory of this distribution.
###############################################################################

import stomp
import argparse
import time
import os
import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger('[send_queue]')

# TODO: handle None keys in passed conn args
# TODO: test wait=true on connect() in firewalled nodes
# This is supported in stomp...


class MyListener(stomp.ConnectionListener):
    def __init__(self, conn):
        self.conn = conn
        self.status = True
        self.message = ''

    def on_error(self, headers, message):
        logger.error('received an error \n%s' % message)
        self.status = False
        self.message = message

    def on_message(self, headers, message):
        logger.info('received a message "%s"' % message)


def send_message(filepath, connection):
    """ expects a filepath string, and a dict of args"""

    if os.path.isfile(filepath) is False:
        raise IOError("The result input file {} does not exist"
                      .format(filepath))

    with open(filepath, 'r') as f:
        message_contents = f.read()

    conn = stomp.Connection(host_and_ports=[(connection['server'],
                                            int(connection['port']))])
    conn.set_listener('mylistener', MyListener(conn))
    conn.start()

    if 'key' in connection and 'cert' in connection:
        conn.set_ssl(for_hosts=[connection['server']],
                     cert_file=connection['cert'],
                     key_file=connection['key'],
                     # TODO: verify SSL support
                     ssl_version=5)  # <_SSLMethod.PROTOCOL_TLSv1_2: 5>
        conn.connect(wait=True)
        logger.info("AMQ SSL: certificate based authentication")
    elif 'username' in connection and 'password' in connection:
        conn.connect(connection['username'], connection['password'], wait=True)
        logger.info("AMQ Plain: user-password based authentication")
    else:
        raise IOError("The input arguments do not include a valid pair of authentication\
                     (certificate, key) or (user,password)")

    logger.info("Sending results to AMQ topic")
    conn.start()
    time.sleep(5)
    conn.send(connection['topic'], message_contents, "application/json")

    time.sleep(5)

    if conn.get_listener('mylistener').status is False:
        raise Exception("ERROR: {}".format(conn.get_listener('mylistener').message))
    conn.stop()
    conn.disconnect()

    logger.info("Results sent to AMQ topic")


def main():
    parser = argparse.ArgumentParser(
        prog='send_queue',
        description="This sends a file.json to an AMQ broker via STOMP. \
            Default STOMP port is 61613, if not overridden")
    parser.add_argument("-p", "--port",     required=True, type=int, help="Queue port")
    parser.add_argument("-s", "--server",   required=True, help="Queue host")
    parser.add_argument("-u", "--username", nargs='?', default=None, help="Queue username")
    parser.add_argument("-w", "--password", nargs='?', default=None, help="Queue password")
    parser.add_argument("-t", "--topic",    required=True, help="Queue name")
    parser.add_argument("-k", "--key",      nargs='?', default=None, help="AMQ authentication key")
    parser.add_argument("-c", "--cert",     nargs='?', default=None, help="AMQ authentication certificate")
    parser.add_argument("-f", "--file",     required=True, help="File to send")
    args = parser.parse_args()

    # Get non-None cli arguments
    non_empty = {k: v for k, v in vars(args).items() if v is not None}

    # Populate active config with cli override
    connection_details = {}
    for i in non_empty.keys():
        connection_details[i] = non_empty[i]

    send_message(args.file, connection_details)


if __name__ == '__main__':
    main()
