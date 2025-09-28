import pytest

from utils.helpers import *


class TestUAskSecurity:
    @pytest.fixture(scope="class")
    def locators(self):
        """Load locators for the tests."""
        return load_locators()

    @pytest.fixture(scope="class")
    def test_data(self):
        """Load test data for security tests."""
        return load_test_data()

    @pytest.mark.parametrize(
        "xss_attempt",
        load_test_data()["security_tests"]["xss_attempts"]
    )
    def test_08_xss_security_protection(self, driver, locators, test_data, xss_attempt):
        """
        Verify chatbot is protected against XSS attacks.
        """
        test_name = (
            f"xss_{''.join(e for e in xss_attempt[:10] if e.isalnum())}"
        )

        # Step 1: Setup chat
        input_box = setup_chat(driver, locators)

        # Step 2: Send malicious input
        input_box.send_keys(xss_attempt + Keys.ENTER)
        
        # Step 3: Wait for AI shimmer to disappear
        wait_for_shimmer(driver, locators,timeout=20)

        # Step 4: Get AI response
        ai_response = get_ai_response(driver, locators)
        response_html = ai_response.get_attribute("innerHTML").lower()

        # Step 5: Check for disallowed tags
        failure_reasons = [
            f"XSS: {tag} detected"
            for tag in test_data["security_tests"]["xss_expected_strings"]
            if tag.lower() in response_html
        ]

        # Step 6: Assert
        assert_with_logging(
            condition=not failure_reasons,
            driver=driver,
            test_name=test_name,
            success_details=f"XSS attempt sanitized successfully: {xss_attempt}",
            failure_details="; ".join(failure_reasons) or f"XSS not sanitized: {xss_attempt}"
        )

    @pytest.mark.parametrize(
        "malicious_prompt",
        load_test_data()["security_tests"]["malicious_prompts"]
    )
    def test_09_malicious_prompts(self, driver, locators, test_data, malicious_prompt):
        """
        Verify chatbot rejects malicious prompt injections.
        """
        test_name = f"malicious_{''.join(e for e in malicious_prompt[:15] if e.isalnum())}"

        # Step 1: Setup chat
        input_box = setup_chat(driver, locators)

        # Step 2: Send malicious prompt
        input_box.send_keys(malicious_prompt + Keys.ENTER)

        # Step 3: Wait for response completion
        wait_for_shimmer(driver, locators, timeout=10)

        # Step 4: Get AI response
        ai_response = get_ai_response(driver, locators)
        response_text = ai_response.text

        # Step 5: Validate response
        expected_phrases = test_data["security_tests"]["expected_rejection_phrases"]
        condition = malicious_response_checker(response_text, expected_phrases)

        # Step 6: Assert
        assert_with_logging(
            condition=condition,
            driver=driver,
            test_name=test_name,
            success_details=f"Malicious prompt properly rejected: {malicious_prompt}",
            failure_details=f"No expected rejection phrase matched. Response was: {response_text}"
        )
