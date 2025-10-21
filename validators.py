import re
from pathlib import Path
from typing import List

class Validator: 
    #Clase para validaciones de email, contraseña, archivos y música
    
    def validate_alias(alias:str):
        if not alias or len(alias) < 3: 
            raise ValueError("El alias debe tener al menos 3 caracteres.")
        if not re.match(r'^[a-zA-Z0-9_-]+$', alias):
            raise ValueError("El alias solo puede contener letras, números, guiones y guines bajos.")
    
    def validate_email(email: str):
        #Valida el formato de email usando una expresion regular estandar
        pattern =  r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email): 
            raise ValueError("Formato de email invalido.")
    
    def validate_password_strength(password: str): 
        if len(password) < 7: 
            raise ValueError("La contraseña debe tener al menos 7 caracteres.")
        if not re.search(r'[A-Z]', password):
            raise ValueError("La contraseña debe contener al menos una mayúscula.")
        if not re.search(r'[a-z]', password):
            raise ValueError("La contraseña debe contener al menos una minúscula.")
        if not re.search(r'[0-9]', password):
            raise ValueError("La contraseña debe contener al menos un número.")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValueError("La contraseña debe contener al menos un símbolo especial.")
    
    def validate_file_path(file_path: str): 
        #Verifica si una ruta de archivo existe en el sistema
        return Path(file_path).exists() if file_path else True
    
    def validate_mp3_files(files: List[str]): 
        for f in files: 
            if not Path(f).exists() or not f.lower().endswith(".mp3"): 
                raise ValueError(f"Archivo de música inválido: {f}")

class UniquenessValidator:
    #Verifica la unicidad del alias y email contra la de otros jugadores
    
    def __init__(self, existing_players: dict = None):
        self.existing_players = existing_players or {}
    
    #Alias unico 
    def is_alias_unique(self, alias: str, exclude_id: str = None): 
        for pid, pdata in self.existing_players.items():
            if exclude_id and pid == exclude_id:
                continue
            if pdata.get("alias") == alias:
                return False
        return True

    #Email unico 
    def is_email_unique(self, email: str, exclude_id: str = None):
        for pid, pdata in self.existing_players.items():
            if exclude_id and pid == exclude_id:
                continue
            if pdata.get("email") == email:
                return False
        return True