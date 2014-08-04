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

"""
Test date_format.
"""

import os
import datetime
from unittest import TestCase
from supervisor_remote_logging import SyslogFormatter


class SupervisorLoggingDateFormatTestCase(TestCase):
    """
    Tests date format.
    """

    def test_default_date_format(self):
        """
        Test default date format.
        """
        date = datetime.datetime(2000, 1, 1, 1, 0, 0)
        date_format = SyslogFormatter().date_format()
        self.assertEqual(date.strftime(date_format), '2000-01-01T01:00:00')

    def test_custom_date_format(self):
        """
        Test custom date format.
        """
        date = datetime.datetime(2000, 1, 1, 1, 0, 0)
        os.environ['DATE_FORMAT'] = '%b %d %H:%M:%S'
        date_format = SyslogFormatter().date_format()
        self.assertEqual(date.strftime(date_format), 'Jan 01 01:00:00')
        os.environ['DATE_FORMAT'] = SyslogFormatter.DEFAULT_DATE_FORMAT
