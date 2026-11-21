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


---

## AGROPESO-019: Pantalla de login y sesión en el frontend

El frontend ahora tiene pantalla de inicio de sesión. Guarda el token JWT, redirige según el rol y envía el token en cada petición. Además, la API de proveedores quedó protegida.

### Archivos

| Archivo | Cambio |
|---|---|
| `frontend/html/login.html` | Nuevo: formulario de usuario y contraseña |
| `frontend/js/auth.js` | Nuevo: manejo de sesión compartido por todas las pantallas |
| `routers/supplier_router.py` | `GET` exige token; `POST` solo admin |
| `crear_cliente.py` | Script para crear usuarios con rol cliente asociados a un proveedor (eliminado en AGROPESO-024: reemplazado por `POST /users/`) |

### Cómo funciona

1. `login.html` envía `username` y `password` a `POST /auth/login` como formulario (`application/x-www-form-urlencoded`).
2. Si la respuesta es 200, `auth.js` lee el `rol` del token, lo guarda en `localStorage` con la clave `access_token` y redirige: `admin` → `admin.html`, `cliente` → `cliente.html`.
3. Si es 401, muestra "Usuario o contraseña incorrectos" y si el rol es desconocido no guarda el token.
4. `fetchConToken(url, opciones)` agrega el encabezado `Authorization: Bearer <token>` a cada petición. Si no hay token o la API responde 401, borra la sesión y vuelve al login.

### Decisiones técnicas

- **Un solo archivo de sesión**: `auth.js` concentra la clave del token, la lectura del payload y las peticiones autenticadas, para que todas las pantallas usen lo mismo.
- **Redirección por rol**: la tabla `PAGINAS_POR_ROL` define el destino de cada rol; sumar un rol es agregar una línea.
- **Sin `innerHTML`**: los mensajes de error se asignan con `textContent`.
- **El frontend no decide permisos**: leer el rol del token sirve solo para elegir la pantalla; la autorización real la hace el backend.

### Cómo probarlo

1. Abrir `http://localhost:5500/html/login.html` con la API encendida.
2. Con credenciales incorrectas aparece el mensaje en rojo.
3. Con un admin se redirige a `admin.html`.
4. Con el servidor apagado aparece "No se pudo conectar con el servidor".

### Pendientes conocidos

- `cliente.html` todavía no existe: un login de cliente redirige a una página inexistente hasta el ticket de la vista de cliente.

---

## AGROPESO-020: Dashboard del administrador

La vista operativa se transformó en el panel de control del administrador, con guardia de rol, buscador, alta de tickets, acciones rápidas y lista de tickets abiertos de hoy.

### Archivos

| Archivo | Cambio |
|---|---|
| `frontend/html/admin.html` | Nuevo: panel en tres columnas y modal reutilizable |
| `frontend/js/admin.js` | Nuevo: lógica del panel |
| `frontend/js/auth.js` | Nueva función `obtenerSesion` (valida existencia y vencimiento del token) |
| `tests/test_endpoints.py` | Nuevo: pruebas de 401 y 403 con `TestClient` |
| `requirements.txt` | Agrega `httpx` (lo necesita `TestClient`) |
| `index.html`, `app.js` | Eliminados: eran el panel anterior, que enviaba peticiones sin token |
| `operator_dashboard.html`, `client_dashboard.html`, `prueba_repo.py` | Eliminados: estaban vacíos o eran un script de prueba suelto |
| `.gitignore` | Corregido el typo `__pychache__/` |

### Cómo funciona

1. **Guardia de rol**: al cargar, `obtenerSesion()` verifica que haya token y que no esté vencido, y que el `rol` sea `admin`. Si no, borra el token y redirige a `login.html`.
2. **Barra superior**: botón "Cerrar sesión (usuario)" arriba a la derecha y buscador a lo ancho.
3. **Buscador**: sin texto, la tabla muestra los tickets `abierto` con la fecha de hoy. Con texto, busca entre **todos** los tickets (abiertos y cerrados) por nombre de proveedor o patente.
4. **Columna izquierda**: formulario Nuevo ticket (chofer, patente, peso tara, peso bruto opcional y desplegable dinámico de proveedores).
5. **Columna central**: botones redondeados Cerrar ticket (pide el ID), Agregar proveedor (`POST /suppliers/`) y Agregar producto.
6. **Columna derecha**: tabla de tickets abiertos de hoy, con botón Cerrar en cada fila.
7. **Modal**: reemplaza a `prompt()` y `alert()` con una ventana de W3.CSS; se cierra con Cancelar, `Esc` o clic en el fondo, y valida el dato antes de aceptarlo.

### Decisiones técnicas

- **Fuente única de verdad**: tras crear o cerrar un ticket, o crear un proveedor, se vuelve a pedir la lista a la API; el frontend no modifica datos localmente.
- **Filtrado en el navegador**: se pide la lista una vez y el buscador filtra sin nuevas peticiones.
- **Fecha local**: "hoy" se calcula con la fecha del navegador (no con `toISOString()`, que usa UTC y podría dar otro día).
- **Sin `innerHTML` con datos**: filas, celdas y opciones se crean con `createElement`, `textContent` y `replaceChildren`; los eventos se enlazan con `addEventListener`.
- **Estilo**: solo clases de W3.CSS; no fue necesario modificar `styles.css`.
- **Tests de seguridad**: `test_endpoints.py` sustituye al usuario con `dependency_overrides`, así que no necesita base de datos.

### Cómo probarlo

1. Sin sesión, abrir `admin.html`: redirige a `login.html`.
2. Entrar como cliente y abrir `admin.html` a mano: redirige y borra el token.
3. Entrar como admin: se ve el panel con el usuario arriba a la derecha.
4. Crear un ticket solo con tara: aparece en la tabla como `abierto`.
5. Crear uno con tara y bruto: queda `cerrado` y no aparece en la lista de abiertos de hoy.
6. Cerrar un ticket desde su fila y desde el botón central.
7. Agregar un proveedor: aparece en el desplegable sin recargar.
8. Buscar por patente y por proveedor; al borrar el texto vuelve la lista de hoy.
9. Ejecutar `pytest`.

### Pendientes conocidos

- **Agregar producto** solo muestra un aviso: no existe aún el endpoint de productos.
- "Hoy" se calcula con la fecha del navegador y la API usa la fecha del servidor; si MySQL corre en UTC, un ticket cargado por la noche puede quedar con la fecha del día siguiente.
- `cliente.html` (vista de cliente de solo lectura) queda para el próximo ticket.

---

## AGROPESO-022: Validación de existencia y unicidad de proveedores (backend)

La API ya no responde 500 cuando se crea un ticket con un proveedor inexistente, y no permite registrar dos proveedores con el mismo nombre.

### Archivos

