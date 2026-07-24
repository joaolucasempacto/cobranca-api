import logging

from fastapi import FastAPI

from app.core.logging import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI()


@app.get("/")
def home():
    logger.info("Health check endpoint acessado")
    return {"message": "API rodando 🚀"}