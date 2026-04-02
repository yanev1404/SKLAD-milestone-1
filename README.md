# Warehouse Inventory Management System

A self-hosted, desktop-local inventory system for managing stage fixtures and transport containers across multiple locations. Tracks equipment packed into containers, supports load operations with barcode scanner input, and maintains a full audit trail of every status change.

---

## Stack

| Layer | Technology |
|---|---|
| Database | PostgreSQL 15+ |
| Backend API | Python 3.14 + FastAPI (latest) |
| Interface | Swagger UI at `localhost:8000/docs` |
| Local server | Windows 10, runs manually from cmd |
| Phase 2 (planned) | React frontend at `localhost:3000` |

---

## Project Structure

```
SKLAD\
├── .env                        ← your local credentials (never commit)
├── .env.example                ← template — copy this to .env
├── .gitignore
├── README.md
├── start_server.bat            ← double-click or run from cmd
├── .venv\                      ← Python virtual environment (local only)
├── db\
│   └── schema.sql              ← full PostgreSQL schema + seed data
└── backend\
    ├── __init__.py
    ├── main.py                 ← FastAPI app entry point
    ├── config.py               ← reads .env for DB credentials
    ├── database.py             ← SQLAlchemy engine + session
    ├── models.py               ← ORM table definitions
    ├── schemas.py              ← Pydantic request/response models
    ├── requirements.txt
    └── routers\
        ├── __init__.py
        ├── statuses.py
        ├── contacts.py
        ├── locations.py
        ├── containers.py
        ├── fixtures.py
        └── loads.py            ← Pack a Load workflow + storno
```

---

## Setting Up on a New Machine

### Prerequisites

