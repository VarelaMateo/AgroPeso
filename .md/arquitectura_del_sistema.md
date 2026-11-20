# Arquitectura del Sistema

El proyecto AgroPeso sigue una **Arquitectura de N-Capas** orientada al dominio, separando claramente las responsabilidades.

## Responsabilidad de cada capa

| Capa | Carpetas | Responsabilidad |
|---|---|---|
| **Presentación** | `routers/`, `schemas/` | Recibir peticiones HTTP, validar el formato del JSON y devolver respuestas con el código correcto. |
| **Lógica de negocio** | `services/`, entidad `Ticket` en `models/` | Aplicar las reglas del sistema, sin conocer HTTP ni la base de datos. |
| **Acceso a datos** | `repository/`, modelos en `models/`, `config/` | Guardar y leer en MySQL, convirtiendo entre entidades y modelos de base de datos (Patrón Repository). |
| **Transversal** | `utils/`, `middleware/` | Excepciones, logs y seguridad, usados por todas las capas. |

Las dependencias fluyen siempre hacia adentro (hacia la base de datos):
`Router → Service → Repository → Base de datos`

---

## Las tres representaciones de un ticket

Cada capa de la arquitectura tiene su propia forma de ver un ticket, por eso no se reutiliza una sola clase para todo. Esto garantiza el desacoplamiento.

| Clase | Capa | Para qué sirve |
|---|---|---|
| `TicketDB` | Acceso a datos | Guardarse en MySQL (modelo de SQLAlchemy). |
| `Ticket` | Negocio | Reglas y lógica (entidad pura, sin dependencias externas). |
| `TicketCreate` / `TicketResponse` | Presentación | Lo que entra y sale por la API (esquemas de Pydantic). |

### Reglas de dependencia:
* La entidad `Ticket` no importa nada de SQLAlchemy ni de Pydantic.
* Los esquemas de Pydantic solo se usan en la capa de presentación (routers y controladores).
* Los modelos de SQLAlchemy solo se usan dentro del repositorio.
* La conversión entre una representación y otra la hace la capa que está en el límite: el repositorio convierte entre `Ticket` y `TicketDB`, y el router convierte entre los esquemas y `Ticket`.

### Entidades Auxiliares (Proveedores y Usuarios)

El mismo principio de separación de responsabilidades se aplica a los proveedores:

| Clase | Capa | Para qué sirve |
|---|---|---|
| `Supplier` | Acceso a datos | Modelo de SQLAlchemy para guardar/leer en MySQL |
| `SupplierEntity` | Negocio | Entidad pura de dominio, sin dependencias externas |
| `SupplierCreate` / `SupplierResponse` | Presentación | Esquemas Pydantic para validar los JSON en la API |

El `SupplierRepository` actúa como frontera: recibe `SupplierEntity` de la capa de negocio, la convierte a `Supplier` para la base de datos, y devuelve nuevamente una `SupplierEntity`.

Productos sigue el mismo patrón:

| Clase | Capa | Para qué sirve |
|---|---|---|
| `Product` | Acceso a datos | Modelo de SQLAlchemy en la tabla `products` |
| `ProductEntity` | Negocio | Entidad pura de dominio |
| `ProductCreate` / `ProductResponse` | Presentación | Esquemas Pydantic para validar los JSON en la API |

`TicketService` recibe por inyección `TicketRepository`, `SupplierRepository` y `ProductRepository`, para validar que el proveedor y el producto de un ticket existan antes de guardarlo.

Este mismo patrón exacto se utiliza para el sistema de seguridad y roles de usuario:

| Clase | Capa | Para qué sirve |
|---|---|---|
| `UserDB` | Acceso a datos | Modelo de SQLAlchemy en la tabla `users` |
| `User` | Negocio | Entidad pura de dominio (con enum de roles) |
| `UserCreate` / `UserResponse` | Presentación | Esquemas Pydantic para validar entradas |

*Nota de seguridad:* El esquema `UserResponse` omite intencionalmente el campo `password_hash` para garantizar que la contraseña encriptada nunca abandone la capa de negocio o datos hacia el cliente.

---

### Flujo completo de una petición autenticada

```text
HTTP (Bearer Token) → Middleware (get_current_user) → Router (esquemas + exigir_admin) → TicketService (reglas + filtro por UsuarioActual) → TicketRepository → MySQL
```


---

## Frontend y sesión

El frontend se separa en vistas por rol; no se ocultan botones en una misma pantalla.

| Archivo | Responsabilidad |
|---|---|
| `login.html` | Autenticación; redirige según el rol |
| `admin.html` + `admin.js` | Operativa de báscula (solo rol `admin`) |
| `auth.js` | Sesión compartida: token, lectura del payload, `fetchConToken` |

```text
login.html → POST /auth/login → token en localStorage → admin.html (guardia de rol) → fetchConToken → API
```

* La guardia del frontend (`obtenerSesion()` + rol) solo decide qué pantalla mostrar. La autorización real es del backend (`exigir_admin` y el filtrado por `UsuarioActual`).
* Ante un 401, `fetchConToken` borra el token y vuelve al login.
* Todo el DOM dinámico se construye con `createElement` y `textContent` (sin `innerHTML` con datos), y los eventos se enlazan con `addEventListener`.
