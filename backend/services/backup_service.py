from datetime import date, datetime
from pathlib import Path
from typing import Optional

from sqlalchemy import insert
from sqlalchemy.dialects import mysql

from models.products import Product
from models.suppliers import Supplier
from models.ticket_model import TicketDB
from models.user_model import UserDB
from repository.backup_repository import BackupRepository

# Orden de las tablas: primero las que no dependen de otras (por las claves foráneas)
TABLAS = [Supplier.__table__, Product.__table__, UserDB.__table__, TicketDB.__table__]


def nombre_de_backup(dia: date) -> str:
    return f"agropeso_backup_{dia.isoformat()}.sql"


class BackupService:
    def __init__(self, repository: BackupRepository):
        self.repository = repository

    def generar_sql(self, ahora: Optional[datetime] = None) -> str:
        """Volcado completo en SQL (INSERT INTO ...) sin depender de mysqldump."""
        ahora = ahora or datetime.now()
        datos = {tabla.name: self.repository.leer_tabla(tabla) for tabla in TABLAS}
        dialecto = mysql.dialect()

        lineas = [
            "-- AgroPeso: copia de seguridad completa",
            f"-- fecha_generacion: {ahora.isoformat(timespec='seconds')}",
            f"-- total_proveedores: {len(datos['suppliers'])}",
            f"-- total_productos: {len(datos['products'])}",
            f"-- total_usuarios: {len(datos['users'])}",
            f"-- total_tickets: {len(datos['tickets'])}",
            "-- Restaurar sobre una base vacía con las tablas creadas (python create_table.py):",
            "--   mysql -u root -p AgroPeso < este_archivo.sql",
            "-- ATENCION: incluye los hashes de las contraseñas. Guardarlo en un lugar seguro.",
            "",
            "SET NAMES utf8mb4;",
            "SET FOREIGN_KEY_CHECKS = 0;",
        ]
        for tabla in TABLAS:
            lineas.append("")
            lineas.append(f"-- Tabla {tabla.name} ({len(datos[tabla.name])} filas)")
            for fila in datos[tabla.name]:
                # literal_binds: SQLAlchemy escribe los valores escapados para MySQL (comillas, NULL, fechas)
                sentencia = insert(tabla).values(**fila).compile(
                    dialect=dialecto, compile_kwargs={"literal_binds": True})
                lineas.append(f"{sentencia};")
        lineas += ["", "SET FOREIGN_KEY_CHECKS = 1;", ""]
        return "\n".join(lineas)

    def guardar_backup_del_dia(self, carpeta: Path, hoy: Optional[date] = None) -> Optional[Path]:
        """Escribe el backup de hoy en la carpeta si todavía no existe. Devuelve la ruta creada, o None."""
        archivo = carpeta / nombre_de_backup(hoy or date.today())
        if archivo.exists():
            return None
        carpeta.mkdir(parents=True, exist_ok=True)
        temporal = archivo.with_suffix(".tmp")
        temporal.write_text(self.generar_sql(), encoding="utf-8")
        temporal.replace(archivo)  # se renombra al final: nunca queda un .sql a medio escribir
        return archivo
