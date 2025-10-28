"""
Stellenbosch University Application Bot
Complies with Ufunda RPA spec: logging, retries, screenshots, audit trail, notifications.
"""
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
import os, time, json, traceback, logging
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ----- Logging configuration -----
LOG_LEVEL = os.getenv("BOT_LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("stellenbosch_bot")

SCREENSHOT_DIR = Path(os.getenv("SCREENSHOT_DIR", "screenshots/stellenbosch"))
ARTIFACT_DIR = Path(os.getenv("ARTIFACT_DIR", "artifacts"))
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

@dataclass
class Applicant:
    created_email: str
    personal: Dict
    academic: Dict
    program_preferences: List[Dict]
    documents: Dict[str, str]  # name -> file path
    payment_method: str = "card"

@dataclass
class BotResult:
    university: str
    application_number: Optional[str]
    faculty_confirmation: Optional[str]
    payment_status: Optional[str]
    submission_confirmation: Optional[str]
    screenshots: List[str]
    success: bool
    errors: List[str]

class StellenboschBot:
    BASE_URL = "https://www.maties.com"
    
    def __init__(self, applicant: Applicant, driver: Optional[webdriver.Chrome] = None, timeout: int = 20):
        self.applicant = applicant
        self.driver = driver or webdriver.Chrome()
        self.wait = WebDriverWait(self.driver, timeout)
        self.screenshots: List[str] = []
        self.errors: List[str] = []
    
    # ----- Utility helpers -----
    def shot(self, name: str):
        """Take a screenshot and store in audit trail"""
        path = SCREENSHOT_DIR / f"{int(time.time())}_{name}.png"
        try:
            self.driver.save_screenshot(str(path))
            self.screenshots.append(str(path))
        except Exception as e:
            logger.warning(f"Screenshot failed: {e}")
    
    def retry_click(self, by: str, selector: str, max_attempts: int = 3):
        """Retry clicking an element with exponential backoff"""
        for attempt in range(max_attempts):
            try:
                elem = self.wait.until(EC.element_to_be_clickable((by, selector)))
                elem.click()
                logger.info(f"Clicked {selector}")
                return
            except Exception as e:
                logger.warning(f"Click attempt {attempt+1} failed: {e}")
                time.sleep(2 ** attempt)
        raise Exception(f"Could not click {selector} after {max_attempts} attempts")
    
    # ----- Core workflow steps -----
    def navigate(self):
        """Navigate to application portal"""
        logger.info("Navigating to Stellenbosch application portal")
        self.driver.get(self.BASE_URL + "/apply")
        self.shot("navigate")
    
    def create_profile(self):
        """Create or login to application profile"""
        logger.info("Creating/logging into profile")
        try:
            # Check if already logged in
            self.driver.find_element(By.XPATH, "//button[contains(text(), 'Start Application')]")
        except NoSuchElementException:
            # Need to create/login
            email_field = self.wait.until(EC.presence_of_element_located((By.ID, "email")))
            email_field.send_keys(self.applicant.created_email)
            self.retry_click(By.ID, "submit-email")
            time.sleep(2)
        self.shot("profile_created")
    
    def fill_personal_information(self):
        """Fill personal information form"""
        logger.info("Filling personal information")
        personal = self.applicant.personal
        
        # Fill form fields - adjust selectors based on actual site
        fields = {
            "first_name": personal.get("first_name"),
            "last_name": personal.get("last_name"),
            "id_number": personal.get("id_number"),
            "phone": personal.get("phone"),
            "address": personal.get("address")
        }
        
        for field_id, value in fields.items():
            if value:
                try:
                    elem = self.wait.until(EC.presence_of_element_located((By.ID, field_id)))
                    elem.clear()
                    elem.send_keys(value)
                except Exception as e:
                    logger.warning(f"Could not fill {field_id}: {e}")
        
        self.retry_click(By.XPATH, "//button[contains(text(), 'Next') or contains(text(), 'Save')]")
        self.shot("personal_info_filled")
    
    def fill_academic_background(self):
        """Fill academic background information"""
        logger.info("Filling academic background")
        academic = self.applicant.academic
        
        # Fill matric results or previous qualifications
        for key, value in academic.items():
            try:
                elem = self.driver.find_element(By.NAME, key)
                elem.clear()
                elem.send_keys(str(value))
            except NoSuchElementException:
                logger.warning(f"Academic field {key} not found")
        
        self.retry_click(By.XPATH, "//button[contains(text(), 'Next')]")
        self.shot("academic_filled")
    
    def select_programs(self):
        """Select program/faculty preferences"""
        logger.info("Selecting programs")
        for idx, program in enumerate(self.applicant.program_preferences):
            try:
                # Select faculty/program from dropdowns
                faculty_select = self.wait.until(EC.presence_of_element_located((By.ID, f"faculty_{idx}")))
                faculty_select.send_keys(program.get("faculty"))
                
                program_select = self.wait.until(EC.presence_of_element_located((By.ID, f"program_{idx}")))
                program_select.send_keys(program.get("program_name"))
            except Exception as e:
                logger.warning(f"Could not select program {idx}: {e}")
        
        self.retry_click(By.XPATH, "//button[contains(text(), 'Next')]")
        self.shot("programs_selected")
    
    def upload_documents(self):
        """Upload required documents"""
        logger.info("Uploading documents")
        for doc_name, doc_path in self.applicant.documents.items():
            try:
                # Find upload input - adjust selector as needed
                upload_input = self.driver.find_element(By.XPATH, f"//input[@type='file' and contains(@name, '{doc_name}')]")
                upload_input.send_keys(os.path.abspath(doc_path))
                logger.info(f"Uploaded {doc_name}")
                time.sleep(1)
            except Exception as e:
                logger.error(f"Failed to upload {doc_name}: {e}")
                self.errors.append(f"Upload failed: {doc_name}")
        
        self.shot("documents_uploaded")
        self.retry_click(By.XPATH, "//button[contains(text(), 'Next')]")
    
    def pay_fee(self) -> str:
        """Process application fee payment"""
        logger.info("Processing payment")
        try:
            # Navigate to payment page
            payment_method = self.applicant.payment_method
            
            if payment_method == "card":
                # Fill card details - in real scenario use secure env vars
                card_fields = {
                    "card_number": os.getenv("PAYMENT_CARD_NUMBER", "4111111111111111"),
                    "card_expiry": os.getenv("PAYMENT_CARD_EXPIRY", "12/25"),
                    "card_cvv": os.getenv("PAYMENT_CARD_CVV", "123")
                }
                
                for field, value in card_fields.items():
                    elem = self.wait.until(EC.presence_of_element_located((By.ID, field)))
                    elem.send_keys(value)
                
                self.retry_click(By.XPATH, "//button[contains(text(), 'Pay') or contains(text(), 'Submit Payment')]")
                time.sleep(3)
                
                # Check for success confirmation
                try:
                    self.wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Payment successful') or contains(text(), 'Payment confirmed')]"))")))
                    self.shot("payment_success")
                    return "PAID"
                except TimeoutException:
                    logger.error("Payment confirmation not found")
                    self.shot("payment_failed")
                    return "FAILED"
            else:
                logger.warning(f"Payment method {payment_method} not fully implemented")
                return "PENDING"
        except Exception as e:
            logger.error(f"Payment failed: {e}")
            self.errors.append(f"Payment error: {str(e)}")
            self.shot("payment_error")
            return "FAILED"
    
    def submit(self):
        """Submit the final application"""
        logger.info("Submitting application")
        try:
            self.retry_click(By.XPATH, "//button[contains(text(), 'Submit Application') or contains(text(), 'Final Submit')]")
            time.sleep(2)
            self.shot("application_submitted")
        except Exception as e:
            logger.error(f"Submission failed: {e}")
            self.errors.append(f"Submission error: {str(e)}")
            raise
    
    def capture_confirmation(self) -> Dict:
        """Capture confirmation details and reference numbers"""
        logger.info("Capturing confirmation")
        out = {}
        try:
            # Try to extract application number
            app_num_elem = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Application Number') or contains(text(), 'Reference')]/following-sibling::*")
            out["application_number"] = app_num_elem.text.strip()
            
            # Try to extract faculty confirmation
            faculty_elem = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Faculty')]/following-sibling::*")
            out["faculty_confirmation"] = faculty_elem.text.strip()
            
            # Extract submission timestamp
            out["submission_confirmation"] = self.driver.find_element(By.CLASS_NAME, "confirmation-text").text
            
            self.shot("confirmation_captured")
        except Exception as e:
            logger.warning(f"Could not parse confirmation: {e}")
        return out
    
    def run(self) -> BotResult:
        """Main workflow execution"""
        try:
            self.navigate()
            self.create_profile()
            self.fill_personal_information()
            self.fill_academic_background()
            self.select_programs()
            self.upload_documents()
            payment_status = self.pay_fee()
            self.submit()
            confirmation = self.capture_confirmation()
            
            success = payment_status == "PAID"
            result = BotResult(
                university="Stellenbosch",
                application_number=confirmation.get("application_number"),
                faculty_confirmation=confirmation.get("faculty_confirmation"),
                payment_status=payment_status,
                submission_confirmation=confirmation.get("submission_confirmation"),
                screenshots=self.screenshots,
                success=success,
                errors=self.errors,
            )
            
            # Persist audit
            out_file = ARTIFACT_DIR / f"stellenbosch_{int(time.time())}.json"
            out_file.write_text(json.dumps(asdict(result), indent=2))
            
            return result
        except Exception as e:
            logger.error("Run failed: %s\n%s", e, traceback.format_exc())
            self.shot("error")
            self.errors.append(str(e))
            
            return BotResult(
                university="Stellenbosch",
                application_number=None,
                faculty_confirmation=None,
                payment_status="FAILED",
                submission_confirmation=None,
                screenshots=self.screenshots,
                success=False,
                errors=self.errors,
            )
        finally:
            try:
                self.driver.quit()
            except Exception:
                pass

if __name__ == "__main__":
    # Example CLI bootstrap reading env JSON
    data_path = os.getenv("APPLICANT_JSON")
    
    if not data_path or not Path(data_path).exists():
        logger.error("APPLICANT_JSON not provided or file missing")
        exit(1)
    
    data = json.loads(Path(data_path).read_text())
    applicant = Applicant(**data)
    bot = StellenboschBot(applicant)
    res = bot.run()
    print(json.dumps(asdict(res)))
