"""
Integration tests for the Dimension Data cloud provider
"""

# Import Python Libs

# Import Salt Testing Libs
from tests.integration.cloud.helpers.cloud_test_base import (
    CloudTest,
    requires_provider_config,
)


@requires_provider_config("key", "region", "user_id")
class DimensionDataTest(CloudTest):
    """
    Integration tests for the Dimension Data cloud provider in Salt-Cloud
    """

    PROVIDER = "dimensiondata"

    PROVIDER = "dimensiondata"
    REQUIRED_PROVIDER_CONFIG_ITEMS = ("key", "region", "user_id")

    def test_list_images(self):
        """
        Tests the return of running the --list-images command for the dimensiondata cloud provider
        """
        image_list = self.run_cloud(
            "--list-images {}".format(self.provider_config_name),
            timeout=self.TEST_TIMEOUT,
        )
        self.assertIn("Ubuntu 14.04 2 CPU", [i.strip() for i in image_list])

    def test_list_locations(self):
        """
        Tests the return of running the --list-locations command for the dimensiondata cloud provider
        """
        _list_locations = self.run_cloud(
            "--list-locations {}".format(self.provider_config_name),
            timeout=self.TEST_TIMEOUT,
        )
        self.assertIn(
            "Australia - Melbourne MCP2", [i.strip() for i in _list_locations]
        )

    def test_list_sizes(self):
        """
        Tests the return of running the --list-sizes command for the dimensiondata cloud provider
        """
        _list_sizes = self.run_cloud(
            "--list-sizes {}".format(self.provider_config_name),
            timeout=self.TEST_TIMEOUT,
        )
        self.assertIn("default", [i.strip() for i in _list_sizes])

    def test_instance(self):
        """
        Test creating an instance on Dimension Data's cloud
        """
        self.assertCreateInstance()
        self.assertDestroyInstance()
