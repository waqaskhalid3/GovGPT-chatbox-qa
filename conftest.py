import pytest

from utils.helpers import *


# Load locators
with open("data/locators.json") as f:
    locators = json.load(f)

# Load test data
with open("data/test-data.json") as f:
    test_data = json.load(f)

# ---------------------------
# Pytest command-line options
# ---------------------------
def pytest_addoption(parser):
    parser.addoption(
        "--query-limit",
        action="store",
        default=3,            
        type=int,
        help="Number of queries to run per test (default=3)"
    )
    parser.addoption(
        "--threshold",
        action="store",
        default=0.8,
        type=float,
        help="Similarity threshold for response validation (0.0-1.0)"
    )
    parser.addoption(
        "--headless",
        action="store_true",
        default=True, 
        help="Run Chrome in headless mode"
    )

# ---------------------------
# Fixtures to access options
# ---------------------------
@pytest.fixture
def headless_mode(request):
    return request.config.getoption("--headless")

@pytest.fixture(scope="session")
def query_limit(request):
    return request.config.getoption("query_limit")

@pytest.fixture(scope="session")
def threshold(request):
    return request.config.getoption("threshold")


def pytest_generate_tests(metafunc):
    """
    Dynamically parametrize tests that request query_item_en or query_item_ar fixtures.
    This ensures pytest creates only the desired number of test items, no skips.
    """
    if "query_item_en" in metafunc.fixturenames:
        limit = metafunc.config.getoption("query_limit")
        all_queries = load_test_data()["response_validation"]["common_queries"]
        capped = min(max(0, limit), len(all_queries))
        metafunc.parametrize("query_item_en", all_queries[:capped])

    if "query_item_ar" in metafunc.fixturenames:
        limit = metafunc.config.getoption("query_limit")
        all_queries = load_test_data()["response_validation"]["common_queries"]
        capped = min(max(0, limit), len(all_queries))
        metafunc.parametrize("query_item_ar", all_queries[:capped])

# ---------------------------
# WebDriver fixture
# ---------------------------
@pytest.fixture(scope="function")
def driver(headless_mode):
    """Launch Chrome WebDriver and log in to dashboard."""
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1920,1080")
    if headless_mode:
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    driver.get("https://govgpt.sandbox.dge.gov.ae/")
    wait = WebDriverWait(driver, 10)

    try:
        # Click "Login with Credentials"
        login_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, locators["login_page"]["login_credentials_button"]))
        )
        login_btn.click()

        # Enter Email
        email_input = wait.until(
            EC.presence_of_element_located((By.ID, locators["login_page"]["email_input"]))
        )
        email_input.send_keys(test_data["credentials"]["email"])

        # Enter Password
        password_input = driver.find_element(By.ID, locators["login_page"]["password_input"])
        password_input.send_keys(test_data["credentials"]["password"])

        # Click Sign In
        driver.find_element(By.CSS_SELECTOR, locators["login_page"]["sign_in_button"]).click()

        # Wait for Dashboard greeting
        wait.until(
            EC.presence_of_element_located((By.XPATH, locators["dashboard_page"]["welcome_message"]))
        )

    except Exception:
        driver.quit()
        raise

    yield driver
    driver.quit()
