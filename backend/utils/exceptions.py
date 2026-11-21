class ReglaNegocioError(Exception):
    pass

class TicketNoEncontradoError(Exception):
    pass

class ProveedorDuplicadoError(Exception):
    pass

class ProductoDuplicadoError(Exception):
    pass

class UsuarioDuplicadoError(Exception):
    pass

class ReferenciaNoEncontradaError(Exception):
    """Al editar un ticket: el proveedor o producto indicado no existe (404)."""
    pass

class FacturaDuplicadaError(Exception):
    pass
