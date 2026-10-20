# Cinema API

API REST completa desarrollada con **FastAPI** para gestionar un sistema de compra
de entradas de cine (autenticación, películas, funciones y reservas).

- **Frontend web:** http://127.0.0.1:8000/
- **Documentación Swagger UI:** http://127.0.0.1:8000/docs
- **Documentación ReDoc:** http://127.0.0.1:8000/redoc
- **OpenAPI JSON:** http://127.0.0.1:8000/openapi.json
- **Colección Postman:** `backend/Cinema-API.postman_collection.json`

## Características

- **Frontend web** incluido con **React + Vite + Bootstrap** (responsive): cartelera,
  funciones, compra de entradas, login/registro, panel de gestión y dashboard.
- **Autenticación JWT** con **tres roles** (`admin` / `manager` / `user`) y
  contraseñas almacenadas **cifradas** (hash bcrypt, nunca en texto plano).
- **Paginación** en todos los listados (`?page=` y `?size=`).
- CRUD de **Películas** (`/movies`) — escritura para `manager` y `admin`.
- CRUD de **Funciones/Sesiones** (`/showtimes`) — para `manager` y `admin`, con
  protección para no borrar funciones/películas con entradas vendidas.
- **Panel de estadísticas** (`/stats/dashboard`) para el personal: ventas,
  ocupación de las salas, usuarios por rol, películas más taquilleras y últimas
  reservas.
- **Gestión de usuarios** (`/auth/users`, solo `admin`): cambiar roles, restablecer
  contraseñas con **doble confirmación** en la web (siempre cifradas) y eliminar
  cuentas.
- **Info del sistema** (`/stats/system`, solo `admin`): versión, base de datos sin
  credenciales, estado de la `SECRET_KEY`, verificación de claves cifradas y las
  **tecnologías usadas** con su versión y propósito.
- **Reserva de entradas** (`/tickets/book`, requiere autenticación) con control de
  asientos disponibles. Si no hay asientos suficientes devuelve **400**; si los hay,
  los descuenta y confirma la compra.
- **Selección de butacas**: mapa de asientos por función (`GET /showtimes/{id}/seats`)
  y compra indicando las butacas concretas. No se puede repetir una butaca dentro de
  una compra ni reservar una ya ocupada (**409**), y el número de butacas debe
  coincidir con el de entradas.
- **Cancelación de entradas** (`DELETE /tickets/{id}`, manager o admin): cuando un
  cliente se equivoca al comprar, el personal anula la reserva y **las butacas
  vuelven a estar libres al instante** (el aforo se recalcula como en la edición
  de funciones) y la venta desaparece del dashboard. El **reembolso del dinero no
  está implementado en la web** (tampoco lo está el pago: no hay pasarela de pago).
- **Listado de todas las reservas** (`GET /tickets?scope=all`, manager o admin) con
  filtro `?search=` por nombre de cliente o de usuario: el jefe localiza «las
  entradas de un jugador» y las cancela desde la pestaña **Entradas** de la gestión.
  Cada entrada expone además el usuario comprador y la película, sala y hora.
- Base de datos **SQLite** (sin configuración) mediante SQLAlchemy 2.0.
- **Datos de prueba automáticos**: 3 usuarios, 20 películas y 10 funciones al primer arranque.
- CORS habilitado para pruebas desde Postman o front-ends.

## Estructura del proyecto

