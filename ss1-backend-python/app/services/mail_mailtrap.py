import mailtrap as mt
from app.core.config import settings

class MailService:
    def __init__(self):
        self.api_token = settings.MAILTRAP_API_TOKEN
        self.from_email = settings.MAIL_FROM
        self.from_name = settings.MAIL_FROM_NAME
        
        if not self.api_token:
            raise RuntimeError("MAILTRAP_API_TOKEN no está configurado")
        
        if not self.from_email:
            raise RuntimeError("MAIL_FROM no está configurado")
        
        self.client = mt.MailtrapClient(token=self.api_token)

    def send_text_email(self, to: str, subject: str, text: str) -> None:
        try:
            mail = mt.Mail(
                sender=mt.Address(email=self.from_email, name=self.from_name),
                to=[mt.Address(email=to)],
                subject=subject,
                text=text,
                category="2FA",
            )
            
            response = self.client.send(mail)
            return response
        except Exception as e:
            raise RuntimeError(f"Error al enviar correo: {str(e)}")
