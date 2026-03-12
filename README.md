# Nerius Backend

Mini proyecto base para un backend con FastAPI, SQLAlchemy y Alembic.

## Requisitos

- Python 3.11 o superior

## Instalacion

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Variables de entorno

La configuracion se carga desde `.env` usando `pydantic-settings`.

Variables principales:

- `APP_NAME`
- `APP_ENV`
- `APP_DEBUG`
- `API_V1_PREFIX`
- `DATABASE_URL`
- `DB_ECHO`

## Ejecutar la API

```bash
uvicorn src.main:app --reload
```

## Ejecutar migraciones

Crear una nueva migracion:

```bash
alembic revision --autogenerate -m "descripcion"
```

Aplicar migraciones:

```bash
alembic upgrade head
```