from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging
from datetime import datetime
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="University Application Orchestrator",
    description="Central orchestration server for university application automation",
    version="1.0.0"
)

# In-memory storage (replace with database in production)
applications = {}
email_queue = []
bot_status = {}

# Data Models
class EmailNotification(BaseModel):
    email_id: str
    university_name: str
    application_link: str
    subject: str
    received_at: str
    applicant_data: Optional[Dict] = None

class BotStatus(BaseModel):
    bot_id: str
    university_name: str
    status: str  # idle, running, completed, failed
    current_task: Optional[str] = None
    last_updated: str

class ApplicationStatus(BaseModel):
    application_id: str
    university_name: str
    status: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None

# Orchestrator Endpoints

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "University Application Orchestrator",
        "version": "1.0.0",
        "status": "active",
        "endpoints": [
            "/email/notify",
            "/bot/status",
            "/application/status/{application_id}",
            "/applications/list"
        ]
    }

@app.post("/email/notify")
async def receive_email_notification(notification: EmailNotification, background_tasks: BackgroundTasks):
    """
    Receive notification from Gmail bot about new university email
    """
    logger.info(f"Received email notification for {notification.university_name}")
    
    # Generate unique application ID
    app_id = f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{notification.university_name.lower().replace(' ', '_')}"
    
    # Store application
    applications[app_id] = {
        "id": app_id,
        "university_name": notification.university_name,
        "application_link": notification.application_link,
        "email_id": notification.email_id,
        "subject": notification.subject,
        "status": "pending",
        "received_at": notification.received_at,
        "applicant_data": notification.applicant_data
    }
    
    # Add to email queue
    email_queue.append(app_id)
    
    # Trigger bot in background
    background_tasks.add_task(trigger_university_bot, app_id)
    
    return {
        "success": True,
        "application_id": app_id,
        "message": f"Application queued for {notification.university_name}"
    }

@app.post("/bot/status")
async def update_bot_status(status: BotStatus):
    """
    Receive status updates from university bots
    """
    logger.info(f"Bot status update: {status.bot_id} - {status.status}")
    
    bot_status[status.bot_id] = status.dict()
    
    return {"success": True, "message": "Bot status updated"}

@app.get("/application/status/{application_id}")
async def get_application_status(application_id: str):
    """
    Get status of a specific application
    """
    if application_id not in applications:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return applications[application_id]

@app.get("/applications/list")
async def list_applications(status: Optional[str] = None):
    """
    List all applications, optionally filtered by status
    """
    if status:
        filtered = {k: v for k, v in applications.items() if v["status"] == status}
        return {"applications": list(filtered.values()), "count": len(filtered)}
    
    return {"applications": list(applications.values()), "count": len(applications)}

@app.post("/application/{application_id}/update")
async def update_application_status(
    application_id: str,
    status: str,
    error_message: Optional[str] = None
):
    """
    Update application status from university bot
    """
    if application_id not in applications:
        raise HTTPException(status_code=404, detail="Application not found")
    
    applications[application_id]["status"] = status
    applications[application_id]["last_updated"] = datetime.now().isoformat()
    
    if status == "completed":
        applications[application_id]["completed_at"] = datetime.now().isoformat()
    
    if error_message:
        applications[application_id]["error_message"] = error_message
    
    logger.info(f"Application {application_id} status updated to {status}")
    
    return {"success": True, "application": applications[application_id]}

async def trigger_university_bot(application_id: str):
    """
    Background task to trigger appropriate university bot
    """
    logger.info(f"Triggering bot for application {application_id}")
    
    application = applications[application_id]
    university_name = application["university_name"]
    
    # Update status
    applications[application_id]["status"] = "processing"
    applications[application_id]["started_at"] = datetime.now().isoformat()
    
    # Here you would implement logic to:
    # 1. Identify the correct bot for the university
    # 2. Send request to the bot service
    # 3. Monitor bot execution
    
    # Placeholder for bot triggering logic
    logger.info(f"Bot triggered for {university_name}")
    
    # In production, this would make an API call to the specific university bot
    # For now, we'll just log the action
    bot_endpoint = f"http://localhost:8001/bot/{university_name.lower().replace(' ', '_')}"
    logger.info(f"Would call bot endpoint: {bot_endpoint}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
