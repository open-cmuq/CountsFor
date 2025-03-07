"""
this script is the entry point for the FastAPI application.
"""
from fastapi import FastAPI
from backend.app.routers import courses

app = FastAPI()

app.include_router(courses.router)
