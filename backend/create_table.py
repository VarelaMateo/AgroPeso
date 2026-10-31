from config.database import Base, engine
import models  # noqa: F401  (importa los modelos para que Base los conozca)

Base.metadata.create_all(engine)
print("Tablas creadas")