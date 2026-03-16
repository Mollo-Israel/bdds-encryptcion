from fastapi import FastAPI

from config import ALGORITHM, BANK_NAME
from database.connection import init_db
from routes.accounts import router as accounts_router
from routes.health import router as health_router

app = FastAPI(
    title=f"{BANK_NAME} - Bank Service",
    description=f"Microservicio bancario | Algoritmo: {ALGORITHM}",
    version="1.0.0",
)

app.include_router(health_router)
app.include_router(accounts_router)


@app.on_event("startup")
def startup():
    init_db()
