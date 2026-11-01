from datetime import date

from config.database import SessionLocal
from models.suppliers import Supplier
from models.ticket_model import Ticket
from repository.ticket_repository import TicketRepository

with SessionLocal() as session:
    # Necesitamos un proveedor porque supplier_id es obligatorio
    proveedor = Supplier(name="Berg")
    session.add(proveedor)
    session.commit()

    repo = TicketRepository(session)

    # 1. Crear
    nuevo = repo.create_ticket(
        Ticket(
            fecha=date.today(),
            chofer="Ivan Derio",
            patente="HKN279",
            peso_tara=15160,
            peso_bruto=48260,
            supplier_id=proveedor.id,
        )
    )
    print("Creado:", nuevo)
    assert nuevo.id is not None
    assert nuevo.peso_neto == 33100

    # 2. Leer
    leido = repo.get_ticket_by_id(nuevo.id)
    print("Leído:", leido)
    assert leido == nuevo  # los dataclass se pueden comparar

    # 3. Id inexistente
    assert repo.get_ticket_by_id(999999) is None

    print("Todo OK")