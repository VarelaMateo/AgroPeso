from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models.products import Product, ProductEntity
from utils.exceptions import ProductoDuplicadoError


class ProductRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all_products(self) -> list[ProductEntity]:
        consulta = select(Product).order_by(Product.name)
        return [self._to_entity(p) for p in self.session.scalars(consulta).all()]

    def get_product_by_id(self, product_id: int) -> Optional[ProductEntity]:
        product_db = self.session.get(Product, product_id)
        if product_db is None:
            return None
        return self._to_entity(product_db)

    def get_product_by_name(self, name: str) -> Optional[ProductEntity]:
        # Sin distinguir mayúsculas: "Soja" y "soja" son el mismo producto
        consulta = select(Product).where(func.lower(Product.name) == name.lower())
        product_db = self.session.scalars(consulta).first()
        if product_db is None:
            return None
        return self._to_entity(product_db)

    def create_product(self, product: ProductEntity) -> ProductEntity:
        product_db = self._to_db(product)
        self.session.add(product_db)
        try:
            self.session.commit()
        except IntegrityError:
            # Otra petición creó el mismo nombre entre la validación del servicio y este insert
            self.session.rollback()
            raise ProductoDuplicadoError(f"Ya existe un producto con el nombre '{product.name}'")
        self.session.refresh(product_db)
        return self._to_entity(product_db)

    def _to_db(self, product: ProductEntity) -> Product:
        return Product(name = product.name)

    def _to_entity(self, product_db: Product) -> ProductEntity:
        return ProductEntity(id = product_db.id, name = product_db.name)
