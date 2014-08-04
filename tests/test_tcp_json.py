#
# Copyright 2014  Didip Kerabat
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import json
from unittest import TestCase
from supervisor_remote_logging import JsonFormatter, new_tcp_json_handler


class TcpjsonTestCase(TestCase):
    def test_json_format(self):
        record = logging.LogRecord(
            name='foo',
            level=logging.INFO,
            pathname=None,
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        formatted = JsonFormatter().format(record)
        deserialized = json.loads(formatted)
        self.assertEqual(deserialized['name'], record.name)
        self.assertEqual(deserialized['message'], record.msg)
        self.assertTrue(deserialized['asctime'] != None)
        self.assertTrue(deserialized['process'] != None)


    def test_default_values(self):
        handler = new_tcp_json_handler()
        self.assertEqual(handler.host, '127.0.0.1')
        self.assertEqual(handler.port, 5565)
