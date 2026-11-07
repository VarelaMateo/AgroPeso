# Historial de Desarrollo (Tickets)

Este documento registra los Sprints y tareas completadas en la evolución del proyecto.

### AGROPESO-001: Configuración de la conexión a MySQL
* Se configuró SQLAlchemy (`engine`, `SessionLocal`, `Base`).
* Implementación de variables de entorno `.env` con `python-dotenv`.
* Driver utilizado: `PyMySQL`.

### AGROPESO-002: Entidad pura `Ticket` y modelo `TicketDB`
* Creación de `Ticket` (Entidad Pura con `@dataclass`) aislada del ORM.
* Creación de `TicketDB` (Modelo SQLAlchemy).
* Se eliminó el modelo provisorio `Pesada`.

### AGROPESO-003: Repositorio de tickets (Patrón Repository)
* Implementación de `TicketRepository` aislando la capa de datos.
* Métodos implementados: `create_ticket`, `get_ticket_by_id`.
* Conversiones `_to_db` y `_to_entity` encapsuladas para proteger las capas superiores.

### AGROPESO-004: Servicio de tickets (Capa de negocio)
* Implementación de `TicketService`.
* Inyección de dependencias (`TicketRepository`).
* Reglas de negocio: el peso bruto debe ser mayor a la tara.
* Creación de excepciones propias (`ReglaNegocioError`, `TicketNoEncontradoError`).

### AGROPESO-005: Esquemas de la API (Pydantic)
* Implementación de validaciones de entrada (`TicketCreate`) y salida (`TicketResponse`).
* Separación de responsabilidades: Pydantic valida formato, el Service valida negocio.

### AGROPESO-006: Endpoints de FastAPI
* Creación de `ticket_router.py` (`APIRouter`).
* Inyección de sesión de BD mediante `Depends(get_db)`.
* Manejo de códigos HTTP basado en excepciones del servicio.

### AGROPESO-007: Punto de entrada de la aplicación
* Configuración de `main.py` (FastAPI).
* Configuración de `CORSMiddleware` inyectando orígenes desde `.env` (`CORS_ORIGINS`).

### AGROPESO-008: Interfaz de usuario HTML
* Maquetado en `frontend/html/index.html` usando `W3.CSS`.
* Validaciones nativas alineadas con los esquemas de Pydantic.

### AGROPESO-009: Conexión Frontend-Backend (JavaScript)
* Script `app.js` utilizando `Fetch API`.
* Intercepción del formulario, armado del JSON, y parseo de respuestas HTTP.
* Prevención de doble envío y manejo unificado de errores (400, 422, 500).

### AGROPESO-010: Listado y Flujo de Estados (Abiertos/Cerrados)
* Incorporación de la enumeración `EstadoTicket`.
* Endpoints para listar (`GET`) y cerrar (`PATCH`) tickets.
* Lógica modificada para admitir tickets sin `peso_bruto` en su creación inicial.