# AgroPeso
Es una plataforma web para la gestión de tickets de pesadas de la bascula publica. 


---

## 📁 Estructura del Proyecto

```text
AgroPeso/
├── .env                       # credenciales (nuevo, lo creás vos)
├── .gitignore
├── requirements.txt
├── env/                       # entorno virtual (no se toca a mano)
└── backend/
    ├── config/
    │   ├── __init__.py
    │   └── database.py        # engine, SessionLocal, Base
    ├── models/
    │   ├── __init__.py
    │   ├── supplier.py        # class Supplier
    │   ├── product.py         # class Product
    │   └── pesada.py          # class Pesada
    ├── repository/
    │   └── pesada_repository.py
    ├── services/
    │   └── pesada_service.py
    ├── controllers/           # reciben la petición y llaman al servicio
    ├── routers/               # definen las rutas (/pesadas, etc.)
    ├── middleware/            # JWT, logs
    └── utils/                 # funciones auxiliares (hash de contraseñas, etc.)
```

---

## Historial de tickets

### AGROPESO-001: Configuración de la conexión a MySQL

Se configuró la conexión a la base de datos MySQL usando SQLAlchemy.

- `backend/config/database.py` exporta el `engine`, `SessionLocal` (fábrica de sesiones) y `Base` (clase declarativa de la que heredan los modelos).
- Las credenciales (`DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`) no están escritas en el código: se leen desde un archivo `.env` con `python-dotenv`.
- El archivo `.env` está excluido del repositorio mediante `.gitignore`.
- Se usa el driver `PyMySQL` (`mysql+pymysql://`).

### AGROPESO-002: Entidad pura `Ticket` y modelo `TicketDB`

Se separó el concepto de ticket de pesaje en dos clases, dentro de `backend/models/ticket_model.py`:

- `Ticket`: entidad pura de dominio, implementada con `@dataclass`. No conoce SQLAlchemy ni MySQL. Contiene fecha, chofer, patente, peso de tara, peso bruto, proveedor, producto (opcional), transporte y número de ticket (opcional). El peso neto es una propiedad calculada (`peso_bruto - peso_tara`).
- `TicketDB`: modelo de SQLAlchemy asociado a la tabla `tickets`, con claves foráneas hacia `suppliers` y `products`. El número de ticket es único y admite valores nulos.

Se eliminó el modelo provisorio `Pesada`, que fue reemplazado por `TicketDB`. Las tablas `suppliers`, `products` y `tickets` se crean con el script `create_table.py`.

### AGROPESO-003: Repositorio de tickets (capa de acceso a datos)

Se implementó el patrón Repository en `backend/repository/ticket_repository.py`.

- `TicketRepository` recibe la sesión de SQLAlchemy por constructor.
- `create_ticket(ticket)`: recibe una entidad `Ticket`, la convierte a `TicketDB`, la guarda y devuelve un `Ticket` con el `id` asignado por la base.
- `get_ticket_by_id(ticket_id)`: devuelve un `Ticket` o `None` si no existe.
- Las conversiones entre entidad y modelo (`_to_db` y `_to_entity`) están encapsuladas en el repositorio, por lo que las capas superiores nunca manejan objetos de SQLAlchemy.
- Se corrigieron las relaciones de `Supplier` y `Product` para que apunten a `TicketDB` mediante el atributo `tickets`.

## Entorno de desarrollo (GitHub Codespaces)

- El servidor de base de datos es MariaDB, instalado dentro del Codespace (`sudo apt install mariadb-server`).
- Al reabrir el Codespace hay que iniciar el servicio: `sudo service mariadb start`.
- Base de datos: `AgroPeso`, con un usuario dedicado configurado en el `.env`.
- Entorno virtual: `source env/bin/activate`. Dependencias en `requirements.txt`.
- Los scripts se ejecutan desde la carpeta `backend/`.
