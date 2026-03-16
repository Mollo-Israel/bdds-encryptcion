# Bank Service Template

Plantilla base para los 14 microservicios bancarios.
Cada banco hereda esta estructura y sobreescribe `encryption_service.py` con su algoritmo.

## Variables de entorno

| Variable | Descripción | Ejemplo |
|---|---|---|
| `BANK_ID` | ID numérico del banco | `1` |
| `BANK_NAME` | Nombre del banco | `Banco Unión S.A.` |
| `ALGORITHM` | Algoritmo de cifrado | `CESAR` |
| `DB_ENGINE` | Motor de BD | `sqlite` / `postgresql` / `mysql` |
| `DB_URL` | Cadena de conexión | `sqlite:///./bank.db` |
| `PORT` | Puerto del servicio | `8001` |

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Estado, banco, algoritmo, uptime |
| GET | `/accounts` | Lista cuentas con saldo cifrado |
| POST | `/accounts/load` | Carga y cifra cuentas nuevas |
| POST | `/accounts/update` | Actualiza saldo convertido en Bs. |

## Cómo replicar para un banco específico

1. Copiar esta carpeta: `cp -r bank_service_template banco_union`
2. Crear `services/encryption_service.py` con el algoritmo del banco
3. Configurar variables de entorno o `.env`
4. Ejecutar:

```bash
pip install -r requirements.txt
BANK_ID=1 BANK_NAME="Banco Union S.A." ALGORITHM=CESAR python -m uvicorn main:app --port 8001
```

## Estructura

```
bank_service_template/
├── main.py                      # App FastAPI + startup
├── config.py                    # Variables de configuración
├── requirements.txt
├── database/
│   └── connection.py            # SQLAlchemy engine + session
├── models/
│   └── account.py               # ORM + Pydantic schemas
├── routes/
│   ├── health.py                # GET /health
│   └── accounts.py              # GET|POST /accounts
└── services/
    ├── encryption_service.py    # Interfaz base (sobreescribir por banco)
    └── account_service.py       # Lógica de negocio
```
