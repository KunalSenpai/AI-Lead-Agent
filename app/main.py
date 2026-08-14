from fastapi import FastAPI

from app.api.leads import router as leads_router
from app.core.logging_config import setup_logging


app = FastAPI()

setup_logging()

@app.get("/")
def home():
    return {
        "message": "AI Lead Agent is running!"
    }


app.include_router(leads_router)