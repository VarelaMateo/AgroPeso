import asyncio
import logging
import os
from pathlib import Path

from config.database import SessionLocal
from repository.backup_repository import BackupRepository
from services.backup_service import BackupService

logger = logging.getLogger("agropeso.backup")

CARPETA_BACKUPS = Path(os.getenv("BACKUP_DIR", Path(__file__).resolve().parent.parent / "backups"))
INTERVALO_SEGUNDOS = 3600  # se revisa cada 1 hora


def respaldar_si_falta() -> None:
    """Genera backups/agropeso_backup_<hoy>.sql si todavía no existe."""
    db = SessionLocal()
    try:
        creado = BackupService(BackupRepository(db)).guardar_backup_del_dia(CARPETA_BACKUPS)
        if creado:
            logger.info("Backup diario guardado en %s", creado)
    finally:
        db.close()


async def respaldo_diario() -> None:
    """Tarea de fondo: cada hora verifica que exista el backup del día."""
    while True:
        try:
            # La base es sincrónica: se corre en otro hilo para no bloquear la API
            await asyncio.to_thread(respaldar_si_falta)
        except Exception:
            logger.exception("No se pudo generar el backup automático")
        await asyncio.sleep(INTERVALO_SEGUNDOS)