```
cinema-api/
├── backend/                   # Todo el código del servidor (API)
│   ├── app/
│   │   ├── main.py            # App FastAPI, CORS, routers y /docs
│   │   ├── database.py        # Motor y sesión SQLAlchemy
│   │   ├── models.py          # Modelos ORM (User, Movie, Showtime, Ticket, ReservedSeat)
│   │   ├── schemas.py         # Esquemas Pydantic de entrada/salida
│   │   ├── auth.py            # Hashing, JWT, roles y dependencias de autenticación
│   │   ├── pagination.py      # PageParams, Page[T] y helper paginate()
│   │   ├── seats.py           # Plano de butacas y validación de asientos
│   │   ├── seed.py            # Datos de prueba (usuarios, 20 películas, 10 funciones)
│   │   └── routers/
│   │       ├── auth.py        # Módulo Autenticación + gestión de usuarios
│   │       ├── movies.py      # Módulo Películas
│   │       ├── showtimes.py   # Módulo Funciones
│   │       ├── tickets.py     # Módulo Reservas
│   │       └── stats.py       # Módulo Estadísticas + info del sistema
│   ├── tests/
│   │   ├── conftest.py            # BD de pruebas aislada y fixtures
│   │   ├── test_unit_auth.py      # Unitarias: hashing, JWT y roles
│   │   ├── test_unit_pagination.py# Unitarias: paginación
│   │   ├── test_auth.py           # Funcionales: autenticación
│   │   ├── test_roles.py          # Funcionales: roles, claves cifradas y stats
│   │   ├── test_movies.py         # Funcionales: películas
│   │   ├── test_showtimes.py      # Funcionales: funciones
│   │   ├── test_tickets.py        # Funcionales: reservas
│   │   ├── test_unit_seats.py     # Unitarias: plano de butacas
│   │   ├── test_seats.py          # Funcionales: selección de asientos
│   │   └── live_check.py          # Caja negra contra un servidor real
│   ├── cinema.db              # Base de datos SQLite (se crea al arrancar)
│   ├── pytest.ini
│   ├── requirements.txt
│   ├── requirements-dev.txt       # Dependencias de pruebas (pytest)
│   └── Cinema-API.postman_collection.json
├── frontend/                  # Frontend web (React + Vite + Bootstrap)
│   ├── index.html             # Punto de entrada de Vite
│   ├── package.json           # Dependencias y scripts (dev/build)
│   ├── vite.config.js         # Configuración de Vite (proxy en desarrollo)
│   ├── src/
│   │   ├── main.jsx           # Arranque de React + Bootstrap + tema
│   │   ├── App.jsx            # Rutas, providers y modales globales
│   │   ├── api/               # Cliente HTTP de la API
│   │   ├── context/           # Auth (JWT), notificaciones e interfaz
│   │   ├── components/        # Header, Hero, tarjetas, modales, butacas, tabs…
│   │   ├── pages/            # Cartelera, Funciones, Mis entradas, Gestión, Dashboard, Usuarios, Sistema
│   │   ├── lib/               # Utilidades (fechas, géneros, bus de eventos)
│   │   └── styles/theme.css   # Tema neón retro-arcade sobre Bootstrap
│   └── dist/                  # Build de producción (lo sirve FastAPI)
├── start.bat / start.ps1      # Lanzadores (doble clic): compilan el front y arrancan backend/
└── README.md
```

> El **backend** (API + pruebas + base de datos + dependencias) está en `backend/`;
> el **frontend** (React) está en `frontend/` y, una vez compilado en `frontend/dist`,
> lo sirve la API como archivos estáticos.

## Puesta en marcha

### Opción rápida (Windows): doble clic

Haz **doble clic en `start.bat`**. El lanzador:

1. Localiza Python y crea el entorno virtual (`.venv`) si no existe.
2. Instala las dependencias de `backend/requirements.txt`.
3. Compila el frontend React (`frontend/dist`) si aún no está compilado (requiere Node.js 18+).
4. Arranca la API en `http://127.0.0.1:8000` y **abre la web** en el navegador.

Para usar otro puerto: `start.bat 8001`.
En PowerShell: `.\start.ps1 -Port 8001` (si da error de permisos, ejecuta antes
`Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`).

> Deja esa ventana abierta mientras usas la API (Postman/Swagger). `CTRL+C` la detiene.

### Opción manual

```bash
# 1. Crear y activar un entorno virtual (recomendado)
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
# source .venv/bin/activate

# 2. Instalar dependencias del backend
pip install -r backend/requirements.txt

# 3. Compilar el frontend (React + Vite; requiere Node.js 18+)
cd frontend
npm install
npm run build        # genera frontend/dist
cd ..

# 4. Arrancar el servidor (desde la carpeta backend/)
cd backend
uvicorn app.main:app --reload
```

La API quedará disponible en `http://127.0.0.1:8000` y la documentación en
`http://127.0.0.1:8000/docs`.

### Desarrollo del frontend (con recarga en caliente)

Si vas a tocar la interfaz, arranca el backend y el servidor de Vite en paralelo.
Vite hace de *proxy* hacia la API, así que no hay problemas de CORS:

```bash
# Terminal 1: backend en http://127.0.0.1:8000
cd backend && uvicorn app.main:app --reload

# Terminal 2: frontend en http://127.0.0.1:5173 (recarga en caliente)
cd frontend && npm run dev
```

