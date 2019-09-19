# -*- coding: utf-8 -*-
'''
Integration tests for DigitalOcean APIv2
'''

# Import Python Libs
from __future__ import absolute_import, print_function, unicode_literals
import base64
import hashlib
import os
from Crypto.PublicKey import RSA

# Import Salt Testing Libs
from tests.integration.cloud.helpers.cloud_test_base import CloudTest, TIMEOUT
from tests.support.runtests import RUNTIME_VARS

# Import Salt Libs
from salt.ext.six.moves import range
import salt.cloud
import salt.utils.stringutils


class DigitalOceanTest(CloudTest):
    '''
    Integration tests for the DigitalOcean cloud provider in Salt-Cloud
    '''
    PROVIDER = 'digitalocean'
    REQUIRED_PROVIDER_CONFIG_ITEMS = ('personal_access_token', 'ssh_key_file', 'ssh_key_name')

    def test_list_images(self):
        '''
        Tests the return of running the --list-images command for digitalocean
        '''
        image_list = self.run_cloud('--list-images {0}'.format(self.PROVIDER))
        self.assertIn(
            '14.04.5 x64',
            [i.strip() for i in image_list]
        )

    def test_list_locations(self):
        '''
        Tests the return of running the --list-locations command for digitalocean
        '''
        _list_locations = self.run_cloud('--list-locations {0}'.format(self.PROVIDER))
        self.assertIn(
            'San Francisco 2',
            [i.strip() for i in _list_locations]
        )

    def test_list_sizes(self):
        '''
        Tests the return of running the --list-sizes command for digitalocean
        '''
        _list_sizes = self.run_cloud('--list-sizes {0}'.format(self.PROVIDER))
        self.assertIn(
            '16gb',
            [i.strip() for i in _list_sizes]
        )

    def test_key_management(self):
        '''
        Test key management
        '''
        do_key_name = self.instance_name + '-key'

        # generate key and fingerprint
        ssh_key = RSA.generate(4096)
        pub = salt.utils.stringutils.to_str(ssh_key.publickey().exportKey("OpenSSH"))
        key_hex = hashlib.md5(base64.b64decode(pub.strip().split()[1].encode())).hexdigest()
        finger_print = ':'.join([key_hex[x:x+2] for x in range(0, len(key_hex), 2)])

        try:
            _key = self.run_cloud('-f create_key {0} name="{1}" public_key="{2}"'.format(self.PROVIDER,
                                                                                         do_key_name, pub))

            # Upload public key
            self.assertIn(
                finger_print,
                [i.strip() for i in _key]
            )

            # List all keys
            list_keypairs = self.run_cloud('-f list_keypairs {0}'.format(self.PROVIDER))

            self.assertIn(
                finger_print,
                [i.strip() for i in list_keypairs]
            )

            # List key
            show_keypair = self.run_cloud('-f show_keypair {0} keyname={1}'.format(self.PROVIDER, do_key_name))
            self.assertIn(
                finger_print,
                [i.strip() for i in show_keypair]
            )
        except AssertionError:
            # Delete the public key if the above assertions fail
            self.run_cloud('-f remove_key {0} id={1}'.format(self.PROVIDER, finger_print))
            raise
        finally:
            # Delete public key
            self.assertTrue(self.run_cloud('-f remove_key {0} id={1}'.format(self.PROVIDER, finger_print)))

    def test_instance(self):
        '''
        Test creating an instance on DigitalOcean
        '''
        # check if instance with salt installed returned
        ret_str = self.run_cloud('-p {0} {1}'.format(self.profile, self.instance_name), timeout=TIMEOUT)
        self.assertInstanceExists(ret_str)

        self.assertDestroyInstance(timeout=TIMEOUT)

    def test_cloud_client_create_and_delete(self):
        '''
        Tests that a VM is created successfully when calling salt.cloud.CloudClient.create(),
        which does not require a profile configuration.

        Also checks that salt.cloud.CloudClient.destroy() works correctly since this test needs
        to remove the VM after creating it.

        This test was created as a regression check against Issue #41971.
        '''
        IMAGE_NAME = '14.04.5 x64'
        config_file = os.path.join(RUNTIME_VARS.TMP_CONF_CLOUD_PROVIDER_INCLUDES, 'digitalocean.conf')
        cloud_client = salt.cloud.CloudClient(config_file)

        images = self.run_cloud('--list-images {0}'.format(self.profile_str))
        if IMAGE_NAME not in [i.strip(': ') for i in images]:
            self.skipTest('Image \'{1}\' was not found in image search.  Is the {0} provider '
                          'configured correctly for this test?'.format(self.PROVIDER, IMAGE_NAME))

        # Create the VM using salt.cloud.CloudClient.create() instead of calling salt-cloud
        ret_val = cloud_client.create(
            provider=self.profile_str,
            names=[self.instance_name],
            image=IMAGE_NAME,
            location='sfo1',
            size='512mb',
            vm_size='512mb',
            profile=self.config_path,
        )

        self.assertTrue(ret_val, 'Error in {} creation, no return value from create()'.format(self.instance_name))

        # Check that the VM was created correctly
        self.assertInstanceExists(ret_val)

        # Clean up after ourselves and delete the VM
        deletion_ret = cloud_client.destroy(names=[self.instance_name])

        # Check that the VM was deleted correctly
        self.assertDestroyInstance(deletion_ret=deletion_ret, timeout=TIMEOUT)
