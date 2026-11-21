from typing import Optional

from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models.factura_model import Factura, FacturaDB
from models.ticket_model import EstadoTicket, TicketDB
from utils.exceptions import FacturaDuplicadaError


class FacturaRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_factura_by_id(self, factura_id: int) -> Optional[Factura]:
        return next(iter(self._consultar(FacturaDB.id == factura_id)), None)

    def get_factura_by_numero(self, numero_factura: str) -> Optional[Factura]:
        return next(iter(self._consultar(FacturaDB.numero_factura == numero_factura)), None)

    def get_all_facturas(self, supplier_id: Optional[int] = None) -> list[Factura]:
        return self._consultar(FacturaDB.supplier_id == supplier_id) if supplier_id is not None else self._consultar()

    def crear_factura(self, factura: Factura) -> Optional[Factura]:
        """Crea la factura y le asigna las pesadas cerradas y sin facturar del proveedor en el período,
        todo en una sola transacción. Si no había pesadas para facturar, no guarda nada y devuelve None."""
        factura_db = FacturaDB(
            numero_factura=factura.numero_factura, supplier_id=factura.supplier_id,
            fecha_factura=factura.fecha_factura, fecha_desde=factura.fecha_desde,
            fecha_hasta=factura.fecha_hasta, total=factura.total,
            pagado=factura.pagado, metodo_pago=factura.metodo_pago,
        )
        self.session.add(factura_db)
        try:
            self.session.flush()  # para tener el id antes de asignar las pesadas
        except IntegrityError:
            # Otra petición usó el mismo número entre la validación del servicio y este insert
            self.session.rollback()
            raise FacturaDuplicadaError(f"Ya existe la factura '{factura.numero_factura}'")

        asignadas = self.session.execute(
            update(TicketDB)
            .where(TicketDB.supplier_id == factura.supplier_id,
                   TicketDB.fecha >= factura.fecha_desde,
                   TicketDB.fecha <= factura.fecha_hasta,
                   TicketDB.estado == EstadoTicket.CERRADO.value,
                   TicketDB.facturado.is_(False))
            .values(facturado=True, factura_id=factura_db.id)
        ).rowcount
        if asignadas == 0:
            self.session.rollback()
            return None
        self.session.commit()
        return self.get_factura_by_id(factura_db.id)

    def actualizar_pago(self, factura_id: int, pagado: bool, metodo_pago: Optional[str]) -> Optional[Factura]:
        factura_db = self.session.get(FacturaDB, factura_id)
        if factura_db is None:
            return None
        factura_db.pagado = pagado
        factura_db.metodo_pago = metodo_pago
        self.session.commit()
        return self.get_factura_by_id(factura_id)

    def anular_factura(self, factura_id: int) -> bool:
        """Borra la factura y sus pesadas vuelven a quedar sin facturar. False si no existía."""
        if self.session.get(FacturaDB, factura_id) is None:
            return False
        self.session.execute(
            update(TicketDB).where(TicketDB.factura_id == factura_id).values(facturado=False, factura_id=None))
        self.session.execute(delete(FacturaDB).where(FacturaDB.id == factura_id))
        self.session.commit()
        return True

    def _consultar(self, *condiciones) -> list[Factura]:
        cantidad = func.count(TicketDB.id).label("cantidad")
        consulta = (
            select(FacturaDB, cantidad)
            .outerjoin(TicketDB, TicketDB.factura_id == FacturaDB.id)
            .where(*condiciones)
            .group_by(FacturaDB.id)
            .order_by(FacturaDB.fecha_factura.desc(), FacturaDB.id.desc())
        )
        return [self._to_entity(f, n) for f, n in self.session.execute(consulta).all()]

    def _to_entity(self, factura_db: FacturaDB, cantidad_tickets: int) -> Factura:
        return Factura(
            id=factura_db.id,
            numero_factura=factura_db.numero_factura,
            supplier_id=factura_db.supplier_id,
            fecha_factura=factura_db.fecha_factura,
            fecha_desde=factura_db.fecha_desde,
            fecha_hasta=factura_db.fecha_hasta,
            total=factura_db.total,
            pagado=bool(factura_db.pagado),
            metodo_pago=factura_db.metodo_pago,
            cantidad_tickets=cantidad_tickets,
        )
