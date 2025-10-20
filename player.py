import uuid
import bcrypt
from typing import List, Optional
from validators import Validator, UniquenessValidator

class Player:
    """Clase que representa un jugador"""

    def __init__(self, alias: str, full_name: str, email: str, password: str,
                 profile_picture: str = "", spaceship_image: str = "",
                 favorite_music: Optional[List[str]] = None):
        self._id = str(uuid.uuid4())
        self._alias = alias
        self._full_name = full_name
        self._email = email

        Validator.validate_password_strength(password)
        self._password_hash = self._hash_password(password)
        self._profile_picture = profile_picture
        self._spaceship_image = spaceship_image
        self._favorite_music = favorite_music or []
        self._uniqueness_validator: Optional[UniquenessValidator] = None

        Validator.validate_email(self._email)

    # ================= Métodos de contraseña =================
    def _hash_password(self, password: str) -> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def verify_password(self, password: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), self._password_hash.encode("utf-8"))

    def set_password(self, new_password: str):
        """Actualiza la contraseña del jugador con hash seguro"""
        Validator.validate_password_strength(new_password)
        self._password_hash = self._hash_password(new_password)

    # ================= Validador de unicidad =================
    def set_uniqueness_validator(self, validator: UniquenessValidator):
        self._uniqueness_validator = validator

    # ================= Propiedades =================
    @property
    def alias(self):
        return self._alias

    @alias.setter
    def alias(self, value):
        Validator.validate_alias(value) # Si tienes una validación de formato
        if self._uniqueness_validator and not self._uniqueness_validator.is_alias_unique(value, self._id):
            # Si se encuentra que el nuevo alias no es único (excluyendo su propio ID), lanza un error.
            raise ValueError("Alias ya en uso") 
        self._alias = value

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, value):
        Validator.validate_email(value)
        if self._uniqueness_validator and not self._uniqueness_validator.is_email_unique(value, self._id):
            raise ValueError("Email ya registrado")
        self._email = value

    # ================= Serialización =================
    def to_dict(self):
        return {
            "id": self._id,
            "alias": self._alias,
            "full_name": self._full_name,
            "email": self._email,
            "password_hash": self._password_hash,
            "profile_picture": self._profile_picture,
            "spaceship_image": self._spaceship_image,
            "favorite_music": self._favorite_music
        }

    @classmethod
    def from_dict(cls, data: dict):
        player = cls.__new__(cls)
        player._id = data.get("id", str(uuid.uuid4()))
        player._alias = data.get("alias", "")
        player._full_name = data.get("full_name", "")
        player._email = data.get("email", "")
        player._password_hash = data.get("password_hash", "")
        player._profile_picture = data.get("profile_picture", "")
        player._spaceship_image = data.get("spaceship_image", "")
        player._favorite_music = data.get("favorite_music", [])
        player._uniqueness_validator = None
        return player