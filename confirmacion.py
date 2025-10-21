from flask import Flask, request
import json
import uuid
import os
from pathlib import Path
from persistence import PlayerRepository
from player import Player

app = Flask(__name__)
repo = PlayerRepository("data/players.json")

@app.route('/confirmar')
def confirmar():
    token = request.args.get('token')
    ruta_pendientes = Path(__file__).parent / 'data/pending_players.json'

    if not token:
        return 'Token no proporcionado.', 400
    
    if not ruta_pendientes.exists():
        return 'No hay jugadores pendientes', 400

    # Cargar usuarios pendientes
    with open(str(ruta_pendientes), 'r', encoding='utf-8') as f:
        jugadores = json.load(f)
    
    jugador_encontrado = None
    nuevos_pendientes = []

    for jugador in jugadores: 
        if jugador.get('token') == token:
            jugador_encontrado = jugador
        else: 
            nuevos_pendientes.append(jugador)
    
    # Si no se encontró el token
    if not jugador_encontrado: 
        return 'Token inválido o usuario no encontrado', 404
    
    # Guardar el resto de pendientes 
    with open(str(ruta_pendientes), 'w', encoding='utf-8') as f:
        json.dump(nuevos_pendientes, f, ensure_ascii=False, indent=2)
    
    # Crear el jugador confirmado
    password = jugador_encontrado.get("password", str(uuid.uuid4()))
    nuevo_jugador = Player(
        alias=jugador_encontrado["alias"],
        full_name=jugador_encontrado["full_name"],
        email=jugador_encontrado["email"],
        password=password,
        profile_picture=jugador_encontrado.get("profile_picture", ""),
        spaceship_image=jugador_encontrado.get("spaceship_image", ""),
        favorite_music=jugador_encontrado.get("favorite_music", [])
    )

    # Guardar en players.json
    try: 
        repo.add_player(nuevo_jugador)
    except ValueError as e: 
        return f"Error al confirmar el correo: {e}", 400
    
    return f"Correo de {nuevo_jugador.email} confirmado correctamente."

if __name__ == '__main__':
    app.run(port=5000)