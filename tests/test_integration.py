#
# Copyright 2014  Didip Kerabat
# Copyright 2014  Infoxchange Australia
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

"""
Test supervisor_logging.
"""

import os
import re
import socket
import SocketServer as socketserver
import subprocess
import threading

from time import sleep

from unittest import TestCase
import supervisor_remote_logging


def strip_volatile(message):
    """
    Strip volatile parts (PID, datetime) from a logging message.
    """

    volatile = (
        (socket.gethostname(), 'HOST'),
        (r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}-\d{4}', 'DATE'),
    )

    for regexp, replacement in volatile:
        message = re.sub(regexp, replacement, message)

    return message


class IntegrationTestCase(TestCase):
    def setUp(self):
        self.old_env = os.environ.copy()


    def tearDown(self):
        os.environ = self.old_env


    def test_syslog_logging(self):
        """
        Test logging.
        """

        messages = []

        class SyslogHandler(socketserver.BaseRequestHandler):
            """
            Save received messages.
            """

            def handle(self):
                messages.append(self.request[0].strip().decode())

        syslog = socketserver.UDPServer(('0.0.0.0', 0), SyslogHandler)
        try:
            threading.Thread(target=syslog.serve_forever).start()

            os.environ['SYSLOG_SERVER'] = syslog.server_address[0]
            os.environ['SYSLOG_PORT'] = str(syslog.server_address[1])
            os.environ['SYSLOG_PROTO'] = 'udp'

            mydir = os.path.dirname(__file__)

            supervisor = subprocess.Popen(
                ['supervisord', '-c', os.path.join(mydir, 'supervisord.conf')],
                env=os.environ,
            )
            try:
                sleep(3)

                print subprocess.check_output(['supervisorctl', 'status'])

                pid = subprocess.check_output(
                    ['supervisorctl', 'pid', 'messages']
                ).strip()

                sleep(8)

                print messages

                self.assertEqual(
                    list(map(strip_volatile, messages)),
                    ['<14>DATE HOST messages[{pid}]: Test {i} \n\x00'.format(pid=pid, i=i) for i in range(4)]
                )
            finally:
                supervisor.terminate()

        finally:
            syslog.shutdown()


    def test_new_handler(self):
        handler = supervisor_remote_logging.new_handler()
        self.assertTrue(isinstance(handler, supervisor_remote_logging.SysLogHandler))

        os.environ['SUPERVISOR_LOG_TYPE'] = 'tcp_json'

        handler = supervisor_remote_logging.new_handler()
        self.assertEqual(handler.host, '127.0.0.1')
        self.assertEqual(handler.port, 5565)

