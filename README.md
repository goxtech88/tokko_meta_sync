# ⚡ TokkoSync — Tokko Broker → Meta Ads Catalog

Sincroniza automáticamente las propiedades publicadas en **Tokko Broker** con un catálogo de **Meta Ads** (Facebook/Instagram) para crear campañas de listings inmobiliarios.

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green?logo=fastapi)
![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Features

- 🔗 **Conexión a Tokko Broker API** — Obtiene propiedades publicadas en venta/alquiler
- 📘 **Integración con Meta Ads** — Crea y actualiza catálogos de Home Listings
- 🖥️ **Interfaz Web moderna** — Dark mode, glassmorphism, responsive
- 🔑 **Sistema de licencia** — Validación por UUID
- 🐳 **Docker-ready** — Un solo `docker compose up` en cualquier VPS
- 📊 **Dashboard** — Historial de syncs, estadísticas, logs

## 🚀 Quick Start

### Con Docker (recomendado)

```bash
git clone https://github.com/tu-usuario/tokko-meta-sync.git
cd tokko-meta-sync
docker compose up -d
```

Acceder a `http://localhost:8000`

### Sin Docker

```bash
git clone https://github.com/tu-usuario/tokko-meta-sync.git
cd tokko-meta-sync
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## ⚙️ Configuración

Al iniciar la app por primera vez:

1. **Activar licencia** — Ingresar la clave UUID proporcionada
2. **Configurar Tokko Broker** — Ir a ⚙️ Configuración → Ingresar API Key → Test conexión
3. **Configurar Meta Ads** — Ingresar App ID, Secret, Access Token y Business ID → Test conexión
4. **Sincronizar** — Ir a 🔄 Sincronizar → Ejecutar Sync

### Credenciales necesarias

| Credencial | Dónde obtenerla |
|---|---|
| **Tokko API Key** | tokkobroker.com → Mi Empresa → Permisos |
| **Meta App ID / Secret** | developers.facebook.com → Tu App |
| **Meta Access Token** | Graph API Explorer o token de larga duración |
| **Meta Business ID** | business.facebook.com → Configuración |

## 🏗️ Arquitectura

```
tokko-meta-sync/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── database.py          # SQLite storage
│   ├── models.py            # Pydantic schemas
│   ├── routers/             # API endpoints
│   │   ├── settings.py      # CRUD credenciales
│   │   ├── sync.py          # Ejecutar/ver syncs
│   │   ├── properties.py    # Listar propiedades
│   │   └── license.py       # Activación de licencia
│   ├── services/            # Business logic
│   │   ├── tokko_client.py  # Tokko Broker API
│   │   ├── meta_catalog.py  # Meta Ads SDK
│   │   └── mapper.py        # Tokko → Meta mapping
│   └── static/              # Frontend SPA
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## 📖 API Docs

Con la app corriendo, visitar: `http://localhost:8000/docs` (Swagger UI automático de FastAPI)

## 📄 License

MIT — ver [LICENSE](LICENSE)