### Variables de entorno

| Variable                     | Por defecto                              | Descripción                          |
| ---------------------------- | ---------------------------------------- | ------------------------------------ |
| `DATABASE_URL`               | `sqlite:///…/backend/cinema.db`          | Cadena de conexión de la base datos. |
| `SECRET_KEY`                 | `cambia-esta-clave-en-produccion-...`    | Clave de firma de los JWT.           |
| `ACCESS_TOKEN_EXPIRE_MINUTES`| `60`                                     | Minutos de validez del token.        |

> En producción **define siempre** `SECRET_KEY`.

> Para recrear la base de datos desde cero, borra `backend/cinema.db` y vuelve a arrancar,
> o ejecuta `python -m app.seed` desde la carpeta `backend/`.

## Usuarios de prueba

Creados automáticamente al primer arranque (si ya existen se respetan; solo se
añaden los que falten):

| Usuario   | Contraseña   | Rol       | Permisos                                                              |
| --------- | ------------ | --------- | --------------------------------------------------------------------- |
| `admin`   | `admin123`   | `admin`   | Informático: todo lo del jefe + gestionar usuarios, roles y claves, y ver la información del sistema. |
| `manager` | `manager123` | `manager` | Jefe: añadir/modificar/eliminar películas y funciones, ver el dashboard y cancelar entradas. |
| `user`    | `user123`    | `user`    | Cliente: comprar entradas y ver únicamente sus propias reservas.      |

## Roles y permisos

La web tiene **tres perfiles** con responsabilidades bien separadas:

| Acción                                   | `user` | `manager` | `admin` |
| ---------------------------------------- | :----: | :-------: | :-----: |
| Comprar entradas y ver las propias       |   ✅   |    ✅     |   ✅    |
| Ver todas las entradas y cancelarlas     |   ❌   |    ✅     |   ✅    |
| Ver el dashboard de estadísticas         |   ❌   |    ✅     |   ✅    |
| Añadir / modificar / eliminar películas  |   ❌   |    ✅     |   ✅    |
| Añadir / modificar / eliminar funciones  |   ❌   |    ✅     |   ✅    |
| Gestionar usuarios, roles y claves       |   ❌   |    ❌     |   ✅    |
| Ver la información técnica del sistema   |   ❌   |    ❌     |   ✅    |

* **`admin` (informático):** funciones técnicas específicas. Administra las
  cuentas (crear roles, restablecer claves, eliminar usuarios) y consulta el
  estado del sistema. Se protege para no quedarse sin administrador: no puede
  quitarse el rol al último `admin`, ni eliminar su propia cuenta.
* **`manager` (jefe):** lo justo y necesario para operar el negocio sin romper la
  web: gestiona el catálogo, ve las estadísticas y **cancela entradas** de los
  clientes cuando se equivocan al comprar (sin reembolso automático: el dinero se
  devuelve fuera de la web), pero **no** toca usuarios ni configuración del
  sistema. Además, no puede borrar películas ni funciones que ya tengan
  **entradas vendidas** (el servidor responde `409`).
* **`user` (cliente):** igual que siempre.

### Seguridad de las claves

Las contraseñas se guardan **siempre cifradas** con **bcrypt** (con *salt*
aleatorio); la clave en texto plano nunca se almacena ni se devuelve por la API:

* El registro, el seed y el restablecimiento de claves hashean antes de guardar.
* Al arrancar, `ensure_passwords_encrypted()` revisa la base de datos y cifra
  cualquier clave que hubiera quedado en texto plano (por ejemplo, de una
  importación antigua), sin cambiar la contraseña que usa el usuario.
* El endpoint público de registro solo puede crear cuentas con rol `user`.

## Frontend web

Con el servidor arrancado, la web está en **http://127.0.0.1:8000/** y consume la
misma API (mismo origen). Incluye:

- **Cartelera**: rejilla de películas con **póster** (imagen real incluida en el
  catálogo; respaldo gráfico si no carga) y paginación; pulsa una para ver su ficha y funciones.
- **Funciones**: listado con filtro por película, sala, hora, precio y asientos disponibles.
- **Compra**: selector de butacas interactivo (sin poder elegir más que las entradas),
  confirmación y descuento de asientos (error `400` si no hay, `409` si la butaca se ocupó).
