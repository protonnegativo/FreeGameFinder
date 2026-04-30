import os
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr
from typing import List, Dict

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
    api_url = os.getenv("API_URL", "http://localhost:8000")
    # O link aponta para a API do backend, que vai retornar uma página de confirmação
    verification_link = f"{api_url}/api/v1/subscribe/confirm?token={token}"

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

async def send_new_games_alert(emails: List[str], games: List[Dict]):
    """
    Envia um e-mail de alerta sobre novos jogos para os inscritos usando Cópia Oculta (BCC).
    """
    if not emails or not games:
        return

    games_html = ""
    for game in games:
        cover = f'<img src="{game["cover_image_url"]}" alt="{game["title"]}" style="width: 100%; max-width: 400px; border-radius: 8px; margin-bottom: 10px;">' if game.get("cover_image_url") else ''
        price_text = f'<span style="text-decoration: line-through; color: #888;">R$ {game["original_price"]}</span> <strong style="color: #00FF41;">GRÁTIS</strong>' if game.get("original_price") else '<strong style="color: #00FF41;">GRÁTIS</strong>'

        games_html += f"""
        <div style="background-color: #151A23; border: 1px solid #2a303c; border-radius: 10px; padding: 20px; margin-bottom: 20px; text-align: left;">
            {cover}
            <h2 style="color: #E0E0E0; margin-top: 0;">{game["title"]}</h2>
            <p style="color: #A0A0A0; font-size: 14px; margin-bottom: 10px;">Plataforma: <strong>{game["platform"]}</strong></p>
            <p style="font-size: 16px;">{price_text}</p>
            <a href="{game["claim_url"]}" target="_blank" style="background-color: #00FF41; color: #0B0E14; padding: 12px 20px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block; margin-top: 10px;">
                Resgatar Agora
            </a>
        </div>
        """

    html = f"""
    <div style="font-family: sans-serif; text-align: center; background-color: #0B0E14; padding: 20px;">
        <div style="max-width: 600px; margin: auto; background-color: #0B0E14; padding: 20px; border-radius: 10px; color: #E0E0E0;">
            <h1 style="color: #00FF41;">Novos Jogos Grátis!</h1>
            <p style="font-size: 16px; margin-bottom: 30px;">O radar do FreeGameFinder apitou! Acabamos de encontrar estas ofertas com 100% de desconto:</p>
            {games_html}
            <p style="color: #666; font-size: 12px; margin-top: 30px;">
                Você está recebendo este e-mail porque se inscreveu no FreeGameFinder.
            </p>
        </div>
    </div>
    """

    message = MessageSchema(subject="🚨 Novos Jogos Grátis Encontrados!", recipients=[os.getenv("MAIL_FROM", "seu@email.com")], bcc=emails, body=html, subtype="html")
    fm = FastMail(conf)
    await fm.send_message(message)