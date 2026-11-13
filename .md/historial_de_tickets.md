# Historial de Desarrollo (Tickets)

Este documento registra los Sprints y tareas completadas en la evolución del proyecto.

---
### AGROPESO-001: Configuración de la conexión a MySQL
* Se configuró SQLAlchemy (`engine`, `SessionLocal`, `Base`).
* Implementación de variables de entorno `.env` con `python-dotenv`.
* Driver utilizado: `PyMySQL`.

---
### AGROPESO-002: Entidad pura `Ticket` y modelo `TicketDB`
* Creación de `Ticket` (Entidad Pura con `@dataclass`) aislada del ORM.
* Creación de `TicketDB` (Modelo SQLAlchemy).
* Se eliminó el modelo provisorio `Pesada`.

---
### AGROPESO-003: Repositorio de tickets (Patrón Repository)
* Implementación de `TicketRepository` aislando la capa de datos.
* Métodos implementados: `create_ticket`, `get_ticket_by_id`.
* Conversiones `_to_db` y `_to_entity` encapsuladas para proteger las capas superiores.

---
### AGROPESO-004: Servicio de tickets (Capa de negocio)
* Implementación de `TicketService`.
* Inyección de dependencias (`TicketRepository`).
* Reglas de negocio: el peso bruto debe ser mayor a la tara.
* Creación de excepciones propias (`ReglaNegocioError`, `TicketNoEncontradoError`).

---
### AGROPESO-005: Esquemas de la API (Pydantic)
* Implementación de validaciones de entrada (`TicketCreate`) y salida (`TicketResponse`).
* Separación de responsabilidades: Pydantic valida formato, el Service valida negocio.

---
### AGROPESO-006: Endpoints de FastAPI
* Creación de `ticket_router.py` (`APIRouter`).
* Inyección de sesión de BD mediante `Depends(get_db)`.
* Manejo de códigos HTTP basado en excepciones del servicio.

---
### AGROPESO-007: Punto de entrada de la aplicación
* Configuración de `main.py` (FastAPI).
* Configuración de `CORSMiddleware` inyectando orígenes desde `.env` (`CORS_ORIGINS`).

---
### AGROPESO-008: Interfaz de usuario HTML
* Maquetado en `frontend/html/index.html` usando `W3.CSS`.
* Validaciones nativas alineadas con los esquemas de Pydantic.

---
### AGROPESO-009: Conexión Frontend-Backend (JavaScript)
* Script `app.js` utilizando `Fetch API`.
* Intercepción del formulario, armado del JSON, y parseo de respuestas HTTP.
* Prevención de doble envío y manejo unificado de errores (400, 422, 500).

---
### AGROPESO-010: Listado y Flujo de Estados (Abiertos/Cerrados)
* Incorporación de la enumeración `EstadoTicket`.
* Endpoints para listar (`GET`) y cerrar (`PATCH`) tickets.
* Lógica modificada para admitir tickets sin `peso_bruto` en su creación inicial.

---
### AGROPESO-012: Interfaz del historial (HTML + JS)

Se agregó a la interfaz web una tabla con los tickets registrados, que consume el endpoint `GET /tickets/`.

- **`frontend/html/index.html`**: nueva sección debajo del formulario, con una tabla de W3.CSS (`w3-table-all`, con scroll horizontal en pantallas chicas). Tiene su propio contenedor, más ancho que el del formulario, para que las columnas no queden apretadas.
- **`frontend/js/app.js`**: la función `cargarHistorial()` hace un `fetch()` GET a la API y dibuja las filas de la tabla de forma dinámica.

#### Cuándo se carga

- Al abrir la página.
- Cada vez que se registra una pesada desde el formulario, para que el nuevo ticket aparezca sin recargar.

#### Columnas

| Columna | Campo de la API | Formato |
|---|---|---|
| ID | `id` | Número |
| Fecha | `fecha` | `día/mes/año` |
| Chofer | `chofer` | Texto |
| Patente | `patente` | Texto, o `—` si no tiene |
| Proveedor (ID) | `supplier_id` | Número |
| Tara (kg) | `peso_tara` | Con separador de miles |
| Bruto (kg) | `peso_bruto` | Con separador de miles, o `—` si el ticket está abierto |
| Neto (kg) | `peso_neto` | Con separador de miles, o `—` si el ticket está abierto |
| Estado | `estado` | Etiqueta de color: naranja (`abierto`) o verde (`cerrado`) |

