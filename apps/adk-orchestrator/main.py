import os, uuid, json, logging, yaml
from datetime import datetime
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, APIRouter, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware

from security.jwt import get_principal, get_tenant
from security.models import Principal, TenantContext

# --- simple JSON logger ---
logging.basicConfig(level=logging.INFO, format='{"level":"%(levelname)s","msg":"%(message)s"}')
log = logging.getLogger("kyros")

# --- Security Headers Middleware ---
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Set security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "accelerometer=(), geolocation=(), microphone=()"
        
        # Only set HSTS in production (commented in dev)
        if os.getenv("NODE_ENV") == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response

# --- config loader ---
def load_config():
    base_path = os.path.join(os.path.dirname(__file__), "config")
    def read(name):
        p = os.path.join(base_path, name)
        return yaml.safe_load(open(p)) if os.path.exists(p) else {}
    cfg = {}
    for part in ("base.yaml","development.yaml"):
        cfg.update(read(part))
    return cfg

# --- DTOs ---
class PRRef(BaseModel):
    repo: str; pr_number: int; branch: str; head_sha: str
    html_url: Optional[str] = None

class RunRequest(BaseModel):
    pr: PRRef
    mode: str = Field(..., pattern="^(plan|implement|critic|integrate|pipeline)$")
    labels: List[str] = []
    extra: Dict[str, Any] = {}

class RunResponse(BaseModel):
    run_id: str; status: str; started_at: str; notes: Optional[str] = None

# --- very small "workflow" shim (will call engine later) ---
ROUTER_BASE = os.getenv("LLM_ROUTER_BASE", "http://localhost:4000")
MODEL_PLANNER = os.getenv("MODEL_PLANNER", "gpt-5-high")
MODEL_IMPL    = os.getenv("MODEL_IMPL", "gemini-2.5-pro")
MODEL_DEEP    = os.getenv("MODEL_DEEP", "claude-4-sonnet")
def run_with_engine(mode: str, pr: PRRef, labels: List[str], extra: Dict[str, Any]) -> str:
    needs_deep = any(l in labels for l in ["needs:deep-refactor","complex"])
    impl = MODEL_DEEP if needs_deep else MODEL_IMPL
    return f"[{mode}] {pr.repo}#{pr.pr_number} ({pr.branch}) planner={MODEL_PLANNER} impl={impl}"

# --- FastAPI setup ---
app = FastAPI(title="Kyros Orchestrator")

# Add security middleware (order matters - added in reverse order of execution)
config = load_config()

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.localhost"]
)

# Add GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add CORS middleware
cors_origins = config.get("cors", {}).get("allowed_origins", ["http://localhost:3001"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,  # Token-only auth, no cookies
    allow_methods=["*"],
    allow_headers=["*"],
)

api = APIRouter(prefix="/v1")

@api.post("/runs/plan", response_model=RunResponse)
def runs_plan(
    req: RunRequest,
    principal: Principal = Depends(get_principal),
    tenant: TenantContext = Depends(get_tenant)
):
    run_id = str(uuid.uuid4())
    notes = run_with_engine("plan", req.pr, req.labels, req.extra)
    
    # Log with request context
    log.info(json.dumps({
        "event": "run_started",
        "request_id": run_id,
        "actor": principal.sub,
        "tenant_id": tenant.id,
        "mode": "plan"
    }))
    
    return RunResponse(run_id=run_id, status="started", started_at=datetime.utcnow().isoformat()+"Z", notes=notes)

# other run endpoints would be similar
app.include_router(api)

@app.get("/healthz")
def healthz(): return {"ok": True}

@app.get("/readyz")
def readyz(): return {"ready": True}

@app.get("/v1/config")
def cfg(): return load_config()