import pytest

from utils.helpers import *


class TestUAskUIBehavior:

    @pytest.fixture(scope="class")
    def locators(self):
        """Load locators for the tests."""
        return load_locators()

    @pytest.fixture(scope="class")
    def test_data(self):
        """Load test data for UI behavior tests."""
        return load_test_data()

    @pytest.mark.ui
    def test_01_chat_widget_loads_desktop_and_mobile(self, driver: WebDriver, locators: EC.Any):
        """Test chat widget loads in both desktop and mobile views."""

        # Desktop check
        switch_view(driver, "desktop")
        widget = get_chat_widget(driver, locators)
        assert_with_logging(
            widget.is_displayed(),
            driver,
            test_name="widget_loads_desktop",
            success_details="Chat widget visible in desktop view",
            failure_details="Chat widget not visible in desktop view",
        )

        # Mobile check
        switch_view(driver, "mobile")
        widget = get_chat_widget(driver, locators)
        assert_with_logging(
            widget.is_displayed(),
            driver,
            test_name="widget_loads_mobile",
            success_details="Chat widget visible in mobile view",
            failure_details="Chat widget not visible in mobile view",
        )

    @pytest.mark.ui
    def test_02_user_can_send_message(self, driver: WebDriver, locators: EC.Any):
        """Test user can send a message and shimmer appears and disappears."""
        test_data = load_test_data()
        test_msg = test_data["ui_tests"]["test_messages"]["input_field_test"]["message"]

        # Step 1: Setup chat input (instead of repeating find_element)
        input_box = setup_chat(driver, locators)

        # Step 2: Send message
        input_box.send_keys(test_msg + Keys.ENTER)

        # Step 3: Wait for shimmer using helper
        try:
            wait_for_shimmer(driver, locators)
            condition = True
            success_details = "User can send message, shimmer appeared and completed correctly"
            failure_details = ""
        except AssertionError as e:
            # In case shimmer fails, capture that
            condition = False
            success_details = ""
            failure_details = f"Shimmer issue: {str(e)}"

        # Step 4: Final assert with logging
        assert_with_logging(
            condition,
            driver,
            test_name="user_can_send_message",
            success_details=success_details,
            failure_details=failure_details or "User cannot send message — possibly no internet or send failed",
        )


    @pytest.mark.ui
    def test_03_ai_response_rendered(self, driver: WebDriver, locators: EC.Any):
        """Test AI response is rendered after sending a message."""

        # Step 1: Setup chat input
        input_box = setup_chat(driver, locators)

        # Step 2: Get test message from test data
        test_msg = load_test_data()["ui_tests"]["test_messages"]["input_field_test"]["message"]

        # Step 3: Send the test message
        input_box.send_keys(test_msg + Keys.ENTER)

        # Step 4: Wait for shimmer (ensures AI is processing and completes)
        wait_for_shimmer(driver, locators, timeout=30)
        
        # Step 5: Capture the AI response
        ai_response = get_ai_response(driver, locators)

        # Step 6: Validate AI response (visible + not empty)
        condition, failure_msg = validate_ai_response(ai_response)

        # Step 7: Assert with logging
        assert_with_logging(
            condition,
            driver,
            test_name="ai_response_rendered",
            success_details="AI response visible and has content",
            failure_details=failure_msg,
        )


    @pytest.mark.ui
    def test_04_multilingual_support(self, driver: WebDriver, locators: EC.Any, test_data):
        """Test multilingual support and directionality."""
        lang_cases = test_data["ui_tests"]["language_direction"]

        for case in lang_cases:
            language = case["language"]
            expected_dir = case["expected_direction"]

            # Switch language if not English
            if language != "en":
                switch_language(driver, locators, to_lang=language)

            # Fetch <html> attributes
            lang_attr, dir_attr = get_html_attributes(driver, locators)

            # Assertions with logging
            condition = lang_attr.startswith(language) and dir_attr == expected_dir
            failure_msg = f"Expected {language}/{expected_dir}, got {lang_attr}/{dir_attr}"

            assert_with_logging(
                condition,
                driver,
                test_name=f"multilingual_{language}",
                success_details=f"Language '{language}' with direction '{expected_dir}' verified",
                failure_details=failure_msg,
            )

    @pytest.mark.ui
    def test_05_input_is_cleared_after_sending(self, driver: WebDriver, locators: EC.Any):
        """Test input field is cleared after sending a message."""

        # Step 1: Setup chat input
        input_box = setup_chat(driver, locators)

        # Step 2: Get test message from test data
        test_msg = load_test_data()["ui_tests"]["test_messages"]["input_field_test"]["message"]

        # Step 3: Send the test message
        input_box.send_keys(test_msg + Keys.ENTER)

        # Step 4: Wait for input field to be ready again
        input_field = get_chat_widget(driver, locators, 30)

        # Step 5: Verify input is cleared by checking inner <p> with empty class
        empty_paragraph = input_field.find_element(By.CSS_SELECTOR, locators["chat_widget"]["empty_indicator"])
        is_empty = empty_paragraph is not None

        assert_with_logging(
            is_empty,
            driver,
            test_name="input_cleared_after_sending",
            success_details="Input cleared after sending",
            failure_details="Input not cleared; 'is-empty is-editor-empty' <p> not found",
        )


    @pytest.mark.ui
    def test_06_scroll_and_accessibility(self, driver: WebDriver, locators: EC.Any):
        """Verify chat scroll functionality and input field accessibility."""
        wait = WebDriverWait(driver, 30)

        # Step 1: Setup chat input
        input_box = setup_chat(driver, locators)

        # Step 2: Retrieve test message from JSON
        test_msg = load_test_data()["ui_tests"]["test_messages"]["input_field_test"]["message"]

        # Step 3: Send the message
        input_box.send_keys(test_msg + Keys.ENTER)

        # Step 4: Wait for messages container to load
        container = wait.until(
            EC.presence_of_element_located(
                (By.ID, locators["chat_widget"]["message_container"])
            )
        )

        # Step 5: Scroll to top
        driver.execute_script("arguments[0].scrollTop = 0", container)

        # Step 6: Optional short wait to allow DOM update
        WebDriverWait(driver, 2).until(
            lambda d: driver.execute_script("return arguments[0].scrollTop", container) == 0
        )

        # Step 7: Verify scroll position
        scroll_position = driver.execute_script("return arguments[0].scrollTop", container)
        assert_with_logging(
            scroll_position == 0,
            driver,
            test_name="scroll_to_top",
            success_details="Scrolled to top successfully",
            failure_details=f"Scroll position not at top. Value: {scroll_position}"
        )


    @pytest.mark.ui
    def test_07_accessibility_input_field(self, driver: WebDriver, locators: EC.Any):
        """
        Verify the chatbot input field meets global accessibility standards.
        Checks include ARIA roles, labels, contenteditable, placeholders, and language/direction.
        """
        # Step 1: Wait for chat widget / input field
        input_element = get_chat_widget(driver, locators, timeout=15)

        # Step 2: Collect key accessibility attributes
        attrs_to_check = {
            "role": input_element.get_attribute("role"),
            "aria-label": input_element.get_attribute("aria-label"),
            "aria-labelledby": input_element.get_attribute("aria-labelledby"),
            "aria-describedby": input_element.get_attribute("aria-describedby"),
            "contenteditable": input_element.get_attribute("contenteditable"),
            "placeholder": input_element.get_attribute("placeholder"),
            "lang": input_element.get_attribute("lang"),
            "dir": input_element.get_attribute("dir"),
            "tabindex": input_element.get_attribute("tabindex"),
        }

        # Step 3: Build detailed attribute report
        attr_report = "\n".join([f"{k}: {v or 'None'}" for k, v in attrs_to_check.items()])

        # Step 4: Define global accessibility pass conditions
        checks = [
            bool(attrs_to_check["role"]),  # must expose ARIA role
            bool(attrs_to_check["aria-label"] or attrs_to_check["aria-labelledby"]),  # label present
            attrs_to_check["contenteditable"] in ("true", "plaintext-only", "True"),  # editable field
            bool(attrs_to_check["placeholder"]),  # helpful hint present
            bool(attrs_to_check["tabindex"]),  # must be focusable via keyboard
        ]
        passed = all(checks)

        # Step 5: Assert with logging
        failure_msg = f"Accessibility check failed. Attributes:\n{attr_report}"
        success_msg = f"Accessibility attributes verified.\nAttributes:\n{attr_report}"

        assert_with_logging(
            passed,
            driver,
            test_name="accessibility_input_field",
            success_details=success_msg,
            failure_details=failure_msg
        )
        
    