import pytest

from utils.helpers import *


class TestGPTResponseValidation:

    @pytest.fixture(scope="class")
    def locators(self):
        """Load locators for the tests."""
        return load_locators()

    @pytest.fixture(scope="class")
    def test_data(self):
        """Load test data for response validation."""
        return load_test_data()["response_validation"]["common_queries"]

    @pytest.mark.ui
    def test_11_english_query_response(self, driver: WebDriver, locators, query_item_en, threshold):
        """
        Validate a single English AI query item. pytest_generate_tests will create
        as many test instances as the CLI --query-limit requests, no skips.
        """
        # validate_language_based_responses accepts a list of query items, here we pass one
        validate_language_based_responses(
            driver,
            locators,
            [query_item_en],
            lang="en",
            num_queries=1,
            threshold=threshold
        )

    @pytest.mark.ui
    def test_12_arabic_query_response(self, driver: WebDriver, locators, query_item_ar, threshold):
        """
        Validate a single Arabic AI query item. the session is reused per test instance.
        """

        validate_language_based_responses(
            driver,
            locators,
            [query_item_ar],
            lang="ar",
            num_queries=1,
            threshold=threshold
        )

    
    @pytest.mark.ui
    def test_10_network_throttle_fallback(self, driver: WebDriver, locators):
        """Test network throttling/fallback messages for offline scenario."""
        test_name = "network_failure_fallback"
        passed = True
        failure_details = ""

        input_field = setup_chat(driver, locators)

        driver.execute_cdp_cmd("Network.enable", {})
        driver.execute_cdp_cmd("Network.emulateNetworkConditions", {
            "offline": True,
            "latency": 0,
            "downloadThroughput": 0,
            "uploadThroughput": 0
        })

        # Step 3: Send a valid message while offline
        input_field.send_keys("test network failure" + Keys.ENTER)

        try:
            wait_for_shimmer(driver, locators, timeout=15)
            # If shimmer completes → fail in this test
            passed = False
            failure_details = "Shimmer appeared in offline mode, expected fallback instead."
        except AssertionError:
            # Shimmer did not appear/disappear properly → PASS for offline case
            passed = True

        # Step 5: Restore network
        driver.execute_cdp_cmd("Network.emulateNetworkConditions", {
            "offline": False,
            "latency": 0,
            "downloadThroughput": -1,
            "uploadThroughput": -1
        })

        # Step 6: Assert final result
        assert_with_logging(
            passed,
            driver,
            test_name=test_name,
            success_details="Offline network fallback behavior verified",
            failure_details=failure_details or "Network fallback validation failed"
        )