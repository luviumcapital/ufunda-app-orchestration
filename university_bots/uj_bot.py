"""
UJ Application Automation Bot (uj_bot.py)
- Stepwise navigation through UJ online application portal
- Form filling by sections with validation
- Document upload (ID, results, proof of residence, affidavit)
- Fee handling (UJ application fee or waiver)
- Output logging compatible with orchestrator

Follows bot_template.py interfaces: BotBase.run(context) and emits structured events.
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
import time
import logging

# Minimal selenium-style abstraction expected by other bots
try:
    from selenium.webdriver import Chrome
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
except Exception:  # allow running in dry-run/testing without selenium installed
    Chrome = object  # type: ignore
    By = object  # type: ignore
    WebDriverWait = object  # type: ignore
    EC = object  # type: ignore
    TimeoutException = Exception  # type: ignore
    NoSuchElementException = Exception  # type: ignore


@dataclass
class UJConfig:
    portal_url: str = "https://student.uj.ac.za/StayConnected/Anonymous/Login.aspx"  # entry to UJ Apply
    timeout: int = 25


class UJBot:
    def __init__(self, driver: Any, logger: Optional[logging.Logger] = None):
        self.driver = driver
        self.wait = (lambda sec: WebDriverWait(self.driver, sec)) if hasattr(self.driver, "get") else None
        self.log = logger or logging.getLogger("uj_bot")
        if not self.log.handlers:
            logging.basicConfig(level=logging.INFO)
        self.events: List[Dict[str, Any]] = []
        self.cfg = UJConfig()

    def emit(self, type_: str, data: Dict[str, Any]):
        evt = {"type": type_, "ts": time.time(), **data}
        self.events.append(evt)
        self.log.info(f"UJBot event: {evt}")

    def _fill(self, by, selector, value, clear=True):
        el = self._find(by, selector)
        if clear:
            el.clear()
        el.send_keys(value)

    def _click(self, by, selector):
        el = self._find(by, selector)
        el.click()

    def _find(self, by, selector):
        if self.wait:
            return self.wait(self.cfg.timeout).until(EC.presence_of_element_located((by, selector)))
        return None

    def login_or_create(self, context: Dict[str, Any]):
        self.emit("step", {"name": "navigate_login", "url": self.cfg.portal_url})
        self.driver.get(self.cfg.portal_url)
        # If existing UJ profile
        if context.get("uj_username") and context.get("uj_password"):
            self.emit("step", {"name": "login_existing"})
            try:
                self._fill(By.ID, "txtUserName", context["uj_username"])  # username/email
                self._fill(By.ID, "txtPassword", context["uj_password"])  # password
                self._click(By.ID, "btnLogin")
            except Exception as e:
                self.emit("warning", {"phase": "login", "error": str(e)})
        else:
            # Create profile pathway (placeholder selectors)
            self.emit("step", {"name": "create_profile"})
            try:
                self._click(By.ID, "lnkCreateProfile")
                self._fill(By.ID, "txtEmail", context["email"])  # required
                self._fill(By.ID, "txtID", context.get("id_number", ""))
                self._fill(By.ID, "txtMobile", context.get("mobile", ""))
                self._click(By.ID, "btnCreate")
            except Exception as e:
                self.emit("warning", {"phase": "create_profile", "error": str(e)})

    def step_personal_details(self, context: Dict[str, Any]):
        self.emit("step", {"name": "personal_details"})
        try:
            self._fill(By.ID, "firstName", context.get("first_name", ""))
            self._fill(By.ID, "lastName", context.get("last_name", ""))
            self._fill(By.ID, "dob", context.get("dob", ""))
            self._fill(By.ID, "idNumber", context.get("id_number", ""))
            self._fill(By.ID, "email", context.get("email", ""))
            self._fill(By.ID, "cell", context.get("mobile", ""))
            self._click(By.CSS_SELECTOR, "button.next, .btn-next")
        except Exception as e:
            self.emit("error", {"phase": "personal_details", "error": str(e)})
            raise

    def step_academic_program(self, context: Dict[str, Any]):
        self.emit("step", {"name": "academic_program"})
        try:
            self._click(By.ID, "applyNew")
            self._fill(By.ID, "qualificationSearch", context.get("programme", ""))
            self._click(By.CSS_SELECTOR, ".search-results .select:first-child, .result-row .select")
            self._click(By.CSS_SELECTOR, "button.next, .btn-next")
        except Exception as e:
            self.emit("error", {"phase": "academic_program", "error": str(e)})
            raise

    def step_address_and_background(self, context: Dict[str, Any]):
        self.emit("step", {"name": "address_background"})
        try:
            self._fill(By.ID, "addressLine1", context.get("address1", ""))
            self._fill(By.ID, "suburb", context.get("suburb", ""))
            self._fill(By.ID, "city", context.get("city", ""))
            self._fill(By.ID, "postalCode", context.get("postal_code", ""))
            self._click(By.CSS_SELECTOR, "button.next, .btn-next")
        except Exception as e:
            self.emit("error", {"phase": "address", "error": str(e)})
            raise

    def step_documents(self, context: Dict[str, Any]):
        self.emit("step", {"name": "upload_documents"})
        try:
            uploads = context.get("uploads", {})
            def set_file(input_selector: str, path_key: str):
                fpath = uploads.get(path_key)
                if not fpath:
                    self.emit("warning", {"phase": "upload", "missing": path_key})
                    return
                el = self._find(By.CSS_SELECTOR, input_selector)
                el.send_keys(fpath)

            set_file("input[type=file][name='id_doc']", "id_doc")
            set_file("input[type=file][name='results']", "results")
            set_file("input[type=file][name='residence_proof']", "residence_proof")
            set_file("input[type=file][name='affidavit']", "affidavit")
            self._click(By.CSS_SELECTOR, "button.next, .btn-next")
        except Exception as e:
            self.emit("error", {"phase": "documents", "error": str(e)})
            raise

    def step_fee_payment(self, context: Dict[str, Any]):
        self.emit("step", {"name": "fee_payment"})
        try:
            if context.get("fee_waiver", False):
                self._click(By.ID, "chkWaiver")
            else:
                self._click(By.ID, "payNow")
                # Redirect to payment gateway; simulate capture
                self._fill(By.ID, "cardNumber", context.get("card_number", ""))
                self._fill(By.ID, "cardName", context.get("card_name", ""))
                self._fill(By.ID, "expiry", context.get("card_expiry", ""))
                self._fill(By.ID, "cvv", context.get("card_cvv", ""))
                self._click(By.ID, "btnPay")
            self._click(By.CSS_SELECTOR, "button.next, .btn-next")
        except Exception as e:
            self.emit("error", {"phase": "fee_payment", "error": str(e)})
            raise

    def step_review_submit(self, context: Dict[str, Any]):
        self.emit("step", {"name": "review_submit"})
        try:
            self._click(By.ID, "terms")
            self._click(By.ID, "submitApplication")
            # capture reference number
            ref = None
            try:
                ref_el = self._find(By.CSS_SELECTOR, ".reference-number, #refNumber")
                ref = ref_el.text if ref_el else None
            except Exception:
                pass
            self.emit("result", {"status": "submitted", "reference": ref})
        except Exception as e:
            self.emit("error", {"phase": "submit", "error": str(e)})
            raise

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        self.emit("start", {"bot": "uj_bot"})
        try:
            self.login_or_create(context)
            self.step_personal_details(context)
            self.step_academic_program(context)
            self.step_address_and_background(context)
            self.step_documents(context)
            self.step_fee_payment(context)
            self.step_review_submit(context)
            self.emit("done", {"ok": True})
        except Exception as e:
            self.emit("done", {"ok": False, "error": str(e)})
        return {"events": self.events}


def run(driver: Any, context: Dict[str, Any]) -> Dict[str, Any]:
    return UJBot(driver).run(context)
