import json
import re
import uuid
from validators import Validator, UniquenessValidator
from player import Player
from persistence import PlayerRepository

#Contiene la lógica de negocio para interactuar con los jugadores.
# Actúa como un intermediario entre la interfaz de usuario y el almacenamiento.
class PlayerService:
    def __init__(self, repo: PlayerRepository, email_sender):
        self.repo = repo
        self.email_sender = email_sender

    #crear un nuevo jugador 
    def registrar_jugador(self, alias, full_name, email, password, profile_picture="", spaceship_image="", favorite_music=None):
        # Validaciones
        self.repo.validate_alias_email(alias, email)
        Validator.validate_email(email)
        Validator.validate_password_strength(password)

        token = str(uuid.uuid4())
        jugador_data = {
            "alias": alias,
            "full_name": full_name,
            "email": email,
            "password": password,
            "profile_picture": profile_picture,
            "spaceship_image": spaceship_image,
            "favorite_music": favorite_music or [],
            "token": token,
            "confirmed": False
        }

        # Guardar pendiente: Almacena temporalmente en pending_players
        self.repo.add_pending_player(jugador_data)

        # Enviar correo
        self.email_sender.enviar_correo_confirmacion(email, token)
        return jugador_data # Retorna datos del jugador pendiente

    def confirmar_jugador(self, token: str) -> Player:
        jugador_data = self.repo.get_pending_player_by_token(token)
        # Si no se encuentra, el token es inválido o ya se usó.
        if not jugador_data:
            raise ValueError("Token inválido o jugador no encontrado")
        # Mueve los datos del jugador pendiente a la lista de jugadores confirmados (`players.json`).
        # El repositorio se encarga de hashear la contraseña en este proceso.
        self.repo.confirm_pending_player(jugador_data)
        return self.repo.get_player_by_email(jugador_data["email"])
    
    def validar_contraseña(self,contraseña: str): 
        if len(contraseña) < 7:
            raise ValueError("La contraseña debe tener al menos 7 caracteres")
        if not re.search(r'[A-Z]', contraseña):
            raise ValueError("Debe contener al menos una mayúscula")
        if not re.search(r'[a-z]', contraseña):
            raise ValueError("Debe contener al menos una minúscula")
        if not re.search(r'[0-9]', contraseña):
            raise ValueError("Debe contener al menos un número")
        if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', contraseña):
            raise ValueError("Debe contener al menos un símbolo especial")
    
    # Método para actualizar la información de un jugador existente.
    def actualizar_jugador(self, player_id, alias, full_name, email, profile_picture, spaceship_image, favorite_music):
        print(f"DEBUG: Iniciando actualizar_jugador()")
        print(f"player_id: {player_id}")
        print(f"full_name antiguo: SERÁ ACTUALIZADO A: {full_name}")
        
        # Obtener el jugador existente por ID
        jugador_existente = self.repo.get_player_by_id(player_id)
        if not jugador_existente:
            raise ValueError("Jugador no encontrado")
        
        print(f"Jugador encontrado: {jugador_existente.alias}")
        
        # Configurar el validador de unicidad (excluyendo el ID del jugador actual)
        current_players = self.repo.get_all_dict()
        jugador_existente.set_uniqueness_validator(UniquenessValidator(current_players))
        
        # Usa los setters de alias y email 
        jugador_existente.alias = alias
        jugador_existente.email = email
        print(f"Alias y email actualizados")
        
        # Asigna el resto de valores directamente al objeto Player en memoria
        jugador_existente._full_name = full_name
        jugador_existente._profile_picture = profile_picture
        jugador_existente._spaceship_image = spaceship_image
        jugador_existente._favorite_music = [m.strip() for m in favorite_music if m.strip()]
        print(f" Otros datos actualizados: full_name={jugador_existente._full_name}")

        # Guardar cambios: Notifica al repositorio para que persista el objeto Player actualizado en el archivo JSON.
        self.repo.update_player_info(jugador_existente) 
        print(f"Cambios guardados en disco\n")
        
        #Retorna el objeto Player actualizado
        return jugador_existente