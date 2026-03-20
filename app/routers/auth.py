from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

import bcrypt

from app.db.postgres import get_postgres_connection


router = APIRouter(tags=["Auth"])
templates = Jinja2Templates(directory="app/templates")

COOKIE_NAME = "mvp_user_email"

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@router.post("/login", response_class=HTMLResponse)
def do_login(request: Request, email: str = Form(...), senha: str = Form(...)):
    conn = get_postgres_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT email, senha_hash, situacao
                FROM public.usuario
                WHERE email = %s
                LIMIT 1
                """,
                (email,)
            )
            row = cur.fetchone()

        if not row:
            return templates.TemplateResponse("login.html", {"request": request, "error": "Credenciais inválidas"})

        email_db, senha_hash_db, situacao = row

        if situacao != 1:
            return templates.TemplateResponse("login.html", {"request": request, "error": "Usuário inativo"})

        if not bcrypt.checkpw(senha.encode("utf-8"), senha_hash_db.encode("utf-8")):
            return templates.TemplateResponse("login.html", {"request": request, "error": "Credenciais inválidas"})

        resp = RedirectResponse(url="/home", status_code=302)
        resp.set_cookie(COOKIE_NAME, email_db, httponly=True)
        return resp
    finally:
        conn.close()

@router.get("/home", response_class=HTMLResponse)
def home(request: Request):
    user_email = request.cookies.get(COOKIE_NAME)
    if not user_email:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("home.html", {"request": request, "user_email": user_email})

@router.get("/logout")
def logout():
    resp = RedirectResponse(url="/login", status_code=302)
    resp.delete_cookie(COOKIE_NAME)
    return resp
