# -*- coding: utf-8 -*-
#
# Author: Tyler Johnson <tjohnson@saltstack.com>
#

"""
Idem Support
============

This state provides access to idem states
"""
from __future__ import absolute_import, print_function, unicode_literals

import logging
import os
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


def _get_refs(hub, sources):
    """
    Determine where the sls sources are
    """
    sls_sources = []
    SLSs = []
    for sls in sources:
        if os.path.isfile(sls):
            if sls.endswith(".sls"):
                ref = sls[:-4]
            else:
                ref = sls
            SLSs.append(ref)
            sls_dir = os.path.dirname(sls)
            implied = f"file://{sls_dir}"
            if implied not in sls_sources:
                sls_sources.append(implied)
        else:
            SLSs.append(sls)
    if hub.OPT.idem.tree:
        tree = f"file://{hub.OPT.idem.tree}"
        if tree not in sls_sources:
            sls_sources.insert(0, tree)
    return sls_sources, SLSs


def state(
    name, sls, test=False, acct_file=None, acct_key=None, acct_profile=None,
):
    """
    Call an idem state through a salt state

    .. versionadd:: 3002

    sls
        A list of idem sls files or sources

    acct_file
        Path to the acct file used in generating idem ctx parameters.
        Defaults to the value in the ACCT_FILE environment variable.

    acct_key
        Key used to decrypt the acct file.
        Defaults to the value in the ACCT_KEY environment variable.

    acct_profile
        Name of the profile to add to idem's ctx.acct parameter
        Defaults to the value in the ACCT_PROFILE environment variable.

    .. code-block:: yaml

        cheese:
          idem.state:
            - idem.sls
            - sls_source

    :maturity:      new
    :depends:       acct, pop, pop-config, idem
    :platform:      all
    """
    hub: pop.Hub = __context__["idem.hub"]

    if isinstance(sls, str):
        sls = [sls]

    sls_sources, SLSs = _get_refs(hub, sls)
    coro = hub.idem.state.apply(
        name=name,
        sls_sources=sls_sources,
        render=hub.OPT.idem.render,
        runtime=hub.OPT.idem.runtime,
        subs=["states"],
        cache_dir=hub.OPT.idem.cache_dir,
        sls=SLSs,
        test=test,
        acct_file=acct_file or hub.OPT.acct.acct_file,
        acct_key=acct_key or hub.OPT.acct.acct_key,
        acct_profile=acct_profile or hub.OPT.acct.acct_profile or "default",
    )
    hub.pop.Loop.run_until_complete(coro)

    errors = hub.idem.RUNS[name]["errors"]
    running = hub.idem.RUNS[name]["running"]

    # This is the bare minimum of what salt looks for in a custom state module
    return {
        "name": name,
        "result": not errors,
        "comment": errors,
        # Attach all the idem state run results to 'changes'
        "changes": running,
    }
