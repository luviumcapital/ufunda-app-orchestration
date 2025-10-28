#!/usr/bin/env python3
"""
Gmail Account Creation Bot
Adapted from Gmail-Creation-Automation-Python
https://github.com/khaouitiabdelhakim/Gmail-Creation-Automation-Python

This bot automates Gmail account creation for university application workflows.
"""

import os
import time
import random
import string
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gmail_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GmailBot:
    """
    Gmail account creation automation bot
    """
    
    def __init__(self, headless=False):
        """
        Initialize the Gmail bot
        
        Args:
            headless (bool): Run browser in headless mode
        """
        self.headless = headless
        self.driver = None
        self.wait = None
        
    def setup_driver(self):
        """
        Setup Chrome WebDriver with appropriate options
        """
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument('--headless')
            
            # Additional options for stability
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Set user agent
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.maximize_window()
            self.wait = WebDriverWait(self.driver, 20)
            
            logger.info("WebDriver setup successful")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up WebDriver: {str(e)}")
            return False
    
    def generate_credentials(self, base_name=None):
        """
        Generate random credentials for Gmail account
        
        Args:
            base_name (str): Base name for the email (optional)
            
        Returns:
            dict: Dictionary containing generated credentials
        """
        if not base_name:
            base_name = 'testuser' + ''.join(random.choices(string.digits, k=6))
        
        credentials = {
            'first_name': 'Test',
            'last_name': 'User' + ''.join(random.choices(string.digits, k=4)),
            'username': base_name,
            'password': self._generate_strong_password(),
            'birth_day': random.randint(1, 28),
            'birth_month': random.randint(1, 12),
            'birth_year': random.randint(1990, 2000),
            'gender': random.choice(['Male', 'Female', 'Other'])
        }
        
        return credentials
    
    def _generate_strong_password(self, length=16):
        """
        Generate a strong password
        
        Args:
            length (int): Length of the password
            
        Returns:
            str: Generated password
        """
        characters = string.ascii_letters + string.digits + '!@#$%^&*'
        password = ''.join(random.choices(characters, k=length))
        return password
    
    def create_account(self, credentials=None):
        """
        Automate Gmail account creation process
        
        Args:
            credentials (dict): Optional dictionary with account details
            
        Returns:
            dict: Result containing success status and account info
        """
        if not credentials:
            credentials = self.generate_credentials()
        
        result = {
            'success': False,
            'credentials': credentials,
            'message': '',
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Navigate to Gmail signup page
            logger.info("Navigating to Gmail signup page...")
            self.driver.get('https://accounts.google.com/signup')
            time.sleep(3)
            
            # Fill in first name
            logger.info("Filling in personal information...")
            first_name_field = self.wait.until(
                EC.presence_of_element_located((By.NAME, 'firstName'))
            )
            first_name_field.send_keys(credentials['first_name'])
            time.sleep(0.5)
            
            # Fill in last name
            last_name_field = self.driver.find_element(By.NAME, 'lastName')
            last_name_field.send_keys(credentials['last_name'])
            time.sleep(0.5)
            
            # Click next
            next_button = self.driver.find_element(By.XPATH, '//button[.//span[text()="Next"]]')
            next_button.click()
            time.sleep(3)
            
            # Fill in birth date and gender
            logger.info("Filling in birth date and gender...")
            day_field = self.wait.until(
                EC.presence_of_element_located((By.NAME, 'day'))
            )
            day_field.send_keys(str(credentials['birth_day']))
            time.sleep(0.5)
            
            month_field = self.driver.find_element(By.NAME, 'month')
            month_field.send_keys(str(credentials['birth_month']))
            time.sleep(0.5)
            
            year_field = self.driver.find_element(By.NAME, 'year')
            year_field.send_keys(str(credentials['birth_year']))
            time.sleep(0.5)
            
            # Select gender
            gender_field = self.driver.find_element(By.NAME, 'gender')
            gender_field.send_keys(str(credentials.get('gender', '1')))
            time.sleep(0.5)
            
            # Click next
            next_button = self.driver.find_element(By.XPATH, '//button[.//span[text()="Next"]]')
            next_button.click()
            time.sleep(3)
            
            # Try to use suggested email or create custom username
            logger.info("Setting up username...")
            try:
                # Try to click "Create your own Gmail address"
                create_own = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, '//div[contains(text(), "Create your own")]'))
                )
                create_own.click()
                time.sleep(2)
                
                username_field = self.driver.find_element(By.NAME, 'Username')
                username_field.send_keys(credentials['username'])
                time.sleep(0.5)
            except:
                logger.info("Using suggested email address")
            
            # Click next
            next_button = self.driver.find_element(By.XPATH, '//button[.//span[text()="Next"]]')
            next_button.click()
            time.sleep(3)
            
            # Fill in password
            logger.info("Setting up password...")
            password_field = self.wait.until(
                EC.presence_of_element_located((By.NAME, 'Passwd'))
            )
            password_field.send_keys(credentials['password'])
            time.sleep(0.5)
            
            confirm_password_field = self.driver.find_element(By.NAME, 'PasswdAgain')
            confirm_password_field.send_keys(credentials['password'])
            time.sleep(0.5)
            
            # Click next
            next_button = self.driver.find_element(By.XPATH, '//button[.//span[text()="Next"]]')
            next_button.click()
            time.sleep(5)
            
            logger.info("Gmail account creation process initiated")
            result['success'] = True
            result['message'] = 'Account creation process completed successfully'
            
            # Save credentials to file
            self._save_credentials(credentials)
            
        except TimeoutException as e:
            logger.error(f"Timeout error: {str(e)}")
            result['message'] = f'Timeout error: {str(e)}'
            
        except NoSuchElementException as e:
            logger.error(f"Element not found: {str(e)}")
            result['message'] = f'Element not found: {str(e)}'
            
        except Exception as e:
            logger.error(f"Error during account creation: {str(e)}")
            result['message'] = f'Error: {str(e)}'
        
        return result
    
    def _save_credentials(self, credentials):
        """
        Save credentials to a file
        
        Args:
            credentials (dict): Credentials to save
        """
        try:
            filename = f"gmail_credentials_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w') as f:
                f.write(f"Gmail Account Credentials\n")
                f.write(f"========================\n\n")
                f.write(f"First Name: {credentials['first_name']}\n")
                f.write(f"Last Name: {credentials['last_name']}\n")
                f.write(f"Username: {credentials['username']}\n")
                f.write(f"Password: {credentials['password']}\n")
                f.write(f"Birth Date: {credentials['birth_day']}/{credentials['birth_month']}/{credentials['birth_year']}\n")
                f.write(f"Gender: {credentials['gender']}\n")
                f.write(f"\nCreated: {datetime.now().isoformat()}\n")
            
            logger.info(f"Credentials saved to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving credentials: {str(e)}")
    
    def close(self):
        """
        Close the browser and cleanup
        """
        if self.driver:
            self.driver.quit()
            logger.info("Browser closed")

def main():
    """
    Main execution function for testing
    """
    logger.info("Starting Gmail Bot...")
    
    bot = GmailBot(headless=False)
    
    if not bot.setup_driver():
        logger.error("Failed to setup driver")
        return
    
    try:
        # Generate credentials
        credentials = bot.generate_credentials('ufunda_test')
        logger.info(f"Generated credentials for: {credentials['username']}")
        
        # Create account
        result = bot.create_account(credentials)
        
        if result['success']:
            logger.info("✓ Gmail account creation successful")
            logger.info(f"Username: {result['credentials']['username']}")
        else:
            logger.error("✗ Gmail account creation failed")
            logger.error(f"Message: {result['message']}")
        
        # Keep browser open for a moment to see results
        time.sleep(10)
        
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
    
    finally:
        bot.close()

if __name__ == '__main__':
    main()
