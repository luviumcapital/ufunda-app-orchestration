"""
University of the Witwatersrand (Wits) Application Bot
Complies with Ufunda RPA spec: logging, retries, screenshots, audit trail.
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

LOG_LEVEL = os.getenv("BOT_LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("wits_bot")

SCREENSHOT_DIR = Path(os.getenv("SCREENSHOT_DIR", "screenshots/wits"))
ARTIFACT_DIR = Path(os.getenv("ARTIFACT_DIR", "artifacts"))
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

@dataclass
class Applicant:
    created_email: str
    personal: Dict
    academic: Dict
    program_preferences: List[Dict]
    documents: Dict[str, str]
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

class WitsBot:
    BASE_URL = "https://www.wits.ac.za"

    def __init__(self, applicant: Applicant, driver: Optional[webdriver.Chrome] = None, timeout: int = 20):
        self.applicant = applicant
        self.driver = driver or webdriver.Chrome()
        self.wait = WebDriverWait(self.driver, timeout)
        self.screenshots: List[str] = []
        self.errors: List[str] = []

    def shot(self, name: str):
        path = SCREENSHOT_DIR / f"{int(time.time())}_{name}.png"
        try:
            self.driver.save_screenshot(str(path))
            self.screenshots.append(str(path))
        except Exception as e:
            logger.warning(f"Screenshot failed: {e}")

    def retry_click(self, by: str, selector: str, max_attempts: int = 3):
        for attempt in range(max_attempts):
            try:
                elem = self.wait.until(EC.element_to_be_clickable((by, selector)))
                elem.click()
                return
            except Exception as e:
                logger.warning(f"Click attempt {attempt+1} failed: {e}")
                time.sleep(2 ** attempt)
        raise Exception(f"Could not click {selector} after {max_attempts} attempts")

    # Workflow steps
    def navigate(self):
        logger.info("Navigating to Wits application portal")
        self.driver.get(self.BASE_URL + "/apply")
        self.shot("navigate")

    def create_profile(self):
        logger.info("Creating/logging into profile")
        try:
            self.driver.find_element(By.XPATH, "//button[contains(text(), 'Start Application')]")
        except NoSuchElementException:
            email_field = self.wait.until(EC.presence_of_element_located((By.ID, "email")))
            email_field.send_keys(self.applicant.created_email)
            self.retry_click(By.ID, "submit-email")
        self.shot("profile_created")

    def fill_personal_information(self):
        logger.info("Filling personal information")
        for key, val in self.applicant.personal.items():
            try:
                elem = self.driver.find_element(By.NAME, key)
                elem.clear(); elem.send_keys(str(val))
            except Exception as e:
                logger.warning(f"Could not fill personal field {key}: {e}")
        self.retry_click(By.XPATH, "//button[contains(text(), 'Next')]")
        self.shot("personal_info_filled")

    def fill_academic_background(self):
        logger.info("Filling academic background")
        for key, val in self.applicant.academic.items():
            try:
                elem = self.driver.find_element(By.NAME, key)
                elem.clear(); elem.send_keys(str(val))
            except Exception as e:
                logger.warning(f"Could not fill academic field {key}: {e}")
        self.retry_click(By.XPATH, "//button[contains(text(), 'Next')]")
        self.shot("academic_filled")

    def select_programs(self):
        logger.info("Selecting programs")
        for idx, program in enumerate(self.applicant.program_preferences):
            try:
                self.wait.until(EC.presence_of_element_located((By.ID, f"faculty_{idx}"))).send_keys(program.get("faculty"))
                self.wait.until(EC.presence_of_element_located((By.ID, f"program_{idx}"))).send_keys(program.get("program_name"))
            except Exception as e:
                logger.warning(f"Could not select program {idx}: {e}")
        self.retry_click(By.XPATH, "//button[contains(text(), 'Next')]")
        self.shot("programs_selected")

    def upload_documents(self):
        logger.info("Uploading documents")
        for doc_name, doc_path in self.applicant.documents.items():
            try:
                input_el = self.driver.find_element(By.XPATH, f"//input[@type='file' and contains(@name, '{doc_name}')]")
                input_el.send_keys(os.path.abspath(doc_path))
                time.sleep(1)
            except Exception as e:
                logger.error(f"Upload failed for {doc_name}: {e}")
                self.errors.append(f"Upload failed: {doc_name}")
        self.shot("documents_uploaded")
        self.retry_click(By.XPATH, "//button[contains(text(), 'Next')]")

    def pay_fee(self) -> str:
        logger.info("Processing payment")
        try:
            if self.applicant.payment_method == "card":
                fields = {
                    "card_number": os.getenv("PAYMENT_CARD_NUMBER", "4111111111111111"),
                    "card_expiry": os.getenv("PAYMENT_CARD_EXPIRY", "12/25"),
                    "card_cvv": os.getenv("PAYMENT_CARD_CVV", "123"),
                }
                for fid, val in fields.items():
                    self.wait.until(EC.presence_of_element_located((By.ID, fid))).send_keys(val)
                self.retry_click(By.XPATH, "//button[contains(text(), 'Pay') or contains(text(), 'Submit Payment')]")
                time.sleep(3)
                try:
                    self.wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Payment successful') or contains(text(), 'Payment confirmed')]")))
                    self.shot("payment_success")
                    return "PAID"
                except TimeoutException:
                    self.shot("payment_failed")
                    return "FAILED"
            else:
                logger.warning("Non-card payment flow not implemented, marking as PENDING")
                return "PENDING"
        except Exception as e:
            logger.error(f"Payment failed: {e}")
            self.errors.append(str(e))
            self.shot("payment_error")
            return "FAILED"

    def submit(self):
        logger.info("Submitting application")
        self.retry_click(By.XPATH, "//button[contains(text(), 'Submit Application') or contains(text(), 'Final Submit')]")
        time.sleep(2)
        self.shot("application_submitted")

    def capture_confirmation(self) -> Dict:
        logger.info("Capturing confirmation")
        out = {}
        try:
            app_num = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Application Number') or contains(text(), 'Reference')]/following-sibling::*").text
            out["application_number"] = app_num.strip()
            try:
                faculty = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Faculty')]/following-sibling::*").text
                out["faculty_confirmation"] = faculty.strip()
            except Exception:
                pass
            try:
                out["submission_confirmation"] = self.driver.find_element(By.CLASS_NAME, "confirmation-text").text
            except Exception:
                pass
            self.shot("confirmation_captured")
        except Exception as e:
            logger.warning(f"Confirmation parse failed: {e}")
        return out

    def run(self) -> BotResult:
        try:
            self.navigate()
            self.create_profile()
            self.fill_personal_information()
            self.fill_academic_background()
            self.select_programs()
            self.upload_documents()
            payment_status = self.pay_fee()
            self.submit()
            conf = self.capture_confirmation()
            result = BotResult(
                university="Wits",
                application_number=conf.get("application_number"),
                faculty_confirmation=conf.get("faculty_confirmation"),
                payment_status=payment_status,
                submission_confirmation=conf.get("submission_confirmation"),
                screenshots=self.screenshots,
                success=payment_status == "PAID",
                errors=self.errors,
            )
            (ARTIFACT_DIR / f"wits_{int(time.time())}.json").write_text(json.dumps(asdict(result), indent=2))
            return result
        except Exception as e:
            logger.error("Run failed: %s\n%s", e, traceback.format_exc())
            self.shot("error")
            self.errors.append(str(e))
            return BotResult(
                university="Wits",
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
    data_path = os.getenv("APPLICANT_JSON")
    if not data_path or not Path(data_path).exists():
        logger.error("APPLICANT_JSON not provided or file missing")
        exit(1)
    data = json.loads(Path(data_path).read_text())
    app = Applicant(**data)
    bot = WitsBot(app)
    res = bot.run()
    print(json.dumps(asdict(res)))