Los tickets se muestran del más reciente al más antiguo, que es el orden en que los devuelve la API.

#### Mensajes de la tabla

| Situación | Lo que se muestra |
|---|---|
| Mientras carga | "Cargando..." |
| No hay tickets en la base | "Todavía no hay pesadas registradas" |
| La API no responde o devuelve un error | "No se pudo cargar el historial. ¿Está encendida la API?" (el detalle del error queda en la consola del navegador) |

#### Detalles de implementación

- Las filas se construyen con `createElement` y `textContent`, no con `innerHTML`, de modo que cualquier texto recibido (por ejemplo, un nombre de chofer) se muestra como texto y no se interpreta como HTML.
- Para vaciar y volver a llenar la tabla se usa `replaceChildren()`, que reemplaza todas las filas de una vez. No confundir con `replaceChild()`, que reemplaza un único hijo y falla si no se le indica cuál.
- El navegador exige que el origen desde el que se abre el frontend esté incluido en `CORS_ORIGINS` del `.env`. `http://localhost:5500` y `http://127.0.0.1:5500` son orígenes distintos, por lo que conviene incluir ambos. Después de modificar el `.env` hay que reiniciar la API por completo, ya que `--reload` no vigila ese archivo.

#### Cómo probarlo

1. Iniciar MariaDB y la API (`uvicorn main:app --reload`, desde `backend/`).
2. Servir el frontend desde la carpeta `frontend/` con `python3 -m http.server 5500`.
3. Abrir `http://localhost:5500/html/index.html`.

| Prueba | Resultado esperado |
|---|---|
| Abrir la página | La tabla muestra los tickets existentes, los más nuevos arriba |
| Un ticket abierto | Etiqueta naranja y `—` en bruto y neto |
| Registrar una pesada desde el formulario | Aparece arriba en la tabla sin recargar la página |
| Apagar la API y recargar | Fila con el mensaje de que no se pudo cargar el historial |

#### Pendientes conocidos

- La columna de proveedor muestra el ID, porque la API de tickets devuelve solo `supplier_id`. Para mostrar el nombre hace falta un endpoint de proveedores.
- La tabla muestra todos los tickets. Más adelante conviene paginarla y agregar un filtro por estado (la API ya lo soporta con `?estado=abierto` o `?estado=cerrado`).
- Desde la interfaz todavía no se puede cerrar un ticket abierto (el endpoint `PATCH /tickets/{ticket_id}` ya existe, falta la pantalla).
- No hay tests automáticos del router ni del frontend, y un error de nombres como el de `obtener_todos_los_tickets` solo se detectó al probar a mano.

---
## AGROPESO-014: Desplegable dinámico de proveedores

El campo **Proveedor** del formulario dejó de tener opciones escritas a mano en el HTML: ahora se llena solo con los proveedores que existen en la base de datos.

### Cómo funciona

1. Al cargar la página, `iniciar()` ejecuta `cargarProveedores()`.
2. `cargarProveedores()` hace un `fetch` a `GET /suppliers/` (endpoint del ticket 13).
3. Con el JSON recibido (`[{id, name}, ...]`) se crean los elementos `<option>`: el `value` es el **id** del proveedor (lo que se envía al backend) y el texto visible es el **nombre**.
4. Las opciones se colocan en el `<select id="supplier_id">` con `replaceChildren()`.
5. Una vez cargados los proveedores, `iniciar()` carga el historial, que muestra el **nombre** del proveedor en cada fila (a partir del mapa `proveedoresPorId`) en lugar de su ID.

### Estados del desplegable

| Situación | Texto mostrado |
|---|---|
| Mientras carga | Cargando proveedores... |
| Carga correcta | Elegí un proveedor |
| No hay proveedores en la base | No hay proveedores cargados |
| Falla el fetch o responde error | No se pudieron cargar los proveedores |

### Decisiones técnicas

