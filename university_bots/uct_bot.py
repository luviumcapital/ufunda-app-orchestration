#!/usr/bin/env python3
"""
UCT Application Bot (Sample)

This script demonstrates a sample structure for automating a University of Cape Town (UCT)
application flow using Selenium. The actual UCT application portal may require authentication,
MFA, captchas, or dynamic elements that cannot be fully automated without proper access and
consent. This sample is for demonstration and testing within the ufunda-app-orchestration framework.
"""

import os
import time
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('uct_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class Applicant:
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    id_number: Optional[str] = None
    program: Optional[str] = None

class UCTBot:
    """
    Sample UCT application bot using Selenium.
    """

    def __init__(self, headless: bool = True, timeout: int = 20):
        self.headless = headless
        self.timeout = timeout
        self.driver = None
        self.wait: Optional[WebDriverWait] = None

    def setup_driver(self) -> bool:
        try:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--window-size=1440,900')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, self.timeout)
            logger.info('WebDriver initialized for UCT bot')
            return True
        except Exception as e:
            logger.error(f'Failed to initialize WebDriver: {e}')
            return False

    def go_to_portal(self) -> None:
        # Placeholder: replace with official UCT application portal URL
        portal_url = os.getenv('UCT_PORTAL_URL', 'https://www.uct.ac.za/apply')
        logger.info(f'Navigating to UCT portal: {portal_url}')
        self.driver.get(portal_url)
        time.sleep(2)

    def login_if_required(self) -> None:
        """Handle login flow if the portal requires authentication."""
        try:
            # Example selectors - update based on actual UCT portal
            if self._element_exists(By.NAME, 'username'):
                username = os.getenv('UCT_USERNAME', '')
                password = os.getenv('UCT_PASSWORD', '')
                if not username or not password:
                    logger.warning('No UCT credentials provided; skipping login step')
                    return
                self.wait.until(EC.presence_of_element_located((By.NAME, 'username'))).send_keys(username)
                self.driver.find_element(By.NAME, 'password').send_keys(password)
                self.driver.find_element(By.XPATH, "//button[contains(., 'Login') or contains(., 'Sign in')]").click()
                logger.info('Submitted login form')
                time.sleep(2)
        except Exception as e:
            logger.warning(f'Login step skipped/failed: {e}')

    def start_application(self) -> None:
        """Navigate to start a new application."""
        try:
            # Example link/button to start application
            if self._element_exists(By.XPATH, "//a[contains(., 'Apply') or contains(., 'Start application')]"):
                self.driver.find_element(By.XPATH, "//a[contains(., 'Apply') or contains(., 'Start application')]").click()
                logger.info('Clicked start application')
                time.sleep(2)
        except Exception as e:
            logger.error(f'Could not start application: {e}')

    def fill_applicant_details(self, applicant: Applicant) -> None:
        """Fill basic applicant details on the form."""
        try:
            mappings = {
                'first_name': ['firstName', 'given_name', 'first_name'],
                'last_name': ['lastName', 'family_name', 'last_name'],
                'email': ['email', 'emailAddress'],
                'phone': ['phone', 'mobile', 'phoneNumber'],
                'id_number': ['idNumber', 'national_id', 'id'],
            }
            data = applicant.__dict__
            for key, candidates in mappings.items():
                value = data.get(key)
                if not value:
                    continue
                for cname in candidates:
                    if self._element_exists(By.NAME, cname):
                        self.driver.find_element(By.NAME, cname).clear()
                        self.driver.find_element(By.NAME, cname).send_keys(value)
                        break
            logger.info('Filled applicant details')
        except Exception as e:
            logger.error(f'Error filling applicant details: {e}')

    def select_program(self, program: str) -> None:
        try:
            # Example: generic dropdown search
            if self._element_exists(By.NAME, 'program'):
                self.driver.find_element(By.NAME, 'program').send_keys(program)
                logger.info(f'Selected program: {program}')
        except Exception as e:
            logger.warning(f'Program selection skipped/failed: {e}')

    def upload_documents(self, docs: Dict[str, str]) -> None:
        """Upload required documents. docs is a mapping of field name -> file path."""
        for field, path in docs.items():
            try:
                if not os.path.exists(path):
                    logger.warning(f'Document not found: {path}')
                    continue
                # Try input[type=file]
                if self._element_exists(By.NAME, field):
                    self.driver.find_element(By.NAME, field).send_keys(os.path.abspath(path))
                    logger.info(f'Uploaded document for {field}')
                else:
                    # Fallback: any file inputs on page
                    inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
                    if inputs:
                        inputs[0].send_keys(os.path.abspath(path))
                        logger.info(f'Uploaded document via fallback: {field}')
                time.sleep(1)
            except Exception as e:
                logger.warning(f'Upload failed for {field}: {e}')

    def submit_application(self) -> bool:
        try:
            # Attempt to click submit
            if self._element_exists(By.XPATH, "//button[contains(., 'Submit') or contains(., 'Finish')]"):
                self.driver.find_element(By.XPATH, "//button[contains(., 'Submit') or contains(., 'Finish')]").click()
                logger.info('Clicked submit')
                # Wait for confirmation element/text
                confirmation = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(., 'Thank you') or contains(., 'submitted') or contains(., 'reference number')]")
                ))
                logger.info('Submission confirmation detected')
                return True
            logger.warning('Submit button not found')
            return False
        except TimeoutException:
            logger.error('Timed out waiting for submission confirmation')
            return False
        except Exception as e:
            logger.error(f'Error during submission: {e}')
            return False

    def _element_exists(self, by: By, locator: str) -> bool:
        try:
            self.driver.find_element(by, locator)
            return True
        except NoSuchElementException:
            return False

    def close(self):
        if self.driver:
            self.driver.quit()
            logger.info('Browser closed')


def run_sample(applicant: Optional[Applicant] = None, headless: bool = True) -> Dict[str, Any]:
    bot = UCTBot(headless=headless)
    if not bot.setup_driver():
        return {"success": False, "message": "WebDriver setup failed"}

    try:
        if applicant is None:
            applicant = Applicant(
                first_name=os.getenv('UCT_FIRST_NAME', 'Test'),
                last_name=os.getenv('UCT_LAST_NAME', 'Applicant'),
                email=os.getenv('UCT_EMAIL', 'test.applicant@example.com'),
                phone=os.getenv('UCT_PHONE', ''),
                id_number=os.getenv('UCT_ID', ''),
                program=os.getenv('UCT_PROGRAM', 'Computer Science')
            )

        bot.go_to_portal()
        bot.login_if_required()
        bot.start_application()
        bot.fill_applicant_details(applicant)
        if applicant.program:
            bot.select_program(applicant.program)

        # Example uploads - set env paths if you wish to test
        docs = {
            'idDocument': os.getenv('UCT_DOC_ID', ''),
            'transcript': os.getenv('UCT_DOC_TRANSCRIPT', ''),
        }
        # Remove empty entries
        docs = {k: v for k, v in docs.items() if v}
        if docs:
            bot.upload_documents(docs)

        submitted = bot.submit_application()
        return {
            'success': submitted,
            'message': 'Submitted successfully' if submitted else 'Submission not confirmed',
        }
    finally:
        bot.close()


if __name__ == '__main__':
    result = run_sample(headless=True)
    logger.info(f"UCT Bot result: {result}")
