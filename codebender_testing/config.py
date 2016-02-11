import os

from selenium import webdriver
from selenium.webdriver import chrome
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import yaml
import simplejson
import pytest


def _rel_path(*args):
    """Returns a path relative to config.py file's directory."""
    return os.path.join(os.path.dirname(__file__), *args)

def get_path(directory, filename=None):
    """Returns an absolute path as seen from your current working directory.
    If a file is passed as argument, returns an aboslute path including the
    file."""
    path = os.path.join(os.path.dirname( __file__ ), '..', directory)
    if filename:
        path = os.path.join(os.path.dirname( __file__ ), '..', directory, filename)
    return os.path.abspath(path)

def jsondump(data):
    return simplejson.dumps(data, sort_keys=True, indent=4 * ' ')

# URL of the default site to be used for testing.
BASE_URL = "http://localhost"
# URL of the actual Codebender website.
LIVE_SITE_URL = "https://codebender.cc"
STAGING_SITE_URL = "https://staging.codebender.cc"

# User whose projects we'd like to compile in our compile_tester
# test case(s).
COMPILE_TESTER_URL = "/user/cb_compile_tester"
COMPILE_TESTER_STAGING_URL = "/user/demo_user"

# The prefix for all filenames of log files.
# Note that it is given as a time format string, which will
# be formatted appropriately.
LOGFILE_PREFIX = _rel_path("..", "logs", "%Y-%m-%d_%H-%M-%S-{log_name}.json")

# Logfile for COMPILE_TESTER compilation results.
COMPILE_TESTER_LOGFILE = LOGFILE_PREFIX.format(log_name="cb_compile_tester")
COMPILE_TESTER_LOGFILE_STAGING = LOGFILE_PREFIX.format(log_name="staging_cb_compile_tester")

# Logfile for /libraries compilation results.
LIBRARIES_TEST_LOGFILE = LOGFILE_PREFIX.format(log_name="libraries_test")

# Logfile for /libraries fetch results.
LIBRARIES_FETCH_LOGFILE = LOGFILE_PREFIX.format(log_name="libraries_fetch")

# Directory in which Firefox and Chrome extensions are stored.
_EXTENSIONS_DIR = _rel_path('..', 'extensions')

#  Firefox plugin for all Firefox versions.
_FIREFOX_EXTENSION_FNAME = 'codebender.xpi'
# Chrome extension for Chrome versions < 42.
_CHROME_EXTENSION_FNAME = 'codebendercc-extension.crx'
# Chrome extension for Chrome versions >= 42.
_CHROME_APP_FNAME = 'chrome-app-1.0.0.8.zip'

# Maximum version number that we can use the Chrome extension with.
# For versions higher than this, we need to use the newer Codebender app.
CHROME_EXT_MAX_CHROME_VERSION = 41

# Path to YAML file specifying capability list.
DEFAULT_CAPABILITIES_FILE = os.getenv('CAPABILITIES', 'capabilities.yaml')
DEFAULT_CAPABILITIES_FILE_PATH = _rel_path(DEFAULT_CAPABILITIES_FILE)

# Files used for testing.
TEST_DATA_DIR = _rel_path('..', 'test_data')
TEST_DATA_INO = os.path.join(TEST_DATA_DIR, 'upload_ino.ino')
TEST_DATA_ZIP = os.path.join(TEST_DATA_DIR, 'upload_zip.zip')

# Directory in which the local compile tester files are stored.
COMPILE_TESTER_DIR = os.path.join(TEST_DATA_DIR, 'cb_compile_tester')

TEST_PROJECT_NAME = "test_project"

TIMEOUT = {
    'LOCATE_ELEMENT': 30
}

DEFAULT_USER_AGENT = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:43.0) Gecko/20100101 Firefox/43.0 codebender-selenium'
TESTS_USER_AGENT = os.getenv('SELENIUM_USER_AGENT', DEFAULT_USER_AGENT)

DEFAULT_USER_AGENT_CHROME = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36'
TESTS_USER_AGENT_CHROME = os.getenv('SELENIUM_USER_AGENT_CHROME', DEFAULT_USER_AGENT_CHROME)

BROWSER = "firefox"

# Set up Selenium Webdrivers to be used for selenium tests.
def _get_firefox_profile():
    """Returns the Firefox profile to be used for the FF webdriver.
    Specifically, we're equipping the webdriver with the Codebender
    extension.
    """
    firefox_profile = webdriver.FirefoxProfile()
    if pytest.config.getoption("--plugin"):
        firefox_profile.add_extension(
            extension=os.path.join(_EXTENSIONS_DIR, _FIREFOX_EXTENSION_FNAME)
        )
    return firefox_profile

def get_browsers(capabilities_file_path=None):
    """Returns a list of capabilities. Each item in the list will cause
    the entire suite of tests to be re-run for a browser with those
    particular capabilities.

    `capabilities_file_path` is a path to a YAML file specifying a list of
    capabilities for each browser. "Capabilities" are the dictionaries
    passed as the `desired_capabilities` argument to the webdriver constructor.
    """
    if capabilities_file_path is None:
        capabilities_file_path = DEFAULT_CAPABILITIES_FILE_PATH
    stream = file(capabilities_file_path, 'rb')
    return yaml.load(stream)


def create_webdriver(command_executor, desired_capabilities):
    """Creates a new remote webdriver with the following properties:
      - The remote URL of the webdriver is defined by `command_executor`.
      - desired_capabilities is a dict with the same interpretation as
        it is used elsewhere in selenium. If no browserName key is present,
        we default to firefox.
    """
    if 'browserName' not in desired_capabilities:
        desired_capabilities['browserName'] = 'firefox'
    browser_name = desired_capabilities['browserName']
    # Fill in defaults from DesiredCapabilities.{CHROME,FIREFOX} if they are
    # missing from the desired_capabilities dict above.
    _capabilities = desired_capabilities
    browser_profile = None
    browser_profile_path = None

    if browser_name == "chrome":
        BROWSER = "chrome"
        desired_capabilities = DesiredCapabilities.CHROME.copy()
        desired_capabilities.update(_capabilities)
        if desired_capabilities["version"] > CHROME_EXT_MAX_CHROME_VERSION:
            # Add new chrome extension to capabilities.
            options = chrome.options.Options()
            options.add_extension(os.path.join(_EXTENSIONS_DIR, _CHROME_APP_FNAME))
            options.add_argument("--user-agent=" + TESTS_USER_AGENT_CHROME)
            desired_capabilities.update(options.to_capabilities())
            desired_capabilities.update(_capabilities)
        else:
            raise ValueError("The testing suite only supports Chrome versions greater than v%d, "
                            "but v%d was specified. Please specify a higher version number."
                            % (CHROME_EXT_MAX_CHROME_VERSION, desired_capabilities["version"]))

    elif browser_name == "firefox":
        BROWSER = "firefox"
        desired_capabilities = DesiredCapabilities.FIREFOX.copy()
        desired_capabilities.update(_capabilities)
        browser_profile = _get_firefox_profile()
        browser_profile_path = browser_profile.path
        browser_profile.set_preference("general.useragent.override", TESTS_USER_AGENT)
        desired_capabilities["firefox_profile"] = browser_profile.update_preferences()
    else:
        raise ValueError("Invalid webdriver %s (only chrome and firefox are supported)" % browser_name)
    return {
        'driver': webdriver.Remote(
            command_executor=command_executor,
            desired_capabilities=desired_capabilities,
            browser_profile=browser_profile,
        ),
        'profile_path': browser_profile_path
    }