| Archivo | Cambio |
|---|---|
| `utils/exceptions.py` | Nueva excepción `ProveedorDuplicadoError` |
| `repository/supplier_repository.py` | Nuevos `get_supplier_by_id` y `get_supplier_by_name` (sin distinguir mayúsculas); `create_supplier` traduce el `IntegrityError` de la restricción única a `ProveedorDuplicadoError` |
| `services/supplier_service.py` | `crear_proveedor` rechaza nombres repetidos |
| `routers/supplier_router.py` | Traduce `ProveedorDuplicadoError` a 409 |
| `services/ticket_service.py` | Recibe también un `SupplierRepository`; nueva regla `validar_proveedor` |
| `routers/ticket_router.py` | Helper `crear_servicio(db)` que arma el servicio con sus dos repositorios |
| `models/suppliers.py` | `name` con `unique=True` |
| `tests/test_server.py`, `tests/test_suppliers.py` | Tests de las nuevas reglas y de las búsquedas del repositorio |
| `tests/test_endpoints.py` | Tests HTTP de 409 y 400 contra la base real (con rollback) |

### Cómo funciona

| Situación | Antes | Ahora |
|---|---|---|
| `POST /tickets/` con `supplier_id` inexistente | 500 (error de clave foránea de MySQL) | **400** `No existe el proveedor con id X` |
| `POST /suppliers/` con un nombre que ya existe (`Berg`, `berg`, `BERG`) | Se creaba un duplicado | **409** `Ya existe un proveedor con el nombre 'X'` |

### Decisiones técnicas

- **Validar en el servicio, antes de tocar la base**: el error de MySQL se evita en lugar de atraparlo, así el mensaje es claro y no depende del texto del driver.
- **Proveedor inexistente → 400 (`ReglaNegocioError`)**: es un dato inválido dentro del ticket, no un recurso faltante en la URL (eso sería 404). Se reutiliza la excepción y el router no cambia.
- **Duplicado → 409 Conflict**: el formato es válido, pero choca con un dato que ya existe.
- **Inyección de `SupplierRepository` en `TicketService`**: el servicio de tickets consulta proveedores a través de su repositorio, sin importar SQLAlchemy. En los tests se reemplaza por uno en memoria.
- **Restricción `UNIQUE` en la base**: es la garantía final si dos administradores crean el mismo proveedor al mismo tiempo. En ese caso el repositorio atrapa el `IntegrityError`, hace rollback y lanza `ProveedorDuplicadoError`, así la respuesta también es 409. `create_all` no agrega la restricción a tablas existentes; ver la guía de desarrollo.
- **Frontend sin cambios**: `admin.js` ya muestra el `detail` de la API en el modal de error.

### Cómo probarlo

1. En una base existente, agregar la restricción única (ver *Guía de Desarrollo → Base de Datos*).
2. En `/docs`, como admin, `POST /suppliers/` con un nombre existente en otra combinación de mayúsculas: debe responder 409.
3. `POST /tickets/` con `"supplier_id": 9999`: debe responder 400 con el mensaje del proveedor.
4. Desde `admin.html`, agregar un proveedor repetido: el modal muestra el error.
5. Ejecutar `pytest`.

### Pendientes conocidos

- `numero_ticket` repetido y `product_id` inexistente siguen respondiendo 500 (el segundo se resuelve junto con el CRUD de productos).

---

## AGROPESO-023: Flujo completo de productos (backend + frontend admin)

El botón **Cargar producto** del panel del administrador ya crea productos reales, y el formulario de nuevo ticket permite elegir uno (opcional).

### Archivos

| Archivo | Cambio |
|---|---|
| `models/products.py` | Nueva entidad pura `ProductEntity` (el modelo `Product` ya existía) |
| `repository/product_repository.py` | Nuevo: `get_all_products`, `get_product_by_id`, `get_product_by_name` (sin distinguir mayúsculas) y `create_product` (traduce el `IntegrityError` a `ProductoDuplicadoError`) |
| `services/product_service.py` | Nuevo: listar y crear, rechazando nombres repetidos |
| `schemas/product_schema.py` | Nuevo: `ProductCreate` y `ProductResponse` |
| `routers/product_router.py` | Nuevo: `GET /products/` y `POST /products/` |
| `main.py` | Registra el router de productos |
| `utils/exceptions.py` | Nueva excepción `ProductoDuplicadoError` |
| `services/ticket_service.py` | Recibe un `ProductRepository`; nueva regla `validar_producto` |
| `routers/ticket_router.py` | `crear_servicio(db)` agrega el `ProductRepository` |
| `frontend/html/admin.html` | Nuevo desplegable **Producto (opcional)** en el formulario |
| `frontend/js/admin.js` | `cargarProductos`, `agregarProducto` y `product_id` en el envío del ticket |
| `tests/test_products.py` | Nuevo: esquemas, servicio, repositorio e `IntegrityError` simulado |
| `tests/test_server.py`, `tests/test_endpoints.py`, `tests/conftest.py` | Tests de `product_id` en tickets, permisos y 409 de productos; fixture `producto` |

### Cómo funciona

| Acción | Resultado |
|---|---|
| `GET /products/` | Lista de productos ordenada por nombre (admin y cliente) |
| `POST /products/` (admin) | 201 con el producto; 409 si el nombre ya existe; 403 si es cliente |
| `POST /tickets/` con `product_id` inexistente | 400 `No existe el producto con id X` (antes: 500) |
| `POST /tickets/` sin `product_id` | Igual que antes: el producto es opcional |

En el panel:

1. Al iniciar, proveedores y productos se cargan en paralelo (`Promise.all`) antes que los tickets.
2. **Cargar producto** abre el modal; valida nombre vacío o de más de 200 caracteres antes de llamar a la API.
3. Si se crea, el desplegable se recarga y aparece el mensaje verde. Si la API responde 409, el modal muestra el detalle.
4. El desplegable empieza en **Sin producto**, que se puede elegir y envía `product_id: null`. `form.reset()` vuelve a esa opción.

### Decisiones técnicas

- **Mismo patrón que proveedores**: entidad pura, repositorio como frontera, validación de duplicados en el servicio y `UNIQUE` en la base como garantía ante altas simultáneas.
- **La tabla `products` ya existía con `UNIQUE (name)`**: no hace falta migración.
- **`GET /products/` visible para clientes**: el catálogo de productos no es información sensible.
- **Primera opción seleccionable** (a diferencia de proveedores): el producto es opcional, así que "Sin producto" es una elección válida.

### Cómo probarlo

1. Reiniciar uvicorn (o esperar el `--reload`) y forzar la recarga de `admin.html` con `Ctrl + Shift + R`.
2. **Cargar producto** con el nombre vacío: el modal muestra el error sin llamar a la API.
3. Crear "Soja": aparece en el desplegable del formulario.
4. Crear "soja": el modal muestra el 409.
5. Registrar una pesada con y sin producto.
6. Ejecutar `pytest`.

### Pendientes conocidos

