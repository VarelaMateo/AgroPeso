# Documentación de la API (AgroPeso)

## Endpoints

| Método | Ruta | Descripción | Respuesta |
|---|---|---|---|
| **GET** | `/tickets/` | Lista los tickets, los más recientes primero. Filtro opcional `?estado=abierto` o `?estado=cerrado` | `list[TicketResponse]` (200) |
| **POST** | `/tickets/` | Registra una nueva pesada. Si se envía sin `peso_bruto` queda abierto. | `TicketResponse` (201) |
| **PATCH** | `/tickets/{ticket_id}/cerrar`| Registra la segunda pesada y cierra el ticket. | `TicketResponse` (200) |
| **PUT** | `/tickets/{ticket_id}` | Edita un ticket abierto o cerrado (solo admin). Recalcula el neto. | `TicketResponse` (200) |

---

## Esquemas de Datos

### Campos de `TicketCreate` (JSON de entrada)

| Campo | Tipo | Obligatorio | Regla |
|---|---|---|---|
| `chofer` | texto | Sí | No vacío, máximo 200 caracteres |
| `patente` | texto | No | Máximo 11 caracteres |
| `peso_tara` | entero | Sí | Mayor a 0 |
| `peso_bruto` | entero | No | Mayor a 0 |
| `supplier_id` | entero | Sí | Mayor a 0 |
| `product_id` | entero | No | Mayor a 0 |
| `transporte` | texto | No | Por defecto `"Equipo"`, máximo 50 caracteres |
| `numero_ticket` | entero | No | Único en la base de datos |
| `fecha` | fecha | No | Por defecto, la fecha de hoy (del servidor). No puede ser posterior a hoy (`400`) |

*Nota: `TicketResponse` (lo que sale) incluye los mismos campos, más `id`, `estado` y `peso_neto` (calculado).*

### Campos de `TicketUpdate` (JSON de entrada de `PUT /tickets/{id}`)

Reemplaza todos los campos editables: hay que mandar el ticket completo, no solo lo que cambia. Rechaza campos extra (`422`), por ejemplo `estado`, `peso_neto`, `fecha` o `id`.

| Campo | Tipo | Obligatorio | Regla |
|---|---|---|---|
| `chofer` | texto | Sí | No vacío (se recortan espacios), máximo 200 caracteres |
| `patente` | texto | No | Máximo 11 caracteres |
| `peso_tara` | entero | Sí | Mayor a 0 |
| `peso_bruto` | entero | No | Mayor a 0. `null` = el ticket queda abierto (no se permite en un ticket cerrado) |
| `supplier_id` | entero | Sí | Debe existir (si no, `404`) |
| `product_id` | entero | No | Si viene, debe existir (si no, `404`) |
| `fecha` | fecha | No | `YYYY-MM-DD`. Si no se manda, se conserva la que tenía. No puede ser posterior a hoy (`400`) |

---

## Estados del Ticket

| Estado | Significado | Datos |
|---|---|---|
| `abierto` | Se registró solo la primera pesada (la tara) | `peso_bruto` y `peso_neto` vacíos (`null`) |
| `cerrado` | Se registró la segunda pesada (el peso bruto) | `peso_neto = peso_bruto - peso_tara` |

**Reglas de negocio:**
* La primera pesada es la tara. El estado lo decide el servicio; el cliente no puede enviarlo.
* Un ticket solo se puede cerrar si existe, está abierto y el peso bruto es mayor a la tara.
* Al **editar** (`PUT`): sin `peso_bruto` el ticket queda abierto; con `peso_bruto` tiene que ser mayor a la tara, el ticket queda cerrado y el neto se recalcula. Un ticket cerrado no se puede reabrir mandando `peso_bruto: null` (`400`).

---

## Códigos de Respuesta HTTP

| Código | Cuándo ocurre |
|---|---|
| **200 / 201** | La operación se realizó correctamente. |
| **400** | Violación de regla de negocio (ej: bruto no es mayor a la tara, ticket ya cerrado, fecha posterior a hoy, `supplier_id` o `product_id` inexistente). |
| **404** | No existe el ticket solicitado. Al editar un ticket, también si no existe el `supplier_id` o `product_id` enviado. |
| **409** | Ya existe un proveedor, producto o usuario con ese nombre (sin distinguir mayúsculas). |
| **422** | El JSON no cumple el formato (tipos incorrectos, valores negativos, filtro de estado inválido). |
| **500** | Error interno (ej: `numero_ticket` repetido, rechazado por MySQL). |

