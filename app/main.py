from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

from app.api.leads import router as leads_router
from app.core.logging_config import setup_logging
from app.api.gmail import router as gmail_router


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_logging()

@app.get("/")
def home():
    return {
        "message": "AI Lead Agent is running!"
    }


app.include_router(leads_router)
app.include_router(gmail_router)