- ~~La tabla de tickets del panel todavía no muestra el producto.~~ Resuelto en *fix-ticket023*.
- `numero_ticket` repetido sigue respondiendo 500.
- No se pueden editar ni borrar productos.

---

## fix-ticket023: columna Producto en las tablas de tickets

Las tablas de tickets ahora muestran el producto de cada pesada, tanto en el panel del administrador como en el del cliente.

### Archivos

| Archivo | Cambio |
|---|---|
| `frontend/html/admin.html` | Columna **Producto** después de *Proveedor* (`colspan` 10 → 11) |
| `frontend/js/admin.js` | Mapa `productosPorId` (se llena en `cargarProductos`) y función `nombreProducto` |
| `frontend/html/cliente.html` | Columna **Producto** en *Todos los tickets* y en *Tickets del mes* (`colspan` 8 → 9 y 5 → 6) |
| `frontend/js/cliente.js` | `cargarProductos` antes de dibujar, `nombreProducto` y constantes `COLUMNAS_TODOS` / `COLUMNAS_MES` |

### Cómo funciona

1. Al iniciar, la pantalla pide `GET /products/` y arma `productosPorId` (`{id: nombre}`), igual que `proveedoresPorId` en el admin.
2. Los tickets se dibujan después, así que el nombre ya está disponible en el primer dibujado.
3. Cada fila muestra:

| Caso | Se muestra |
|---|---|
| Ticket sin producto (`product_id: null`) | `—` |
| Producto conocido | Su nombre |
| Producto que no vino en la lista (o falló la carga) | Su id, como respaldo |

### Decisiones técnicas

- **Sin cambios en el backend**: la API de tickets sigue devolviendo solo `product_id`; el nombre se resuelve en el navegador con la lista de productos, el mismo criterio que ya se usaba para proveedores.
- **Constantes para los `colspan` en `cliente.js`**: el número de columnas aparecía repetido en varias llamadas; ahora se cambia en un solo lugar.
- **Si falla `GET /products/`** la pantalla sigue funcionando y muestra los ids.

### Cómo probarlo

1. Forzar la recarga (`Ctrl + Shift + R`) de `admin.html` y `cliente.html`.
2. Registrar una pesada con producto y otra sin producto desde el panel del admin.
3. Buscar ambos tickets en el admin: uno muestra el nombre del producto y el otro `—`.
4. Entrar como cliente de ese proveedor: las dos tablas muestran la columna *Producto*.

---

## AGROPESO-024: Gestión de cuentas de clientes desde la API (`POST /users/`)

El administrador ya puede dar de alta usuarios con rol `cliente` desde el panel, sin usar el script `crear_cliente.py`.

### Archivos

| Archivo | Cambio |
|---|---|
| `schemas/user_schema.py` | Nuevo esquema `ClienteCreate` (`username`, `password`, `supplier_id`) |
| `services/user_service.py` | Nuevo: `UserService.crear_cliente` |
| `routers/user_router.py` | Nuevo: `POST /users/` (solo admin) |
| `repository/user_repository.py` | `create_user` traduce el `IntegrityError` a `UsuarioDuplicadoError` |
| `utils/exceptions.py` | Nueva excepción `UsuarioDuplicadoError` |
| `main.py` | Registra el router de usuarios |
| `crear_cliente.py` | **Eliminado**: reemplazado por el endpoint (`crear_admin.py` se mantiene para el primer admin) |
| `frontend/html/admin.html` | Botón **Cargar cliente** debajo de las acciones y modal de alta con varios campos |
| `frontend/js/admin.js` | Lógica del modal: validación, envío y errores dentro del modal |
| `tests/test_users.py`, `tests/test_endpoints.py` | Tests del esquema, servicio, repositorio y endpoint (incluye login del cliente creado) |

### Cómo funciona

1. **Cargar cliente** abre un modal con usuario, contraseña, repetir contraseña y proveedor (los mismos que el formulario de tickets).
2. El navegador valida largo del usuario, contraseña mínima, límite de 72 bytes, coincidencia y proveedor elegido.
3. Se envía `POST /users/`. El servicio:
   - rechaza el usuario si ya existe (409),
   - rechaza el proveedor si no existe (400),
   - guarda la contraseña con hash bcrypt y rol `cliente`.
4. Si hay un error, se muestra **dentro del modal** sin borrar lo escrito. Si sale bien, el modal se cierra, se limpia el formulario y aparece el mensaje verde.

### Decisiones técnicas

- **El endpoint solo crea clientes**: el rol lo fija el servidor y `ClienteCreate` no lo acepta (`extra="forbid"`). Así no se puede crear un admin desde la pantalla, ni por error ni manipulando la petición.
- **La contraseña no se recorta** (`UserCreate` sí usa `str_strip_whitespace`): el login no recorta, así que una clave con un espacio al final quedaría inutilizable.
- **Límite de 72 bytes**: es lo máximo que bcrypt procesa; se valida en el esquema y en el navegador, igual que hacía el script.
- **Usuario único sin distinguir mayúsculas**: la colación de MariaDB ya trata `Berg` y `berg` como iguales, tanto en el login como en la restricción `UNIQUE`.
- **Modal propio**: el modal genérico tiene un solo campo; este tiene cuatro y muestra los errores sin cerrarse. Al cerrar se hace `reset()` para no dejar la contraseña en el DOM.

### Cómo probarlo

1. Forzar la recarga de `admin.html` (`Ctrl + Shift + R`).
2. **Cargar cliente** → enviar vacío: aparece el error de usuario.
3. Contraseñas distintas: "Las contraseñas no coinciden".
4. Completar todo bien: mensaje verde "Cliente ... creado para ...".
5. Repetir el mismo usuario en mayúsculas: el modal muestra el 409.
6. Cerrar sesión y entrar con el cliente nuevo: abre `cliente.html` con los tickets de su proveedor.
7. Ejecutar `pytest`.

### Pendientes conocidos

- No hay listado, edición, baja ni cambio de contraseña de clientes.
- El primer admin se sigue creando con `crear_admin.py`.

---

## AGROPESO-025: Filtros avanzados y exportación a Excel/CSV (admin y cliente)

El administrador y el cliente pueden combinar filtros (proveedor, producto, texto y rango de fechas) y descargar un CSV listo para Excel con exactamente las filas filtradas y una fila de totales.

### Archivos

| Archivo | Cambio |
|---|---|
| `frontend/js/exportar.js` | **Nuevo**, compartido: filtros combinables, generación del CSV, nombre del archivo y descarga |
| `frontend/html/admin.html` | Botón **Exportar Excel** al lado del buscador (mismo tamaño que *Cerrar sesión*) y barra de filtros: proveedor, producto, desde, hasta, limpiar |
| `frontend/js/admin.js` | `leerFiltros`, `renderizarTabla` con filtros `AND`, `exportarExcel`, selectores de filtro poblados desde `proveedoresPorId` / `productosPorId` |
| `frontend/html/cliente.html` | Botón **Descargar Excel** al lado del buscador, barra de filtros (producto, desde, hasta, limpiar) y tarjeta **Total neto filtrado** |
| `frontend/js/cliente.js` | Filtros sobre *Todos los tickets*, total neto filtrado y `descargarExcel` |
| `.md/guia_de_desarrollo.md`, `.md/arquitectura_del_sistema.md` | Funciones de `exportar.js` y formato del CSV |