- **Autenticación**: modal de login/registro; el JWT se guarda en `localStorage`.
- **Mis entradas**: historial del usuario autenticado.
- **Gestión** (`/admin`, `manager` y `admin`): crear, modificar y eliminar
  películas y funciones desde el catálogo, y pestaña **Entradas** para buscar por
  cliente o usuario y **cancelar una reserva** (libera las butacas; el reembolso
  se gestiona fuera de la web).
- **Dashboard** (`/dashboard`, `manager` y `admin`): ingresos, entradas vendidas,
  ocupación de las salas, usuarios por rol, películas más taquilleras y últimas
  reservas.
- **Usuarios** (`/admin/usuarios`, solo `admin`): cambiar roles, restablecer
  claves y eliminar cuentas.
- **Sistema** (`/admin/sistema`, solo `admin`): información técnica del servicio.

Está implementado con **React 18 + Vite + Bootstrap 5** y se sirve compilado
(`frontend/dist`) como archivos estáticos por FastAPI (`StaticFiles`). El tema
personalizado (`src/styles/theme.css`) conserva la estética neón retro-arcade
sobre el sistema de grid y componentes *responsive* de Bootstrap.

Para recompilar tras cambios: `cd frontend && npm run build` (o `npm run dev`
para desarrollo con recarga en caliente). El lanzador `start.bat` compila
automáticamente si `frontend/dist` no existe.

> Referencias de diseño: **estructura** tomada de la cartelera de *Cine Yelmo*;
> **estética** neón retro-arcade tomada de *Arcade Planet*.
>
> Los pósters del catálogo de prueba se enlazan a imágenes de *Wikipedia*
> (`upload.wikimedia.org`). Son solo para la demo; puedes sustituirlos por los
> que quieras desde el panel de admin (`poster_url`).

## Autenticación

1. **Registro** (rol `user`): `POST /auth/register`

   ```json
   { "username": "ana", "email": "ana@example.com", "password": "secreto123" }
   ```

2. **Login**: `POST /auth/login` (formato OAuth2, `application/x-www-form-urlencoded`)

   ```bash
   curl -X POST http://127.0.0.1:8000/auth/login \
     -d "username=user&password=user123"
   ```

   Respuesta:

   ```json
   { "access_token": "eyJhbGciOiJIUzI1NiI...", "token_type": "bearer" }
   ```

3. **Usar el token**: envía la cabecera `Authorization: Bearer <token>`.

   ```bash
   curl http://127.0.0.1:8000/auth/me -H "Authorization: Bearer <token>"
   ```

En **Swagger UI** pulsa **Authorize** 🔒, introduce usuario y contraseña, y todas
las peticiones se enviarán autenticadas automáticamente.

### Resumen de protección

| Endpoint                        | Acceso requerido      |
| ------------------------------- | --------------------- |
| `GET /movies`, `GET /showtimes` | Público               |
| `POST /movies`, `PUT /movies`, `DELETE /movies` | Manager o admin |
| `POST /showtimes`, `PUT /showtimes`, `DELETE /showtimes` | Manager o admin |
| `POST /tickets/book`            | Usuario autenticado   |
| `GET /tickets`                  | Autenticado (admin ve todas; manager y user solo las suyas; `?scope=all` solo manager/admin) |
| `DELETE /tickets/{id}`          | Manager o admin (cancela y libera butacas) |
| `GET /stats/dashboard`          | Manager o admin       |
| `GET /stats/system`             | Admin                 |
| `GET /auth/users`, `PATCH /auth/users/{id}` | Admin       |
| `POST /auth/users/{id}/password`, `DELETE /auth/users/{id}` | Admin |

## Paginación

Todos los listados (`GET /movies`, `GET /showtimes`, `GET /tickets`) aceptan:

- `page` — número de página, desde 1 (por defecto `1`).
- `size` — elementos por página, entre 1 y 100 (por defecto `10`).

Ejemplo: `GET /movies?page=2&size=10`

Respuesta (envoltorio genérico `Page`):

```json
{
  "items": [ { "id": 11, "title": "...", "genre": "...", "duration_minutes": 120, "poster_url": "https://…/poster.jpg" } ],
  "total": 20,
  "page": 2,
  "size": 10,
  "pages": 2,
  "has_next": false,
  "has_prev": true
}
```

## Endpoints

### Autenticación

