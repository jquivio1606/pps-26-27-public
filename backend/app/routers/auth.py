"""Endpoints del módulo de Autenticación y gestión de usuarios."""

import os
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..auth import (
    ROLE_ADMIN,
    ROLE_USER,
    create_access_token,
    get_current_user,
    get_github_config,
    hash_password,
    is_valid_role,
    require_admin,
    verify_password,
)
from ..database import get_db
from ..models import User
from ..pagination import Page, PageParams, paginate
from ..schemas import (
    Message,
    Token,
    UserCreate,
    UserPasswordReset,
    UserRead,
    UserUpdate,
)

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.get("/github/config", summary="Ver configuración GitHub OAuth (debug)")
def github_config_debug():
    GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, GITHUB_REDIRECT_URI = get_github_config()
    return {
        "client_id": GITHUB_CLIENT_ID[:8] + "..." if GITHUB_CLIENT_ID else None,
        "redirect_uri": GITHUB_REDIRECT_URI,
        "has_secret": bool(GITHUB_CLIENT_SECRET),
    }


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo usuario",
)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    """Crea un usuario con rol ``user``.

    El rol de administrador o manager nunca se asigna desde este endpoint
    público: solo desde los datos de prueba o desde el panel de usuarios
    (exclusivo del administrador). La contraseña se guarda hasheada (bcrypt).
    """
    exists = db.execute(
        select(User).where(
            or_(User.username == payload.username, User.email == payload.email)
        )
    ).scalar_one_or_none()
    if exists is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El nombre de usuario o el email ya están registrados",
        )

    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=ROLE_USER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token, summary="Iniciar sesión (obtener token JWT)")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
) -> Token:
    """Autentica por usuario/contraseña y devuelve un token de acceso.

    Usa el formato OAuth2 (``application/x-www-form-urlencoded``) con los campos
    ``username`` y ``password``. En Swagger puedes usar el botón **Authorize**.
    """
    user = db.execute(
        select(User).where(User.username == form_data.username)
    ).scalar_one_or_none()

    if user is None or not user.hashed_password or not verify_password(
        form_data.password, user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return Token(access_token=create_access_token(user))


@router.get("/me", response_model=UserRead, summary="Datos del usuario autenticado")
def read_me(current_user: User = Depends(get_current_user)) -> User:
    """Devuelve la información del usuario asociado al token enviado."""
    return current_user


@router.get("/github", summary="Iniciar autenticación con GitHub (OAuth)")
def github_login():
    GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, GITHUB_REDIRECT_URI = get_github_config()
    if not GITHUB_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GitHub OAuth no configurado. Añade GITHUB_CLIENT_ID y GITHUB_CLIENT_SECRET en .env",
        )
    print(f"[DEBUG] GitHub OAuth redirect_uri: {GITHUB_REDIRECT_URI}", flush=True)
    print(f"[DEBUG] GitHub OAuth client_id: {GITHUB_CLIENT_ID[:8]}...", flush=True)
    params = {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": GITHUB_REDIRECT_URI,
        "scope": "user:email",
        "allow_signup": "true",
    }
    url = "https://github.com/login/oauth/authorize?" + urlencode(params)
    print(f"[DEBUG] GitHub auth URL: {url}", flush=True)
    return RedirectResponse(url=url)


