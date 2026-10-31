# AgroPeso
Es una plataforma web para la gestión de tickets de pesadas de la bascula publica. 


---

## ⧉ Estructura del Proyecto
## 📁 Estructura del Proyecto

```text
AgroPeso/
├── .env                       # credenciales (nuevo, lo creás vos)
├── .gitignore
├── requirements.txt
├── env/                       # entorno virtual (no se toca a mano)
└── backend/
    ├── config/
    │   ├── __init__.py
    │   └── database.py        # engine, SessionLocal, Base
    ├── models/
    │   ├── __init__.py
    │   ├── supplier.py        # class Supplier
    │   ├── product.py         # class Product
    │   └── pesada.py          # class Pesada
    ├── repository/
    │   └── pesada_repository.py
    ├── services/
    │   └── pesada_service.py
    ├── controllers/           # reciben la petición y llaman al servicio
    ├── routers/               # definen las rutas (/pesadas, etc.)
    ├── middleware/            # JWT, logs
    └── utils/                 # funciones auxiliares (hash de contraseñas, etc.)
```

---
