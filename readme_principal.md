# AgroPeso
Es una plataforma web para la gestión de tickets de pesadas de la báscula pública. 

Para mantener el proyecto organizado, la documentación se ha dividido en los siguientes módulos. Por favor, consulta el archivo correspondiente según lo que necesites:

* 🏗️ **[Arquitectura y Diseño](.md/arquitectura_del_sistema.md):** Estructura de carpetas, responsabilidades de las capas (N-Capas) y el flujo de datos.
* 🔌 **[Documentación de la API](.md/documentacion_de_la_api.md):** Endpoints, esquemas JSON, códigos de respuesta y estados de los tickets.
* 🛠️ **[Guía de Desarrollo](.md/guia_de_desarrollo.md):** Instrucciones para levantar el entorno, base de datos, ejecución de la API y Tests.
* 📋 **[Historial de Tickets](.md/historial_de_tickets.md):** Registro detallado de la evolución del proyecto y los tickets de desarrollo completados.

---

## 📁 Estructura General del Proyecto

```text
AgroPeso/
├── backend/
│   ├── config/          # Conexión a BD
│   ├── models/          # Capa de dominio (Entidades y BD)
│   ├── repository/      # Capa de acceso a datos
│   ├── routers/         # Capa de presentación (Endpoints)
│   ├── schemas/         # Capa de presentación (Pydantic)
│   ├── services/        # Capa de lógica de negocio
│   ├── tests/           # Pruebas (Pytest)
│   ├── utils/           # Excepciones propias
│   ├── create_table.py  # Script de BD
│   └── main.py          # Punto de entrada FastAPI
├── frontend/
│   ├── css/
│   ├── html/
│   └── js/
├── docs/                # Documentación del proyecto
├── env/                 # Entorno virtual
├── .env                 # Variables de entorno
├── .gitignore
└── requirements.txt
```
