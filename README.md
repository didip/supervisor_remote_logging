supervisor-remote-logging
=========================

A [supervisor] plugin to stream events to remote endpoints.

Installation
------------

```
pip install supervisor-remote-logging
```

SYSLOG
------

The Syslog instance to send the events to is configured with the environment variables:

* `SYSLOG_SERVER`
* `SYSLOG_PORT`
* `SYSLOG_PROTO`

TCP JSON
--------

The TCP instance to send the events to is configured with the environment variables:

* `TCP_SERVER`
* `TCP_PORT`

Add the plugin as an event listener:

```
[eventlistener:logging]
command = supervisor_logging
events = PROCESS_LOG
```

[supervisor]: http://supervisord.org/
