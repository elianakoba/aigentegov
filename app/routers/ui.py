from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.db.agendas import listar_filtros, consultar_agendas

router = APIRouter(tags=["UI"])
templates = Jinja2Templates(directory="app/templates")

COOKIE_NAME = "mvp_user_email"


def _require_login(request: Request):
    """
    Retorna o email do usuário se estiver logado.
    Caso contrário, retorna None.
    """
    return request.cookies.get(COOKIE_NAME)


@router.get("/home", response_class=HTMLResponse)
def home_page(request: Request):
    user_email = _require_login(request)
    if not user_email:
        return RedirectResponse(url="/login", status_code=302)

    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "title": "Dashboard",
            "header_title": "Dashboard",
            "active_page": "home",
            "user_email": user_email,
        },
    )


@router.get("/agendas", response_class=HTMLResponse)
def agendas_page(
    request: Request,
    id_pessoaagenteia: str | None = None,
    id_servicoespecializado: str | None = None,
    id_profissional: str | None = None,
    id_departamento: str | None = None,
):
    user_email = _require_login(request)
    if not user_email:
        return RedirectResponse(url="/login", status_code=302)

    # Converte strings vazias para None ou int
    def to_int(value):
        if value is None or value == "":
            return None
        return int(value)

    id_pessoaagenteia = to_int(id_pessoaagenteia)
    id_servicoespecializado = to_int(id_servicoespecializado)
    id_profissional = to_int(id_profissional)
    id_departamento = to_int(id_departamento)

    # Carrega filtros sempre
    especialidades, profissionais, unidades = listar_filtros()

    registros = None
    error = None

    if any([
        id_pessoaagenteia,
        id_servicoespecializado,
        id_profissional,
        id_departamento,
    ]):
        try:
            registros = consultar_agendas(
                id_pessoaagenteia=id_pessoaagenteia,
                id_servicoespecializado=id_servicoespecializado,
                id_profissional=id_profissional,
                id_departamento=id_departamento,
            )
        except Exception as e:
            error = str(e)

    return templates.TemplateResponse(
        "agendas.html",
        {
            "request": request,
            "title": "Agendas",
            "header_title": "Agendas",
            "active_page": "agendas",
            "user_email": user_email,

            # filtros
            "especialidades": especialidades,
            "profissionais": profissionais,
            "unidades": unidades,

            # valores selecionados (para manter seleção)
            "id_pessoaagenteia": id_pessoaagenteia,
            "id_servicoespecializado": id_servicoespecializado,
            "id_profissional": id_profissional,
            "id_departamento": id_departamento,

            # resultado
            "registros": registros,
            "error": error,
        },
    )
