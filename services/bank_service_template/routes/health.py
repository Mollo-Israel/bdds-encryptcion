import time

from fastapi import APIRouter
from pydantic import BaseModel

from config import ALGORITHM, BANK_ID, BANK_NAME

router = APIRouter()
_start_time = time.time()


class HealthResponse(BaseModel):
    status: str
    bank_id: int
    bank_name: str
    algorithm: str
    uptime_seconds: float


@router.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="ok",
        bank_id=BANK_ID,
        bank_name=BANK_NAME,
        algorithm=ALGORITHM,
        uptime_seconds=round(time.time() - _start_time, 2),
    )