- Windows 10
- [PostgreSQL 15+](https://www.postgresql.org/download/windows/) — install with default settings, note the password you set for the `postgres` user
- [pgAdmin 4](https://www.pgadmin.org/download/) — usually bundled with PostgreSQL installer
- [Python 3.11 or 3.12](https://www.python.org/downloads/) — **do not use Python 3.14**, pre-built wheels for some dependencies are not available yet. During install, check **"Add Python to PATH"**
- [Git](https://git-scm.com/download/win)

> **Python version note:** The project was initially developed with Python 3.14 on Windows, which required installing packages without a virtual environment due to missing pre-built wheels. Python 3.11 or 3.12 is strongly recommended on new machines to avoid this.

---

### 1. Clone the repository

Open cmd and run:

```bat
cd C:\Users\%USERNAME%\Downloads
git clone https://github.com/avlasarev/warehouse.git SKLAD
cd SKLAD
```

---

### 2. Create the Python virtual environment

```bat
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r backend\requirements.txt
```

You should see all packages install cleanly without any Rust/compilation errors. If you see errors about `pydantic-core` requiring Rust, your Python version is too new — install Python 3.12 and repeat.

---

### 3. Configure credentials

Copy the example env file and fill in your PostgreSQL password:

```bat
copy .env.example .env
notepad .env
```

Edit the file:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=warehouse_db
DB_USER=postgres
DB_PASS=your_postgres_password_here
SERVER_HOST=127.0.0.1
SERVER_PORT=8000
```

Save and close. The `.env` file is excluded from git by `.gitignore` — it will never be committed.

---

### 4. Create the database in pgAdmin

Open pgAdmin 4 and connect to your local PostgreSQL server.

**Create the database:**
- In the left panel, right-click **Databases** → **Create** → **Database**
- Name: `warehouse_db`
- Click **Save**

**Apply the schema:**
- Click on `warehouse_db` to select it
- Click **Tools** → **Query Tool**
- Click the folder icon → navigate to `SKLAD\db\schema.sql` → open
- Press **F5** to execute

You should see output ending with no errors. This creates all tables, seeds the default statuses, and creates a default `WH-MAIN` warehouse location with its placeholder container.

**Verify it worked:**
- In the left panel expand `warehouse_db` → **Schemas** → **public** → **Tables**
- You should see: `contacts`, `containers`, `fixtures`, `load_containers`, `load_fixtures`, `load_log`, `loads`, `locations`, `status_change_log`, `statuses`

---

### 5. Start the API server

Option A — double-click `start_server.bat` in the SKLAD folder.

Option B — from cmd:

```bat
cd C:\Users\%USERNAME%\Downloads\SKLAD
.venv\Scripts\activate.bat
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Wait for:

```
INFO:     Application startup complete.
```

Keep this window open — closing it stops the server.

---

### 6. Verify everything works

Open your browser and go to:

```
http://localhost:8000/docs
```

You should see the Swagger UI. To confirm the database connection:

- Expand **GET /statuses/** → click **Try it out** → **Execute**
- You should get back a list of 6 statuses: `in storage`, `packed`, `in transit`, `on location`, `in repair`, `retired`

If you get a `500` error, check that:
1. PostgreSQL is running (open pgAdmin — if it connects, PostgreSQL is running)
2. The password in `.env` matches your pgAdmin login password
3. The schema was applied successfully in step 4

---

## Using the System (Phase 1)

All data entry and operations are done through the Swagger UI at `http://localhost:8000/docs`.

### Recommended data entry order

Enter data in this sequence to satisfy foreign key dependencies:

1. **Statuses** — review defaults, add any custom ones via `POST /statuses/`
2. **Contacts** — companies and people linked to locations
3. **Locations** — each location auto-creates a placeholder container on creation
4. **Containers** — assign to a location and status
5. **Fixtures** — assign to a container and status

### Importing data from Excel/CSV

Use pgAdmin's built-in import tool for bulk data entry:

- In pgAdmin, right-click the target table → **Import/Export Data**
- Set **Format** to `csv`, enable **Header**
- Select your CSV file and map columns to match the table fields
- Click **OK**

CSV column order for each table must match the schema. Key rules:
- `contacts` before `locations` (locations reference contacts)
- `locations` before `containers` (containers reference locations)
- `containers` before `fixtures` (fixtures reference containers)
- All `status_id` values must reference existing rows in the `statuses` table

---

## Pack a Load Workflow

1. In Swagger UI, open **POST /loads/**
2. Provide:
   - `origin_location_id` — where containers currently are
   - `destination_location_id` — where they are going
   - `container_ids` — list of container IDs (numeric, matches barcode)
   - `deselected_fixture_ids` — fixtures to leave behind (moved to origin placeholder)
   - `note` — optional
3. On submit, all selected containers and fixtures move to the destination with status `packed`. Deselected fixtures move to the origin placeholder container.

### View load manifest

```
GET /loads/{load_id}/manifest
```

Returns all containers, their fixtures, total weight (kg), and total volume (m³).

### Undo a load (Storno)

```
POST /loads/{load_id}/storno
```

Only the most recently completed load can be stornoed. Restores all containers and fixtures to their previous status and location.

---

## Barcode Scanner

Container barcodes encode the numeric `container_id` only. The scanner acts as a keyboard input — scanning sends the number and Enter, which maps to:

```
GET /containers/{container_id}
```

Returns the container and all its fixtures. Any additional printed text on the label is for human reading only and is ignored by the system.

---

## API Quick Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/statuses` | List all statuses |
| POST | `/statuses` | Add a new status |
| DELETE | `/statuses/{id}` | Delete a status (blocked if in use) |
| GET/POST/PUT/DELETE | `/contacts` | Manage contacts |
| GET/POST/PUT/DELETE | `/locations` | Manage locations |
| GET/POST/PUT/DELETE | `/containers` | Manage containers |
| GET | `/containers/{id}` | Barcode lookup — returns container + fixtures |
| POST | `/containers/{id}/status` | Manual status change (logged) |
| GET/POST/PUT/DELETE | `/fixtures` | Manage fixtures |
| POST | `/fixtures/{id}/status` | Manual status change (logged) |
| POST | `/loads` | Create and complete a load |
| GET | `/loads/{id}/manifest` | Live load manifest report |
| POST | `/loads/{id}/storno` | Undo the most recent load |

Full interactive docs always available at `http://localhost:8000/docs`.

---

## Database Views (pgAdmin)

Query these directly in pgAdmin's Query Tool for quick inspection:

| View | Description |
|---|---|
| `v_fixtures_full` | All fixtures with container, location, and status |
| `v_container_summary` | Containers with tare weight, fixture weight, volume, counts |
| `v_load_manifest` | All containers and fixtures per load |

Example:
```sql
SELECT * FROM v_fixtures_full;
SELECT * FROM v_container_summary WHERE location = 'WH-MAIN';
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `500 Internal Server Error` on any request | Check uvicorn window for DB error — usually wrong password in `.env` |
| `password authentication failed` | Update `DB_PASS` in `.env`, restart server |
| `database "warehouse_db" does not exist` | Run step 4 — create DB and apply schema in pgAdmin |
| `No module named 'backend'` | You're running uvicorn from inside the `backend\` folder — always run from the project root |
| `No module named 'fastapi'` | Virtual environment not activated — run `.venv\Scripts\activate.bat` first |
| `Extra inputs are not permitted` (pydantic error) | `config.py` is missing `"extra": "ignore"` in `model_config` — see config.py fix below |
| `pydantic-core` Rust compilation error during pip install | Python version too new — use Python 3.11 or 3.12 |

### config.py fix (if needed)

If you see a pydantic validation error about `server_host` or `server_port`, open `backend\config.py` and make sure the last line of the class reads:

```python
model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}
```

---

## Roadmap

- [x] PostgreSQL schema with full audit logging
- [x] FastAPI backend — CRUD for all entities
- [x] Pack a Load workflow with deselection and placeholder logic
- [x] Load manifest with weight and volume totals
- [x] Storno — sequential load undo
- [x] Manual status change with audit log
- [ ] CSV import endpoint (upload directly via API)
- [ ] React frontend — data entry forms
- [ ] React frontend — Pack a Load form with barcode scanner input
- [ ] React frontend — live manifest report view
- [ ] React frontend — Storno UI
- [ ] Windows Service wrapper for auto-start on boot

---

## Important Notes

- The `status_change_log` table is append-only — never delete rows from it
- Placeholder containers are auto-created when a location is created — do not delete them manually
- The server must always be started from the **project root** folder, not from inside `backend\`
- The `.env` file must never be committed to git — it is excluded by `.gitignore`
- All timestamps are stored in UTC

---

## License

Internal use — not for public distribution.