---
#### Autorización y Permisos en Tickets

Todos los endpoints de `/tickets` requieren enviar el token JWT en el encabezado `Authorization: Bearer <token>`.

| Endpoint | Admin | Cliente | Sin token |
|---|---|---|---|
| `POST /tickets/` | Permitido | 403 Forbidden | 401 Unauthorized |
| `PATCH /tickets/{id}/cerrar` | Permitido | 403 Forbidden | 401 Unauthorized |
| `PUT /tickets/{id}` | Permitido | 403 Forbidden | 401 Unauthorized |
| `GET /tickets/` | Todos los tickets | Solo los de su `supplier_id` | 401 Unauthorized |
| `GET /tickets/{id}` | Cualquier ticket | Solo si pertenece a su `supplier_id` (si no, 404) | 401 Unauthorized |

**Códigos de seguridad adicionales:**
- **401 Unauthorized:** No se envió token, o el token es inválido, fue alterado o está vencido.
- **403 Forbidden:** El usuario está autenticado como `cliente` e intenta realizar una operación exclusiva de `admin`.
- **404 Not Found (por visibilidad):** Si un cliente consulta por ID un ticket de otro proveedor, se devuelve 404 para no revelar que ese registro existe.
---

## Ejemplos de Solicitudes

**Abrir un ticket (`POST /tickets/`, sin `peso_bruto`):**
```json
{
  "chofer": "Ivan Derio",
  "patente": "HKN279",
  "peso_tara": 15160,
  "supplier_id": 1
}
```
*Respuesta (201): Devuelve el ticket con `"estado": "abierto"` y pesos neto/bruto en `null`.*

**Cerrar el ticket (`PATCH /tickets/1/cerrar`):**
```json
{
  "peso_bruto": 48260
}
```
*Respuesta (200): Devuelve el ticket con `"estado": "cerrado"`, `"peso_bruto": 48260` y `"peso_neto": 33100`.*

**Editar el ticket (`PUT /tickets/1`), corrigiendo la tara:**
```json
{
  "chofer": "Ivan Derio",
  "patente": "HKN279",
  "peso_tara": 16000,
  "peso_bruto": 48260,
  "supplier_id": 1,
  "product_id": null
}
```
*Respuesta (200): `"estado": "cerrado"` y `"peso_neto": 32260` (recalculado).*

---

## Proveedores

#### Endpoints

| Método | Ruta | Descripción | Respuesta |
|---|---|---|---|
| GET | `/suppliers/` | Lista los proveedores, ordenados por nombre | `list[SupplierResponse]` (200) |
| POST | `/suppliers/` | Crea un proveedor. Si el nombre ya existe (sin distinguir mayúsculas) responde 409 | `SupplierResponse` (201) |

#### Autorización y Permisos en Proveedores

| Endpoint | Admin | Cliente | Sin token |
|---|---|---|---|
| `GET /suppliers/` | ✅ | ✅ | 401 |
| `POST /suppliers/` | ✅ | 403 | 401 |

---

## Productos

#### Endpoints

| Método | Ruta | Descripción | Respuesta |
|---|---|---|---|
| GET | `/products/` | Lista los productos, ordenados por nombre | `list[ProductResponse]` (200) |
| POST | `/products/` | Crea un producto. Si el nombre ya existe (sin distinguir mayúsculas) responde 409 | `ProductResponse` (201) |

#### Autorización y Permisos en Productos

| Endpoint | Admin | Cliente | Sin token |
|---|---|---|---|
| `GET /products/` | ✅ | ✅ | 401 |
| `POST /products/` | ✅ | 403 | 401 |

#### Esquemas

| Esquema | Campo | Tipo | Regla |
|---|---|---|---|
| `ProductCreate` | `name` | texto | Obligatorio, sin espacios en los extremos, no vacío, máx 200 caracteres. (Forbid extra) |
| `ProductResponse` | `id` | entero | Asignado por la base de datos |
| `ProductResponse` | `name` | texto | Nombre del producto |

Al crear un ticket, `product_id` es opcional; si se envía y no existe, la API responde 400.

---

## Usuarios

#### Endpoints

| Método | Ruta | Descripción | Respuesta |
|---|---|---|---|
| POST | `/users/` | Da de alta un usuario con rol `cliente` asociado a un proveedor | `UserResponse` (201) |

#### Autorización y Permisos en Usuarios

| Endpoint | Admin | Cliente | Sin token |
|---|---|---|---|
| `POST /users/` | ✅ | 403 | 401 |

#### Esquema de entrada `ClienteCreate`