### Cómo funciona

**Admin**

| Situación | Tabla | Archivo |
|---|---|---|
| Sin filtros | Tickets abiertos de hoy (como antes) | Esos mismos tickets → `AgroPeso_General_2026-11-20.csv` |
| Con algún filtro | Todos los tickets (abiertos y cerrados) que cumplen **todos** los filtros, con la cantidad en el título | Esas mismas filas → `AgroPeso_Berg_2026-11-01_a_2026-11-20.csv` |
| *Desde* posterior a *Hasta* | "La fecha Desde es posterior a Hasta" | No descarga |
| Sin resultados | "Ningun ticket coincide con los filtros" | Aviso inline, no descarga |

El buscador de texto busca en patente, chofer y nombre del proveedor. Si se filtra un producto, su nombre también va en el archivo (`AgroPeso_General_Soja_...csv`).

**Cliente**

* Los filtros (producto, desde, hasta y texto por patente o chofer; también acepta la fecha escrita) afectan *Todos los tickets*. *Tickets del mes* no cambia.
* La tarjeta **Total neto filtrado** suma el peso neto de los tickets **cerrados** que pasan el filtro y muestra cuántos son.
* **Descargar Excel** exporta esas filas → `MisPesadas_2026-11-01_a_2026-11-20.csv` (con el producto si se filtró uno). El backend ya devuelve solo los tickets del proveedor del cliente.

**Archivo**

| Columna | Contenido |
|---|---|
| N° Ticket | `id` del ticket (el mismo que se ve en las tablas) |
| Fecha y Hora | Fecha `dd/mm/aaaa` |
| Estado | `Abierto` / `Cerrado` |
| Proveedor | Nombre (en el cliente, siempre el suyo) |
| Producto | Nombre, o `-` |
| Patente, Chofer | Texto |
| Peso Tara / Bruto / Neto (kg) | Número sin separador de miles, o `-` si está abierto |

Al final: una fila vacía y la fila `TOTALES` con `X cerradas de Y`, la suma de la tara de todos los tickets exportados y la suma de bruto y neto de los cerrados.

### Decisiones técnicas

- **Filtrado en el navegador**: la lista ya viene completa (y limitada por rol) desde `GET /tickets/`; no hizo falta tocar el backend.
- **Lo que se ve es lo que se exporta**: `ticketsVisibles` (admin) y `ticketsFiltrados` (cliente) alimentan la tabla y el archivo, así nunca difieren.
- **Módulo compartido `exportar.js`**: admin y cliente generan exactamente el mismo formato.
- **Protección contra inyección de fórmulas**: un chofer cargado como `=HYPERLINK(...)` se exporta como texto (`'=HYPERLINK(...)`). Un `-` solo (campo vacío) no se modifica.
- **Selectores con `createElement` + `textContent` + `replaceChildren`**: sin `innerHTML`. Al recargar proveedores o productos se conserva la opción elegida.
- **Sin dependencias nuevas**: CSV con BOM en lugar de `.xlsx`, que requeriría una librería.

### Cómo probarlo

1. Admin: elegir un proveedor → la tabla muestra solo sus tickets → **Exportar Excel** descarga solo esos.
2. Admin: proveedor + *Desde* / *Hasta* → la tabla y el archivo respetan las dos condiciones; el nombre incluye el rango.
3. Admin: un rango sin tickets → aviso "No hay tickets para exportar con los filtros seleccionados" y no se descarga nada.
4. Cliente: cambiar fechas o producto → cambia **Total neto filtrado** → **Descargar Excel** baja esas filas.
5. Abrir el archivo en Excel: columnas separadas, tildes y ñ correctas, fila `TOTALES` al final.

### Pendientes conocidos

- El ticket no guarda la hora, solo la fecha: la columna *Fecha y Hora* muestra solo la fecha. Para incluir la hora hay que agregar un campo de fecha y hora en `tickets` (y migrar los datos existentes).
- `N° Ticket` usa el `id`; el campo opcional `numero_ticket` no se carga desde el panel.
- Con muchos tickets, filtrar en el navegador deja de escalar: conviene mover los filtros a la API (`GET /tickets/?desde=...`) junto con la paginación pendiente.

---

## AGROPESO-026: Edición de tickets abiertos y cerrados (backend + panel admin)

El administrador puede corregir cualquier ticket ya creado (patente, chofer, proveedor, producto, tara y bruto), esté abierto o cerrado. El peso neto siempre lo recalcula el backend.

### Archivos

| Archivo | Cambio |
|---|---|
| `backend/schemas/ticket_schema.py` | **Nuevo** `TicketUpdate`: `extra="forbid"`, recorta espacios, mismos límites que `TicketCreate` |
| `backend/services/ticket_service.py` | **Nuevo** `editar_ticket`: valida ticket, proveedor, producto y pesos, y decide el estado |
| `backend/routers/ticket_router.py` | **Nuevo** `PUT /tickets/{ticket_id}` (solo admin) |
| `backend/utils/exceptions.py` | **Nueva** `ReferenciaNoEncontradaError` (proveedor/producto inexistente al editar → `404`) |
| `backend/repository/ticket_repository.py` | Sin cambios: `update_ticket` ya guardaba todos los campos y el neto calculado |
| `backend/tests/test_server.py`, `backend/tests/test_endpoints.py` | 15 tests nuevos |
| `frontend/html/admin.html` | **Nuevo** modal `#modal-editar-ticket` |
| `frontend/js/admin.js` | Botón **Editar** en cada fila, `abrirModalEditar`, vista previa del neto, `validarEdicion` y envío con `PUT` |

### Cómo funciona

| Situación | Resultado |
|---|---|
| Ticket abierto, sin `peso_bruto` | Se corrigen los datos; sigue `abierto` con neto `null` |
| Ticket abierto, con `peso_bruto` válido | Queda `cerrado` y se calcula el neto |
| Ticket cerrado, con `peso_bruto` válido | Sigue `cerrado` y el neto se recalcula (`bruto - tara`) |
| `peso_bruto <= peso_tara` | `400`, no se guarda nada |
| Ticket cerrado con `peso_bruto: null` | `400` (no se reabre un ticket desde la edición) |
| Ticket, proveedor o producto inexistente | `404` |
| Rol `cliente` / sin token | `403` / `401` |