| Método | Ruta              | Descripción                          |
| ------ | ----------------- | ------------------------------------ |
| POST   | `/auth/register`  | Registrar un nuevo usuario (rol `user`). |
| POST   | `/auth/login`     | Iniciar sesión y obtener el token.   |
| GET    | `/auth/me`        | Datos del usuario autenticado.       |

### Usuarios (solo admin)

| Método | Ruta                          | Descripción                                   |
| ------ | ----------------------------- | --------------------------------------------- |
| GET    | `/auth/users`                 | Listar usuarios (paginado, filtro `?role=`).  |
| PATCH  | `/auth/users/{id}`            | Cambiar rol y/o email de un usuario.          |
| POST   | `/auth/users/{id}/password`   | Restablecer la clave (se guarda cifrada).     |
| DELETE | `/auth/users/{id}`            | Eliminar una cuenta.                          |

> Nunca se devuelve la clave ni su hash (solo `id`, `username`, `email`, `role`
> y `created_at`). Cambiar el rol al **último** administrador devuelve `409`.

### Películas

| Método | Ruta            | Descripción                              |
| ------ | --------------- | ---------------------------------------- |
| GET    | `/movies`       | Listar películas (paginado).             |
| POST   | `/movies`       | Añadir película (manager/admin).         |
| GET    | `/movies/{id}`  | Obtener una película por ID.             |
| PUT    | `/movies/{id}`  | Modificar una película (manager/admin).  |
| DELETE | `/movies/{id}`  | Eliminar una película (manager/admin).   |

```json
{
  "title": "Origen",
  "genre": "Ciencia ficción",
  "duration_minutes": 148,
  "poster_url": "https://upload.wikimedia.org/wikipedia/en/2/2e/Inception_%282010%29_theatrical_poster.jpg"
}
```

> `poster_url` es **opcional**. El catálogo de prueba ya incluye un póster real
> para cada una de las 20 películas. Si se omite (o la imagen no carga), el
> frontend dibuja un póster de respaldo con degradado y emoji según el género.

### Funciones

| Método | Ruta                | Descripción                              |
| ------ | ------------------- | ---------------------------------------- |
| GET    | `/showtimes`        | Listar funciones, filtro `?movie_id=`.   |
| POST   | `/showtimes`        | Crear una función (manager/admin).       |
| GET    | `/showtimes/{id}`   | Obtener una función por ID.              |
| PUT    | `/showtimes/{id}`   | Modificar una función (manager/admin).   |
| DELETE | `/showtimes/{id}`   | Eliminar una función (manager/admin).    |
| GET    | `/showtimes/{id}/seats` | Mapa de butacas (libres/ocupadas).   |

```json
{
  "movie_id": 1,
  "room": "Sala 1",
  "start_time": "2026-10-13T18:00:00",
  "total_seats": 100,
  "price": 8.5
}
```

### Reservas

| Método | Ruta              | Descripción                                |
| ------ | ----------------- | ------------------------------------------ |
| POST   | `/tickets/book`   | Comprar/reservar entradas (autenticado).   |
| GET    | `/tickets`        | Listar reservas (paginado; `?scope=all`, `?search=`). |
| GET    | `/tickets/{id}`   | Obtener una reserva por ID.                |
| DELETE | `/tickets/{id}`   | Cancelar una reserva y liberar butacas (manager/admin; sin reembolso automático). |

Compra indicando las butacas elegidas (se devuelven en `ticket.seats`):

```json
{
  "showtime_id": 1,
  "customer_name": "Ana López",
  "quantity": 2,
  "seats": ["A1", "A2"]
}
```

Reglas de la selección de asientos (aplicadas en el servidor):

- El número de butacas (`seats`) debe **coincidir** con `quantity`.
- No se puede repetir la misma butaca dentro de una compra (**400**).
- Una butaca ya ocupada por otra compra devuelve **409**.
- Butacas inexistentes en la sala devuelven **400**.
- Si se omite `seats`, se asignan automáticamente las primeras libres.

La restricción se refuerza además en la base de datos con un índice único
`(showtime_id, seat_label)`, de modo que **dos entradas nunca comparten butaca**.

Respuesta `201`:

```json
{
  "message": "Compra realizada con éxito",
  "ticket": {
    "id": 1,
    "showtime_id": 1,
    "user_id": 2,
    "customer_name": "Ana López",
    "quantity": 2,
    "total_price": 17.0,
    "created_at": "2026-10-13T12:00:00"
  },
  "showtime_id": 1,
  "remaining_seats": 118
}
```

