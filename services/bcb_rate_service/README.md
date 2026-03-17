# BCB Rate Service

Microservicio que simula el tipo de cambio oficial del Banco Central de Bolivia (BCB).

## Configuración (`config.py`)

| Parámetro | Valor por defecto | Descripción |
|---|---|---|
| `BASE_RATE` | `6.86` | Tipo de cambio base USD → Bs |
| `UPDATE_INTERVAL_SECONDS` | `180` | Intervalo de actualización (3 min) |
| `MAX_VARIATION` | `0.9999` | Variación máxima ±0.9999 |
| `PRECISION` | `4` | Decimales de precisión |

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Estado del servicio y uptime |
| GET | `/rate` | Tasa de cambio actual |
| GET | `/snapshot` | Tasa + timestamp + próxima actualización |

## Ejecución

```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Documentación automática: `http://localhost:8000/docs`