**Panel admin**: cada fila de la tabla (abiertos de hoy y resultados de filtros) tiene **Editar**; los abiertos además mantienen **Cerrar**. El modal se abre con los valores actuales del ticket. En un ticket cerrado el bruto es obligatorio (`*`). El **Peso neto** se recalcula en vivo al cambiar tara o bruto (en rojo si el bruto no supera la tara). Los errores, tanto los de la validación en el navegador como los `400`/`404`/`422` de la API, se muestran dentro del modal sin perder lo escrito. Al guardar, el modal se cierra y la lista se vuelve a pedir a la API.

### Decisiones técnicas

- **`PUT` y no `PATCH`**: el modal siempre manda el ticket completo, así no hay ambigüedad entre "no lo mandé" y "lo quiero vacío" (por ejemplo, quitar la patente o el producto).
- **`404` para proveedor/producto inexistente al editar** (como pide el ticket), mientras que al crear sigue siendo `400`. Por eso existe `ReferenciaNoEncontradaError`, separada de `ReglaNegocioError`.
- **Se valida todo antes de modificar la entidad**: si algo falla, el ticket queda como estaba.
- **El neto no se recibe**: lo calcula la entidad `Ticket` (`peso_bruto - peso_tara`) y el repositorio lo guarda.
- **Sin `innerHTML`**: opciones con `createElement`, errores con `textContent`, botones con `addEventListener`.

### Cómo probarlo

1. Admin: en un ticket abierto, **Editar** → cambiar patente, chofer, proveedor, producto o tara → **Guardar cambios**: la tabla muestra los datos nuevos y sigue abierto.
2. Admin: en un ticket abierto, cargar un bruto mayor a la tara → queda cerrado con su neto.
3. Admin: buscar un ticket cerrado → **Editar** → cambiar la tara → la vista previa del neto cambia; al guardar, la tabla muestra el neto recalculado.
4. Poner un bruto menor o igual a la tara → mensaje en rojo dentro del modal; no se guarda.
5. `PUT /tickets/{id}` con token de cliente → `403`.

### Pendientes conocidos

- No hay registro de auditoría: no queda guardado quién editó un ticket ni qué valores tenía antes.
- No se puede editar `fecha`, `transporte` ni `numero_ticket` (no estaban en el alcance del ticket).

---

## AGROPESO-027: Copia de seguridad total de la base y respaldo automático cada 24 hs

El administrador puede descargar un volcado completo de la base (proveedores, productos, usuarios y tickets) en `agropeso_backup_YYYY-MM-DD.sql`. Además, el servidor guarda un backup por día en disco.

### Archivos

| Archivo | Cambio |
|---|---|
| `backend/repository/backup_repository.py` | **Nuevo**: `leer_tabla(tabla)` devuelve todas las filas ordenadas por `id` |
| `backend/services/backup_service.py` | **Nuevo**: `generar_sql` (metadatos + `INSERT INTO` escapados por SQLAlchemy para MySQL) y `guardar_backup_del_dia` |
| `backend/routers/backup_router.py` | **Nuevo**: `GET /backup/descargar` (solo admin) |
| `backend/utils/backup_automatico.py` | **Nuevo**: tarea de fondo que cada hora crea el backup del día si falta |
| `backend/main.py` | `lifespan` que lanza la tarea, router de backup y `expose_headers=["Content-Disposition"]` en CORS |
| `backend/tests/test_backup.py` | **Nuevo**: 7 tests |
| `frontend/html/admin.html` | Botón **Descargar Backup DB** debajo de *Cargar cliente* |
| `frontend/js/admin.js` | `descargarBackup` y `descargarBackupManual` (descarga con `Blob` + aviso) |
| `.gitignore` | `backend/backups/` |
| `.md/documentacion_de_la_api.md`, `.md/guia_de_desarrollo.md` | Endpoint, formato, cómo restaurar y limitaciones |

### Cómo funciona

| Situación | Resultado |
|---|---|
| Admin hace clic en **Descargar Backup DB** | Descarga `agropeso_backup_<fecha del servidor>.sql` y muestra "Copia de seguridad descargada: ..." |
| Admin abre el panel | No descarga nada |
| La API arranca o pasa una hora | Si no existe `backend/backups/agropeso_backup_<hoy>.sql`, lo genera |
| Cliente / sin token llama al endpoint | `403` / `401` |

### Decisiones técnicas

- **SQL con `INSERT INTO` en lugar de JSON**: se restaura directo con `mysql`, sin escribir un script de importación. Los metadatos que pedía el ticket (`fecha_generacion` y totales) van como comentarios al principio.
- **Los valores los escapa SQLAlchemy** (`compile(dialect=mysql, literal_binds=True)`): comillas, barras invertidas, `NULL` y fechas quedan bien sin armar el SQL a mano.
- **Orden de tablas por claves foráneas** (`suppliers` → `products` → `users` → `tickets`) y `FOREIGN_KEY_CHECKS = 0` durante la carga.
- **Escritura atómica en disco**: se escribe un `.tmp` y se renombra, así nunca queda un `.sql` cortado que impida generar el del día.
- **La tarea de fondo corre la consulta en otro hilo** (`asyncio.to_thread`) para no frenar la API, y si falla lo registra en el log y sigue intentando cada hora.
- **El nombre del archivo lo decide el servidor** (header `Content-Disposition`); si el navegador no puede leerlo, usa la fecha local.
- **Sin descarga automática en el navegador**: el ticket pedía un temporizador con `localStorage` que descargara solo cada 24 hs, pero como la marca es por navegador, se descargaría en cada PC donde se abra el panel. Se dejó solo el botón; el respaldo automático diario lo hace el servidor.

### Verificación

- 132 tests pasan (7 nuevos).
- Se restauró el backup de la base local dentro de una transacción (borrar todo → ejecutar el `.sql` → comparar → `ROLLBACK`): mismas cantidades, ids, suma de neto, nombres, usuarios y hashes. La base quedó intacta.
- En el navegador: el botón descarga el archivo con el nombre del servidor y muestra el aviso; al abrir el panel no se descarga nada.

### Pendientes conocidos

- En Railway, `backend/backups/` se pierde en cada deploy: conviene activar los backups del servicio MySQL de Railway o subir los archivos a un almacenamiento externo.
- No se borran los backups viejos de `backend/backups/` (uno por día): si crece mucho, agregar una limpieza (por ejemplo, conservar los últimos 30).

---

## AGROPESO-028: Fecha editable al crear y editar tickets

El administrador puede elegir la fecha de un ticket para cargar pesadas de días anteriores. Si no la cambia, se usa la de hoy.

### Archivos

