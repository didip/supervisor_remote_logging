#!/usr/bin/env python
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

from __future__ import print_function

import logging
import logging.handlers
import os
import re
import socket
import sys
import json
import datetime

#Support order in python 2.7 and 3
try:
    from collections import OrderedDict
except ImportError:
    pass

# http://docs.python.org/library/logging.html#logrecord-attributes
RESERVED_ATTRS = (
    'args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
    'funcName', 'levelname', 'levelno', 'lineno', 'module',
    'msecs', 'message', 'msg', 'name', 'pathname', 'process',
    'processName', 'relativeCreated', 'thread', 'threadName'
)

RESERVED_ATTR_HASH = dict(zip(RESERVED_ATTRS, RESERVED_ATTRS))


class FormatterMixin(object):
    HOSTNAME = re.sub(r':\d+$', '', os.environ.get('SITE_DOMAIN', socket.gethostname()))
    DEFAULT_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S%z'
    DEFAULT_MESSAGE_FORMAT = '%(asctime)s %(hostname)s %(name)s[%(process)d]: %(message)s'


    def message_format(self):
        """
        Use user defined message format via
        os.environ['MESSAGE_FORMAT'] or
        DEFAULT_MESSAGE_FORMAT as default.
        """
        fmt = os.environ.get('MESSAGE_FORMAT', self.DEFAULT_MESSAGE_FORMAT)

        return fmt.replace('%(hostname)s', self.HOSTNAME)  # Accepts hostname in the form of %(hostname)s


    def date_format(self):
        """
        Use user defined message format via
        os.environ['DATE_FORMAT'] or
        DEFAULT_DATE_FORMAT as default.
        """
        return os.environ.get('DATE_FORMAT', self.DEFAULT_DATE_FORMAT)


class JsonFormatter(logging.Formatter, FormatterMixin):
    """
    A custom formatter to format logging records as json strings.
    extra values will be formatted as str() if nor supported by
    json default encoder
    """
    def __init__(self, *args, **kwargs):
        """
        :param json_default: a function for encoding non-standard objects
            as outlined in http://docs.python.org/2/library/json.html
        :param json_encoder: optional custom encoder
        """
        self.json_default = kwargs.pop("json_default", None)
        self.json_encoder = kwargs.pop("json_encoder", None)

        kwargs['fmt'] = self.message_format()
        kwargs['datefmt'] = self.date_format()

        super(JsonFormatter, self).__init__(*args, **kwargs)

        if not self.json_encoder and not self.json_default:
            def _default_json_handler(obj):
                '''Prints dates in ISO format'''
                if isinstance(obj, datetime.datetime):
                    return obj.strftime(self.datefmt or '%Y-%m-%dT%H:%M')
                elif isinstance(obj, datetime.date):
                    return obj.strftime('%Y-%m-%d')
                elif isinstance(obj, datetime.time):
                    return obj.strftime('%H:%M')
                return str(obj)
            self.json_default = _default_json_handler

        self._required_fields = self.parse()
        self._skip_fields = dict(zip(self._required_fields, self._required_fields))
        self._skip_fields.update(RESERVED_ATTR_HASH)


    def parse(self):
        """Parses format string looking for substitutions"""
        standard_formatters = re.compile(r'\((.+?)\)', re.IGNORECASE)
        return standard_formatters.findall(self._fmt)


    def merge_record_extra(self, record, target, reserved=RESERVED_ATTR_HASH):
        """
        Merges extra attributes from LogRecord object into target dictionary

        :param record: logging.LogRecord
        :param target: dict to update
        :param reserved: dict or list with reserved keys to skip
        """
        for key, value in record.__dict__.items():
            #this allows to have numeric keys
            if (key not in reserved and not (hasattr(key,"startswith") and key.startswith('_'))):
                target[key] = value
        return target


    def format(self, record):
        """Formats a log record and serializes to json"""
        extras = {}
        if isinstance(record.msg, dict):
            extras = record.msg
            record.message = None
        else:
            record.message = record.getMessage()
        # only format time if needed
        if "asctime" in self._required_fields:
            record.asctime = self.formatTime(record, self.datefmt)

        try:
            log_record = OrderedDict()
        except NameError:
            log_record = {}

        for field in self._required_fields:
            log_record[field] = record.__dict__.get(field)
        log_record.update(extras)
        self.merge_record_extra(record, log_record, reserved=self._skip_fields)

        return json.dumps(log_record, default=self.json_default, cls=self.json_encoder)


class SyslogFormatter(logging.Formatter, FormatterMixin):
    """
    A formatter for the Pallet environment.
    """
    def __init__(self):
        super(SyslogFormatter, self).__init__(fmt=self.message_format(), datefmt=self.date_format())


    def format(self, record):
        message = super(SyslogFormatter, self).format(record)
        return message.replace('\n', ' ') + '\n'


class SysLogHandler(logging.handlers.SysLogHandler):
    """
    A SysLogHandler not appending NUL character to messages
    """
    append_nul = False


def get_headers(line):
    """
    Parse Supervisor message headers.
    """

    return dict([x.split(':') for x in line.split()])


def eventdata(payload):
    """
    Parse a Supervisor event.
    """

    headerinfo, data = payload.split('\n', 1)
    headers = get_headers(headerinfo)
    return headers, data


def supervisor_events(stdin, stdout):
    """
    An event stream from Supervisor.
    """

    while True:
        stdout.write('READY\n')
        stdout.flush()

        line = stdin.readline()
        headers = get_headers(line)

        payload = stdin.read(int(headers['len']))
        event_headers, event_data = eventdata(payload)

        yield event_headers, event_data

        stdout.write('RESULT 2\nOK')
        stdout.flush()


def new_syslog_handler():
    host = os.environ.get('SYSLOG_SERVER', '127.0.0.1')
    port = int(os.environ.get('SYSLOG_PORT', '514'))
    proto = os.environ.get('SYSLOG_PROTO', 'udp')
    socktype = socket.SOCK_DGRAM if proto == 'udp' else socket.SOCK_STREAM

    handler = SysLogHandler(
        address=(host, port),
        socktype=socktype,
    )
    handler.setFormatter(SyslogFormatter())

    return handler


def new_tcp_json_handler():
    host = os.environ.get('TCP_SERVER', '127.0.0.1')
    port = int(os.environ.get('TCP_PORT', '5565'))
    handler = logging.handlers.SocketHandler(host, port)
    handler.setFormatter(JsonFormatter())

    return handler


def new_handler():
    log_type = os.environ.get('SUPERVISOR_LOG_TYPE', 'syslog')
    if log_type == 'tcp_json':
        return new_tcp_json_handler()
    elif log_type == 'syslog':
        return new_syslog_handler()
    else:
        return None


def main():
    handler = new_handler()

    if handler:
        for event_headers, event_data in supervisor_events(sys.stdin, sys.stdout):
            event = logging.LogRecord(
                name=event_headers['processname'],
                level=logging.INFO,
                pathname=None,
                lineno=0,
                msg=event_data,
                args=(),
                exc_info=None,
            )
            event.process = int(event_headers['pid'])
            handler.handle(event)


if __name__ == '__main__':
    main()
