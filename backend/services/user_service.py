from models.user_model import Rol, User
from repository.supplier_repository import SupplierRepository
from repository.user_repository import UserRepository
from services.auth_service import get_password_hash
from utils.exceptions import ReglaNegocioError, UsuarioDuplicadoError, UsuarioNoEncontradoError


class UserService:
    def __init__(self, repository: UserRepository, supplier_repository: SupplierRepository):
        self.repository = repository
        self.supplier_repository = supplier_repository

    def crear_cliente(self, username: str, password: str, supplier_id: int) -> User:
        if self.repository.get_user_by_username(username) is not None:
            raise UsuarioDuplicadoError(f"Ya existe el usuario '{username}'")
        if self.supplier_repository.get_supplier_by_id(supplier_id) is None:
            raise ReglaNegocioError(f"No existe el proveedor con id {supplier_id}")

        cliente = User(
            username = username,
            password_hash = get_password_hash(password),  # nunca se guarda el texto plano
            rol = Rol.CLIENTE,
            supplier_id = supplier_id,
        )
        return self.repository.create_user(cliente)

    def modificar_cliente(self, username: str, password: str, supplier_id: int) -> User:
        """Cambia la contraseña y el proveedor de un cliente que ya existe."""
        cliente = self.repository.get_user_by_username(username)
        if cliente is None:
            raise UsuarioNoEncontradoError(f"No existe el usuario '{username}'")
        if cliente.rol != Rol.CLIENTE:
            raise ReglaNegocioError("Solo se pueden modificar usuarios con rol 'cliente'")
        if self.supplier_repository.get_supplier_by_id(supplier_id) is None:
            raise ReglaNegocioError(f"No existe el proveedor con id {supplier_id}")

        cliente.password_hash = get_password_hash(password)
        cliente.supplier_id = supplier_id
        return self.repository.update_user(cliente)

    def desactivar_cliente(self, username: str, supplier_id: int) -> None:
        """Baja lógica: el cliente deja de poder entrar. No se borra nada de la base."""
        cliente = self.repository.get_user_by_username(username)
        if cliente is None:
            raise UsuarioNoEncontradoError(f"No existe el usuario '{username}'")
        if cliente.rol != Rol.CLIENTE:
            raise ReglaNegocioError("Solo se pueden eliminar usuarios con rol 'cliente'")
        if cliente.supplier_id != supplier_id:
            raise ReglaNegocioError(f"El usuario '{username}' no pertenece a ese proveedor")

        cliente.activo = False
        self.repository.update_user(cliente)
