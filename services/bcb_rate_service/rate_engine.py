"""
Motor de tipo de cambio BCB.

Diseño:
  - tipo_cambio_base  : valor base configurable (env o API)
  - oscilacion        : ajuste manual configurable, rango [-0.9999, 0.9999]
  - tipo_final        : base + oscilacion  (mínimo 0.0001 para evitar cero)

No hay variación aleatoria: el tipo es determinista y sólo cambia
cuando un operador llama PATCH /config.
"""

import threading
from datetime import datetime

from config import BASE_RATE, OSCILACION, PRECISION

_OSCILACION_MIN = -0.9999
_OSCILACION_MAX = 0.9999


def _clamp_oscilacion(value: float) -> float:
    return max(_OSCILACION_MIN, min(_OSCILACION_MAX, value))


def _compute_rate(base: float, oscilacion: float, precision: int) -> float:
    raw = base + oscilacion
    return round(max(raw, 0.0001), precision)


class RateEngine:
    def __init__(self):
        self._base: float = BASE_RATE
        self._oscilacion: float = _clamp_oscilacion(OSCILACION)
        self._precision: int = PRECISION
        self._current_rate: float = _compute_rate(self._base, self._oscilacion, self._precision)
        self._last_update: datetime = datetime.utcnow()
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Setters configurables
    # ------------------------------------------------------------------

    def set_base(self, value: float) -> float:
        """Actualiza tipo_cambio_base y recalcula. Devuelve el tipo final."""
        with self._lock:
            self._base = value
            self._current_rate = _compute_rate(self._base, self._oscilacion, self._precision)
            self._last_update = datetime.utcnow()
            return self._current_rate

    def set_oscilacion(self, value: float) -> float:
        """
        Actualiza oscilacion (rango [-0.9999, 0.9999]) y recalcula.
        Devuelve el tipo final.
        Lanza ValueError si el valor está fuera del rango permitido.
        """
        if value < _OSCILACION_MIN or value > _OSCILACION_MAX:
            raise ValueError(
                f"oscilacion debe estar en [{_OSCILACION_MIN}, {_OSCILACION_MAX}], "
                f"se recibió {value}"
            )
        with self._lock:
            self._oscilacion = value
            self._current_rate = _compute_rate(self._base, self._oscilacion, self._precision)
            self._last_update = datetime.utcnow()
            return self._current_rate

    def set_config(self, base: float | None = None, oscilacion: float | None = None) -> float:
        """
        Actualiza base y/o oscilacion en una sola operación atómica.
        Devuelve el tipo final resultante.
        """
        if oscilacion is not None and (oscilacion < _OSCILACION_MIN or oscilacion > _OSCILACION_MAX):
            raise ValueError(
                f"oscilacion debe estar en [{_OSCILACION_MIN}, {_OSCILACION_MAX}], "
                f"se recibió {oscilacion}"
            )
        with self._lock:
            if base is not None:
                self._base = base
            if oscilacion is not None:
                self._oscilacion = oscilacion
            self._current_rate = _compute_rate(self._base, self._oscilacion, self._precision)
            self._last_update = datetime.utcnow()
            return self._current_rate

    # ------------------------------------------------------------------
    # Getters
    # ------------------------------------------------------------------

    def get_rate(self) -> float:
        with self._lock:
            return self._current_rate

    def get_snapshot(self) -> dict:
        with self._lock:
            return {
                "rate": self._current_rate,
                "tipo_cambio_base": self._base,
                "oscilacion": self._oscilacion,
                "timestamp": self._last_update,
            }


# Instancia global compartida
rate_engine = RateEngine()
