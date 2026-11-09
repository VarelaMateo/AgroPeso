from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from models.user_model import Rol, User, UserDB

class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_user_by_username(self, username: str) -> Optional[User]:
        stmt = select(UserDB).where(UserDB.username == username)
        user_db = self.session.scalars(stmt).first()
        
        return self._to_entity(user_db) if user_db else None

    def create_user(self, user:User) -> User:
        user_db = self._to_db(user)
        self.session.add(user_db)
        self.session.commit()
        self.session.refresh(user_db)

        return self._to_entity(user_db)

    @staticmethod
    def _to_db(user: User) -> UserDB:
        return UserDB(
            username = user.username,
            password_hash = user.password_hash,
            rol = user.rol.value,
            supplier_id = user.supplier_id
        )

    @staticmethod
    def _to_entity(user_db: UserDB) -> User:
        return User(
            id = user_db.id,
            username = user_db.username,
            password_hash = user_db.password_hash,
            rol = Rol(user_db.rol),
            supplier_id = user_db.supplier_id
        )