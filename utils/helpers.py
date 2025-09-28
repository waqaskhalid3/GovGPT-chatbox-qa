import os
import re
import time
import json
import random
import requests
from datetime import datetime
from difflib import SequenceMatcher

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager


# -------------------------
# Data loading utilities
# -------------------------

def load_locators():
    with open(os.path.join(os.path.dirname(__file__), '../data/locators.json')) as f:
        return json.load(f)

def load_test_data():
    with open(os.path.join(os.path.dirname(__file__), '../data/test-data.json')) as f:
        return json.load(f)

# -------------------------
# Screenshot and logging utilities
# -------------------------

def save_screenshot(driver, test_name):
    """Save a screenshot of the current page and log message input"""
    folder = "screenshots"
    os.makedirs(folder, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = os.path.join(folder, f"{test_name}_{timestamp}.png")
    driver.save_screenshot(screenshot_path)

LOG_FILE = "logs/logs.log"  # single consistent log file

def log_ui_result(test_name: str, passed: bool, details: str = "", language: str | None = None):
    """Write a concise UI behavior result line to logs/logs.log (append, no loss)."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "PASS" if passed else "FAIL"
    os.makedirs("logs", exist_ok=True)
    line = (
        f"{timestamp} | {status} | {test_name}"
        + (f" | lang={language}" if language else "")
        + (f" | {details}" if details else "")
        + "\n"
    )
    print(line.strip())
    # Open in append mode to keep existing logs
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)

def log_and_screenshot(driver, test_name: str, passed: bool, details: str = "", language: str | None = None):
    """Capture screenshot with pass/fail suffix and log a UI result line."""
    suffix = "pass" if passed else "fail"
    save_screenshot(driver, f"{test_name}_{suffix}")
    log_ui_result(test_name=test_name, passed=passed, details=details, language=language)

def assert_with_logging(condition: bool, driver, test_name: str, success_details: str = "", failure_details: str = "", language: str | None = None):
    """Assert a condition while guaranteeing logs and screenshots for both outcomes."""
    if condition:
        log_and_screenshot(driver, test_name, True, success_details, language)
        return
    log_and_screenshot(driver, test_name, False, failure_details or "Assertion failed", language)
    assert condition, failure_details or f"Assertion failed in {test_name}"

# -------------------------
# Viewport helpers
# -------------------------

def switch_view(driver, mode="desktop"):
    """Set browser window size for desktop or mobile view."""
    if mode == "desktop":
        driver.set_window_size(1920, 1080)
    elif mode == "mobile":
        driver.set_window_size(390, 844)
    else:
        raise ValueError(f"Unsupported mode: {mode}")

def get_chat_widget(driver, locators, timeout=10):
    """Wait for chat widget to load and return it."""
    wait = WebDriverWait(driver, timeout)
    return wait.until(
        EC.presence_of_element_located(
            (By.ID, locators["chat_widget"]["widget_container"])
        )
    )


# -------------------------
# Chat helpers
# -------------------------

def setup_chat(driver, locators):
    return WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.ID, locators["chat_widget"]["widget_container"]))
    )

def wait_for_shimmer(driver, locators, timeout=60):
    """Wait for shimmer to appear (optional) and then disappear, with fallback handling."""
    shimmer_locator = (By.CLASS_NAME, locators["chat_widget"]["loading_shimmer"])
    failure_details = ""

    # Step 1: Wait for shimmer to appear (best-effort)
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(shimmer_locator)
        )
    except TimeoutException:
        failure_details += "Loading shimmer did not appear within 20s.\n"

    # Step 2: Wait for shimmer to disappear (main requirement)
    try:
        WebDriverWait(driver, timeout).until(
            EC.invisibility_of_element_located(shimmer_locator)
        )
    except TimeoutException:
        failure_details += f"Loading shimmer still visible after {timeout}s.\n"

    if failure_details:
        raise AssertionError(failure_details)

def get_ai_response(driver, locators, timeout=10):
    """Wait until AI response is visible and return the element."""
    ai_locator = (By.XPATH, locators["chat_widget"]["ai_message"])
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located(ai_locator))

def validate_ai_response(ai_element):
    """Return tuple (condition, failure_message)."""
    is_visible = ai_element.is_displayed()
    has_content = ai_element.text.strip() != ""

    condition = is_visible and has_content
    failure_details = []
    if not is_visible:
        failure_details.append("not visible")
    if not has_content:
        failure_details.append("empty content")

    return condition, f"AI response failed: {', '.join(failure_details)}" if failure_details else ""

# -------------------------
# Response accuracy checker
# -------------------------

def validate_language_based_responses(
    driver,
    locators,
    test_data,
    lang="en",
    num_queries: int | None = 3,
    threshold: float = 0.8
):
    """
    Validate AI responses in a single browser session for a language.
    
    :param driver: Selenium WebDriver
    :param locators: JSON locators
    :param test_data: List of queries with expected responses
    :param lang: Language code ("en" or "ar")
    :param num_queries: Number of queries to validate (default 3, max = total queries)
    :param threshold: Minimum similarity threshold (0.0-1.0)
    """

    total_queries = len(test_data)
    num_to_run = min(num_queries or 3, total_queries)

    # Iterate over the first num_to_run queries
    for i in range(num_to_run):
        query_item = test_data[i]  # pick query based on iteration
        test_name = f"{lang}_response_{i+1}"

        # Step 1: Setup chat input
        input_box = setup_chat(driver, locators)
        message = query_item[lang]  # pick query text for this language
        input_box.send_keys(message + Keys.ENTER)

        # Step 2: Wait for shimmer/loading and response completion
        wait_for_shimmer(driver, locators, timeout=15)
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, locators["chat_widget"]["response_complete_indicator"])
            )
        )

        # Step 3: Get AI response
        ai_element = get_ai_response(driver, locators, timeout=20)
        actual_response = ai_element.text

        # Step 4: Get the corresponding expected response for this query
        expected_response = query_item["expected_response"][lang][0]  # always pick the first string in the list

        # Step 5: Check accuracy
        passed, matched_percentage = response_accuracy_checker(actual_response, expected_response, threshold)

        # Step 6: Build success/failure details
        success_details = (
            f"{lang.upper()} response passed.\n"
            f"Query: {message}\n"
            f"Matched: {matched_percentage}%\n"
            f"Expected: {expected_response}\n"
            f"Response: {actual_response}"
        )
        failure_details = (
            f"{lang.upper()} response failed.\n"
            f"Query: {message}\n"
            f"Matched: {matched_percentage}% < Threshold\n"
            f"Expected: {expected_response}\n"
            f"Response: {actual_response}"
        )

        # Step 7: Assert with logging
        assert_with_logging(
            passed,
            driver,
            test_name,
            success_details,
            failure_details,
            language=lang
        )


def response_accuracy_checker(actual_response: str, expected_response: str, threshold: float = 0.8):
    """
    Compare actual response with expected content using API Ninjas Text Similarity API.
    Returns: (passed: bool, matched_percentage: float)
    """
    api_url = "https://api.api-ninjas.com/v1/textsimilarity"
    api_key = "4K/u77Y6FrpJfaxhfLpPpQ==3oaVNNWwd9YVBcaE"

    body = {
        "text_1": expected_response,
        "text_2": actual_response
    }

    try:
        response = requests.post(api_url, headers={"X-Api-Key": api_key}, json=body)
        if response.status_code == requests.codes.ok:
            result = response.json()
            similarity = result.get("similarity", 0.0)  # value between 0.0 and 1.0
            matched_percentage = round(similarity * 100, 2)
            passed = similarity >= threshold
        else:
            print(f"Error: {response.status_code}, {response.text}")
            matched_percentage = 0.0
            passed = False
    except Exception as e:
        print(f"Exception while checking similarity: {e}")
        matched_percentage = 0.0
        passed = False

    print(
        f"[Response Accuracy Check] Matched {matched_percentage}% | "
        f"Threshold: {threshold*100}%\n"
        f"Expected snippet: {expected_response[:100]}...\n"
        f"Actual snippet: {actual_response[:100]}..."
    )

    return passed, matched_percentage


def malicious_response_checker(actual_response: str, expected_phrases: list[str]) -> bool:
    """
    Check if the actual response contains at least one of the expected rejection phrases.
    Case insensitive match. Simple pass/fail.
    """
    actual_response_lower = actual_response.lower()
    for phrase in expected_phrases:
        if phrase.lower() in actual_response_lower:
            print(f"[Malicious Check] Matched expected phrase: '{phrase}'")
            return True

    print(f"[Malicious Check] No expected phrases matched. Response: {actual_response[:120]}...")
    return False


# -------------------------
# Language helpers
# -------------------------

def get_html_attributes(driver, locators):
    """Return current html tag's lang and dir attributes."""
    html_tag = driver.find_element(By.XPATH, locators["dashboard_page"]["html_tag"])
    return html_tag.get_attribute("lang"), html_tag.get_attribute("dir")

def switch_language(driver, locators, to_lang="ar"):
    """
    Dynamically switch language (supports Arabic <-> English).
    Reads locator key from locators.json.
    """
    wait = WebDriverWait(driver, 20)

    # Step 1: Open profile menu
    profile_btn = wait.until(
        EC.element_to_be_clickable((By.XPATH, locators["dashboard_page"]["profile_button"]))
    )
    profile_btn.click()

    # Step 2: Pick correct locator dynamically
    lang_map = {
        "ar": "switch_to_arabic",
        "en": "switch_to_english"
    }

    if to_lang not in lang_map:
        raise ValueError(f"Unsupported target language: {to_lang}")

    locator_key = lang_map[to_lang]

    # Step 3: Click target language
    switch_btn = wait.until(
        EC.element_to_be_clickable((By.XPATH, locators["dashboard_page"][locator_key]))
    )
    switch_btn.click()