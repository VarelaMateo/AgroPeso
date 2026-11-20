from models.products import ProductEntity
from repository.product_repository import ProductRepository
from utils.exceptions import ProductoDuplicadoError


class ProductService:
    def __init__(self, repository: ProductRepository):
        self.repository = repository

    def obtener_todos_los_productos(self) -> list[ProductEntity]:
        return self.repository.get_all_products()

    def crear_producto(self, product: ProductEntity) -> ProductEntity:
        if self.repository.get_product_by_name(product.name) is not None:
            raise ProductoDuplicadoError(f"Ya existe un producto con el nombre '{product.name}'")
        return self.repository.create_product(product)
