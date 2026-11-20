from models.suppliers import SupplierEntity
from repository.supplier_repository import SupplierRepository
from models.user_model import Rol
from utils.exceptions import ProveedorDuplicadoError

class SupplierService:
    def __init__(self, repository: SupplierRepository):
        self.repository = repository

    def obtener_todos_los_proveedores(self, user) -> list[SupplierEntity]:
        todos = self.repository.get_all_suppliers()
        if user.rol == Rol.CLIENTE:
            return [s for s in todos if s.id == user.supplier_id]
        return todos

    def crear_proveedor(self, supplier: SupplierEntity) -> SupplierEntity:
        if self.repository.get_supplier_by_name(supplier.name) is not None:
            raise ProveedorDuplicadoError(f"Ya existe un proveedor con el nombre '{supplier.name}'")
        return self.repository.create_supplier(supplier)
