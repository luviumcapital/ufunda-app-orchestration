from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
import requests
import os
from typing import Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UniversityBotTemplate:
    """
    Template class for creating university-specific application bots.
    Copy this file and customize for each university portal.
    """
    
    def __init__(self, orchestrator_url: str = "http://localhost:8000"):
        self.orchestrator_url = orchestrator_url
        self.driver = None
        self.university_name = "TEMPLATE_UNIVERSITY"  # Change this
        self.bot_id = f"bot_{self.university_name.lower().replace(' ', '_')}"
        
    def setup_driver(self):
        """Initialize Selenium WebDriver"""
        try:
            options = webdriver.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            # Uncomment for headless mode
            # options.add_argument('--headless')
            
            self.driver = webdriver.Chrome(options=options)
            logger.info(f"WebDriver initialized for {self.university_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            return False
    
    def report_status(self, status: str, task: Optional[str] = None):
        """Report bot status to orchestrator"""
        try:
            payload = {
                "bot_id": self.bot_id,
                "university_name": self.university_name,
                "status": status,
                "current_task": task,
                "last_updated": self._get_timestamp()
            }
            
            response = requests.post(
                f"{self.orchestrator_url}/bot/status",
                json=payload
            )
            
            if response.status_code == 200:
                logger.info(f"Status reported: {status}")
            else:
                logger.warning(f"Failed to report status: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error reporting status: {e}")
    
    def update_application_status(self, application_id: str, status: str, error: Optional[str] = None):
        """Update application status in orchestrator"""
        try:
            url = f"{self.orchestrator_url}/application/{application_id}/update"
            params = {"status": status}
            
            if error:
                params["error_message"] = error
            
            response = requests.post(url, params=params)
            
            if response.status_code == 200:
                logger.info(f"Application {application_id} status updated to {status}")
            else:
                logger.warning(f"Failed to update application status: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error updating application status: {e}")
    
    def navigate_to_portal(self, application_link: str):
        """Navigate to university application portal"""
        try:
            logger.info(f"Navigating to {application_link}")
            self.driver.get(application_link)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            logger.info("Successfully navigated to portal")
            return True
            
        except Exception as e:
            logger.error(f"Failed to navigate to portal: {e}")
            return False
    
    def fill_personal_information(self, applicant_data: Dict):
        """Fill personal information section"""
        try:
            # TODO: Customize these selectors for the specific university
            # Example:
            # first_name_field = self.driver.find_element(By.ID, "firstName")
            # first_name_field.send_keys(applicant_data.get("first_name", ""))
            
            logger.info("Personal information section filled")
            return True
            
        except Exception as e:
            logger.error(f"Failed to fill personal information: {e}")
            return False
    
    def fill_contact_information(self, applicant_data: Dict):
        """Fill contact information section"""
        try:
            # TODO: Customize these selectors for the specific university
            # Example:
            # email_field = self.driver.find_element(By.ID, "email")
            # email_field.send_keys(applicant_data.get("email", ""))
            
            logger.info("Contact information section filled")
            return True
            
        except Exception as e:
            logger.error(f"Failed to fill contact information: {e}")
            return False
    
    def fill_academic_information(self, applicant_data: Dict):
        """Fill academic information section"""
        try:
            # TODO: Customize these selectors for the specific university
            
            logger.info("Academic information section filled")
            return True
            
        except Exception as e:
            logger.error(f"Failed to fill academic information: {e}")
            return False
    
    def submit_application(self):
        """Submit the application"""
        try:
            # TODO: Customize submit button selector
            # Example:
            # submit_button = self.driver.find_element(By.ID, "submitBtn")
            # submit_button.click()
            
            # Wait for confirmation
            # WebDriverWait(self.driver, 10).until(
            #     EC.presence_of_element_located((By.CLASS_NAME, "success-message"))
            # )
            
            logger.info("Application submitted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to submit application: {e}")
            return False
    
    def process_application(self, application_id: str, application_link: str, applicant_data: Dict):
        """Main method to process an application"""
        logger.info(f"Starting application process for {application_id}")
        
        try:
            # Report bot is running
            self.report_status("running", f"Processing {application_id}")
            
            # Update application status to processing
            self.update_application_status(application_id, "processing")
            
            # Setup driver
            if not self.setup_driver():
                raise Exception("Failed to setup WebDriver")
            
            # Navigate to portal
            if not self.navigate_to_portal(application_link):
                raise Exception("Failed to navigate to portal")
            
            # Fill application sections
            if not self.fill_personal_information(applicant_data):
                raise Exception("Failed to fill personal information")
            
            if not self.fill_contact_information(applicant_data):
                raise Exception("Failed to fill contact information")
            
            if not self.fill_academic_information(applicant_data):
                raise Exception("Failed to fill academic information")
            
            # Submit application
            if not self.submit_application():
                raise Exception("Failed to submit application")
            
            # Update status to completed
            self.update_application_status(application_id, "completed")
            self.report_status("completed", f"Completed {application_id}")
            
            logger.info(f"Application {application_id} completed successfully")
            return True
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Application processing failed: {error_msg}")
            
            # Update status to failed
            self.update_application_status(application_id, "failed", error_msg)
            self.report_status("failed", error_msg)
            
            return False
            
        finally:
            # Cleanup
            if self.driver:
                self.driver.quit()
                logger.info("WebDriver closed")
    
    def _get_timestamp(self):
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.now().isoformat()


if __name__ == "__main__":
    # Example usage
    bot = UniversityBotTemplate()
    
    # Example application data
    test_application = {
        "application_id": "test_app_001",
        "application_link": "https://example.com/apply",
        "applicant_data": {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1234567890"
        }
    }
    
    # Process the application
    bot.process_application(
        test_application["application_id"],
        test_application["application_link"],
        test_application["applicant_data"]
    )
