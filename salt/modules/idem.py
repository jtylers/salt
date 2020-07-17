# -*- coding: utf-8 -*-
#
# Author: Tyler Johnson <tjohnson@saltstack.com>
#

"""
Idem Support
============

This module provides access to idem execution modules
"""
from __future__ import absolute_import, print_function, unicode_literals

import logging
import sys

try:
    import pop.hub

    HAS_LIBS = True, None
except ImportError as e:
    HAS_LIBS = False, e

log = logging.getLogger(__name__)

# Function alias to make sure not to shadow built-in's
__func_alias__ = {"exec_": "exec"}
__virtualname__ = "idem"


def __virtual__():
    if sys.version_info < (3, 6):
        return False, "idem only works on python3.6 and later"
    if not HAS_LIBS[0]:
        return HAS_LIBS
    return __virtualname__


def __init__(opts):
    if "idem.hub" not in __context__:
        # Initialize the hub
        log.debug("Creating the POP hub")
        hub = pop.hub.Hub()
        log.debug("Initializing the loop")
        hub.pop.loop.create()
        # Load idem grains/states/exec modules onto the hub
        log.debug("Loading subs onto hub")
        hub.pop.sub.add(dyne_name="acct")
        hub.pop.sub.add(dyne_name="config")
        hub.pop.sub.add(dyne_name="idem")
        hub.pop.sub.add(dyne_name="exec")
        hub.pop.sub.add(dyne_name="states")
        log.debug("Reading idem config options")
        hub.config.integrate.load(["acct", "idem"], "idem", parse_cli=False, logs=False)
        __context__["idem.hub"] = hub


def exec_(path, acct_file=None, acct_key=None, acct_profile=None, *args, **kwargs):
    """
    Call an idem execution module

    .. versionadd:: 3002

    path
        The idem path of the idem execution module to run

    acct_file
        Path to the acct file used in generating idem ctx parameters.
        Defaults to the value in the ACCT_FILE environment variable.

    acct_key
        Key used to decrypt the acct file.
        Defaults to the value in the ACCT_KEY environment variable.

    acct_profile
        Name of the profile to add to idem's ctx.acct parameter.
        Defaults to the value in the ACCT_PROFILE environment variable.

    args
        Any positional arguments to pass to the idem exec function

    kwargs
        Any keyword arguments to pass to the idem exec function

    CLI Example:

    .. code-block:: bash

        salt '*' idem.exec test.ping

    :maturity:      new
    :depends:       acct, pop, pop-config, idem
    :platform:      all
    """
    hub = __context__["idem.hub"]
    coro = hub.idem.ex.run(
        path,
        args,
        {k: v for k, v in kwargs.items() if not k.startswith("__")},
        acct_file=acct_file or hub.OPT.acct.acct_file,
        acct_key=acct_key or hub.OPT.acct.acct_key,
        acct_profile=acct_profile or hub.OPT.acct.acct_profile or "default",
    )
    return hub.pop.Loop.run_until_complete(coro)
