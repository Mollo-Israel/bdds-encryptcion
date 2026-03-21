# BCB Rate Service

Microservicio que simula el tipo de cambio oficial del Banco Central de Bolivia (BCB).

El tipo de cambio es **determinista y configurable manualmente** vía API:

```
tipo_final = tipo_cambio_base + oscilacion
```

## Variables de entorno

| Variable | Default | Descripción |
|---|---|---|
| `BASE_RATE` | `6.86` | Tipo de cambio base inicial (BOB/USD) |
| `OSCILACION` | `0.0` | Oscilación inicial sobre la base |
| `PRECISION` | `4` | Decimales de precisión |

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Estado del servicio y uptime |
| GET | `/rate` | Tipo de cambio actual (base + oscilación) |
| GET | `/snapshot` | Tipo de cambio + parámetros de configuración + timestamp |
| GET | `/config` | Consulta configuración actual (base, oscilación, tipo_final) |
| PATCH | `/config` | **Configura manualmente** base y/u oscilación |

## Configurar el tipo de cambio

```bash
# Cambiar base y oscilación en una sola llamada
curl -X PATCH http://localhost:9101/config \
  -H "Content-Type: application/json" \
  -d '{"tipo_cambio_base": 6.86, "oscilacion": 0.14}'
# tipo_final = 7.0000

# Cambiar sólo la oscilación
curl -X PATCH http://localhost:9101/config \
  -H "Content-Type: application/json" \
  -d '{"oscilacion": -0.5}'

# Consultar configuración actual
curl http://localhost:9101/config
```

### Reglas de oscilación
- Rango válido: `[-0.9999, 0.9999]`
- Valores fuera de rango retornan HTTP 422

## Ejecución

```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 9101 --reload
```

Documentación automática: `http://localhost:9101/docs`
