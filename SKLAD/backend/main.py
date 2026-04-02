from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import statuses, contacts, locations, containers, fixtures, loads

app = FastAPI(
    title="Warehouse Management API",
    description="Backend for fixture and container inventory management.",
    version="1.0.0"
)

# Allow localhost frontend (Phase 2 React app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(statuses.router)
app.include_router(contacts.router)
app.include_router(locations.router)
app.include_router(containers.router)
app.include_router(fixtures.router)
app.include_router(loads.router)


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "message": "Warehouse API is running. Visit /docs for the interactive interface."}
