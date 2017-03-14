#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Action Module server

This uses the `Circuits <http://circuitsframework.com/>` framework to
listen on multiple message destinations, send their events to the relevant
handlers, and acknowledge the messages when they have been processed.

"""

from __future__ import print_function

import logging
import os
import filelock
from logging.handlers import RotatingFileHandler
from resilient_circuits.component_loader import ComponentLoader
from resilient_circuits.actions_component import Actions, ResilientComponent
from circuits import Component, Debugger
import resilient_circuits.keyring_arguments as keyring_arguments


# The run() method uses a file lock to prevent multiple simultaneous processes
# running in the same directory.  You can override the lockfile name in the
# (and so allow multiple) by setting APP_LOCK_FILE in the environment.
APP_LOCK_FILE = os.environ.get("APP_LOCK_FILE", "")


def log(log_level):
    logging.getLogger().setLevel(log_level)


# The config file location should usually be set in the environment
APP_CONFIG_FILE = os.environ.get("APP_CONFIG_FILE", None)
APP_LOG_DIR = os.environ.get("APP_LOG_DIR", "logs")

application = None


class AppArgumentParser(keyring_arguments.ArgumentParser):
    """Helper to parse command line arguments."""
    DEFAULT_STOMP_PORT = 65001
    DEFAULT_COMPONENTS_DIR = ''
    DEFAULT_LOG_LEVEL = 'INFO'
    DEFAULT_LOG_FILE = 'app.log'
    DEFAULT_NO_PROMPT_PASS = "False"

    def __init__(self):
        if not APP_CONFIG_FILE:
            if os.path.exists("app.config"):
                config_file = "app.config"
            else:
                config_file = os.path.expanduser(os.path.join("~", ".resilient", "app.config"))
        else:
            config_file = APP_CONFIG_FILE
        super(AppArgumentParser, self).__init__(config_file=config_file)
        default_stomp_port = self.getopt("resilient", "stomp_port") or self.DEFAULT_STOMP_PORT
        default_components_dir = self.getopt("resilient", "componentsdir") or self.DEFAULT_COMPONENTS_DIR
        default_noload = self.getopt("resilient", "noload") or ""
        default_log_dir = self.getopt("resilient", "logdir") or APP_LOG_DIR
        default_log_level = self.getopt("resilient", "loglevel") or self.DEFAULT_LOG_LEVEL
        default_log_file = self.getopt("resilient", "logfile") or self.DEFAULT_LOG_FILE
        default_no_prompt_password = self.getopt("resilient",
                                                 "no_prompt_password") or self.DEFAULT_NO_PROMPT_PASS
        default_no_prompt_password = self._is_true(default_no_prompt_password)
        default_test_actions = self._is_true(self.getopt("resilient",
                                                         "test_actions")) or False
        default_resilient_mock = self.getopt("resilient",
                                             "resilient_mock") or None
        default_test_host = self.getopt("resilient", "test_host") or None
        default_test_port = self.getopt("resilient", "test_port") or None
        default_log_responses = self.getopt("resilient",
                                            "log_http_responses") or ""

        self.add_argument("--stomp-port",
                          type=int,
                          default=default_stomp_port,
                          help="Resilient server STOMP port number")
        self.add_argument("--componentsdir",
                          type=str,
                          default=default_components_dir,
                          help="Circuits components auto-load directory")
        self.add_argument("--noload",
                          type = str,
                          default=default_noload,
                          help = "List of components that should not be loaded")
        self.add_argument("--logdir",
                          type=str,
                          default=default_log_dir,
                          help="Directory for log files")
        self.add_argument("--loglevel",
                          type=str,
                          default=default_log_level,
                          help="Log level")
        self.add_argument("--logfile",
                          type=str,
                          default=default_log_file,
                          help="File to log to")
        self.add_argument("--no-prompt-password",
                          type=bool,
                          default=default_no_prompt_password,
                          help="Never prompt for password on stdin")
        self.add_argument("--test-actions",
                          action="store_true",
                          default=default_test_actions,
                          help="Enable submitting test actions?")
        self.add_argument("--resilient-mock",
                          type=str,
                          action="store",
                          default=default_resilient_mock,
                          help=("Mock class defintion. "
                                "(lib/my_mock_file.MyMockClass)"))
        self.add_argument("--test-host",
                          type=str,
                          action="store",
                          default=default_test_host,
                          help=("For use with --test-actions option. "
                                "Host or IP to bind test server to."))
        self.add_argument("--test-port",
                          type=int,
                          action="store",
                          default=default_test_port,
                          help=("For use with --test-actions option. "
                                "Port to bind test server to."))
        self.add_argument("--log-http-responses",
                          type=str,
                          default=default_log_responses,
                          help=("Log all responses from Resilient "
                                "REST API to this directory"))

    def parse_args(self, args=None, namespace=None):
        """Parse commandline arguments and construct an opts dictionary"""
        opts = super(AppArgumentParser, self).parse_args(args, namespace)
        if self.config:
            for section in self.config.sections():
                items = dict((item.lower(), self.config.get(section, item)) for item in self.config.options(section))
                opts.update({section: items})
        return opts

    @staticmethod
    def _is_true(value):
        if value:
            return value.lower()[0] in ("1", "t", "y")
        else:
            return False


# Main component for our application
class App(Component):
    """Our main app component, which sets up the Resilient services and other components"""

    FILE_LOG_FORMAT = '%(asctime)s %(levelname)s [%(module)s] %(message)s'
    SYSLOG_LOG_FORMAT = '%(module)s: %(levelname)s %(message)s'
    STDERR_LOG_FORMAT = '%(asctime)s %(levelname)s [%(module)s] %(message)s'

    def __init__(self, auto_load_components=True):
        super(App, self).__init__()
        # Read the configuration options
        self.action_component = None
        self.component_loader = None
        self.auto_load_components = auto_load_components
        self.do_initialization()

    def do_initialization(self):
        self.opts = AppArgumentParser().parse_args()

        self.config_logging(self.opts["logdir"], self.opts["loglevel"],
                            self.opts['logfile'])
        LOG.info("Configuration file is %s", APP_CONFIG_FILE)
        LOG.info("Resilient user: %s", self.opts.get("email"))
        LOG.info("Resilient org: %s", self.opts.get("org"))

        if self.opts.get("test_actions", False):
            # Make all components aware that we are in test mode
            ResilientComponent.test_mode = True

        # Connect to events from Action Module.
        # Note: this must be done before components are loaded, because it uses
        # each component's "channel" to initiate subscription to the message queue.
        self.action_component = Actions(self.opts)
        self.action_component.register(self)

        # Register a `loader` to dynamically load
        # all Circuits components in the 'componentsdir' directory
        if self.auto_load_components:
            LOG.info("Components auto-load directory: %s",
                     self.opts["componentsdir"])
            self.component_loader = ComponentLoader(self.opts)
            self.component_loader.register(self)

    def config_logging(self, logdir, loglevel, logfile):
        """ set up some logging """
        global LOG_PATH, LOG
        LOG_PATH = os.path.join(logdir, logfile)
        LOG_PATH = os.path.expanduser(LOG_PATH)
        LOG = logging.getLogger(__name__)

        # Ignore syslog errors from message-too-long
        logging.raiseExceptions = False

        try:
            numeric_level = getattr(logging, loglevel)
            logging.getLogger().setLevel(numeric_level)
        except AttributeError as e:
            logging.getLogger().setLevel(logging.INFO)
            LOG.warning("Invalid logging level specified. Using INFO level")

        if logging.getLogger().getEffectiveLevel() == logging.DEBUG:
            self += Debugger()
            logging.getLogger("stomp.py").setLevel(logging.DEBUG)
        else:
            # STOMP is too noisy by default
            logging.getLogger("stomp.py").setLevel(logging.WARN)

        file_handler = RotatingFileHandler(LOG_PATH, maxBytes=10000000,
                                           backupCount=10)
        file_handler.setFormatter(logging.Formatter(self.FILE_LOG_FORMAT))
        logging.getLogger().addHandler(file_handler)
        syslog = logging.handlers.SysLogHandler()
        syslog.setFormatter(logging.Formatter(self.SYSLOG_LOG_FORMAT))
        logging.getLogger().addHandler(syslog)
        stderr = logging.StreamHandler()
        stderr.setFormatter(logging.Formatter(self.STDERR_LOG_FORMAT))
        logging.getLogger().addHandler(stderr)

    def load_all_success(self, event):
        """OK, component loader says we're ready"""
        LOG.info("Components loaded")

    def load_all_failure(self, event):
        """OK, component loader says we're unable to start"""
        LOG.error("A component failed to load.  The application cannot start.")
        self.stop()

    def reload_opts(self):
        """Reload the configuration options in case they changed"""
        LOG.debug("Reload opts")
        self.opts.update(AppArgumentParser().parse_args())

    def started(self, event, component):
        """Started Event Handler"""
        LOG.info("App Started")

    def stopped(self, event, component):
        """Stopped Event Handler"""
        LOG.info("App Stopped")


def run(*args, **kwargs):
    """Main app"""

    # define lock
    # this prevents multiple, identical circuits from running at the same time
    if not APP_LOCK_FILE:
       lockfile = os.path.expanduser(os.path.join("~", ".resilient", "resilient_circuits_lockfile"))
       resilient_dir = os.path.dirname(lockfile)
       if not os.path.exists(resilient_dir):
           oks.makedirs(resilient_dir)
    else:
        lockfile =  os.path.expanduser(APP_LOCK_FILE)
    lock = filelock.FileLock(lockfile)

    # The main app component initializes the Resilient services
    global application
    try:
        # attempt to lock file, wait 1 second for lock
        with lock.acquire(timeout=1):
            assert lock.is_locked
            application = App(*args, **kwargs)
            application.run()

    except filelock.Timeout:
        # file is probably already locked
        print("Failed to acquire lock on {0} - you may have another instance of Resilient Circuits running".format(os.path.abspath(lockfile)))
    except OSError as exc:
        # Some other problem accessing the lockfile
        print("Unable to lock {0}: {1}".format(os.path.abspath(lockfile), exc))
    # finally:
    #    LOG.info("App finished.")


if __name__ == "__main__":
    run()
