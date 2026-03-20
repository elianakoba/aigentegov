from pathlib import Path
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# ==========================================
# Paths robustos (não dependem do "cd")
# ==========================================
BASE_DIR = Path(__file__).resolve().parent  # ...\web
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="AiGENTEGOV - Web (Agendamento)")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# ==========================================
# Static (CSS/JS/IMG) do site
# URL: /static/...
# ==========================================
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# ==========================================
# Rotas WEB (renderizam templates)
# ==========================================
@app.get("/", response_class=HTMLResponse)
def root():
    return RedirectResponse(url="/login", status_code=302)

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, error: str | None = None):
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": error, "title": "Login | AiGENTEGOV"}
    )

@app.post("/login")
def login_submit(email: str = Form(...), senha: str = Form(...)):
    # MVP: validação simples (trocar depois por auth real)
    if email and senha:
        return RedirectResponse(url="/home", status_code=302)
    return RedirectResponse(url="/login?error=Credenciais inválidas", status_code=302)

@app.get("/logout")
def logout():
    return RedirectResponse(url="/login", status_code=302)

@app.get("/home", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "title": "Dashboard | AiGENTEGOV",
            "active_page": "home",
            "header_title": "Dashboard",
            "user_email": "admin@aigentegov.com",
        }
    )

@app.get("/central_agenda", response_class=HTMLResponse)
def central_agenda(request: Request):
    # Depois: buscar nas APIs do app (http://localhost:8000/...)
    especialidades = [(1, "Clínica Geral"), (2, "Odontologia")]
    profissionais = [(1, "Dr. João"), (2, "Dra. Maria")]
    unidades = [(1, "UBS Centro"), (2, "UBS Norte")]

    return templates.TemplateResponse(
        "central_agenda.html",
        {
            "request": request,
            "title": "Central de Agendas | AiGENTEGOV",
            "active_page": "central_agenda",
            "header_title": "Central de Agendas",
            "user_email": "admin@aigentegov.com",
            "especialidades": especialidades,
            "profissionais": profissionais,
            "unidades": unidades,
        }
    )
