#!/usr/bin/env python3
###############################################################################
# Copyright 2019-2020 CERN. See the COPYRIGHT file at the top-level directory
# of this distribution. For licensing information, see the COPYING file at
# the top-level directory of this distribution.
###############################################################################

from datetime import datetime
import json
import os
import unittest
from unittest.mock import patch, mock_open, MagicMock
from hepbenchmarksuite import send_queue


class TestAMQ(unittest.TestCase):
    """
    AMQ send_queue functionality
    Reads a minimal test json format2.0 from data/
    """
    # get CI environment args.
    # TODO(anyone): fix for testing without gitlab CI vars
    ci_args = {
        'username': os.getenv('QUEUE_USERNAME'),
        'password': os.getenv('QUEUE_PASSWORD'),
        'server':   os.getenv('QUEUE_HOST'),
        'port':     os.getenv('QUEUE_PORT'),
        'topic':    os.getenv('QUEUE_NAME'),
        'cert':     os.getenv('CERT_FILE'),
        'key':      os.getenv('KEY_FILE')
    }

    def genJSON(self, message="None"):
        """Generate JSON with passed message, return its path"""
        self.assertTrue(isinstance(message, str),
                        'Message is not a string')
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        self.test_json['_timestamp'] = self.test_json['_timestamp_end'] = timestamp
        self.test_json['host']['freetext'] = message
        with open(self.test_file_path, 'w') as profile:
            profile.write(json.dumps(self.test_json))
        return (self.test_json)

    def setUp(self):
        """Collect CI env and setup testing objects"""

        self.test_dir = os.path.join(os.getcwd(), "tests/")
        self.test_file_path = os.path.join(self.test_dir, "/data/result_profile.json")

        # TODO(anyone): add better test json2.0 with other results
        with open(self.test_dir + "data/result_profile_db12.json", "r") as t:
            self.test_json = json.loads(t.read())
        self.assertTrue(isinstance(self.test_json, dict))

    @patch('builtins.open', new_callable=mock_open())
    def test_genJSON(self, mock_open_file):
        """Test if the json creation is successfull."""

        ret = self.genJSON("testString")

        mock_open_file.assert_called_once_with(self.test_file_path, 'w')
        mock_open_file.return_value.__enter__().write.assert_called_once_with(json.dumps(self.test_json))
        self.assertDictEqual(ret, self.test_json)
        self.assertEqual(ret['host']['freetext'], "testString")

    def test_parser(self):
        """Command-line arguments test"""
        parser = send_queue.parse_args(
            ['-p', '1',
             '-s', 'google.com',
             '-u', 'mickey',
             '-w', 'mouse',
             '-t', 'hepscore',
             '-k', 'd',
             '-c', 'cert:SSA!~!@',
             '-f', 'howto.json'])
        self.assertEqual(parser.port, 1)
        self.assertEqual(parser.server, "google.com")
        self.assertEqual(parser.username, "mickey")
        self.assertEqual(parser.password, "mouse")
        self.assertEqual(parser.topic, "hepscore")
        self.assertEqual(parser.key, "d")
        self.assertEqual(parser.cert, "cert:SSA!~!@")
        self.assertEqual(parser.file, "howto.json")

        parser = send_queue.parse_args(['-s', 'www', '-t', 'topic', '-f', 'foobar'])
        self.assertEqual(parser.port, 61613)
        self.assertEqual(parser.server, "www")
        self.assertEqual(parser.username, None)
        self.assertEqual(parser.password, None)
        self.assertEqual(parser.topic, "topic")
        self.assertEqual(parser.key, None)
        self.assertEqual(parser.cert, None)
        self.assertEqual(parser.file, "foobar")

        with self.assertRaises(SystemExit) as cm:
            parser = send_queue.parse_args([])
            self.assertEqual(cm.exception.code, 2)

        with self.assertRaises(SystemExit) as cm:
            parser = send_queue.parse_args(['-s'])
            self.assertEqual(cm.exception.code, 2)

        with self.assertRaises(SystemExit) as cm:
            parser = send_queue.parse_args(['-s', 'www', '-t', 'topic', '-f', 'foobar', '--port', "fifteen"])
            self.assertEqual(cm.exception.code, 2)

    def test_send_queue_commandline(self):
        """Pass command line arguments to send_queue"""
        mock_result = send_queue.argparse.Namespace(
            cert=None, file='test.json',
            key=None, password=None,
            port=111, server='google.com',
            topic='a', username=None)
        with patch.object(send_queue, 'parse_args', return_value=mock_result):
            real = send_queue
            real.send_message = MagicMock()
            real.main()
            real.send_message.assert_called_once_with('test.json', {'port': 111, 'server': 'google.com', 'topic': 'a'})

    @patch('hepbenchmarksuite.send_queue.MyListener', autospec=True)
    @patch('hepbenchmarksuite.send_queue.os.path', return_value=True)
    @patch('hepbenchmarksuite.send_queue.stomp', autospec=True)
    def test_send_message(self, mock_stomp, mock_filecheck, mock_listener):
        """Pass config object to send_queue"""
        test_args = {'port': 8181, 'server': 'home.cern', 'topic': 'test'}
        mock_conn = MagicMock()
        mock_stomp.Connection.return_value = mock_conn

        with self.assertRaises(FileNotFoundError) as cm:
            # test bad filepath
            send_queue.send_message(self.test_file_path, test_args)
            self.assertEqual(cm.exception.code, 2)

        with patch('hepbenchmarksuite.send_queue.open', mock_open(read_data="{'test':1}")) as mock_json:

            # Test no credentials
            with self.assertRaises(OSError) as cm:
                send_queue.send_message(self.test_file_path, test_args)
                mock_json.assert_called_once_with(self.test_file_path)
            mock_stomp.Connection.assert_called_once_with(host_and_ports=[(test_args['server'],
                                                                           int(test_args['port']))])
            mock_conn.set_listener.assert_called_once_with('mylistener', mock_listener)
            # TODO(anyone): logging tests
            # Test good credentials
            test_args = {'port': 8181, 'server': 'home.cern', 'topic': 'test', 'username': "Dave", 'password': "password"}
            #with self.assertLogs('hepbenchmarksuite.send_queue.logging.logger', level='INFO') as cm:
            #    send_queue.send_message(self.test_file_path, test_args)
                # self.assertEqual(cm.output, ['INFO:[send_queue]:AMQ Plain: user-password based authentication'])



        #self.mock_filecheck.isfile.assert_called_once_with(self.test_file_path)
        # self.mock_logger.warn.assert_called_with("
        #self.assertTrue(mock_logger.warn.called)


    # def test_bad_UN_PW(self):

    # def test_missing_topic(self):
    # def test_wrong_topic(self):
    # def test_wrong_cert(self):
    # def test_cert_UN_PW(self):
    # def test_success(self):


if __name__ == '__main__':
    unittest.main(verbosity=2)
