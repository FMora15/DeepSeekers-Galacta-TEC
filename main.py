import sys
import random
from typing import Callable, List, Optional

import pygame
import tkinter as tk
from tkinter import filedialog

from persistence import PlayerRepository
from validators import Validator
from services.player_service import PlayerService
from services.email_sender import EmailSender
from player import Player

# ================== CONFIGURACIÓN GLOBAL ==================
pygame.init()
pygame.font.init()

#Definiciones
WINDOW_WIDTH, WINDOW_HEIGHT = 1000, 700 #Ventana principal
#Paleta de colores (momentanea)
BACKGROUND_COLOR = (24, 24, 24)
PANEL_COLOR = (36, 36, 36)
TEXT_COLOR = (235, 235, 235)
ACCENT_COLOR = (59, 130, 246) # Color principal para botones
ACCENT_HOVER = (96, 165, 250) # Color al pasar el mouse sobre botones
ERROR_COLOR = (239, 68, 68)
SUCCESS_COLOR = (34, 197, 94)
BORDER_COLOR = (75, 85, 99)
#Fuentes 
TITLE_FONT = pygame.font.SysFont("arial", 40, bold=True)
FONT = pygame.font.SysFont("arial", 24)
SMALL_FONT = pygame.font.SysFont("arial", 18)


# ================== UTILIDADES DE UI ==================
class MessageBanner:
    """Muestra mensajes temporales en pantalla."""

    def __init__(self):
        self.message: str = ""
        self.color = TEXT_COLOR
        self.expire_at: int = 0

    def show(self, message: str, color=TEXT_COLOR, duration_ms: int = 3500):
        """Configura y activa el banner con un mensaje, color y duración."""
        self.message = message
        self.color = color
        self.expire_at = pygame.time.get_ticks() + duration_ms

    def draw(self, surface: pygame.Surface):
        """Dibuja el banner si está activo y comprueba si debe expirar."""
        if not self.message:
            return
        if pygame.time.get_ticks() > self.expire_at:
            self.message = ""
            return
        banner_rect = pygame.Rect(0, WINDOW_HEIGHT - 60, WINDOW_WIDTH, 60)
        pygame.draw.rect(surface, (0, 0, 0, 120), banner_rect)
        text_surface = SMALL_FONT.render(self.message, True, self.color)
        surface.blit(text_surface, (20, WINDOW_HEIGHT - 40))


