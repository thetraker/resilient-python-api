# (c) Copyright IBM Corp. 2010, 2017. All Rights Reserved.
"""Circuits component for Action Module subscription and message handling"""

import json
import re
import os.path
import random
import datetime
import logging
from circuits import Event, Timer

LOG = logging.getLogger(__name__)


class ActionMessageBase(Event):
    """Superclass for :class:`ActionMessage` and :class:`FunctionMessage`.
    """

    def __init__(self, source=None, headers=None, message=None,
                 test=False, test_msg_id=None, frame=None, log_dir=None):
        super(ActionMessageBase, self).__init__(source=source,
                                                headers=headers,
                                                message=message)
        if headers is None:
            headers = {}
        if message is None:
            message = {}
        LOG.debug("Source: %s", source)
        LOG.debug("Headers: %s", json.dumps(headers, indent=2))
        LOG.debug("Message: %s", json.dumps(message, indent=2))

        self.deferred = False
        self.message = message
        self.frame = frame
        self.context = headers.get("Co3ContextToken")
        self.action_id = message.get("action_id")
        self.object_type = message.get("object_type")
        self.test = test
        self.test_msg_id = test_msg_id

        self.timestamp = None
        ts = headers.get("timestamp")
        if ts is not None:
            self.timestamp = datetime.datetime.utcfromtimestamp(float(ts)/1000)

        self.name = "_unknown_"
        self.displayname = "Unknown"

        # Fire a {name}_success event when this event is successfully processed
        self.success = True

    def __repr__(self):
        "x.__repr__() <==> repr(x)"
        if len(self.channels) > 1:
            channels = repr(self.channels)
        elif len(self.channels) == 1:
            channels = str(self.channels[0])
        else:
            channels = ""
        return "<%s[%s] (%s) %s>" % (self.name, channels,
                                     self.action_id, self.timestamp)

    def __getattr__(self, name):
        """Message attributes are made accessible as properties
           ("incident", "task", "note", "milestone". "task", "artifact";
           and "properties" for the action fields on manual actions)
        """
        if name == "message":
            raise AttributeError()
        try:
            return self.message[name]
        except KeyError:
            raise AttributeError()

    def hdr(self):
        """Get the headers (dict)"""
        return self.kwargs["headers"]

    def msg(self):
        """Get the message (dict)"""
        return self.kwargs["message"]

    def defer(self, component, delay=None):
        """Defer this message for handling later"""
        if self.deferred:
            # This message was already deferred.  You should just handle it.
            # (Mark it as no longer deferred, so that it will ack now)
            self.deferred = False
            return False
        # Fire me again after a dela
        if delay is None:
            delay = 0.5 + random.random()
        self.deferred = True
        LOG.debug("Deferring %s (%s)", self, self.hdr().get("message-id"))
        Timer(delay, self).register(component)
        return True

    def _log_message(self, log_dir):
        """Log Message JSON to File"""
        filename = "_".join((self.__class__.name, self.displayname,
                             datetime.datetime.now().isoformat())).replace('/', '_').replace(':', '-')
        with open(os.path.join(log_dir,
                               filename.format("JSON")), "w+") as logfile:
            logfile.write(json.dumps(self.message, indent=2))


class ActionMessage(ActionMessageBase):
    """A Circuits event for a Resilient Action Module message.

    This event holds details of the Action Module message,
    including its context (the incident, task, artifact... where the action
    was triggered).  Your components will receive these events from the
    Resilient Action Module message destination.

    These events are named by the rule that triggered them (lowercased).
    So a custom action rule named "Manual Action" will generate an event with name
    "manual_action".  To handle that event, you should implement a :class:`ResilientComponent`
    that has a method named :samp:`manual_action`:  the Circuits framework will call
    your component's methods based on the name of the event.

    The parameters for your event-handler method are:
       * event: this event object
       * source: the component that fired the event
       * headers: the Action Module message headers (dict)
       * message: the Action Module message (dict)
    For convenience, the message is also broken out onto event properties,
       * event.incident: the incident that the event relates to
       * event.artifact: the artifact that the event was triggered from (if any)
       * event.task: the task that the event was triggered from (if any)
         (etc).

    To have your component's method with a different name from the action,
    you can use the :func:`handler` decorator:

    .. code-block:: python

        @handler("the_action_name")
        def _any_method_name(self, event, source=None, headers=None, message=None):
            ...

    To have a method handle *any* event on the component's channel,
    use the :func:`handler` decorator with no event name,

    .. code-block:: python

        @handler()
        def _any_method_name(self, event, source=None, headers=None, message=None):
            ...

    Refer to the developer documentation for additional details on writing components and event handlers.
    """

    def __init__(self, source=None, headers=None, message=None,
                 test=False, test_msg_id=None, frame=None, log_dir=None):
        super(ActionMessage, self).__init__(source=source,
                                            headers=headers,
                                            message=message,
                                            test=test,
                                            test_msg_id=test_msg_id,
                                            frame=frame,
                                            log_dir=log_dir)

        self.action_id = message.get("action_id")

        if isinstance(source, str):
            # just for testing
            self.displayname = source
        elif source is not None:
            self.displayname = source.action_name(self.action_id)

        # The name of this event (=the function that subscribers implement)
        # is determined from the name of the action.
        # In future, this should be the action's "programmatic name",
        # but for now it's the downcased displayname with underscores.
        self.name = re.sub(r'\W+', '_', self.displayname.strip().lower())

        if message and log_dir:
            self._log_message(log_dir)


class FunctionMessage(ActionMessageBase):
    """A Circuits event for a Resilient Function call.

    This event holds details of the Function message, including its input parameters.
    Your components will receive these events from their Resilient message destination.

    To handle a function, you should implement a :class:`ResilientComponent` with a method
    annotated with the :func:`function` decorator:

    .. code-block:: python

        @function("the_function_name")
        def _any_method_name(self, event, *args, **kwargs):
            ...

    The parameters for your function method are:
       * event: this event object
       * args and kwargs: additional context
    The `event.message` contains:
       * user: details of the user who triggered the function call
       * function: details of the function being called
       * workflow: information about the workflow containing the function
       * inputs: the input parameter values.

    To return a value from your function, yield or return a :class:`FunctionResult` containing
    the value:

    .. code-block:: python

        yield FunctionResult("xyz")

    Refer to the developer documentation for additional details on writing components and event handlers.
    """

    def __init__(self, source=None, headers=None, message=None,
                 test=False, test_msg_id=None, frame=None, log_dir=None):
        super(FunctionMessage, self).__init__(source=source,
                                              headers=headers,
                                              message=message,
                                              test=test,
                                              test_msg_id=test_msg_id,
                                              frame=frame,
                                              log_dir=log_dir)

        fn = message["function"]
        self.action_id = fn.get("id")

        # The name of this event is the API name name of the function.
        self.name = fn.get("name", "_unnamed_")
        self.displayname = fn.get("display_name", self.name)

        if message and log_dir:
            self._log_message(log_dir)


class StatusMessage(object):
    """Encapsulates a status message yielded from an action or function call"""
    def __init__(self, text):
        super(StatusMessage, self).__init__()
        self.text = text

    def __str__(self):
        return self.text or ""


class FunctionResult(object):
    """Encapsulates the result of a function call."""
    def __init__(self, value):
        super(FunctionResult, self).__init__()
        self.value = value


class StatusMessageEvent(Event):
    """Event that we use to send "action status" update back to resilient"""
    def __init__(self, parent=None, message=None):
        super(StatusMessageEvent, self).__init__(message)
        self.parent = parent

    @property
    def text(self):
        """Text of the message"""
        return self.args[0]