- **`createElement` + `textContent`** en lugar de `innerHTML`: evita inyección de HTML si un nombre de proveedor contiene caracteres especiales.
- **`defaultSelected` en el placeholder**: así `form.reset()` vuelve al texto inicial en lugar de dejar el último proveedor elegido.
- **`proveedoresPorId` con fallback (`?? supplier_id`)**: si un ticket referencia un proveedor que ya no está en la lista, se muestra el ID en vez de una celda vacía.
- **Orden de carga con `async/await`**: el historial espera a los proveedores para poder mostrar nombres desde el primer dibujado.

### Cómo probarlo

1. Levantar el backend y servir el frontend (`python3 -m http.server 5500` desde `frontend/`).
2. Abrir `http://localhost:5500/html/index.html`. Si no se ven cambios, forzar la recarga con `Ctrl + Shift + R` (caché del navegador).
3. Verificar que el desplegable muestre los proveedores por nombre y que el historial muestre el nombre en la columna *Proveedor*.
4. Crear un proveedor nuevo desde `/docs` (`POST /suppliers/`), recargar la página y comprobar que aparece en la lista.
5. Apagar el backend y recargar: debe aparecer "No se pudieron cargar los proveedores".

---
## AGROPESO-015: Interfaz de cierre de ticket (frontend)

El operador ya puede cerrar un ticket abierto desde la tabla del historial, registrando el peso bruto (segunda pesada) sin usar Swagger.

### Cómo funciona

1. `cargarHistorial()` dibuja cada fila y, en la columna **Acciones**, llama a `crearCeldaAcciones(ticket)`.
2. Si el ticket está **abierto**, la celda muestra un botón **Cerrar**; si está **cerrado**, queda vacía.
3. Al hacer clic se ejecuta `cerrarTicket(id)`:
   - Muestra un `prompt()` con el texto "Ingrese el peso bruto:".
   - Si el operador cancela, no pasa nada.
   - Valida que el valor sea un número entero mayor a 0.
   - Envía `PATCH /tickets/{id}/cerrar` con el cuerpo `{"peso_bruto": valor}`.
4. Si la respuesta es exitosa (200 OK), se vuelve a llamar a `cargarHistorial()` y la fila pasa a estado **cerrado**, mostrando el peso bruto y el peso neto.

### Manejo de errores

| Situación | Resultado |
|---|---|
| El operador cancela el prompt | No se hace nada |
| Valor vacío, no numérico o <= 0 | Alert con el mensaje de validación, sin llamar al backend |
| El backend rechaza (ej. peso bruto <= tara) | Alert con el detalle devuelto por la API |
| Sin conexión con el servidor | Alert genérico y error en consola |

### Decisiones técnicas

- **Validación en dos capas**: el frontend filtra entradas obvias para ahorrar una petición, y el backend mantiene la regla de negocio (el bruto debe superar la tara).
- **`addEventListener` en vez de `onclick` en el HTML**: evita armar código dentro de strings y pasa el `id` correctamente a cada botón.
- **Refresco con `cargarHistorial()`**: la tabla siempre refleja lo que está guardado en la base, no un estado local.
- **`prompt()` nativo**: solución simple para esta etapa; más adelante puede reemplazarse por un modal.

### Cómo probarlo

1. Crear un ticket solo con tara: debe aparecer con el botón **Cerrar**.
2. Cerrarlo con un peso bruto mayor a la tara: la fila pasa a cerrado y muestra el peso neto.
3. Probar un bruto menor o igual a la tara: debe mostrarse el error del backend.
4. Cancelar el prompt o ingresar texto: no debe cambiar nada.
5. Verificar que los tickets cerrados no muestran el botón.

---
## AGROPESO-016: Modelo de usuario y repositorio (backend)

Se creó la base para el login y los roles: la tabla de usuarios, sus schemas y el repositorio. Todavía no hay endpoints ni hash de contraseñas; eso se agrega en los próximos tickets.

### Archivos

| Archivo | Contenido |
|---|---|
| `models/user_model.py` | Enum `Rol`, entidad pura `User` y modelo SQLAlchemy `UserDB` |
| `schemas/user_schema.py` | `UserCreate` (entrada) y `UserResponse` (salida) |
| `repository/user_repository.py` | `UserRepository` con `get_user_by_username` y `create_user` |
| `tests/test_users.py` | Tests del repositorio y de la regla de negocio |

### Tabla `users`

