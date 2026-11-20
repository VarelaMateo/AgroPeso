from datetime import date

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from config.database import get_db
from middleware.security import exigir_admin, get_current_user
from models.user_model import UsuarioActual
from repository.backup_repository import BackupRepository
from services.backup_service import BackupService, nombre_de_backup

router = APIRouter(prefix="/backup", tags=["Backup"])


@router.get("/descargar")
def descargar_backup(db: Session = Depends(get_db), user: UsuarioActual = Depends(get_current_user)):
    exigir_admin(user)
    contenido = BackupService(BackupRepository(db)).generar_sql()
    return Response(
        content=contenido.encode("utf-8"),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{nombre_de_backup(date.today())}"'},
    )
