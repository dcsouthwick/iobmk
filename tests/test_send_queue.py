#!/usr/bin/env python3
###############################################################################
# Copyright 2019-2020 CERN. See the COPYRIGHT file at the top-level directory
# of this distribution. For licensing information, see the COPYING file at
# the top-level directory of this distribution.
###############################################################################

import argparse
import builtins
from datetime import datetime
from functools import wraps
import json
import logging
import os
import re
import unittest
from unittest.mock import patch, mock_open, call, MagicMock, create_autospec
from hepbenchmarksuite import send_queue


class TestAMQ(unittest.TestCase):
    """
    AMQ send_queue functionality
    Reads a minimal test json format2.0 from data/
    """
    test_config = dict()

    def genJSON(self, message="None"):
        """Generate JSON with passed message as str"""
        self.assertTrue(isinstance(message, str),
                        'Message is not a string')
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        self.test_json['_timestamp'] = self.test_json['_timestamp_end'] = timestamp
        self.test_json['host']['freetext'] = message
        with open(self.test_file_path, 'w') as profile:
            profile.write(json.dumps(self.test_json))

    def setUp(self):
        """Collect CI env and setup testing objects"""

        self.test_dir = os.path.join(os.getcwd(), "tests/")
        self.test_file_path = os.path.join(self.test_dir,
                                           "/data/result_profile.json")

        # TODO(anyone): add newer test json2.0 with other results
        with open(self.test_dir + "data/result_profile_db12.json", "r") as t:
            self.test_json = json.loads(t.read())
        self.assertTrue(isinstance(self.test_json, dict))

        # get CI environment args.
        # TODO(anyone): fix for testing without gitlab CI vars
        self.test_config = {
            'username': os.getenv('QUEUE_USERNAME'),
            'password': os.getenv('QUEUE_PASSWORD'),
            'server':   os.getenv('QUEUE_HOST'),
            'port':     os.getenv('QUEUE_PORT'),
            'topic':    os.getenv('QUEUE_NAME'),
            'cert':     os.getenv('CERT_FILE'),
            'key':      os.getenv('KEY_FILE')
        }

    @patch('builtins.open', new_callable=mock_open())
    def test_genJSON(self, mock_open_file):
        """Test if the json creation is successfull."""

        self.genJSON("test amq user-password")

        mock_open_file.assert_called_once_with(self.test_file_path, 'w')
        mock_open_file.return_value.__enter__().write.assert_called_once_with(json.dumps(self.test_json))

    def test_parser(self):
        parser = send_queue.parse_args(
            ['-p', '1', '-s', 'google.com', '-u', 'mickey', '-w', 'mouse', '-t', 'hepscore', '-k', 'd', '-c', 'cert:SSA!~!@', '-f', 'howto.json'])
        self.assertEqual(parser.port, 1)
        self.assertEqual(parser.server, "google.com")
        self.assertEqual(parser.username, "mickey")
        self.assertEqual(parser.password, "mouse")
        self.assertEqual(parser.topic, "hepscore")
        self.assertEqual(parser.key, "d")
        self.assertEqual(parser.cert, "cert:SSA!~!@")
        self.assertEqual(parser.file, "howto.json")

    @patch.object(send_queue, 'send_message', autospec=True)
    def test_AMQ_commandline(self, mock_send_queue):
        """Pass command line arguments to send_queue via mock"""
        mock_result = argparse.Namespace(cert=None, file='test.json', key=None, password=None, port=111, server='google.com', topic='a', username=None)
        with patch.object(send_queue, 'parse_args', return_value=mock_result) as mock_args:
            real = send_queue
            real.send_message = MagicMock()
            real.main()
            real.send_message.assert_called_once_with('test.json', {'file': 'test.json', 'port': 111, 'server': 'google.com', 'topic': 'a'})

    # @patch('send_queue.send_message')
    # def test_AMQ_call(self):
    #    """Pass config object to send_queue"""

    #    send_queue.send_message()
    #    test_connection = self.test_config
    #    send_queue.send_message(self.test_file, test_connection)
    #    self.assertLogs()

    # def test_bad_UN_PW(self):

    # def test_missing_topic(self):
    # def test_wrong_topic(self):
    # def test_wrong_cert(self):
    # def test_cert_UN_PW(self):
    # def test_success(self):


if __name__ == '__main__':
    unittest.main(verbosity=2)
