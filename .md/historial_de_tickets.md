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
