from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, String, Numeric, DateTime, Boolean, Text, desc
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import sessionmaker, Session, declarative_base
import os
import uuid
from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional, Dict
from decimal import Decimal
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging

from scraper import fetch_epic_games_free_games, fetch_steam_free_games
from email_utils import send_verification_email, send_new_games_alert

# Configurações do Banco de Dados
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/freegamefinder")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Modelos do Banco de Dados (SQLAlchemy)
class DBGame(Base):
    __tablename__ = "games"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    platform = Column(String, nullable=False)
    original_price = Column(Numeric(10, 2), nullable=True)
    cover_image_url = Column(Text, nullable=True)
    claim_url = Column(Text, nullable=False)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class DBSubscriber(Base):
    __tablename__ = "subscribers"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False)
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Cria as tabelas no banco de dados automaticamente ao iniciar
Base.metadata.create_all(bind=engine)

# Schemas (Pydantic) para serializar os dados para JSON
class GameOut(BaseModel):
    id: str
    title: str
    platform: str
    original_price: Optional[Decimal] = None
    cover_image_url: Optional[str] = None
    claim_url: str
    
    model_config = {"from_attributes": True}

class SubscriberIn(BaseModel):
    email: str


# Dependência para injeção do banco de dados nas rotas
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI(
    title="FreeGameFinder API",
    description="API para buscar jogos gratuitos e gerenciar alertas",
    version="1.0.0"
)

# Configuração do CORS
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
origins = [
    frontend_url,  # Endereço do frontend configurado no .env
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def run_scraper_and_update_db():
    logger.info("Iniciando a varredura por jogos gratuitos...")
    db = SessionLocal()
    try:
        epic_games = await fetch_epic_games_free_games()
        steam_games = await fetch_steam_free_games()
        
        # Combina os resultados de todas as plataformas
        all_games: List[Dict] = epic_games + steam_games
        
        new_games_added = []
        for game_data in all_games:
            # Verifica se o jogo já existe no banco de dados
            exists = db.query(DBGame).filter(DBGame.title == game_data['title'], DBGame.platform == game_data['platform']).first()
            if not exists:
                new_game = DBGame(**game_data)
                db.add(new_game)
                new_games_added.append(game_data)
        
        if new_games_added:
            db.commit()
            logger.info(f"{len(new_games_added)} novo(s) jogo(s) adicionado(s) ao banco de dados.")
            
            # Busca apenas usuários que confirmaram o e-mail
            verified_subs = db.query(DBSubscriber.email).filter(DBSubscriber.is_verified == True).all()
            emails = [sub.email for sub in verified_subs]
            
            if emails:
                try:
                    await send_new_games_alert(emails, new_games_added)
                except Exception as e:
                    logger.error(f"Falha ao enviar e-mails em lote: {e}")
        else:
            logger.info("Nenhum jogo novo encontrado.")
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Bem-vindo ao FreeGameFinder API!"}

@app.get("/api/v1/games", response_model=List[GameOut])
def get_games(db: Session = Depends(get_db)):
    # Retorna os jogos ordenados pela data de criação, mais recentes primeiro
    games = db.query(DBGame).order_by(desc(DBGame.created_at)).all()
    return games

@app.post("/api/v1/subscribe")
async def subscribe(subscriber: SubscriberIn, db: Session = Depends(get_db)):
    # Verifica se o e-mail já existe no banco
    existing_user = db.query(DBSubscriber).filter(DBSubscriber.email == subscriber.email).first()
    if existing_user:
        # Se o usuário existe mas não é verificado, reenviamos o e-mail
        if not existing_user.is_verified:
            await send_verification_email(existing_user.email, existing_user.verification_token)
            return {"message": "E-mail já cadastrado. Enviamos um novo link de confirmação para você!"}
        else:
            return {"message": "Este e-mail já está na nossa lista de alertas!"}
    
    # Gera um token único para confirmação (Double Opt-in)
    token = str(uuid.uuid4())
    
    new_subscriber = DBSubscriber(email=subscriber.email, verification_token=token)
    db.add(new_subscriber)
    db.commit()
    
    try:
        await send_verification_email(new_subscriber.email, token)
    except Exception as e:
        logger.error(f"Falha ao enviar e-mail de verificação para {subscriber.email}: {e}")
        # Mesmo que o e-mail falhe, o usuário está no banco. Ele pode tentar de novo mais tarde.
        raise HTTPException(status_code=500, detail="Não foi possível enviar o e-mail de confirmação. Tente novamente mais tarde.")
    
    return {"message": "Inscrição realizada! Verifique sua caixa de entrada para confirmar seu e-mail."}

@app.get("/api/v1/subscribe/confirm", response_class=HTMLResponse)
def confirm_email(token: str, db: Session = Depends(get_db)):
    subscriber = db.query(DBSubscriber).filter(DBSubscriber.verification_token == token).first()
    
    if not subscriber:
        return """<div style="text-align:center; padding: 50px; font-family: sans-serif;"><h1>Token inválido ou expirado.</h1><p>Tente se cadastrar novamente.</p></div>"""
        
    if subscriber.is_verified:
        return """<div style="text-align:center; padding: 50px; font-family: sans-serif;"><h1>Este e-mail já foi verificado!</h1><p>Você já está pronto para receber alertas.</p></div>"""

    subscriber.is_verified = True
    subscriber.verification_token = None # Opcional: invalidar o token após o uso
    db.commit()
    
    return """<div style="text-align:center; padding: 50px; font-family: sans-serif; color: #00FF41; background: #0B0E14; height: 100vh; display: flex; flex-direction: column; justify-content: center;"><h1>E-mail confirmado com sucesso!</h1><p>Você agora receberá alertas de jogos grátis.</p></div>"""

@app.get("/api/v1/health")
def health_check():
    try:
        with engine.connect() as connection:
            return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": "disconnected", "details": str(e)}

@app.post("/api/v1/scraper/run")
async def force_run_scraper():
    await run_scraper_and_update_db()
    return {"message": "Varredura concluída!"}

# Agendador para rodar o scraper periodicamente
scheduler = AsyncIOScheduler(timezone="UTC")
scheduler.add_job(run_scraper_and_update_db, 'cron', minute='0,30')

@app.on_event("startup")
async def startup_event():
    logger.info("Aplicação iniciada. Rodando o scraper pela primeira vez...")
    await run_scraper_and_update_db()
    scheduler.start()