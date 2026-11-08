from sqlalchemy import select
from sqlalchemy.orm import Session

from models.suppliers import Supplier, SupplierEntity

class SupplierRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all_suppliers(self) -> list[SupplierEntity]:
        consulta = select(Supplier).order_by(Supplier.name)
        Suppliers_db = self.session.scalars(consulta).all()
        return [self._to_entity(s) for s in Suppliers_db]

    def create_supplier(self, supplier: SupplierEntity) -> SupplierEntity:
        supplier_db = self._to_db(supplier)
        self.session.add(supplier_db)
        self.session.commit()
        self.session.refresh(supplier_db)

        return self._to_entity(supplier_db)

    def _to_db(self, supplier: SupplierEntity) -> Supplier:
        return Supplier(name = supplier.name)

    def _to_entity(self, supplier_db: Supplier) -> SupplierEntity:
        return SupplierEntity(id = supplier_db.id, name = supplier_db.name)