Si se solicitan más asientos de los disponibles, la API responde **400**:

```json
{ "detail": "No hay asientos suficientes. Solicitados: 99999, disponibles: 120." }
```

### Estadísticas y sistema

| Método | Ruta               | Descripción                                      |
| ------ | ------------------ | ------------------------------------------------ |
| GET    | `/stats/dashboard` | Resumen de actividad (manager/admin).            |
| GET    | `/stats/system`    | Información técnica del servicio (solo admin).   |

`GET /stats/dashboard` devuelve, entre otros:

```json
{
  "movies": 20,
  "showtimes": 10,
  "users": 3,
  "users_by_role": { "user": 1, "manager": 1, "admin": 1 },
  "tickets": 12,
  "seats_sold": 27,
  "revenue": 214.5,
  "seats_total": 1190,
  "seats_reserved": 27,
  "seats_available": 1163,
  "occupancy_percent": 2.3,
  "top_movies": [
    { "movie_id": 1, "title": "El Padrino", "showtimes": 1, "tickets": 3,
      "seats_sold": 7, "revenue": 59.5 }
  ],
  "recent_tickets": [ { "id": 12, "customer_name": "Ana", "quantity": 2 } ]
}
```

`GET /stats/system` **nunca expone secretos**: informa de la versión, la base de
datos sin credenciales, si la `SECRET_KEY` está configurada, cuántas cuentas
tienen la clave cifrada y las tecnologías usadas (Python, FastAPI, SQLAlchemy,
SQLite, PyJWT y bcrypt con su versión, más las del frontend).

## Pruebas

El proyecto incluye **pruebas unitarias y funcionales** (132 en total) más una
comprobación de caja negra contra un servidor real.

### Pruebas automatizadas (pytest)

```bash
pip install -r backend/requirements-dev.txt
pytest --version   # pytest 8.x
# Desde la carpeta backend/ (o desde la raíz: python -m pytest backend)
cd backend
..\.venv\Scripts\python.exe -m pytest   # 132 passed
```

Usan una base de datos SQLite temporal y aislada (no tocan `backend/cinema.db`);
cada prueba arranca con los datos de ejemplo recién sembrados.

- **Unitarias**: hashing bcrypt, creación/expiración/validez de JWT y paginación.
- **Funcionales**: autenticación y roles (`user`/`manager`/`admin`), CRUD de
  películas y funciones, reservas, control de asientos (incluido el error 400),
  **cancelación de entradas** (libera butacas, 403 a clientes y búsqueda por
  jugador), gestión de usuarios y claves, estadísticas, permisos 401/403 y paginación.
- **Seguridad**: las claves se guardan hasheadas y la migración cifra claves
  antiguas en texto plano (ver `tests/test_roles.py`).

### Prueba contra la web real (caja negra)

Con el servidor arrancado (`start.bat`), en otra terminal:

```bash
python backend/tests/live_check.py
# BASE_URL=http://127.0.0.1:8000 por defecto
```

Hace peticiones HTTP reales (health, docs, login, roles, paginación, compra,
selección de butacas, **cancelación de entradas por el personal**, estadísticas y
error 400 por falta de asientos) y resume el resultado (**59 OK, 0 FALLOS**).

## Probar con Postman

1. Importa `backend/Cinema-API.postman_collection.json` en Postman (*Import → File*).
2. Arranca el servidor (desde `backend/`: `uvicorn app.main:app --reload`).
3. Ejecuta **Autenticación → Login (admin)**, **Login (manager)** o **Login (user)**.
   El token se guarda automáticamente en la variable de colección `{{token}}` y
   se usa en el resto.
4. Ejecuta el resto de peticiones. Los IDs creados se guardan en `movie_id` y
   `showtime_id`.

## Flujo rápido con cURL

```bash
# 1. Login y guarda el token
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/auth/login \
  -d "username=user&password=user123" | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

# 2. Listar películas (paginado, público)
curl "http://127.0.0.1:8000/movies?page=1&size=5"

# 3. Mapa de butacas de la función 1 (público)
curl "http://127.0.0.1:8000/showtimes/1/seats"

# 4. Comprar entradas eligiendo butacas (autenticado)
curl -X POST http://127.0.0.1:8000/tickets/book \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"showtime_id": 1, "customer_name": "Ana", "quantity": 2, "seats": ["A1", "A2"]}'
```
