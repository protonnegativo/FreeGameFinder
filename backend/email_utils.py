import os
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr

# Configuração do serviço de e-mail a partir das variáveis de ambiente
conf = ConnectionConfig(
    MAIL_USERNAME = os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD"),
    MAIL_FROM = os.getenv("MAIL_FROM"),
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587)),
    MAIL_SERVER = os.getenv("MAIL_SERVER"),
    MAIL_STARTTLS = os.getenv("MAIL_STARTTLS", "True").lower() == "true",
    MAIL_SSL_TLS = os.getenv("MAIL_SSL_TLS", "False").lower() == "true",
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)

async def send_verification_email(email: EmailStr, token: str):
    """
    Envia um e-mail de verificação com um link de confirmação.
    """
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    # O link aponta para a API do backend, que vai retornar uma página de confirmação
    verification_link = f"http://localhost:8000/api/v1/subscribe/confirm?token={token}"

    html = f"""
    <div style="font-family: sans-serif; text-align: center; background-color: #f4f4f4; padding: 20px;">
        <div style="max-width: 600px; margin: auto; background-color: #ffffff; padding: 40px; border-radius: 10px;">
            <h1 style="color: #0B0E14;">Bem-vindo ao FreeGameFinder!</h1>
            <p style="color: #333; font-size: 16px;">Clique no botão abaixo para confirmar seu e-mail e começar a receber alertas:</p>
            <a href="{verification_link}" target="_blank" style="background-color: #00FF41; color: #0B0E14; padding: 15px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block; margin-top: 20px;">
                Confirmar Inscrição
            </a>
            <p style="color: #666; font-size: 12px; margin-top: 30px;">Se você não se inscreveu, pode ignorar este e-mail.</p>
        </div>
    </div>
    """

    message = MessageSchema(subject="Confirme sua inscrição no FreeGameFinder", recipients=[email], body=html, subtype="html")
    fm = FastMail(conf)
    await fm.send_message(message)