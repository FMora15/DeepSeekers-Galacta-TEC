# hud_manager.py
import pygame

class HUDManager:
    """Gestiona la interfaz de usuario durante el juego"""
    
    def __init__(self, screen, players_data):
        self.screen = screen
        self.players_data = players_data
        self.font_large = pygame.font.Font(None, 48)  # Para puntajes
        self.font_small = pygame.font.Font(None, 24)  # Para nombres
        self.life_icon = None  # Aquí cargarás el ícono de vidas después
        
    def setup_hud(self):
        """Configura los elementos visuales del HUD"""
        print("HUD configurado correctamente")
        # Aquí luego cargarás imágenes: self.life_icon = pygame.image.load("assets/images/life_icon.png")
        
    def update_player_info(self, player_id, score, lives):
        """Actualiza la información de un jugador en tiempo real"""
        # Buscar el jugador y actualizar sus datos
        for player in self.players_data:
            if player.get('id') == player_id:
                player['score'] = score
                player['lives'] = lives
                break
                
    def draw(self):
        """Dibuja todos los elementos del HUD en la pantalla"""
        self.screen.fill((0, 0, 0))  # Fondo negro temporal
        
        # Dibujar HUD para cada jugador
        for i, player in enumerate(self.players_data):
            self._draw_player_hud(player, i)
            
    def _draw_player_hud(self, player, position):
        """Dibuja el HUD individual de cada jugador"""
        x_position = 50 if position == 0 else self.screen.get_width() - 200
        
        # Nombre del jugador
        name_text = self.font_small.render(f"Jugador: {player.get('alias', 'Player')}", True, (255, 255, 255))
        self.screen.blit(name_text, (x_position, 20))
        
        # Puntaje
        score_text = self.font_large.render(f"Puntos: {player.get('score', 0)}", True, (255, 255, 0))
        self.screen.blit(score_text, (x_position, 50))
        
        # Vidas (por ahora solo texto)
        lives_text = self.font_small.render(f"Vidas: {player.get('lives', 3)}", True, (255, 0, 0))
        self.screen.blit(lives_text, (x_position, 100))
        
        # Aquí luego dibujarás íconos de vidas en lugar de texto

if __name__ == "__main__":
    # Prueba básica del HUD
    print("Módulo HUDManager cargado correctamente")