| Archivo | Cambio |
|---|---|
| `backend/services/ticket_service.py` | **Nuevo** `validar_fecha` (no se aceptan fechas posteriores a hoy), usado al registrar y al editar; `editar_ticket` acepta `fecha` |
| `backend/schemas/ticket_schema.py` | `TicketUpdate` suma `fecha` opcional (sin `fecha` se conserva la que tenía) |
| `backend/tests/test_server.py`, `backend/tests/test_endpoints.py` | 9 tests nuevos |
| `frontend/html/admin.html` | Campo **Fecha** al principio de *Nuevo ticket* y en el modal de edición |
| `frontend/js/admin.js` | `prepararCampoFecha` (hoy por defecto y como máximo), envío de `fecha` al crear y editar, validación local |

### Cómo funciona

| Situación | Resultado |
|---|---|
| Nuevo ticket sin tocar la fecha | Se guarda con la fecha de hoy |
| Nuevo ticket con una fecha anterior | Se guarda con esa fecha (por ejemplo, para cargar tickets viejos) |
| Fecha posterior a hoy | El navegador no deja enviarla; si llega a la API, `400` |
| Editar un ticket | El modal muestra su fecha y se puede cambiar |
| `PUT` sin `fecha` | Se conserva la fecha que tenía el ticket |

### Decisiones técnicas

- **El formulario siempre manda la fecha local del navegador**: antes no la mandaba y la API usaba `date.today()` del servidor. En Railway el servidor está en UTC (3 horas adelante de Argentina), así que un ticket cargado después de las 21 hs quedaba con la fecha del día siguiente. Ahora queda la fecha que ve el operador.
- **Sin fechas futuras**: una fecha futura casi siempre es un error de tipeo. Se valida en el servicio (contra la fecha del servidor, que en Argentina nunca está atrasada) y también en el navegador (atributo `max`).
- **`fecha` opcional en `TicketUpdate`**: así un `PUT` sin fecha sigue funcionando como antes.

### Cómo probarlo

1. Admin: *Nuevo ticket* → la fecha ya está en hoy → registrar → aparece en *abiertos de hoy*.
2. Cambiar la fecha a un día anterior → registrar → no aparece en *abiertos de hoy*; buscarlo con el filtro *Desde/Hasta* de ese día.
3. **Editar** un ticket → cambiar la fecha → guardar → la tabla muestra la fecha nueva.
4. El selector de fecha no deja elegir días posteriores a hoy.

---

## AGROPESO-029: Dashboard de facturación y control de pesadas facturadas

Cada pesada tiene un estado de facturación (*no facturado* por defecto). La nueva pantalla `facturas.html` (solo admin) muestra el estado de cada proveedor y permite marcar como facturadas, en lote, las pesadas de un proveedor en un rango de fechas.

### Base de datos

```sql
ALTER TABLE tickets ADD COLUMN facturado BOOLEAN NOT NULL DEFAULT FALSE;
```

Hay que ejecutarlo en la base local **y en la de Railway antes de publicar**: sin la columna, la API nueva responde `500` en todas las consultas de tickets.

### Archivos

| Archivo | Cambio |
|---|---|
| `backend/models/ticket_model.py` | `facturado` en la entidad `Ticket` (por defecto `False`) y columna `facturado` en `TicketDB` |
| `backend/repository/ticket_repository.py` | `facturado` en `_to_db`, `_to_entity` y `update_ticket`; **nuevo** `facturar_rango` (un solo `UPDATE`) |
| `backend/schemas/ticket_schema.py` | `facturado` en `TicketResponse`; **nuevos** `FacturarRangoRequest` (`extra="forbid"`, valida el orden de las fechas) y `FacturarRangoResponse` |
| `backend/services/ticket_service.py` | **Nuevo** `facturar_por_rango` (verifica el proveedor y devuelve el resumen) |
| `backend/routers/ticket_router.py` | **Nuevo** `PATCH /tickets/facturar` (solo admin) |
| `backend/tests/test_server.py`, `backend/tests/test_endpoints.py` | 12 tests nuevos |
| `frontend/html/admin.html` | Botón **Facturas** al lado de *Exportar Excel* |
| `frontend/html/facturas.html`, `frontend/js/facturas.js` | **Nuevos**: pantalla de facturación |
| `frontend/css/styles.css` | **Nuevo**: tema oscuro (`body.tema-oscuro`), por ahora solo lo usa `facturas.html` |
| `.md/documentacion_de_la_api.md`, `.md/guia_de_desarrollo.md`, `.md/arquitectura_del_sistema.md` | Endpoint, `ALTER TABLE` y la nueva pantalla |

### Cómo funciona

**Vista 1, resumen por proveedor** (al entrar, sin proveedor elegido):

| Cartel | Cuándo |
|---|---|
| Rojo: `N sin facturar` | Tiene pesadas cerradas sin facturar |
| Azul: `Todo facturado` | Todas sus pesadas cerradas están facturadas |
| Gris: `Sin pesadas` / `Sin pesadas cerradas` | No tiene pesadas, o solo tiene abiertas (no hay nada para facturar todavía) |

La columna *Pesadas* indica cuántas tiene y cuántas siguen abiertas. Escribir en el buscador filtra la lista; hacer clic en un proveedor abre su detalle.

**Vista 2, detalle del proveedor** (al hacer clic o al escribir su nombre completo): N° de ticket, fecha, patente, producto, peso neto y un cartel por pesada: azul *Facturado* o rojo *No facturado* (las abiertas además llevan un cartel gris *Abierto*). Arriba, un resumen: cantidad de pesadas, cerradas sin facturar y neto pendiente. Si hay fechas *Desde/Hasta*, se filtra por ese rango.

**Facturar**: con un proveedor elegido y las dos fechas cargadas (*Desde* ≤ *Hasta*), se habilita **Marcar como Facturado**. Pide confirmación (con la cantidad de pesadas pendientes), llama a `PATCH /tickets/facturar` y vuelve a pedir todo a la API: los carteles pasan de rojo a azul y el resumen se actualiza.

**Deshacer**: si se facturó algo por error, con el mismo proveedor y rango, **Desmarcar facturación** (también con confirmación) manda `"facturado": false` al mismo endpoint y esas pesadas vuelven a rojo. Para deshacer una sola pesada, elegir *Desde* y *Hasta* en su día.

### Decisiones técnicas

- **Solo se facturan tickets cerrados** (la "regla recomendada" del ticket): un camión que todavía está adentro no tiene peso neto. Esa pesada sigue en rojo hasta que se cierre y se facture en otro lote.
- **Un solo `UPDATE` en la base** con todas las condiciones (proveedor, rango, cerrado, no facturado). Así es atómico y repetirlo no hace nada (`actualizados: 0`).
- **`fecha` es solo fecha** (sin hora), así que el rango incluye los dos días completos sin tener que armar 00:00:00 / 23:59:59.
- **`facturado` no se puede enviar** al crear ni al editar (`extra="forbid"`): solo se cambia con la facturación por lote. Editar una pesada facturada no la desmarca.
- **Proveedor inexistente → `404`**, igual que al editar un ticket (`ReferenciaNoEncontradaError`).
- **Buscador con `<datalist>`**: se puede escribir para filtrar o elegir de la lista; si lo escrito coincide con un proveedor (sin importar mayúsculas), se abre su detalle.
- **Sin `innerHTML`**: tablas, carteles y opciones con `createElement` y `textContent`.
- **Tema oscuro propio de Facturas** en `frontend/css/styles.css`: fondo `#121413`, tarjetas `#1d201f` con borde `#2d3230` y radio de 14px, inputs oscuros con foco verde y `color-scheme: dark` (calendario oscuro). Carteles: azul *Facturado*, rojo *No facturado* y gris oscuro `#2b302e` para los neutros. Todos los estilos cuelgan de `body.tema-oscuro`, así que no afectan a `admin.html` ni a `cliente.html`, que siguen claros.

