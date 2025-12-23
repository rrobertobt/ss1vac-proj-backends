import boto3
from app.core.config import settings

class SesMailService:
    def __init__(self):
        self.client = boto3.client(
            "ses",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
        )

    def send_text_email(self, to: str, subject: str, text: str) -> None:
        if not settings.MAIL_FROM:
            raise RuntimeError("MAIL_FROM no está configurado")

        self.client.send_email(
            Source=settings.MAIL_FROM,
            Destination={"ToAddresses": [to]},
            Message={
                "Subject": {"Data": subject},
                "Body": {"Text": {"Data": text}},
            },
        )
