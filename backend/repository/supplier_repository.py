from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models.suppliers import Supplier, SupplierEntity
from utils.exceptions import ProveedorDuplicadoError

class SupplierRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all_suppliers(self) -> list[SupplierEntity]:
        consulta = select(Supplier).order_by(Supplier.name)
        Suppliers_db = self.session.scalars(consulta).all()
        return [self._to_entity(s) for s in Suppliers_db]

    def get_supplier_by_id(self, supplier_id: int) -> Optional[SupplierEntity]:
        supplier_db = self.session.get(Supplier, supplier_id)
        if supplier_db is None:
            return None
        return self._to_entity(supplier_db)

    def get_supplier_by_name(self, name: str) -> Optional[SupplierEntity]:
        # Sin distinguir mayúsculas: "Berg" y "berg" son el mismo proveedor
        consulta = select(Supplier).where(func.lower(Supplier.name) == name.lower())
        supplier_db = self.session.scalars(consulta).first()
        if supplier_db is None:
            return None
        return self._to_entity(supplier_db)

    def create_supplier(self, supplier: SupplierEntity) -> SupplierEntity:
        supplier_db = self._to_db(supplier)
        self.session.add(supplier_db)
        try:
            self.session.commit()
        except IntegrityError:
            # Otra petición creó el mismo nombre entre la validación del servicio y este insert
            self.session.rollback()
            raise ProveedorDuplicadoError(f"Ya existe un proveedor con el nombre '{supplier.name}'")
        self.session.refresh(supplier_db)

        return self._to_entity(supplier_db)

    def _to_db(self, supplier: SupplierEntity) -> Supplier:
        return Supplier(name = supplier.name)

    def _to_entity(self, supplier_db: Supplier) -> SupplierEntity:
        return SupplierEntity(id = supplier_db.id, name = supplier_db.name)