### Verificación

- 153 tests pasan (12 nuevos).
- En el navegador, con un proveedor de prueba (borrado después): el resumen marca *3 sin facturar*; con el rango de noviembre el detalle muestra 3 pesadas (la de octubre queda afuera); al confirmar, las 2 cerradas pasan a azul y la abierta sigue en rojo; el resumen pasa a *1 sin facturar* (la de octubre). Un cliente recibe `403` del endpoint y, si abre `facturas.html`, vuelve al login.

### Pendientes conocidos

- No se guarda cuándo ni quién facturó, ni un número de factura.
- El panel del cliente todavía no muestra el estado de facturación de sus pesadas.

---

## dev-fixTemaBlack: tema claro / oscuro en el panel admin

Botón flotante abajo a la derecha en `admin.html` (**🌙 Modo oscuro** / **☀️ Modo claro**) que alterna el tema. La elección se recuerda en ese navegador (`localStorage`, clave `agropeso_tema`); por defecto, claro.

| Archivo | Cambio |
|---|---|
| `frontend/js/tema.js` | **Nuevo**: aplica el tema guardado al principio del `<body>` (sin parpadeo blanco) y maneja el botón |
| `frontend/css/styles.css` | Colores oscuros para las clases de W3.CSS que usa el admin (fondos, campos, tablas, modales, avisos) y estilo del botón flotante. Todo bajo `body.tema-oscuro`: el modo claro queda igual que antes |
| `frontend/html/admin.html` | Enlaza `styles.css` y `tema.js`, y agrega el botón `#btn-tema` |

- El botón queda debajo de los modales (`z-index` 2) y la página tiene espacio abajo para que no tape la última fila de la tabla.
- `facturas.html` sigue siempre en oscuro; `cliente.html` no cambia.

---

## AGROPESO-030: Mis Facturas (cliente) y tema claro / oscuro en el panel del cliente

El cliente tiene una pantalla de solo lectura con el estado de facturación de sus pesadas, y su panel suma el botón flotante de tema claro / oscuro (como el admin), manteniendo el azul característico.

### Archivos

| Archivo | Cambio |
|---|---|
| `frontend/html/cliente_facturas.html`, `frontend/js/cliente_facturas.js` | **Nuevos**: *AgroPeso - Mis Facturas*. Filtros (estado de facturación, desde, hasta, limpiar), contador de pesadas y kilos netos cerrados, y tabla con cartel azul *Facturado* / rojo *No facturado*. Sin acciones |
| `frontend/html/cliente.html` | Botón **Facturas** (hacia `cliente_facturas.html`), botón flotante de tema y fondo blanco explícito |
| `frontend/js/tema.js` | La clase oscura se elige con `<body data-clase-oscura="...">` (por defecto `tema-oscuro`); el cliente usa `cliente-oscuro` |
| `frontend/css/styles.css` | `--verde` pasa a llamarse `--acento` y `boton-verde` a `boton-principal`; **nuevo** `acento-azul` (tema oscuro con azul) y `cliente-oscuro` (panel del cliente en oscuro) |
| `frontend/html/facturas.html` | `boton-verde` → `boton-principal` (se ve igual) |

### Decisiones técnicas

- **Mis Facturas siempre en oscuro**, como *Facturas* del admin, con acento azul (`tema-oscuro acento-azul`).
- **`cliente-oscuro` en vez de `tema-oscuro` en `cliente.html`**: el panel del cliente usa `.barra-superior` y `.tarjeta` con otro diseño (barra tipo píldora, tarjetas con degradado azul) y las reglas de `tema-oscuro` los pisaban. `cliente-oscuro` solo oscurece los grises (`--gris-panel`) y bordes, y deja el azul.
- **La preferencia de tema es una sola por navegador** (`agropeso_tema`): si se elige oscuro en el panel del cliente, el del admin en ese mismo navegador también abre en oscuro.
- **Fondo blanco explícito en `cliente.html`**: sin él, un navegador configurado en modo oscuro pintaba el fondo negro aun en tema claro.
- **Sin cambios en la API**: `GET /tickets/` ya devuelve solo los tickets del proveedor del cliente, con `facturado`.
- La columna *Fecha* muestra solo la fecha: el ticket no guarda la hora.

---

## AGROPESO-031: Facturas completas por proveedor y período

El administrador registra facturas reales (número, fecha, total, estado y método de pago) que agrupan las pesadas cerradas y sin facturar de un proveedor en un período. Reemplaza el marcado por rango de AGROPESO-029.

### Base de datos (local y Railway, antes de publicar)

```sql
CREATE TABLE facturas (
  id INT AUTO_INCREMENT PRIMARY KEY,
  numero_factura VARCHAR(50) NOT NULL UNIQUE,
  supplier_id INT NOT NULL,
  fecha_factura DATE NOT NULL,
  fecha_desde DATE NOT NULL,
  fecha_hasta DATE NOT NULL,
  total DECIMAL(12,2) NOT NULL,
  pagado BOOLEAN NOT NULL DEFAULT FALSE,
  metodo_pago VARCHAR(50) NULL,
  CONSTRAINT fk_facturas_supplier FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
);

ALTER TABLE tickets
  ADD COLUMN factura_id INT NULL,
  ADD CONSTRAINT fk_tickets_factura FOREIGN KEY (factura_id) REFERENCES facturas(id);
```

### Archivos

| Archivo | Cambio |
|---|---|
| `backend/models/factura_model.py` | **Nuevo**: entidad `Factura` y modelo `FacturaDB` |
| `backend/repository/factura_repository.py` | **Nuevo**: crear (con sus pesadas, en una transacción), listar con cantidad de pesadas, registrar pago, anular |
| `backend/services/factura_service.py` | **Nuevo**: proveedor existente (`404`), número único (`409`), sin pesadas para facturar (`400`) |
| `backend/schemas/factura_schema.py` | **Nuevos** `FacturaCreate`, `FacturaPagoUpdate`, `FacturaResponse` |
| `backend/routers/factura_router.py` | **Nuevo**: `POST`, `GET`, `PATCH /{id}/pago`, `DELETE /{id}` en `/facturas/` (solo admin) |
| `backend/models/ticket_model.py`, `repository/ticket_repository.py`, `schemas/ticket_schema.py` | `factura_id` en el ticket |
| `backend/services/backup_service.py` | El backup incluye la tabla `facturas` (antes que `tickets`, por la clave foránea) |
| `backend/tests/test_facturas.py` | **Nuevo**: 11 tests |
| `frontend/html/facturas.html`, `frontend/js/facturas.js` | Generar factura, registrar pago, anular, historial general y por proveedor |
| `frontend/css/styles.css` | Carteles verde *Pagada* / amarillo *Pendiente*, botones chicos y filas del formulario |

