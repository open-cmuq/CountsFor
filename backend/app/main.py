from fastapi import FastAPI
from backend.app.routers import courses

app = FastAPI()

app.include_router(courses.router)


@app.get("/")
def read_root():
    return {"Hello": "World"}

