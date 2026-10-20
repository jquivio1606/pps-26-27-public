"""Seguridad: hashing de contraseñas, JWT y dependencias de autenticación."""

import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_db
from .models import User

# En producción define SECRET_KEY por variable de entorno.
DEFAULT_SECRET_KEY = "cambia-esta-clave-en-produccion-1234567890"
SECRET_KEY = os.getenv("SECRET_KEY", DEFAULT_SECRET_KEY)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# tokenUrl apunta al endpoint de login (Swagger lo usa para el botón "Authorize").
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="No se pudieron validar las credenciales",
    headers={"WWW-Authenticate": "Bearer"},
)


# --------------------------------------------------------------------------- #
#  Roles
# --------------------------------------------------------------------------- #
# user    -> cliente: compra entradas y consulta las suyas (sin permisos de gestión).
# manager -> jefe de la empresa: alta/baja/edición del catálogo y estadísticas,
#            pero nada técnico (no toca usuarios ni configuración del sistema).
# admin   -> informático: todo lo anterior + funciones técnicas específicas
#            (gestión de usuarios/roles/claves e información del sistema).
ROLE_USER = "user"
ROLE_MANAGER = "manager"
ROLE_ADMIN = "admin"

#: Roles válidos en la base de datos. El registro público solo crea ``user``.
ROLES = (ROLE_USER, ROLE_MANAGER, ROLE_ADMIN)

#: Roles con acceso al panel de gestión (jefe + informático).
STAFF_ROLES = (ROLE_MANAGER, ROLE_ADMIN)


def is_admin(user: User) -> bool:
    """Indica si el usuario tiene rol de administrador (informático)."""
    return user.role == ROLE_ADMIN


def is_staff(user: User) -> bool:
    """Indica si el usuario pertenece al personal de la casa (manager o admin)."""
    return user.role in STAFF_ROLES


def is_valid_role(role: str) -> bool:
    """Comprueba que ``role`` es uno de los roles admitidos."""
    return role in ROLES


# --------------------------------------------------------------------------- #
#  Contraseñas (nunca se almacena la clave en texto plano)
# --------------------------------------------------------------------------- #
def hash_password(password: str) -> str:
    """Devuelve el hash bcrypt de una contraseña en texto plano."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Comprueba que una contraseña coincide con su hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except (ValueError, TypeError):
        return False


def is_hashed_password(value: str | None) -> bool:
    """¿El valor almacenado es un hash bcrypt (y no una clave en texto plano)?"""
    return bool(value) and value.startswith(("$2a$", "$2b$", "$2y$"))


def ensure_passwords_encrypted(db: Session) -> int:
    """Migra al arrancar cualquier clave guardada en texto plano a hash bcrypt.

    Garantiza el requisito de *no almacenar nunca claves de usuario en claro*:
    si una base de datos antigua (o importada) contiene claves sin cifrar, aquí
    se hashean con bcrypt antes de seguir. Idempotente: solo toca lo que haga
    falta y devuelve el número de claves migradas.
    """
    migrated = 0
    for user in db.scalars(select(User)).all():
        if not is_hashed_password(user.hashed_password):
            user.hashed_password = hash_password(user.hashed_password)
            migrated += 1
    if migrated:
        db.commit()
    return migrated


# --------------------------------------------------------------------------- #
#  Tokens JWT
# --------------------------------------------------------------------------- #
def create_access_token(
    user: User, expires_delta: timedelta | None = None
) -> str:
    """Genera un JWT firmado con la identidad y el rol del usuario."""
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# --------------------------------------------------------------------------- #
#  Dependencias
# --------------------------------------------------------------------------- #
def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """Devuelve el usuario autenticado a partir del Bearer token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    user = db.get(User, int(user_id))
    if user is None:
        raise credentials_exception
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    """Exige que el usuario autenticado sea administrador (informático).

    Da acceso a las funciones técnicas específicas: gestión de usuarios,
    roles y claves, e información del sistema.
    """
    if not is_admin(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de administrador",
        )
    return user


def require_staff(user: User = Depends(get_current_user)) -> User:
    """Exige rol de personal de la casa: ``manager`` (jefe) o ``admin``.

    Da acceso a la gestión del catálogo (películas y funciones) y al panel de
    estadísticas. Los clientes con rol ``user`` no pasan de aquí.
    """
    if not is_staff(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de gestión (manager o admin)",
        )
    return user