| Columna | Tipo | Detalle |
|---|---|---|
| `id` | Integer | Clave primaria, autoincremental |
| `username` | String(50) | Único, obligatorio |
| `password_hash` | String(255) | Obligatorio; nunca se guarda el texto plano |
| `rol` | String(10) | `admin` o `cliente` |
| `supplier_id` | Integer | FK a `suppliers.id`, anulable |

Un usuario **cliente** se vincula a su proveedor mediante `supplier_id`, lo que permite más adelante mostrarle solo sus propios tickets.

### Regla de negocio

- Rol `cliente` → `supplier_id` **obligatorio**.
- Rol `admin` → `supplier_id` debe ser **nulo**.

Se valida en `UserCreate` con un `model_validator`; si se viola, la API responde 422.

### Decisiones técnicas

- **Entidad pura + modelo de base**: igual que en tickets, `User` no depende de SQLAlchemy y el repositorio convierte entre ambos (`_to_db`, `_to_entity`).
- **Enum `Rol`**: se guarda como texto en la base, pero en Python no se puede usar un rol inválido.
- **`UserResponse` sin contraseña**: lo que no está declarado en el schema de salida nunca se devuelve.
- **`UserCreate` recibe `password`, el repositorio recibe `password_hash`**: el paso de hashear queda para el service.
- **`create_all` no modifica tablas existentes**: si cambia la estructura de `users`, hay que borrar la tabla y recrearla (o usar `ALTER TABLE`).

### Cómo probarlo

1. Ejecutar `python create_table.py` desde `backend/` para crear la tabla `users`.
2. Ejecutar `pytest`: deben pasar todos los tests, incluidos los 6 de `test_users.py`.
   
---
## AGROPESO-017: Servicio de autenticación y generación de token (JWT)

Se implementó el inicio de sesión: la contraseña se guarda cifrada y, al hacer login con credenciales válidas, el backend emite un token JWT. En este ticket solo se **emite** el token; todavía no se usa para proteger rutas.

### Archivos

| Archivo | Contenido |

|---|---|

| `services/auth_service.py` | Hash de contraseñas, creación del token y autenticación |

| `routers/auth_router.py` | Endpoint `POST /auth/login` |

| `crear_admin.py` | Script para crear un usuario admin desde la terminal |

| `tests/test_auth.py` | Tests del servicio de autenticación |

### Funciones del servicio

| Función | Qué hace |

|---|---|

| `get_password_hash(password)` | Devuelve el hash bcrypt de la contraseña |

| `verify_password(plain, hashed)` | Comprueba si una contraseña coincide con su hash |

| `create_access_token(data)` | Genera un JWT firmado con vencimiento |

| `authenticate_user(repo, username, password)` | Devuelve el usuario o `None` si las credenciales no son válidas |

### Endpoint `POST /auth/login`

**Entrada**: formulario (`application/x-www-form-urlencoded`) con `username` y `password`, no JSON.
**Respuesta 200**: `{"access_token": "...", "token_type": "bearer"}`
**Respuesta 401**: `Usuario o contraseña incorrectos` (el mismo mensaje si el usuario no existe o la clave es errónea).

### Contenido del token

El payload incluye `username`, `rol`, `supplier_id` y `exp` (vencimiento). El JWT está **firmado, no cifrado**: cualquiera puede leer su contenido, por lo que no debe incluir datos sensibles. La firma garantiza que no puede modificarse sin la clave secreta.

### Configuración (`backend/.env`)

SECRET_KEY=<clave generada con: python -c “import secrets; print(secrets.token_hex(32))”>
ACCESS_TOKEN_EXPIRE_MINUTES=60

La clave **no se sube al repositorio**. Al cambiar el `.env` hay que reiniciar uvicorn.

### Decisiones técnicas

**Hash de un solo sentido (bcrypt)**: no se puede recuperar la contraseña original; se compara con `verify_password`. La sal aleatoria hace que dos hashes de la misma contraseña sean distintos.
**`bcrypt==4.0.1` fijado**: versiones más nuevas son incompatibles con `passlib`.
**Mismo error para usuario y contraseña incorrectos**: evita revelar qué usuarios existen.
**Clave leída del `.env`**: nunca escrita en el código.
**Tests sin base de datos**: se usa un repositorio falso en memoria.

