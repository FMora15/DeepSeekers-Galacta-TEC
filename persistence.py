import json
import os
from pathlib import Path
from typing import Optional
from player import Player
from validators import UniquenessValidator

class PlayerRepository:
    """Manejo de jugadores confirmados y pendientes"""

    def __init__(self, file_path="data/players.json"):
        current_dir = Path(__file__).parent
        
        # Rutas absolutas a los archivos de datos
        self._file_path = current_dir / file_path 
        self.PENDING_FILE = current_dir / "data/pending_players.json"
        
        self._players = {}
        self._load_players()

    def _load_players(self):
        """Carga los jugadores desde el archivo players.json a la memoria."""
        # Importación local para evitar posibles problemas de dependencia circular
        from player import Player 
        
        if self._file_path.exists():
            with open(self._file_path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    for pdata in data.values():
                        player = Player.from_dict(pdata)
                        player.set_uniqueness_validator(UniquenessValidator(self.get_all_dict()))
                        self._players[player._id] = player
                except json.JSONDecodeError:
                    print("ADVERTENCIA: Archivo players.json vacío o mal formado. Inicializando sin jugadores.")
                    self._players = {}


    def _save_players(self):
        """Guarda los jugadores en memoria en el archivo players.json en disco."""
        # Asegura que el directorio 'data' exista 
        self._file_path.parent.mkdir(exist_ok=True, parents=True)
        
        # Escribe al archivo
        with open(self._file_path, "w", encoding="utf-8") as f:
            json.dump({p._id: p.to_dict() for p in self._players.values()}, f, indent=2, ensure_ascii=False)
        
        #DEBUG: Mostrar lo que se guardó
        print(f"GUARDADO en {self._file_path}:")
        print(json.dumps({p._id: p.to_dict() for p in self._players.values()}, indent=2, ensure_ascii=False))


    def get_all_dict(self):
        """Retorna un diccionario de todos los jugadores (serializados a dict)."""
        return {p._id: p.to_dict() for p in self._players.values()}

    def add_player(self, player: Player):
        """Añade un jugador confirmado y lo guarda en disco. Valida unicidad."""
        # Configura el validador con la lista actual de jugadores
        player.set_uniqueness_validator(UniquenessValidator(self.get_all_dict()))
        
        if not player._uniqueness_validator.is_alias_unique(player.alias):
            raise ValueError("Alias ya en uso")
        if not player._uniqueness_validator.is_email_unique(player.email):
            raise ValueError("Email ya registrado")
            
        self._players[player._id] = player
        self._save_players()

    def get_player_by_alias(self, alias) -> Optional[Player]:
        """Busca un jugador confirmado por alias."""
        for p in self._players.values():
            if p.alias == alias:
                return p
        return None

    def get_player_by_email(self, email) -> Optional[Player]:
        """Busca un jugador confirmado por email."""
        for p in self._players.values():
            if p.email == email:
                return p
        return None
    
    def get_player_by_id(self, player_id) -> Optional[Player]:
        """Busca un jugador por ID."""
        return self._players.get(player_id)
    
    # ---------------------------- PENDIENTES ------------------------------
    def add_pending_player(self, jugador_data: dict):
        """Añade un jugador a la lista de pendientes (aún no confirmado)."""
        # Valida unicidad contra jugadores CONFIRMADOS
        self.validate_alias_email(jugador_data["alias"], jugador_data["email"])
        
        # Asegura que la carpeta 'data' exista
        Path(self.PENDING_FILE).parent.mkdir(exist_ok=True, parents=True)
        
        pendientes = []
        if self.PENDING_FILE.exists(): 
            with open(self.PENDING_FILE, "r", encoding="utf-8") as f:
                try:
                    pendientes = json.load(f)
                except json.JSONDecodeError:
                    pass # Archivo vacío o mal formado

        pendientes.append(jugador_data)
        
        # apertura y escritura del archivo
        with open(self.PENDING_FILE, "w", encoding="utf-8") as f: 
            json.dump(pendientes, f, indent=2, ensure_ascii=False)

    def get_pending_player_by_token(self, token: str) -> Optional[dict]:
        """Busca un jugador pendiente por token de confirmación."""
        if self.PENDING_FILE.exists():
            with open(self.PENDING_FILE, "r", encoding="utf-8") as f:
                try:
                    for j in json.load(f):
                        if j.get("token") == token: 
                            return j
                except json.JSONDecodeError:
                    return None 
        return None

    def confirm_pending_player(self, jugador_data: dict):
        """Confirma un jugador pendiente, lo añade a la lista de jugadores y lo quita de pendientes."""
        # Quitar de pendientes
        pendientes = []
        if self.PENDING_FILE.exists():
            with open(self.PENDING_FILE, "r", encoding="utf-8") as f:
                try:
                    # Filtra y mantiene solo los que NO coinciden con el token
                    pendientes = [j for j in json.load(f) if j.get("token") != jugador_data["token"]]
                except json.JSONDecodeError:
                    pass 
            
            # Re-escribe el archivo de pendientes sin el jugador confirmado
            with open(self.PENDING_FILE, "w", encoding="utf-8") as f:
                json.dump(pendientes, f, indent=2, ensure_ascii=False)
            
        # Crear Player confirmado
        from player import Player # Importación local
        
        # Si no existe la contraseña en los datos de pendiente, usa una temporal
        password = jugador_data.get("password") or "Temp123!" 
        
        nuevo = Player(
            alias=jugador_data["alias"],
            full_name=jugador_data["full_name"],
            email=jugador_data["email"],
            password=password,
            profile_picture=jugador_data.get("profile_picture", ""),
            spaceship_image=jugador_data.get("spaceship_image", ""),
            favorite_music=jugador_data.get("favorite_music", [])
        )
        self.add_player(nuevo)

    def validate_alias_email(self, alias: str, email: str):
        """Valida que el alias y el email no estén ya en uso por jugadores confirmados."""
        if self.get_player_by_alias(alias):
            raise ValueError(f"Alias '{alias}' ya en uso")
        if self.get_player_by_email(email):
            raise ValueError(f"Email '{email}' ya registrado")
    
    def update_password(self, email, new_password):
        """Busca un jugador por email, actualiza su contraseña y guarda en disco."""
        player = self.get_player_by_email(email)
        if player:
            player.set_password(new_password)
            self._save_players()
            return True
        return False
    
    def update_player_info(self, player: Player):
        """Actualiza la información de un jugador existente y lo guarda en disco."""
        if player._id in self._players:
            # Actualiza la referencia en la memoria (diccionario _players)
            self._players[player._id] = player 
            # Llama al método que escribe al disco
            self._save_players() 
            return True
        return False
    
    # ---------------------- MÉTODO DE RECARGA (para login) ----------------------
    def reload_players(self):
        """Fuerza la recarga de jugadores desde el archivo players.json."""
        self._players = {} 
        self._load_players()