# -*- coding: utf-8 -*-
'''
Integration tests for functions located in the salt.cloud.__init__.py file.
'''

# Import Python Libs
from __future__ import absolute_import, print_function, unicode_literals

# Import Salt Testing libs
from tests.integration.cloud.helpers.cloud_test_base import CloudTest

# Import Salt libs
import salt.cloud


class CloudClientTest(CloudTest):
    '''
    Integration tests for the CloudClient class. Uses DigitalOcean as a salt-cloud provider.
    '''
    PROVIDER = 'digitalocean'
    REQUIRED_PROVIDER_CONFIG_ITEMS = ('personal_access_token', 'ssh_key_file', 'ssh_key_name')
    IMAGE_NAME = '14.04.5 x64'

    def setUp(self):
        super(CloudClientTest, self).setUp()

        images = self.run_cloud('--list-images {0}'.format(self.profile_str))

        if self.IMAGE_NAME not in [i.strip(': ') for i in images]:
            self.skipTest('Image \'{1}\' was not found in image search.  Is the {0} provider '
                          'configured correctly for this test?'.format(self.PROVIDER, self.IMAGE_NAME))

    def test_cloud_client_create_and_delete(self):
        '''
        Tests that a VM is created successfully when calling salt.cloud.CloudClient.create(),
        which does not require a profile configuration.

        Also checks that salt.cloud.CloudClient.destroy() works correctly since this test needs
        to remove the VM after creating it.

        This test was created as a regression check against Issue #41971.
        '''
        cloud_client = salt.cloud.CloudClient(opts=self.config)

        # Create the VM using salt.cloud.CloudClient.create() instead of calling salt-cloud
        ret_val = cloud_client.create(
            provider=self.profile_str,
            names=[self.instance_name],
            image=self.IMAGE_NAME,
            location='sfo1', size='512mb', vm_size='512mb'
        )

        self.assertTrue(ret_val, 'Error in cloud client creation, no return value from create')

        # Check that the VM was created correctly
        self.assertInstanceExists(ret_val)

        # Clean up after ourselves and delete the VM
        deleted = cloud_client.destroy(names=[self.instance_name])

        # Check that the VM was deleted correctly
        self.assertIn(self.instance_name, deleted)
