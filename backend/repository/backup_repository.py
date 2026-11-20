from sqlalchemy import Table, select
from sqlalchemy.orm import Session


class BackupRepository:
    def __init__(self, session: Session):
        self.session = session

    def leer_tabla(self, tabla: Table) -> list[dict]:
        """Todas las filas de una tabla, ordenadas por id, como diccionarios columna -> valor."""
        consulta = select(tabla).order_by(tabla.c.id)
        return [dict(fila) for fila in self.session.execute(consulta).mappings().all()]
