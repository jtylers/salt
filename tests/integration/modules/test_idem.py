# -*- coding: utf-8 -*-
"""
Integration tests for the idem execution module
"""

# Import futures
from __future__ import absolute_import, print_function, unicode_literals

# Import Python libs
import logging

# Import salt libs
import salt.modules.idem
import salt.utils.path

# Import salt testing libs
from tests.support.case import ModuleCase
from tests.support.unit import skipIf

log = logging.getLogger(__name__)


@skipIf(not salt.modules.idem.HAS_LIBS[0], salt.modules.idem.HAS_LIBS[1])
@skipIf(not salt.utils.path.which("idem"), "idem is not installed")
class IdemTestCase(ModuleCase):
    """
    Validate the idem module
    """

    def test_exec(self):
        ret = self.run_function("idem.exec", ["test.ping"])
        assert ret is True
