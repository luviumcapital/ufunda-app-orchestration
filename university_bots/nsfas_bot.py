"""
NSFAS/SETA Bursary Application Automation Bot (nsfas_bot.py)
- Navigates NSFAS portal stepwise
- Captures applicant details, household income, institution & course info
- Uploads required documents (ID, proof of income, consent form, academic record)
- Handles OTP and declarations
- Structured event logging for orchestrator
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
import time
import logging

try:
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
except Exception:
    By = object  # type: ignore
    WebDriverWait = object  # type: ignore
    EC = object  # type: ignore


@dataclass
class NSFASConfig:
    portal_url: str = "https://my.nsfas.org.za/"
    timeout: int = 30


class NSFASBot:
    def __init__(self, driver: Any, logger: Optional[logging.Logger] = None):
        self.driver = driver
        self.wait = (lambda sec: WebDriverWait(self.driver, sec)) if hasattr(self.driver, "get") else None
        self.log = logger or logging.getLogger("nsfas_bot")
        if not self.log.handlers:
            logging.basicConfig(level=logging.INFO)
        self.events: List[Dict[str, Any]] = []
        self.cfg = NSFASConfig()

    def emit(self, type_: str, data: Dict[str, Any]):
        evt = {"type": type_, "ts": time.time(), **data}
        self.events.append(evt)
        self.log.info(f"NSFASBot event: {evt}")

    def _find(self, by, selector):
        if self.wait:
            return self.wait(self.cfg.timeout).until(EC.presence_of_element_located((by, selector)))
        return None

    def _fill(self, by, selector, value, clear=True):
        el = self._find(by, selector)
        if clear:
            try:
                el.clear()
            except Exception:
                pass
        el.send_keys(value)

    def _click(self, by, selector):
        el = self._find(by, selector)
        el.click()

    def login_or_register(self, context: Dict[str, Any]):
        self.emit("step", {"name": "navigate_login", "url": self.cfg.portal_url})
        self.driver.get(self.cfg.portal_url)
        if context.get("nsfas_email") and context.get("nsfas_password"):
            self.emit("step", {"name": "login_existing"})
            self._fill(By.ID, "username", context["nsfas_email"])
            self._fill(By.ID, "password", context["nsfas_password"])
            self._click(By.ID, "loginBtn")
        else:
            self.emit("step", {"name": "register"})
            self._click(By.ID, "register")
            self._fill(By.ID, "email", context.get("email", ""))
            self._fill(By.ID, "id_number", context.get("id_number", ""))
            self._fill(By.ID, "cell", context.get("mobile", ""))
            self._click(By.ID, "registerSubmit")

    def step_profile(self, context: Dict[str, Any]):
        self.emit("step", {"name": "profile"})
        self._fill(By.ID, "firstName", context.get("first_name", ""))
        self._fill(By.ID, "lastName", context.get("last_name", ""))
        self._fill(By.ID, "dob", context.get("dob", ""))
        self._fill(By.ID, "address1", context.get("address1", ""))
        self._fill(By.ID, "city", context.get("city", ""))
        self._fill(By.ID, "postalCode", context.get("postal_code", ""))
        self._click(By.CSS_SELECTOR, "button.next, .btn-next")

    def step_household(self, context: Dict[str, Any]):
        self.emit("step", {"name": "household"})
        self._fill(By.ID, "householdSize", str(context.get("household_size", "")))
        self._fill(By.ID, "income", str(context.get("household_income", "")))
        self._click(By.CSS_SELECTOR, "button.next, .btn-next")

    def step_institution(self, context: Dict[str, Any]):
        self.emit("step", {"name": "institution"})
        self._fill(By.ID, "university", context.get("university", ""))
        self._fill(By.ID, "qualification", context.get("programme", ""))
        self._fill(By.ID, "studentNumber", context.get("student_number", ""))
        self._click(By.CSS_SELECTOR, "button.next, .btn-next")

    def step_documents(self, context: Dict[str, Any]):
        self.emit("step", {"name": "documents"})
        uploads = context.get("uploads", {})
        def set_file(selector, key):
            path = uploads.get(key)
            if not path:
                self.emit("warning", {"phase": "upload", "missing": key})
                return
            self._find(By.CSS_SELECTOR, selector).send_keys(path)
        set_file("input[name='id_doc']", "id_doc")
        set_file("input[name='proof_income']", "proof_income")
        set_file("input[name='consent_form']", "consent_form")
        set_file("input[name='academic_record']", "academic_record")
        self._click(By.CSS_SELECTOR, "button.next, .btn-next")

    def step_otp_and_declaration(self, context: Dict[str, Any]):
        self.emit("step", {"name": "otp_declaration"})
        if context.get("otp"):
            self._fill(By.ID, "otp", context["otp"])
            self._click(By.ID, "otpSubmit")
        self._click(By.ID, "acceptDeclaration")
        self._click(By.CSS_SELECTOR, "button.submit, #submitApplication")

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        self.emit("start", {"bot": "nsfas_bot"})
        try:
            self.login_or_register(context)
            self.step_profile(context)
            self.step_household(context)
            self.step_institution(context)
            self.step_documents(context)
            self.step_otp_and_declaration(context)
            self.emit("done", {"ok": True})
        except Exception as e:
            self.emit("done", {"ok": False, "error": str(e)})
        return {"events": self.events}


def run(driver: Any, context: Dict[str, Any]) -> Dict[str, Any]:
    return NSFASBot(driver).run(context)
