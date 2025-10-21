from main import GameApp, LoginScreen

class LoginApp(GameApp):
    """Aplicación dedicada al inicio de sesión dentro del ecosistema Pygame."""

    def __init__(self):
        # Inicializa toda la infraestructura (repositorio, servicios, banner, etc.)
        super().__init__()
        # Fuerza que la pantalla por defecto sea el formulario de login
        self.set_screen(LoginScreen(self))


if __name__ == "__main__":
    LoginApp().run()