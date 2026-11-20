from models.suppliers import SupplierEntity
from repository.supplier_repository import SupplierRepository
from models.user_model import Rol

class SupplierService:
    def __init__(self, repository: SupplierRepository):
        self.repository = repository

    def obtener_todos_los_proveedores(self, user) -> list[SupplierEntity]:
        todos = self.repository.get_all_suppliers()
        if user.rol == Rol.CLIENTE:
            return [s for s in todos if s.id == user.supplier_id]
        return todos

    def crear_proveedor(self, supplier: SupplierEntity) -> SupplierEntity:
        return self.repository.create_supplier(supplier)