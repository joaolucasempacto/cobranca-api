import logging

from fastapi import FastAPI

from app.core.logging import setup_logging
from app.exceptions.base import AppError
from app.exceptions.handlers import (
    app_error_handler,
    unhandled_exception_handler,
)

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)


@app.get("/")
def home():
    logger.info("Health check endpoint acessado")
    return {"message": "API rodando 🚀"}