**Se quitó** `PATCH /tickets/facturar` (y sus tests y los botones *Marcar como Facturado* / *Desmarcar facturación*): permitía marcar pesadas como facturadas sin factura y desmarcar pesadas de una factura.

### Cómo funciona

- **Generar Factura**: con proveedor y período elegidos, se habilita si hay al menos una pesada cerrada sin facturar. El modal muestra proveedor, período, cantidad de pesadas y kilos netos, y pide N° de factura, fecha (hoy por defecto), total, estado (*Pendiente* / *Pagada*) y método (solo si está pagada). Los errores de la API (`400`, `404`, `409`, `422`) se ven dentro del modal.
- **Vista general**: *Estado por proveedor* y *Últimas facturas emitidas* (N° Factura, Fecha, Proveedor, Período, Pesadas, Total, Pago, Método y acciones).
- **Vista de un proveedor**: sus pesadas con el N° de factura de cada una, y el historial de sus facturas.
- **Registrar pago** (facturas pendientes): elige el método y la factura pasa a verde *Pagada*.
- **Anular**: con confirmación, borra la factura y sus pesadas vuelven a *No facturado* (reemplaza al *Desmarcar facturación* de AGROPESO-029).

### Decisiones técnicas

- **Una sola transacción** al crear: se inserta la factura (`flush` para tener el `id`), se asignan las pesadas con un `UPDATE`, y si no había ninguna se hace `rollback` y el servicio responde `400`.
- **`total` como `Numeric(12, 2)`** en la base y `float` en la API (con `asdecimal=False`), para que el JSON tenga un número y no un texto.
- **Pendiente no guarda método**: si llega `metodo_pago` con `pagado: false`, se descarta.
- **`cantidad_tickets` se calcula** con un `COUNT` de las pesadas de cada factura, no es una columna.
- Las pesadas que se marcaron como facturadas con el endpoint viejo (sin factura) siguen como *Facturado* sin número.

### Verificación

- 155 tests pasan (11 nuevos de facturas; se quitaron los 11 del endpoint viejo).
- En el navegador, con un proveedor de prueba (borrado después): factura pendiente con 2 pesadas (la abierta quedó afuera), error inline sin total, pago con E-Cheq, y anulación que devolvió las pesadas a *No facturado*.

---

## AGROPESO-032: Revisión general de seguridad

Revisión de toda la aplicación (API, frontend y configuración). Ya estaban bien: contraseñas con bcrypt, JWT firmado con algoritmo fijo y vencimiento, `exigir_admin` en todas las escrituras, cada cliente ve solo los datos de su proveedor (404 para lo ajeno), validación con `extra="forbid"`, consultas parametrizadas de SQLAlchemy (sin inyección SQL), sin `innerHTML` ni scripts en línea en el frontend, protección contra fórmulas en el CSV, `.env` y backups fuera del repositorio y sin secretos en el historial de git.

### Cambios

| Problema | Riesgo | Arreglo |
|---|---|---|
| El login no limitaba los intentos | Adivinar contraseñas probando miles | Después de 5 fallos de un usuario en 15 minutos responde `429` con `Retry-After` (`routers/auth_router.py`) |
| Con un usuario inexistente el login respondía más rápido | Averiguar qué usuarios existen midiendo el tiempo | Se verifica igual contra un hash de relleno (`services/auth_service.py`) |
| Contraseñas de cualquier largo en el login | Hacer trabajar a bcrypt con textos enormes | Más de 128 caracteres se rechaza sin hashear |
| `echo=True` en la base | Cada consulta, con sus datos (hashes incluidos), terminaba en los logs de Railway | Apagado; se prende con `DB_ECHO=true` (`config/database.py`) |
| `/docs` y `/openapi.json` públicos en producción | Mapa completo de la API para cualquiera | Ocultos en Railway salvo `DOCS_HABILITADOS=true` (`main.py`) |
| CORS con `allow_credentials=True` y cualquier método o header | Más permisos de los necesarios | Sin credenciales (el token va en `Authorization`), solo los métodos y headers que se usan |
| Respuestas sin cabeceras de seguridad | La API se podía mostrar en un `iframe` ajeno, el navegador podía guardar datos privados en caché | `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, `Cache-Control: no-store` y, en Railway, `Strict-Transport-Security` |
| Frontend sin política de contenido | Si alguien lograra inyectar código, podía cargar scripts de afuera o mandar el token a otro sitio | `Content-Security-Policy` en todas las páginas: scripts solo propios y conexiones solo a la API |
| Contraseñas de clientes desde 6 caracteres, y `crear_admin.py` aceptaba cualquiera | Contraseñas fáciles de adivinar | Mínimo 8 caracteres y distinta del usuario, en la API, el formulario y `crear_admin.py` (que además pide repetirla) |
| Pesos y número de ticket sin tope | Un número enorme rompía con `500` en la base | Tope de un `INT` de MySQL (`422`) |

### Recomendaciones (fuera del código)

- **Cambiar la contraseña del admin** de producción por una larga, si es corta o se usó en otro lado.
- Revisar que `SECRET_KEY` en Railway tenga 32 caracteres o más (si no, la API lo avisa en el log). Cambiarla cierra todas las sesiones abiertas.
- Pasar al plan pago de Railway antes de que venza la prueba y activar los backups del volumen.

### Pendientes conocidos

- El límite de intentos vive en memoria: se reinicia al redesplegar y no se comparte si hubiera varias réplicas.
- Alguien puede bloquear el login de un usuario 15 minutos equivocándose a propósito 5 veces con su nombre (es el costo de frenar la fuerza bruta por usuario).
- El token se guarda en `localStorage`: la CSP y la ausencia de `innerHTML` lo protegen, pero no hay forma de cerrar una sesión robada antes de que venza (60 minutos).
- No hay cambio de contraseña ni baja de usuarios desde la app.

### Verificación

- 166 tests pasan (11 nuevos en `tests/test_seguridad.py`: bloqueo y desbloqueo del login, hash de relleno, cabeceras, CORS, contraseñas y topes).
- En el navegador: login, panel admin, Facturas, panel cliente y Mis Facturas cargan sin errores de CSP; un `fetch` a otro sitio y un script externo quedan bloqueados.

