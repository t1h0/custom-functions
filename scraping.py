import typing
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import TimeoutException


def waitClickable(driver: WebDriver, xpath: str, timeout: int = 10) -> typing.Optional[WebElement]:
    """Wait for element in selenium to be clickable and return it.

    Args:
        driver (RemoteWebDriver): Driver to act on.
        xpath (str): XPath to evaluate.
        timeout (int, optional): Timeout in seconds if condition is not met. Defaults to 10.

    Returns:
        WebElement | None: The clickable element or None if timeout.
    """
    try:
        return WebDriverWait(driver, timeout).until(expected_conditions.element_to_be_clickable((By.XPATH, xpath)))
    except TimeoutException:
        return None
