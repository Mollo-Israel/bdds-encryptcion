import random
import threading
import time
from datetime import datetime, timedelta

from config import BASE_RATE, MAX_VARIATION, PRECISION, UPDATE_INTERVAL_SECONDS


class RateEngine:
    def __init__(self):
        self._current_rate: float = BASE_RATE
        self._last_update: datetime = datetime.utcnow()
        self._lock = threading.Lock()
        self._thread = threading.Thread(target=self._update_loop, daemon=True)
        self._thread.start()

    def _calculate_new_rate(self) -> float:
        variation = random.uniform(-MAX_VARIATION, MAX_VARIATION)
        new_rate = BASE_RATE + variation
        return round(max(new_rate, 0.0001), PRECISION)

    def _update_loop(self):
        while True:
            time.sleep(UPDATE_INTERVAL_SECONDS)
            with self._lock:
                self._current_rate = self._calculate_new_rate()
                self._last_update = datetime.utcnow()

    def get_rate(self) -> float:
        with self._lock:
            return self._current_rate

    def get_snapshot(self) -> dict:
        with self._lock:
            next_update = self._last_update + timedelta(seconds=UPDATE_INTERVAL_SECONDS)
            return {
                "rate": self._current_rate,
                "timestamp": self._last_update,
                "next_update": next_update,
            }


# Instancia global compartida
rate_engine = RateEngine()
