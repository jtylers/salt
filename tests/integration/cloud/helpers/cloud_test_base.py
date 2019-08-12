# -*- coding: utf-8 -*-
'''
Tests for the Openstack Cloud Provider
'''

# Import python libs
from __future__ import absolute_import, print_function, unicode_literals
import logging
from time import sleep

# Import Salt Testing libs
from tests.support.case import ShellCase
from tests.support.helpers import generate_random_name

# Import Salt Libs
from salt.ext.six import text_type
from salt.ext.six.moves import range

TIMEOUT = 500

log = logging.getLogger(__name__)


class CloudTest(ShellCase):
    @property
    def instance_name(self):
        if not hasattr(self, '_instance_name'):
            # Create the cloud instance name to be used throughout the tests
            self._instance_name = generate_random_name('cloud-test-').lower()
        return self._instance_name

    def _instance_exists(self, instance_name=None):
        # salt-cloud -a show_instance myinstance
        if not instance_name:
            instance_name = self.instance_name
        query = self.run_cloud('--query')
        log.debug('Checking for "{}" in => {}'.format(instance_name, query))
        return any(instance_name == q.strip(': ') for q in query)

    def assertInstanceExists(self, creation_ret=None, instance_name=None):
        '''
        :param instance_name: Override the checked instance name, otherwise the class default will be used.
        :param creation_ret: The return value from the run_cloud() function that created the instance
        '''
        if not instance_name:
            instance_name = self.instance_name
        if creation_ret:
            self.assertIn(instance_name, [i.strip(': ') for i in creation_ret])
        self.assertTrue(self._instance_exists(instance_name), 'Instance "{}" was not created successfully'
                        .format(instance_name))

    def _destroy_instance(self):
        log.debug('Deleting instance "{}"'.format(self.instance_name))
        delete = self.run_cloud('-d {0} --assume-yes'.format(self.instance_name), timeout=TIMEOUT)
        # example response: ['gce-config:', '----------', '    gce:', '----------', 'cloud-test-dq4e6c:', 'True', '']
        delete_str = ''.join(delete)
        log.debug('Deletion status: {}'.format(delete_str))

        if any([x in delete_str for x in (
            'True',
            'was successfully deleted'
        )]):
            log.debug('Instance "{}" was successfully deleted'.format(self.instance_name))
        elif any([x in delete_str for x in (
            'shutting-down',
            '.delete',
        )]):
            log.debug('Instance "{}" is cleaning up'.format(self.instance_name))
            sleep(30)
        else:
            log.warning('Instance "{}" may not have been deleted properly'.format(self.instance_name))

        # By now it should all be over
        self.assertFalse(self._instance_exists(), 'Could not destroy "{}".  Delete_str: {}'
                         .format(self.instance_name, delete_str))
        log.debug('Instance "{}" no longer exists'.format(self.instance_name))

    def tearDown(self):
        '''
        Clean up after tests, If the instance still exists for any reason, delete it.
        Instances should be destroyed before the tearDown, _destroy_instance() should be called exactly
        one time in a test for each instance created.  This is a failSafe and something went wrong
        if the tearDown is where an instance is destroyed.
        '''
        instance_deleted = True
        tries = 0
        for tries in range(12):
            if self._instance_exists():
                instance_deleted = False
                try:
                    self._destroy_instance()
                    log.debug('Instance "{}" destroyed after {} tries'.format(self.instance_name, tries))
                except AssertionError as e:
                    log.error(e)
                    sleep(30)
            else:
                break
        self.assertFalse(self._instance_exists(), 'Instance exists after multiple attempts to delete: {}'
                         .format(self.instance_name))
        # Complain if the instance was destroyed in this tearDown.
        # Destroying instances in the tearDown is a contingency, not the way things should work by default.
        self.assertTrue(instance_deleted, 'The Instance "{}" was deleted during the tearDown, not the test.  Tries: {}'
                        .format(self.instance_name, tries))