| Campo | Tipo | Obligatorio | Regla |
|---|---|---|---|
| `username` | texto | Sí | Sin espacios en los extremos, entre 3 y 50 caracteres. Único (sin distinguir mayúsculas) |
| `password` | texto | Sí | Mínimo 6 caracteres y máximo 72 bytes (límite de bcrypt). **No se recorta** |
| `supplier_id` | entero | Sí | Mayor a 0 y debe existir |

El rol no se envía: el servidor siempre crea un `cliente` (`extra="forbid"`, mandar `rol` da 422). La respuesta (`UserResponse`) devuelve `id`, `username`, `rol` y `supplier_id`; nunca la contraseña ni su hash.

| Código | Cuándo ocurre |
|---|---|
| 201 | Cliente creado |
| 400 | `supplier_id` inexistente |
| 409 | Ya existe un usuario con ese nombre |
| 422 | Formato inválido (usuario corto/largo, contraseña corta o de más de 72 bytes, campos extra) |

**Ejemplo (`POST /users/`):**
```json
{
  "username": "berg",
  "password": "clave123",
  "supplier_id": 1
}
```

---

## Copia de seguridad (Backup)

#### Endpoints

| Método | Ruta | Descripción | Respuesta |
|---|---|---|---|
| GET | `/backup/descargar` | Descarga un volcado completo de la base en SQL (`INSERT INTO ...`) | Archivo `.sql` (200) |

#### Autorización y Permisos en Backup

| Endpoint | Admin | Cliente | Sin token |
|---|---|---|---|
| `GET /backup/descargar` | ✅ | 403 | 401 |

#### Respuesta

* `Content-Type: application/octet-stream`
* `Content-Disposition: attachment; filename="agropeso_backup_YYYY-MM-DD.sql"` (fecha del servidor). La API lo expone por CORS (`expose_headers`) para que el panel lea el nombre.
* Contenido, en este orden para respetar las claves foráneas: `suppliers`, `products`, `users`, `tickets`, cada tabla ordenada por `id`. Empieza con comentarios de metadatos:

```sql
-- AgroPeso: copia de seguridad completa
-- fecha_generacion: 2026-11-20T19:04:08
-- total_proveedores: 6
-- total_productos: 2
-- total_usuarios: 3
-- total_tickets: 11
...
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;
INSERT INTO suppliers (id, name, cuit, phone, fecha_alta) VALUES (1, 'Berg', NULL, NULL, '2026-11-01');
...
SET FOREIGN_KEY_CHECKS = 1;
```

> ⚠️ Incluye los `password_hash` de los usuarios (hacen falta para restaurar los accesos). El archivo debe guardarse en un lugar seguro.

---

## Autenticación (Auth)

#### Endpoints

| Método | Ruta | Descripción | Entrada | Respuesta |
|---|---|---|---|---|
| POST | `/auth/login` | Inicia sesión y emite un token JWT | `application/x-www-form-urlencoded` (`username`, `password`) | `{"access_token": "...", "token_type": "bearer"}` (200) |

#### Detalles del Token y Respuestas

- **Formato de entrada:** Recibe datos de formulario (`OAuth2PasswordRequestForm`), no JSON.
- **Contenido del JWT (Payload):** Incluye `username`, `rol`, `supplier_id` y `exp` (vencimiento). El token está firmado pero no cifrado, por lo que no contiene datos sensibles.

| Código | Cuándo ocurre |
|---|---|
| 200 | Credenciales válidas; devuelve el `access_token` |
| 401 | `Usuario o contraseña incorrectos` (mismo mensaje para usuario inexistente o clave errónea por seguridad) |
| 422 | Faltan los campos `username` o `password` en el formulario |

#### Esquemas

| Esquema | Campo | Tipo | Regla |
|---|---|---|---|
| `SupplierCreate` | `name` | texto | Obligatorio, sin espacios en los extremos, no vacío, máx 200 caracteres. (Forbid extra) |
| `SupplierResponse` | `id` | entero | Asignado por la base de datos |
| `SupplierResponse` | `name` | texto | Nombre del proveedor |

**Ejemplo de creación (`POST /suppliers/`):**

Petición:
```json
{
  "name": "Berg"
}
 ```

---

## Pendientes conocidos
* Si el `numero_ticket` está repetido, MySQL rechaza la operación y la API responde 500. Falta traducirlo a un error controlado.
* Asunción: La primera pesada es la tara. Revaluar si hay camiones que llegan cargados.
* Paginación pendiente para el `GET /tickets/`.
