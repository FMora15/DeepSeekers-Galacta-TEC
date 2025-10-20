import requests
from sib_api_v3_sdk import ApiClient, Configuration
from sib_api_v3_sdk.api import transactional_emails_api
from sib_api_v3_sdk.models import SendSmtpEmail
from sib_api_v3_sdk.rest import ApiException


def obtener_url_publica():
    #Intenta obtenr la URL pública de ngrok; si falla, retorna localhost"

    try:
        respuesta = requests.get("http://127.0.0.1:4040/api/tunnels")
        data = respuesta.json()
        public_url = data['tunnels'][0]['public_url']
        print(f"URL pública detectada: {public_url}")
        return public_url
    except Exception:
        print("No se pudo obtener la URL pública de ngrok. Usando localhost por defecto.")
        return "http://localhost:5000"


class EmailSender:
    #Abstrae la logica de comunicacion con el servicio de envio de correos (Brevo)"
    def __init__(self, api_key, remitente):
        "Inicializa el clienta de la API de Brevo con la clave y la informacion del remitente"
        self.remitente = remitente
        configuration = Configuration()
        configuration.api_key['api-key'] = api_key
        self.api_client = ApiClient(configuration)
        self.tx_api = transactional_emails_api.TransactionalEmailsApi(self.api_client)

    def enviar_correo_confirmacion(self, destinatario, token):
        #Envia el correo con un enlace de confirmacion de registro
        public_url = obtener_url_publica()
        asunto = "Confirma tu correo"
        cuerpo = f"Haz clic en el siguiente enlace para confirmar tu correo: {public_url}/confirmar?token={token}"

        #crea el objeto modelo de correo a partir de la informacion
        email = SendSmtpEmail(
            sender=self.remitente,
            to=[{"email": destinatario}],
            subject=asunto,
            text_content=cuerpo
        )

        try:
            #Llama a la API para enviar el correo
            response = self.tx_api.send_transac_email(email)
            print(f"Correo enviado a {destinatario}, MessageId: {getattr(response, 'message_id', response)}")
        except ApiException as e:
            #Manejo de errores especificos de la API
            print(f"No se pudo enviar el correo. Status: {getattr(e, 'status', 'N/A')}, Reason: {getattr(e, 'reason', str(e))}")
            try: 
                print("Response body:", e.body)
            except Exception: 
                pass
            raise

    def enviar_codigo_recuperacion(self, destinatario, codigo):
        #Envia un coreo con un codigo temporal para recuperacion de contraseña
        asunto = "Recupera tu contraseña"
        cuerpo = f"Tu código de recuperación es: {codigo}\nEste código expira en 5 minutos."

        #modelo de correo
        email = SendSmtpEmail(
            sender=self.remitente,
            to=[{"email": destinatario}],
            subject=asunto,
            text_content=cuerpo
        )

        #Llama a la API para enviar el correo 
        try:
            self.tx_api.send_transac_email(email)
            print(f"Código enviado a {destinatario}")
        except Exception as e:
            print(f"Error al enviar código: {e}")