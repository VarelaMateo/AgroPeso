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

### Flujo completo de una petición

```text
HTTP  →  Router (esquemas)  →  TicketService (reglas)  →  TicketRepository  →  MySQL
```