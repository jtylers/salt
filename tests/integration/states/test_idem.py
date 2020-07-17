# -*- coding: utf-8 -*-
"""
Tests for the idem state
"""
# Import futures
from __future__ import absolute_import, print_function, unicode_literals

# Import Python libs
import logging
import tempfile

# Import salt libs
import salt.states.idem
import salt.utils.path

# Import salt testing libs
from tests.support.case import ModuleCase
from tests.support.mixins import SaltReturnAssertsMixin
from tests.support.unit import skipIf

log = logging.getLogger(__name__)

SLS_SUCCEED_WITHOUT_CHANGES = """
state_name:
  test.succeed_without_changes:
    - name: idem_test
    - foo: bar
"""


@skipIf(not salt.states.idem.HAS_LIBS[0], salt.states.idem.HAS_LIBS[1])
@skipIf(not salt.utils.path.which("idem"), "idem is not installed")
class IdemTest(ModuleCase, SaltReturnAssertsMixin):
    """
    Validate the idem state
    """

    def test_state(self):
        with tempfile.NamedTemporaryFile(suffix=".sls", delete=True, mode="w+") as fh:
            fh.write(SLS_SUCCEED_WITHOUT_CHANGES)
            fh.flush()
            ret = self.run_state("idem.state", name="idem_test", sls=fh.name)
        self.assertSaltTrueReturn(ret)
        # The result of the idem state run will be the first value in the changes dict
        idem_state_run_ret = tuple(ret.values())[0]["changes"]
        self.assertSaltTrueReturn(idem_state_run_ret)
