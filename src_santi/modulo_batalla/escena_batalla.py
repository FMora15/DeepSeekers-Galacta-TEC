#escena_batalla.py
import pygame
from hud_gestion import HUDManager  # Importa desde tu archivo

class EscenaBatalla:
    """Gestiona la escena principal de batalla del juego"""
    
    def __init__(self, pantalla, datos_jugadores):
        self.pantalla = pantalla
        self.datos_jugadores = datos_jugadores
        self.hud = HUDManager(pantalla, datos_jugadores)
        self.fondo = None
        self.musica_fondo = None
        self.musica_activa = True
        self.mensaje_inicio = None
        
    def preparar_ambiente(self):
        """Prepara el ambiente de batalla - US 9"""
        print("Iniciando partida...")
        self.hud.setup_hud()
        self._cargar_fondo()
        self._cargar_musica()
        self._mostrar_mensaje_inicio()
        
    def _cargar_fondo(self):
        """Carga el fondo espacial"""
        # Por ahora un fondo simple - luego cargarás imagen
        self.fondo = pygame.Surface(self.pantalla.get_size())
        self.fondo.fill((10, 5, 30))  # Azul oscuro espacial
        
        # Agregar algunas "estrellas"
        for _ in range(50):
            x = pygame.time.get_ticks() % self.pantalla.get_width()
            y = pygame.time.get_ticks() % self.pantalla.get_height()
            pygame.draw.circle(self.fondo, (255, 255, 255), (x, y), 1)
        
    def _cargar_musica(self):
        """Configura la música de fondo - US 10"""
        # Placeholder - luego cargarás archivo MP3 real
        print("Música de fondo configurada")
        
    def _mostrar_mensaje_inicio(self):
        """Muestra quién inicia la partida"""
        primer_jugador = self.datos_jugadores[0].get('alias', 'Jugador 1')
        self.mensaje_inicio = f"¡{primer_jugador} inicia la partida!"
        print(f"{self.mensaje_inicio}")
        
    def alternar_musica(self):
        """Activa/desactiva la música - US 10"""
        self.musica_activa = not self.musica_activa
        estado = "activada" if self.musica_activa else "desactivada"
        print(f"Música {estado}")
        
    def ajustar_volumen(self, volumen):
        """Ajusta el volumen de la música"""
        # Placeholder - luego integrar con pygame.mixer
        print(f"Volumen ajustado a: {volumen}%")
        
    def actualizar(self):
        """Actualiza la escena de batalla"""
        # Dibujar fondo
        self.pantalla.blit(self.fondo, (0, 0))
        
        # Actualizar y dibujar HUD
        self.hud.draw()  # ← NOMBRE COMPATIBLE
        
        # Mostrar mensaje inicial temporal
        if hasattr(self, 'mensaje_inicio') and self.mensaje_inicio:
            fuente = pygame.font.Font(None, 36)
            texto = fuente.render(self.mensaje_inicio, True, (255, 255, 0))
            self.pantalla.blit(texto, (100, 200))
            
    def manejar_eventos(self, eventos):
        """Maneja eventos del juego"""
        for evento in eventos:
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_m:  # Tecla M para música
                    self.alternar_musica()
                if evento.key == pygame.K_v:  # Tecla V para volumen
                    self.ajustar_volumen(50)
                if evento.key == pygame.K_1:  # Tecla 1 - prueba jugador 1
                    self.hud.update_player_info(0, 150, 2)  # ← NOMBRE COMPATIBLE
                if evento.key == pygame.K_2:  # Tecla 2 - prueba jugador 2
                    self.hud.update_player_info(1, 75, 3)   # ← NOMBRE COMPATIBLE

if __name__ == "__main__":
    print("Módulo EscenaBatalla cargado correctamente")