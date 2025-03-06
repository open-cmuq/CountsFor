from fastapi import FastAPI
from backend.app.routers import courses, requirements

app = FastAPI()

app.include_router(courses.router)
app.include_router(requirements.router)


@app.get("/")
def read_root():
    return {"Hello": "World"}