### Cómo probarlo

Instalar dependencias: `pip install -r requirements.txt`.
2. Agregar `SECRET_KEY` al `.env` y reiniciar uvicorn.

3. Crear un usuario: `python crear_admin.py` (desde `backend/`).

4. En `/docs`, ejecutar `POST /auth/login` con ese usuario: debe devolver el token. Con una contraseña incorrecta, debe devolver 401.

5. Opcional: pegar el token en jwt.io para ver su contenido.

6. Ejecutar `pytest`.

---

## AGROPESO-018: Middleware de seguridad y autorización

La API ahora exige un token JWT válido y aplica reglas según el rol del usuario. Un cliente solo puede ver el historial de su propia empresa.

### Archivos

| Archivo | Cambio |
|---|---|
| `middleware/security.py` | Nuevo: `get_current_user` y `exigir_admin` |
| `models/user_model.py` | Nueva entidad `UsuarioActual` |
| `services/auth_service.py` | Nueva función `decode_access_token` |
| `routers/ticket_router.py` | Todos los endpoints exigen token; POST y PATCH solo admin |
| `services/ticket_service.py` | Filtrado por rol en listado y en búsqueda por id |
| `repository/ticket_repository.py` | `get_all_tickets` acepta `supplier_id` |

### Cómo funciona

1. El cliente envía el token en el encabezado `Authorization: Bearer <token>`.
2. `get_current_user` (basada en `OAuth2PasswordBearer`) verifica la firma y el vencimiento, y devuelve un `UsuarioActual` con `username`, `rol` y `supplier_id`.
3. Cada endpoint recibe ese usuario con `Depends(get_current_user)`.
4. Las acciones de escritura llaman a `exigir_admin(user)` antes de hacer cualquier otra cosa.
5. Las lecturas pasan el usuario al servicio, que decide qué datos corresponden.

### Permisos por endpoint

| Endpoint | Admin | Cliente | Sin token |
|---|---|---|---|
| `POST /tickets/` | ✅ | 403 | 401 |
| `PATCH /tickets/{id}/cerrar` | ✅ | 403 | 401 |
| `GET /tickets/` | Todos los tickets | Solo los de su proveedor | 401 |
| `GET /tickets/{id}` | Cualquiera | Solo si es de su proveedor (si no, 404) | 401 |

### Códigos de error

- **401**: no se sabe quién es el usuario (sin token, token inválido, alterado o vencido).
- **403**: el usuario está identificado pero no tiene permiso para la acción.
- **404**: un cliente pide un ticket de otro proveedor; se responde igual que si no existiera para no revelar su existencia.

### Decisiones técnicas

- **Falla cerrado**: un cliente sin `supplier_id` recibe lista vacía en lugar de ver todo.
- **Control de acceso por id**: no alcanza con filtrar la lista; `GET /tickets/{id}` también valida que el ticket sea del proveedor del cliente.
- **`UsuarioActual` como entidad propia**: el servicio no depende de FastAPI y se puede probar con usuarios armados a mano.
- **Autorización antes de la lógica**: `exigir_admin` es lo primero que ejecuta cada endpoint de escritura.
- **Servicio separado**: `obtener_ticket` queda como búsqueda interna (la usa `cerrar_ticket`) y `obtener_ticket_de_usuario` aplica la regla de visibilidad.

### Cómo probarlo

1. Reiniciar uvicorn y abrir `/docs`: aparece el botón **Authorize**.
2. Sin token, `GET /tickets/` debe responder 401.
3. Autenticarse como admin: se pueden crear, cerrar y listar todos los tickets.
4. Crear un usuario cliente asociado a un proveedor y autenticarse con él: debe ver solo sus tickets; `POST` y `PATCH` deben dar 403, y pedir un ticket de otro proveedor debe dar 404.
5. Un token alterado o vencido debe responder 401.
6. Ejecutar `pytest`.

### Pendientes conocidos

- El frontend aún no envía el token ni tiene pantalla de login, por lo que la página recibe 401 hasta ese ticket.
- `GET /suppliers/` y `POST /suppliers/` todavía no están protegidos.
- Tests de los endpoints con `TestClient` para verificar automáticamente los 401/403.