@router.get("/github/callback", summary="Callback de GitHub OAuth")
async def github_callback(code: str | None = None, db: Session = Depends(get_db)):
    GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, GITHUB_REDIRECT_URI = get_github_config()
    if not code:
        raise HTTPException(status_code=400, detail="Falta el código de autorización de GitHub")
    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="GitHub OAuth no configurado. Añade GITHUB_CLIENT_ID y GITHUB_CLIENT_SECRET en .env",
        )

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": GITHUB_REDIRECT_URI,
            },
        )
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="No se pudo obtener token de GitHub")

        user_resp = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
                "User-Agent": "Cinema-API",
            },
        )
        gh_user = user_resp.json()

        emails_resp = await client.get(
            "https://api.github.com/user/emails",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
                "User-Agent": "Cinema-API",
            },
        )
        emails = emails_resp.json()
        primary_email = None
        for e in emails:
            if isinstance(e, dict) and e.get("primary") and e.get("verified"):
                primary_email = e.get("email")
                break
        if not primary_email and emails and isinstance(emails[0], dict):
            primary_email = emails[0].get("email")

    github_id = str(gh_user.get("id"))
    username = gh_user.get("login") or f"github_{github_id}"
    email = primary_email or gh_user.get("email") or f"{username}@users.noreply.github.com"

    user = db.execute(
        select(User).where(
            or_(
                User.oauth_provider == "github" and User.oauth_id == github_id,
                User.email == email,
            )
        )
    ).scalar_one_or_none()

    if user is None:
        # Ensure unique username
        base_username = username
        suffix = 0
        while True:
            existing = db.execute(
                select(User).where(User.username == base_username)
            ).scalar_one_or_none()
            if not existing:
                break
            suffix += 1
            base_username = f"{username}_{suffix}"
        user = User(
            username=base_username,
            email=email,
            hashed_password=None,
            role=ROLE_USER,
            oauth_provider="github",
            oauth_id=github_id,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        if not user.oauth_provider:
            user.oauth_provider = "github"
            user.oauth_id = github_id
        db.commit()
        db.refresh(user)

    jwt_token = create_access_token(user)
    # Redirect to frontend with token
    redirect_url = f"/?token={jwt_token}"
    return RedirectResponse(url=redirect_url)


# --------------------------------------------------------------------------- #
#  Gestión de usuarios (solo admin / informático)
# --------------------------------------------------------------------------- #
def _admins_total(db: Session) -> int:
    """Cuenta los administradores existentes (para no quedarnos sin ninguno)."""
    return (
        db.scalar(
            select(func.count()).select_from(User).where(User.role == ROLE_ADMIN)
        )
        or 0
    )


def _get_user_or_404(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


@router.get(
    "/users",
    response_model=Page[UserRead],
    summary="Listar usuarios (solo admin)",
)
def list_users(
    role: str | None = Query(default=None, description="Filtrar por rol"),
    params: PageParams = Depends(),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> dict:
    """Lista los usuarios registrados de forma paginada. **Requiere rol admin.**

    No incluye nunca la clave ni su hash: solo los datos públicos del usuario.
    """
    stmt = select(User).order_by(User.id)
    if role is not None:
        stmt = stmt.where(User.role == role)
    return paginate(db, stmt, params)


@router.patch(
    "/users/{user_id}",
    response_model=UserRead,
    summary="Cambiar el rol o el email de un usuario (solo admin)",
)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> User:
    """Actualiza el rol o el email de un usuario. **Requiere rol admin.**

    Protecciones para no dejar la web sin administrador:

    * No se puede quitar el rol ``admin`` al **último** administrador (``409``).
    * El email debe seguir siendo único (``409``).
    """
    user = _get_user_or_404(db, user_id)

    if payload.role is None and payload.email is None:
        raise HTTPException(status_code=400, detail="No hay cambios que aplicar")
    if payload.role is not None and not is_valid_role(payload.role):
        raise HTTPException(status_code=400, detail="Rol no válido")

    if (
        payload.role is not None
        and user.role == ROLE_ADMIN
        and payload.role != ROLE_ADMIN
        and _admins_total(db) <= 1
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Debe existir al menos un administrador",
        )

    if payload.email is not None and payload.email != user.email:
        taken = db.execute(
            select(User).where(User.email == payload.email, User.id != user.id)
        ).scalar_one_or_none()
        if taken is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ese email ya está registrado",
            )
        user.email = payload.email

    if payload.role is not None:
        user.role = payload.role

    db.commit()
    db.refresh(user)
    return user


@router.post(
    "/users/{user_id}/password",
    response_model=Message,
    summary="Restablecer la clave de un usuario (solo admin)",
)
def reset_user_password(
    user_id: int,
    payload: UserPasswordReset,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> Message:
    """Asigna una clave nueva a un usuario. **Requiere rol admin.**

    La clave se guarda **hasheada con bcrypt**: nunca en texto plano y nunca se
    devuelve por la API.
    """
    user = _get_user_or_404(db, user_id)
    user.hashed_password = hash_password(payload.password)
    db.commit()
    return Message(message=f"Clave de '{user.username}' actualizada")


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un usuario (solo admin)",
)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> None:
    """Elimina un usuario. **Requiere rol admin.**

    * No puedes eliminar tu propia cuenta (``400``).
    * No se puede eliminar al **último** administrador (``409``).
    * Sus reservas se conservan (quedan sin usuario asociado), así que borrar
      una cuenta no rompe el historial de ventas.
    """
    user = _get_user_or_404(db, user_id)

    if user.id == current_user.id:
        raise HTTPException(
            status_code=400, detail="No puedes eliminar tu propia cuenta"
        )
    if user.role == ROLE_ADMIN and _admins_total(db) <= 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Debe existir al menos un administrador",
        )

    # Las reservas se mantienen; solo se desvinculan de la cuenta eliminada.
    for ticket in list(user.tickets):
        ticket.user_id = None

    db.delete(user)
    db.commit()
