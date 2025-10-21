from persistence import PlayerRepository
from player import Player

# Cargar repositorio
repo = PlayerRepository('data/players.json')

# Obtener el jugador existente
player = repo.get_player_by_alias('Mel')
if player:
    print(f'Jugador encontrado: {player.alias} - {player.email}')
    print(f'ID: {player._id}')
else:
    print('Jugador no encontrado')

# Debug de validación por problemas con los datos