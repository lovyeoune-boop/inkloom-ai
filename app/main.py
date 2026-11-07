from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from .manager_bootstrap import bootstrap_manager
from .routes import auth, reports, rule_book

Base.metadata.create_all(bind=engine)

app = FastAPI(title="BrandGuard Kids API", version="0.1.0",
              description="Age-aware child-facing content review MVP. Human review is required.")

@app.on_event("startup")
def initialize_configured_manager():
    bootstrap_manager()

app.add_middleware(
    CORSMiddleware,
     allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router)
app.include_router(reports.router)
app.include_router(rule_book.router)

@app.get("/health")
def health():
    return {"status": "ok", "service": "BrandGuard Kids API"}
