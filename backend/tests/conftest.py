import pytest
from sqlalchemy.orm import Session

import models  # noqa: F401
from config.database import engine
from models.suppliers import Supplier


@pytest.fixture
def session():
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")

    yield session

    session.close()
    transaction.rollback()  # deshace todo lo que hizo el test
    connection.close()


@pytest.fixture
def proveedor(session):
    proveedor = Supplier(name="Proveedor de prueba")
    session.add(proveedor)
    session.commit()
    return proveedor