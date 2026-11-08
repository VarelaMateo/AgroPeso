from models.suppliers import SupplierEntity
from repository.supplier_repository import SupplierRepository

class SupplierService:
    def __init__(self, repository: SupplierRepository):
        self.repository = repository

    def obtener_todos_los_proveedores(self) -> list[SupplierEntity]:
        return self.repository.get_all_suppliers()

    def crear_proveedor(self, supplier: SupplierEntity) -> SupplierEntity:
        return self.repository.create_supplier(supplier)