class InputBox:
    """Campo de texto simple (menja entrada, activación y dibujo)."""

    def __init__(self, x: int, y: int, w: int, h: int, *, placeholder: str = "", text: str = "", password: bool = False):
        self.rect = pygame.Rect(x, y, w, h)
        self.placeholder = placeholder
        self.text = text
        self.password = password
        self.active = False
        self.color_inactive = BORDER_COLOR
        self.color_active = ACCENT_COLOR
        self.color = self.color_inactive
        self.min_width = w
        self.min_height = h
        self.padding_x = 12
        self.padding_y = 10
        self.display_text = ""
        self.rect.width = self.min_width
        self.rect.height = self.min_height
        self._render_text()

    def _display_text(self) -> str:
        """Devuelve el texto a mostrar (contraseña, texto normal o placeholder)."""
        if self.text:
            return "*" * len(self.text) if self.password else self.text
        return self.placeholder

    def _text_color(self) -> pygame.Color:
        "Devuelve el color del texto"
        if self.text:
            return TEXT_COLOR
        return pygame.Color(160, 160, 160)

    def _render_text(self):
        "Genera la superficie dle texto, aplica truncamiento y ajusta el tamaño de la caja"
        display = self._display_text()
        available_width = self.min_width - self.padding_x * 2
        if available_width <= 0:
            available_width = 10
        self.display_text = display
        if FONT.size(display)[0] > available_width:
            truncated = display
            while truncated and FONT.size(truncated + "…")[0] > available_width:
                truncated = truncated[:-1]
            self.display_text = f"{truncated}…" if truncated else "…"
        self.txt_surface = FONT.render(self.display_text, True, self._text_color())
        self.rect.width = self.min_width
        height_needed = self.txt_surface.get_height() + self.padding_y * 2
        self.rect.height = max(self.min_height, height_needed)

    def set_text(self, value: str):
        """Establece el valor del texto y lo vuelve a renderizar."""
        self.text = value
        self._render_text()

    def set_active(self, active: bool):
        """Cambia el estado de enfoque y actualiza el color del borde."""
        self.active = active
        self.color = self.color_active if self.active else self.color_inactive

    def handle_event(self, event: pygame.event.EventType) -> Optional[str]:
        """Procesa eventos de ratón y teclado para la InputBox."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Detecta clic para activar/desactivar el foco
            self.set_active(self.rect.collidepoint(event.pos))
            return None
        if event.type == pygame.KEYDOWN and self.active:
            # Comportamiento especial para teclas
            if event.key == pygame.K_RETURN:
                return "SUBMIT" # Señal para el envío del formulario
            if event.key == pygame.K_TAB:
                return "TAB" # Señal para mover el foco al siguiente campo
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1] # Elimina el último caracter
            elif event.key == pygame.K_ESCAPE:
                self.set_active(False) # Pierde el foco
            else:
                #(soporte para acentos y caracteres especiales)
                if event.unicode:
                    self.text += event.unicode
            self._render_text()
        return None

    def update(self):
        """Método de actualización (vacío, solo para consistencia con BaseScreen)."""
        pass

    def draw(self, surface: pygame.Surface):
        """Dibuja la caja de texto y el texto en la superficie."""
        pygame.draw.rect(surface, PANEL_COLOR, self.rect)
        # Posiciona el texto centrado verticalmente
        text_x = self.rect.x + self.padding_x
        text_y = self.rect.y + (self.rect.height - self.txt_surface.get_height()) // 2
        surface.blit(self.txt_surface, (text_x, text_y))
        pygame.draw.rect(surface, self.color, self.rect, 2)


class Button:
    """Botón básico con callback."""

    def __init__(self, rect: pygame.Rect, text: str, callback: Callable[[], None], *, bg_color=ACCENT_COLOR, text_color=(255, 255, 255)):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.bg_color = bg_color
        self.text_color = text_color
        self.hover = False
        self.padding_x = 20
        self.padding_y = 12
        self.text_surface = FONT.render(self.text, True, self.text_color)
        self._resize_to_text()

    def _resize_to_text(self):
        """Ajusta el ancho y alto del botón en base al texto renderizado y el padding."""
        width = self.text_surface.get_width() + self.padding_x * 2
        height = self.text_surface.get_height() + self.padding_y * 2
        self.rect.width = width
        self.rect.height = height

    def set_text(self, new_text: str):
        """Cambia el texto del botón y ajusta su tamaño si es necesario."""
        if self.text != new_text:
            self.text = new_text
            self.text_surface = FONT.render(self.text, True, self.text_color)
            self._resize_to_text()

    def handle_event(self, event: pygame.event.EventType):
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()

    def draw(self, surface: pygame.Surface):
        color = ACCENT_HOVER if self.hover else self.bg_color
        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        text_pos = self.text_surface.get_rect(center=self.rect.center)
        surface.blit(self.text_surface, text_pos)


class FileDialogHelperMixin:
    """Mixin que provee utilidades para abrir selectores de archivos y actualizar campos."""

    _file_dialog_root: Optional[tk.Tk] = None

    def _init_upload_helpers(self) -> tk.Tk:
        if FileDialogHelperMixin._file_dialog_root is None:
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            FileDialogHelperMixin._file_dialog_root = root
        FileDialogHelperMixin._file_dialog_root.update()
        return FileDialogHelperMixin._file_dialog_root

    def _create_upload_rect(self, index: int) -> pygame.Rect:
        width, height = self.upload_button_size
        input_rect = self.inputs[index].rect
        x = input_rect.right + self.upload_margin
        y = input_rect.y + (input_rect.height - height) // 2
        return pygame.Rect(x, y, width, height)

    def _open_file_dialog(self, input_index: int, *filetypes):
        """Abre un diálogo para seleccionar un solo archivo y actualiza el InputBox."""
        root = self._init_upload_helpers()
        selected = filedialog.askopenfilename(
            parent=root,
            title="Seleccionar archivo",
            filetypes=filetypes or [("Todos", "*.*")],
        )
        if selected:
            self.inputs[input_index].set_text(selected)

    def _open_file_dialog_multiple(self, input_index: int, *filetypes):
        """Abre un diálogo para seleccionar múltiples archivos y actualiza el InputBox."""
        root = self._init_upload_helpers()
        selected = filedialog.askopenfilenames(
            parent=root,
            title="Seleccionar archivos",
            filetypes=filetypes or [("Todos", "*.*")],
        )
        if selected:
            joined = ", ".join(selected)
            self.inputs[input_index].set_text(joined)


# ================== CLASES DE PANTALLA ==================
class BaseScreen:
    def __init__(self, app: "GameApp"):
        self.app = app

    def handle_event(self, event: pygame.event.EventType):
        raise NotImplementedError

    def update(self):
        pass

    def draw(self, surface: pygame.Surface):
        raise NotImplementedError


class MainMenuScreen(BaseScreen):
    def __init__(self, app: "GameApp"):
        super().__init__(app)
        button_width, button_height = 260, 60
        x = (WINDOW_WIDTH - button_width) // 2
        start_y = 260
        spacing = 80
        # Lista de botones con callbacks lambda para cambiar de pantalla
        self.buttons = [
            Button(pygame.Rect(x, start_y, button_width, button_height), "Iniciar sesión", lambda: app.set_screen(LoginScreen(app))),
            Button(pygame.Rect(x, start_y + spacing, button_width, button_height), "Registrarse", lambda: app.set_screen(RegisterScreen(app))),
            Button(pygame.Rect(x, start_y + spacing * 2, button_width, button_height), "Salir", self.exit_app),
        ]

    def exit_app(self):
        self.app.running = False

    def handle_event(self, event: pygame.event.EventType):
        for button in self.buttons:
            button.handle_event(event)

    def draw(self, surface: pygame.Surface):
        surface.fill(BACKGROUND_COLOR)
        title = TITLE_FONT.render("¡Bienvenido!", True, TEXT_COLOR)
        subtitle = SMALL_FONT.render("Menu", True, TEXT_COLOR)
        surface.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 150)))
        surface.blit(subtitle, subtitle.get_rect(center=(WINDOW_WIDTH // 2, 200)))
        for button in self.buttons:
            button.draw(surface)


class LoginScreen(BaseScreen):
    def __init__(self, app: "GameApp"):
        super().__init__(app)
        center_x = WINDOW_WIDTH // 2
        self.inputs: List[InputBox] = [
            InputBox(center_x - 180, 220, 360, 48, placeholder="Alias o correo"),
            InputBox(center_x - 180, 300, 360, 48, placeholder="Contraseña", password=True),
        ]
        for idx, box in enumerate(self.inputs):
            box.set_active(idx == 0)

        self.buttons = [
            Button(pygame.Rect(center_x - 150, 380, 160, 50), "Ingresar", self.attempt_login),
            Button(pygame.Rect(center_x + 10, 380, 200, 50), "Recuperar contraseña", self.request_password_reset),
            Button(pygame.Rect(center_x - 150, 450, 160, 45), "Regresar", lambda: app.set_screen(MainMenuScreen(app))),
        ]

        self.recovery_modal: Optional[RecoveryModal] = None
        self.recovery_code_sent = False

    def _focus_next(self, current: InputBox):
        if current not in self.inputs:
            return
        idx = self.inputs.index(current)
        next_idx = (idx + 1) % len(self.inputs)
        # Desactiva todos y activa el siguiente
        for box in self.inputs:
            box.set_active(False)
        self.inputs[next_idx].set_active(True)

    def attempt_login(self):
        alias_email = self.inputs[0].text.strip()
        password = self.inputs[1].text.strip()

        if not alias_email or not password:
            self.app.banner.show("Debes ingresar alias/email y contraseña.", ERROR_COLOR)
            return

        self.app.repo.reload_players()
        # Busca al jugador por alias O por email
        player = self.app.repo.get_player_by_alias(alias_email) or self.app.repo.get_player_by_email(alias_email)
        if not player:
            self.app.banner.show("Usuario no registrado.", ERROR_COLOR)
            return
        # Verifica la contraseña (asume uso de hashing)
        if not player.verify_password(password):
            self.app.banner.show("Contraseña incorrecta.", ERROR_COLOR)
            return
        # Login exitoso: Muestra banner y cambia a la pantalla de juego
        self.app.banner.show(f"¡Hola {player.alias}!", SUCCESS_COLOR)
        self.app.set_screen(GameScreen(self.app, player))

    def request_password_reset(self):
        """Inicializa el modal de recuperación de contraseña."""
        # Desactiva los campos de login para enfocarse en el modal
        for box in self.inputs:
            box.set_active(False)
        self.recovery_modal = RecoveryModal(self.app, self)

    def handle_event(self, event: pygame.event.EventType):
        """Maneja eventos, priorizando el modal si está activo."""
        if self.recovery_modal:
            self.recovery_modal.handle_event(event)
            return
        # Manejo de eventos de los InputBox
        for box in self.inputs:
            result = box.handle_event(event)
            if result == "TAB":
                self._focus_next(box) #logica de foco
            elif result == "SUBMIT":
                self.attempt_login() #envio de formulario
        for button in self.buttons:
            button.handle_event(event)

    def update(self):
        """Actualiza el modal o los InputBox (si el modal no está activo)."""
        if self.recovery_modal:
            self.recovery_modal.update()
        else:
            for box in self.inputs:
                box.update()

    def draw(self, surface: pygame.Surface):
        surface.fill(BACKGROUND_COLOR)
        title = TITLE_FONT.render("Iniciar sesión", True, TEXT_COLOR)
        surface.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 140)))

        labels = ["Alias o correo", "Contraseña"]
        for idx, label in enumerate(labels):
            text = SMALL_FONT.render(label, True, TEXT_COLOR)
            surface.blit(text, (self.inputs[idx].rect.x, self.inputs[idx].rect.y - 28))

        for box in self.inputs:
            box.draw(surface)
        for button in self.buttons:
            button.draw(surface)

        if self.recovery_modal:
            self.recovery_modal.draw(surface)


class RecoveryModal:
    """Modal de múltiples etapas para recuperar la contraseña (EMAIL -> CODE -> PASSWORD)."""
    def __init__(self, app: "GameApp", login_screen: "LoginScreen"):
        self.app = app
        self.login_screen = login_screen
        self.stage = "EMAIL"  # EMAIL -> CODE -> PASSWORD
        self.email_input = InputBox((WINDOW_WIDTH // 2) - 200, 250, 400, 48, placeholder="Correo registrado")
        self.code_input = InputBox((WINDOW_WIDTH // 2) - 150, 250, 300, 48, placeholder="Código de recuperación")
        self.password_input = InputBox((WINDOW_WIDTH // 2) - 200, 250, 400, 48, placeholder="Nueva contraseña", password=True)
        self.confirm_password_input = InputBox((WINDOW_WIDTH // 2) - 200, 320, 400, 48, placeholder="Confirmar contraseña", password=True)
        self.inputs = [
            self.email_input,
            self.code_input,
            self.password_input,
            self.confirm_password_input,
        ]
        self.visible = True
        self.sent_code: Optional[str] = None
        self.code_expires_at: Optional[int] = None

        self.email_input.set_active(True)

        self.buttons = [
            Button(pygame.Rect((WINDOW_WIDTH // 2) - 150, 420, 160, 48), "Enviar código", self.send_code),
            Button(pygame.Rect((WINDOW_WIDTH // 2) + 10, 420, 160, 48), "Cancelar", self.close),
        ]

    def close(self):
        """Cierra el modal y restablece el estado."""
        self._reset_state()
        self.visible = False
        self.login_screen.recovery_modal = None
        self.login_screen.recovery_code_sent = False

    def _generate_code(self) -> str:
        """Genera un código aleatorio de 6 dígitos."""
        return f"{random.randint(0, 999999):06d}"

    def _reset_state(self):
        self.stage = "EMAIL"
        self.sent_code = None
        self.code_expires_at = None
        self.email_input.text = ""
        self.code_input.text = ""
        self.password_input.text = ""
        self.confirm_password_input.text = ""
        for box in self.inputs:
            box._render_text()
            box.set_active(False)
        self.email_input.set_active(True)
        # Restablece el botón de acción a "Enviar código"
        self.buttons[0] = Button(pygame.Rect((WINDOW_WIDTH // 2) - 150, 420, 160, 48), "Enviar código", self.send_code)

    def send_code(self):
        """Busca el correo del jugador y envía el código de recuperación."""
        email = self.email_input.text.strip()
        if not email:
            self.app.banner.show("Ingresa el correo registrado.", ERROR_COLOR)
            return

        player = self.app.repo.get_player_by_email(email)
        if not player:
            self.app.banner.show("Correo no encontrado.", ERROR_COLOR)
            return

        self.sent_code = f"{random.randint(0, 999999):06d}"
        self.code_expires_at = pygame.time.get_ticks() + 5 * 60 * 1000
        try:
            # Llama al servicio de envío de correo
            self.app.email_sender.enviar_codigo_recuperacion(email, self.sent_code)
        except Exception as error:
            self.app.banner.show(f"No se pudo enviar el código: {error}", ERROR_COLOR)
            return

        self.app.banner.show("Código enviado. Revisa tu correo.", SUCCESS_COLOR)
        self.stage = "CODE"
        self.login_screen.recovery_code_sent = True
        self.buttons[0] = Button(pygame.Rect((WINDOW_WIDTH // 2) - 150, 420, 160, 48), "Validar código", self.validate_code)

    def validate_code(self):
        if not self.sent_code or not self.code_expires_at:
            self.app.banner.show("Primero solicita un código.", ERROR_COLOR)
            return
        #comprueba expiración del código
        if pygame.time.get_ticks() > self.code_expires_at:
            self.app.banner.show("El código ha expirado, solicita uno nuevo.", ERROR_COLOR)
            self.stage = "EMAIL"
            self.buttons[0] = Button(pygame.Rect((WINDOW_WIDTH // 2) - 150, 420, 160, 48), "Enviar código", self.send_code)
            return

        code = self.code_input.text.strip()
        if code != self.sent_code:
            self.app.banner.show("Código incorrecto.", ERROR_COLOR)
            return

        self.app.banner.show("Código validado. Ingresa la nueva contraseña.", SUCCESS_COLOR)
        self.stage = "PASSWORD"
        self.buttons[0] = Button(pygame.Rect((WINDOW_WIDTH // 2) - 150, 420, 160, 48), "Guardar", self.save_new_password)

    def save_new_password(self):
        """Valida la nueva contraseña y la guarda en el repositorio."""
        new_password = self.password_input.text.strip()
        confirm_password = self.confirm_password_input.text.strip()

        if new_password != confirm_password:
            self.app.banner.show("Las contraseñas no coinciden.", ERROR_COLOR)
            return

        email = self.email_input.text.strip()

        try:
            # Utiliza la validación de fortaleza de contraseña
            Validator.validate_password_strength(new_password)
        except ValueError as error:
            self.app.banner.show(str(error), ERROR_COLOR)
            return
        # Actualiza la contraseña en el repositorio
        updated = self.app.repo.update_password(email, new_password)
        if not updated:
            self.app.banner.show("No se pudo actualizar la contraseña. Verifica el correo.", ERROR_COLOR)
            return

        self.app.banner.show("Contraseña actualizada.", SUCCESS_COLOR)
        self.close()

    def handle_event(self, event: pygame.event.EventType):
        if not self.visible:
            return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.close()
            return

        for input_box in self.inputs:
            if input_box in (self.code_input, self.password_input, self.confirm_password_input) and self.stage == "EMAIL":
                continue
            if input_box in (self.password_input, self.confirm_password_input) and self.stage != "PASSWORD":
                continue
            result = input_box.handle_event(event)
            if result == "SUBMIT":
                if self.stage == "EMAIL":
                    self.send_code()
                elif self.stage == "CODE":
                    self.validate_code()
                elif self.stage == "PASSWORD":
                    self.save_new_password()

        for button in self.buttons:
            button.handle_event(event)

    def update(self):
        if not self.visible:
            return

        for input_box in self.inputs:
            input_box.update()

        if self.stage == "CODE" and self.code_expires_at and pygame.time.get_ticks() > self.code_expires_at:
            self.stage = "EMAIL"
            self.app.banner.show("El código expiró.", ERROR_COLOR)
            self.buttons[0] = Button(pygame.Rect((WINDOW_WIDTH // 2) - 150, 420, 160, 48), "Enviar código", self.send_code)

    def draw(self, surface: pygame.Surface):
        if not self.visible:
            return

        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        modal_rect = pygame.Rect((WINDOW_WIDTH // 2) - 250, 180, 500, 360)
        pygame.draw.rect(surface, PANEL_COLOR, modal_rect, border_radius=12)
        pygame.draw.rect(surface, BORDER_COLOR, modal_rect, 2, border_radius=12)

        if self.stage == "EMAIL":
            title = TITLE_FONT.render("Recuperar contraseña", True, TEXT_COLOR)
            surface.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 210)))
            info = SMALL_FONT.render("Ingresa tu correo para recibir un código.", True, TEXT_COLOR)
            surface.blit(info, info.get_rect(center=(WINDOW_WIDTH // 2, 260)))
            self.email_input.draw(surface)
        elif self.stage == "CODE":
            title = TITLE_FONT.render("Validar código", True, TEXT_COLOR)
            surface.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 210)))
            info = SMALL_FONT.render("Revisa tu correo e ingresa el código.", True, TEXT_COLOR)
            surface.blit(info, info.get_rect(center=(WINDOW_WIDTH // 2, 260)))
            self.code_input.draw(surface)
        elif self.stage == "PASSWORD":
            title = TITLE_FONT.render("Nueva contraseña", True, TEXT_COLOR)
            surface.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 210)))
            info = SMALL_FONT.render("Ingresa y confirma tu nueva contraseña.", True, TEXT_COLOR)
            surface.blit(info, info.get_rect(center=(WINDOW_WIDTH // 2, 260)))
            self.password_input.draw(surface)
            self.confirm_password_input.draw(surface)

        for button in self.buttons:
            button.draw(surface)


class RegisterScreen(BaseScreen, FileDialogHelperMixin):
    """Pantalla para el registro de nuevos jugadores (usa el Mixin para subir archivos)."""
    def __init__(self, app: "GameApp"):
        super().__init__(app)
        center_x = WINDOW_WIDTH // 2
        start_y = 150
        field_height = 48
        spacing = 70

        placeholders = [
            ("Alias", ""),
            ("Nombre completo", ""),
            ("Correo", ""),
            ("Contraseña", "", True),
            ("Imagen de perfil", "Ruta opcional"),
            ("Imagen de nave", "Ruta opcional"),
            ("Música favorita", "Separar por coma"),
        ]

        self.inputs: List[InputBox] = []
        for idx, data in enumerate(placeholders):
            placeholder, initial = data[0], data[1]
            password = data[2] if len(data) > 2 else False
            box = InputBox(center_x - 220, start_y + idx * spacing, 440, field_height, placeholder=placeholder, text=initial, password=password)
            self.inputs.append(box)
        self.inputs[0].set_active(True)

        self.upload_margin = 18
        self.upload_button_size = (170, 42)
        self.upload_buttons: List[Button] = []

        self.buttons = [
            Button(pygame.Rect(center_x - 220, start_y + len(self.inputs) * spacing, 200, 52), "Registrarse", self.register_player),
            Button(pygame.Rect(center_x + 20, start_y + len(self.inputs) * spacing, 200, 52), "Cancelar", lambda: app.set_screen(MainMenuScreen(app))),
        ]

        self.upload_buttons.extend(
            [
                Button(self._create_upload_rect(4), "Cargar imagen", lambda: self._open_file_dialog(4, ("Archivos PNG", "*.png"), ("Archivos JPG", "*.jpg;*.jpeg"), ("Todos", "*.*"))),
                Button(self._create_upload_rect(5), "Cargar nave", lambda: self._open_file_dialog(5, ("Archivos PNG", "*.png"), ("Archivos JPG", "*.jpg;*.jpeg"), ("Todos", "*.*"))),
                Button(self._create_upload_rect(6), "Cargar música", lambda: self._open_file_dialog_multiple(6, ("Archivos de audio", "*.mp3;*.wav;*.ogg"), ("Todos", "*.*"))),
            ]
        )

        self.buttons.extend(self.upload_buttons)

    def _focus_next(self, current: InputBox):
        if current not in self.inputs:
            return
        idx = self.inputs.index(current)
        next_idx = (idx + 1) % len(self.inputs)
        for box in self.inputs:
            box.set_active(False)
        self.inputs[next_idx].set_active(True)

    def register_player(self):
        """Recoge los datos del formulario y llama al PlayerService para registrarlos."""
        values = [box.text.strip() for box in self.inputs]
        alias, full_name, email, password, profile_picture, spaceship_image, favorite_music = values
        music_list = [m.strip() for m in favorite_music.split(",") if m.strip()]

        try:
            jugador = self.app.service.registrar_jugador(
                alias=alias,
                full_name=full_name,
                email=email,
                password=password,
                profile_picture=profile_picture,
                spaceship_image=spaceship_image,
                favorite_music=music_list,
            )
        except ValueError as error:
            self.app.banner.show(str(error), ERROR_COLOR)
            return
        except Exception as error:  # Captura errores externos (como envío de correo)
            self.app.banner.show(f"Error al registrar: {error}", ERROR_COLOR)
            return

        self.app.banner.show(f"Registro exitoso. Confirma tu correo: {jugador['email']}", SUCCESS_COLOR)
        self.app.set_screen(MainMenuScreen(self.app))

    def handle_event(self, event: pygame.event.EventType):
        for box in self.inputs:
            result = box.handle_event(event)
            if result == "TAB":
                self._focus_next(box)
            elif result == "SUBMIT":
                self.register_player()
        for button in self.buttons:
            button.handle_event(event)

    def update(self):
        for box in self.inputs:
            box.update()

    def draw(self, surface: pygame.Surface):
        surface.fill(BACKGROUND_COLOR)
        title = TITLE_FONT.render("Registro de jugador", True, TEXT_COLOR)
        surface.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 90)))

        for box in self.inputs:
            label_text = SMALL_FONT.render(box.placeholder, True, TEXT_COLOR)
            surface.blit(label_text, (box.rect.x, box.rect.y - 28))
            box.draw(surface)

        helper_text = SMALL_FONT.render("Puedes cargar archivos o escribir rutas manualmente.", True, (180, 180, 180))
        surface.blit(helper_text, (WINDOW_WIDTH // 2 - helper_text.get_width() // 2, self.inputs[-1].rect.bottom + 16))

        for button in self.buttons:
            button.draw(surface)


class GameScreen(BaseScreen):
    """área de juego después del login exitoso."""
    def __init__(self, app: "GameApp", player: Player):
        super().__init__(app)
        self.player = player
        center_x = WINDOW_WIDTH // 2
        start_y = 260
        spacing = 80
        self.buttons = [
            Button(pygame.Rect(center_x - 170, start_y, 340, 55), "Ver perfil", lambda: app.set_screen(ProfileScreen(app, self.player))),
            Button(pygame.Rect(center_x - 170, start_y + spacing, 340, 55), "Editar perfil", lambda: app.set_screen(EditProfileScreen(app, self.player))),
            Button(pygame.Rect(center_x - 170, start_y + spacing * 2, 340, 55), "Cerrar sesión", lambda: app.set_screen(MainMenuScreen(app))),
        ]

    def handle_event(self, event: pygame.event.EventType):
        for button in self.buttons:
            button.handle_event(event)

    def draw(self, surface: pygame.Surface):
        surface.fill(BACKGROUND_COLOR)
        title = TITLE_FONT.render("Área de juego", True, TEXT_COLOR)
        welcome = FONT.render(f"Bienvenido {self.player.alias}!", True, TEXT_COLOR)
        surface.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 150)))
        surface.blit(welcome, welcome.get_rect(center=(WINDOW_WIDTH // 2, 210)))
        for button in self.buttons:
            button.draw(surface)


class ProfileScreen(BaseScreen):
    def __init__(self, app: "GameApp", player: Player):
        super().__init__(app)
        self.player = player
        self.back_button = Button(pygame.Rect(60, 600, 180, 48), "Volver", lambda: app.set_screen(GameScreen(app, self.player)))

    def handle_event(self, event: pygame.event.EventType):
        self.back_button.handle_event(event)

    def draw(self, surface: pygame.Surface):
        surface.fill(BACKGROUND_COLOR)
        title = TITLE_FONT.render("Mi perfil", True, TEXT_COLOR)
        surface.blit(title, (60, 60))

        info_lines = [
            f"ID: {self.player._id}",
            f"Alias: {self.player.alias}",
            f"Nombre completo: {self.player._full_name}",
            f"Correo: {self.player.email}",
            f"Imagen de perfil: {self.player._profile_picture or 'No configurada'}",
            f"Imagen de nave: {self.player._spaceship_image or 'No configurada'}",
        ]

        if self.player._favorite_music:
            info_lines.append("Música favorita:")
            info_lines.extend([f" - {music}" for music in self.player._favorite_music])
        else:
            info_lines.append("Música favorita: No configurada")

        y = 140
        for line in info_lines:
            text = SMALL_FONT.render(line, True, TEXT_COLOR)
            surface.blit(text, (60, y))
            y += 32

        self.back_button.draw(surface)


class EditProfileScreen(BaseScreen, FileDialogHelperMixin):
    def __init__(self, app: "GameApp", player: Player):
        super().__init__(app)
        self.player = player
        center_x = WINDOW_WIDTH // 2
        start_y = 140
        spacing = 68

        field_data = [
            ("Alias", self.player.alias),
            ("Nombre completo", self.player._full_name),
            ("Correo", self.player.email),
            ("Imagen de perfil", self.player._profile_picture),
            ("Imagen de nave", self.player._spaceship_image),
            ("Música favorita", ", ".join(self.player._favorite_music)),
        ]

        self.inputs: List[InputBox] = []
        for idx, (placeholder, initial) in enumerate(field_data):
            box = InputBox(center_x - 220, start_y + spacing * idx, 440, 48, placeholder=placeholder, text=initial)
            self.inputs.append(box)
        self.inputs[0].set_active(True)

        self.upload_margin = 18
        self.upload_button_size = (170, 42)
        self.upload_buttons: List[Button] = []

        self.buttons = [
            Button(pygame.Rect(center_x - 220, start_y + spacing * len(self.inputs), 200, 52), "Guardar", self.save_changes),
            Button(pygame.Rect(center_x + 20, start_y + spacing * len(self.inputs), 200, 52), "Cancelar", lambda: app.set_screen(GameScreen(app, self.player))),
        ]

        self.upload_buttons.extend(
            [
                Button(self._create_upload_rect(3), "Cargar imagen", lambda: self._open_file_dialog(3, ("Archivos PNG", "*.png"), ("Archivos JPG", "*.jpg;*.jpeg"), ("Todos", "*.*"))),
                Button(self._create_upload_rect(4), "Cargar nave", lambda: self._open_file_dialog(4, ("Archivos PNG", "*.png"), ("Archivos JPG", "*.jpg;*.jpeg"), ("Todos", "*.*"))),
                Button(self._create_upload_rect(5), "Cargar música", lambda: self._open_file_dialog_multiple(5, ("Archivos de audio", "*.mp3;*.wav;*.ogg"), ("Todos", "*.*"))),
            ]
        )

        self.buttons.extend(self.upload_buttons)

    def _focus_next(self, current: InputBox):
        if current not in self.inputs:
            return
        idx = self.inputs.index(current)
        next_idx = (idx + 1) % len(self.inputs)
        for box in self.inputs:
            box.set_active(False)
        self.inputs[next_idx].set_active(True)

    def save_changes(self):
        alias = self.inputs[0].text.strip()
        full_name = self.inputs[1].text.strip()
        email = self.inputs[2].text.strip()
        profile_picture = self.inputs[3].text.strip()
        spaceship_image = self.inputs[4].text.strip()
        favorite_music = [m.strip() for m in self.inputs[5].text.split(",") if m.strip()]

        try:
            updated_player = self.app.service.actualizar_jugador(
                player_id=self.player._id,
                alias=alias,
                full_name=full_name,
                email=email,
                profile_picture=profile_picture,
                spaceship_image=spaceship_image,
                favorite_music=favorite_music,
            )
        except ValueError as error:
            self.app.banner.show(str(error), ERROR_COLOR)
            return
        except Exception as error:
            self.app.banner.show(f"Error al actualizar: {error}", ERROR_COLOR)
            return

        self.app.banner.show("Información actualizada correctamente.", SUCCESS_COLOR)
        self.app.set_screen(GameScreen(self.app, updated_player))

    def handle_event(self, event: pygame.event.EventType):
        for box in self.inputs:
            result = box.handle_event(event)
            if result == "TAB":
                self._focus_next(box)
            elif result == "SUBMIT":
                self.save_changes()
        for button in self.buttons:
            button.handle_event(event)

    def update(self):
        for box in self.inputs:
            box.update()

    def draw(self, surface: pygame.Surface):
        surface.fill(BACKGROUND_COLOR)
        title = TITLE_FONT.render("Editar perfil", True, TEXT_COLOR)
        surface.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 80)))

        for box in self.inputs:
            label_text = SMALL_FONT.render(box.placeholder, True, TEXT_COLOR)
            surface.blit(label_text, (box.rect.x, box.rect.y - 28))
            box.draw(surface)

        helper_text = SMALL_FONT.render("Puedes cargar archivos o escribir rutas manualmente.", True, (180, 180, 180))
        surface.blit(helper_text, (WINDOW_WIDTH // 2 - helper_text.get_width() // 2, self.inputs[-1].rect.bottom + 16))

        for button in self.buttons:
            button.draw(surface)


# ================== APLICACIÓN PRINCIPAL ==================
class GameApp:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Mi Juego - Pygame")
        self.clock = pygame.time.Clock()
        self.running = True

        # Inicialización de repositorio y servicios 
        self.repo = PlayerRepository("data/players.json")
        self.email_sender = EmailSender(
            api_key="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",
            remitente={"email": "melmontoya245@gmail.com", "name": "Mi Juego"},
        )
        self.service = PlayerService(self.repo, self.email_sender)

        self.banner = MessageBanner()
        self.current_screen: BaseScreen = MainMenuScreen(self)

    def set_screen(self, screen: BaseScreen):
        self.current_screen = screen

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    self.current_screen.handle_event(event)

            self.current_screen.update()
            self.current_screen.draw(self.screen)
            self.banner.draw(self.screen)

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()
# ================== PUNTO DE ENTRADA ==================
if __name__ == "__main__":
    GameApp().run()