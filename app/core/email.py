from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from app.config import settings

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
    VALIDATE_CERTS=settings.VALIDATE_CERTS
)

async def send_activation_email(email_to: str, token: str):
    # TODO: Move Frontend URL to settings
    activation_link = f"http://localhost:5173/verify-email?token={token}"
    
    html = f"""
    <html>
        <body>
            <p>Witaj!</p>
            <p>Proszę potwierdź swoje konto klikając w poniższy link:</p>
            <a href="{activation_link}">Aktywuj konto</a>
            <p>Link jest ważny przez 24 godziny.</p>
        </body>
    </html>
    """
    
    message = MessageSchema(
        subject="Aktywacja Konta - Stock API",
        recipients=[email_to],
        body=html,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    await fm.send_message(message)
