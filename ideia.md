# Design Doc: FreeGameFinder

## 1. Visão Geral

O FreeGameFinder é uma plataforma agregadora de ofertas cujo único objetivo é filtrar e exibir jogos que estejam com 100% de desconto (gratuitos). O sistema monitora fontes externas, consolida os dados em um banco de dados local e notifica usuários cadastrados via e-mail sempre que um novo título é detectado.

## 2. Objetivos e Problema

*   **Problema:** Gamers perdem ofertas de tempo limitado porque os jogos ficam gratuitos em plataformas dispersas (Steam, Epic, GOG, IndieGala).
*   **Solução:** Centralizar essas informações em uma interface única e "limpa", com um sistema de alerta push via e-mail para que o usuário não precise checar o site ativamente.

## 3. Arquitetura e Stack Tecnológica

| Componente | Tecnologia Sugerida | Justificativa |
| :--- | :--- | :--- |
| **Backend** | Python (FastAPI) | Excelente para scripts de scraping, tipagem estática e performance assíncrona. |
| **Frontend** | React + Tailwind CSS | Interface rápida, responsiva e moderna. (Pode usar Next.js para SEO). |
| **Banco de Dados** | PostgreSQL | Melhor suporte para concorrência e tipos de dados do que SQLite a longo prazo. |
| **Task Runner** | APScheduler / Celery | Para executar a varredura a cada 30 minutos de forma confiável. |
| **E-mail** | Brevo / Gmail SMTP | Foco em custo zero. Brevo oferece 300 e-mails/dia grátis. SMTP do Gmail oferece até 500/dia grátis. |
| **Infraestrutura** | Oracle Cloud VPS | Instância estável para rodar o backend e o banco 24/7 via Docker. |
| **Proxy/Web Server**| Nginx ou Caddy | Caddy gerencia certificados SSL (HTTPS) automaticamente. |

## 4. Modelagem de Dados (Database Schema)

### Tabela: `games`
Armazena os jogos gratuitos encontrados.
*   `id` (UUID, Primary Key)
*   `title` (String, Not Null)
*   `platform` (String, Not Null) - Ex: 'Epic Games', 'Steam', 'GOG'
*   `original_price` (Decimal) - Opcional, para mostrar o quanto o usuário está economizando.
*   `cover_image_url` (String) - URL da arte do jogo.
*   `claim_url` (String, Not Null) - Link direto para resgate.
*   `start_date` (DateTime) - Quando a oferta começou.
*   `end_date` (DateTime) - Quando a oferta termina (se disponível).
*   `created_at` (DateTime, Default Now)

### Tabela: `subscribers`
Armazena os usuários que desejam receber alertas.
*   `id` (UUID, Primary Key)
*   `email` (String, Unique, Not Null)
*   `is_verified` (Boolean, Default False) - Controle para o Double Opt-in.
*   `verification_token` (String) - Token gerado para confirmar o e-mail.
*   `created_at` (DateTime, Default Now)

## 5. Contratos de API (Endpoints Rest)

**Base URL:** `/api/v1`

### Jogos
*   `GET /games`
    *   *Query Params:* `platform` (opcional), `status` (active/expired).
    *   *Retorno:* Lista dos jogos ativos.

### Inscrição de E-mail
*   `POST /subscribe`
    *   *Body:* `{ "email": "user@example.com" }`
    *   *Ação:* Cria registro inativo e envia e-mail com link de confirmação.
*   `GET /subscribe/confirm?token=XYZ`
    *   *Ação:* Valida o token e altera `is_verified` para `True`.
*   `POST /unsubscribe`
    *   *Body:* `{ "email": "user@example.com", "token": "XYZ" }`
    *   *Ação:* Remove o usuário da lista (obrigatório por leis anti-spam).

## 6. Mapeamento de Funcionalidades

### 6.1. Varrredura (The Scraper/Aggregator)
*   **Fontes:**
    *   API pública da Epic Games Store (promocional promotions).
    *   Feed RSS do subreddit r/GameDeals (filtrando por "[Free]" ou "[100%]").
    *   Scraping HTML/JSON do GG.deals (seção freebies).
*   **Lógica de Execução:** O script roda via Cron/APScheduler a cada 30 min.
*   **Resiliência:** Uso de User-Agents rotativos, `try/except` robusto para não quebrar o scraper caso uma fonte mude o layout, e rate limiting de requisições.

### 6.2. Interface do Usuário (Landing Page)
*   **Hero Section:** Proposta de valor clara ("Nunca mais perca um jogo grátis").
*   **Newsletter Input:** Campo `Email-only` com botão "Ativar Alertas".
*   **Lista de Jogos:** Grid de cards exibindo: Título, Plataforma (ícone), Imagem de capa, Preço Riscado (ex: ~R$ 199,00~ -> Grátis) e Link direto ("Resgatar Agora").
*   **Filtro Simples:** Botões tipo *Pill* para alternar entre "Todos", "Steam", "Epic", "GOG".

### 6.3. Sistema de Notificação
*   **Processamento em Lotes:** A fila de envios processa os e-mails em lotes para não exceder limites diários do plano gratuito (ex: limite de 300/dia no Brevo ou 500/dia no Gmail) e evitar cair em blacklists de spam.
*   **Template HTML:** E-mail responsivo (funciona bem no celular) mostrando a capa do jogo e o botão direto para resgate.

## 7. Fluxo de Dados e Automação

1.  **Coleta:** `Scraper` -> Extrai dados -> Valida se o desconto é efetivamente 100%.
2.  **Persistência:** O backend faz um `UPSERT` no Banco de Dados. Se for um jogo novo (`title` + `platform` inédito), insere e cria um evento de notificação.
3.  **Difusão:** O `Task Runner` capta o evento de notificação -> Recupera lista de inscritos em que `is_verified=True` -> Envia o alerta.
4.  **Exibição:** Frontend consome `GET /api/v1/games` e atualiza a interface.

## 8. Segurança e Boas Práticas

*   **Double Opt-in:** Usuário SÓ recebe alertas após clicar no link do primeiro e-mail. Evita que bots cadastrem e-mails falsos sujando a reputação de envio da plataforma.
*   **Rate Limiting:** A rota `/subscribe` deve ter limite (ex: max 3 requisições por IP a cada 10 min) para evitar ataques de spam de cadastro.
*   **CORS:** Backend (FastAPI) configurado para aceitar requisições APENAS do domínio do frontend.

## 9. Design de Interface (UI/UX)

**Estética: "Dark Gaming Mode"**
*   **Paleta de Cores:**
    *   Fundo: `#0B0E14` (Preto azulado profundo).
    *   Cards de Fundo: `#151A23` (Cria elevação visual).
    *   Destaque (Ação): `#00FF41` (Verde "Matrix/Terminal" indicando sucesso/grátis) ou `#7289DA` (Blurple de comunidade gamer).
    *   Texto: `#E0E0E0` (Cinza claro para reduzir cansaço visual).
*   **Tipografia:** Família Sans-serif moderna (`Inter` ou `Roboto`).
*   **Usabilidade:** Foco no conteúdo. Sem pop-ups ou anúncios intrusivos. O CTA (Call to Action) principal deve estar visível no topo da dobra do site (`above the fold`).

## 10. Requisitos de Ambiente (.env)

*   `DATABASE_URL`: String de conexão do PostgreSQL.
*   `EMAIL_HOST_PASSWORD`: Chave de API do Brevo ou Senha de Aplicativo (App Password) do Gmail.
*   `FRONTEND_URL`: URL do domínio (para geração do link de confirmação e CORS).
*   `SECRET_KEY`: Chave para gerar os tokens JWT ou Hashes de confirmação.

## 11. Próximos Passos (Plano de Ação)

*   **Fase 1: Configuração do Setup Core**
    *   Criar o repositório no GitHub.
    *   Criar o arquivo `docker-compose.yml` local para subir Postgres + FastAPI.
*   **Fase 2: Backend e Scraper (Proof of Concept)**
    *   Desenvolver os modelos do banco de dados (SQLAlchemy ou equivalente).
    *   Escrever o scraper conectando **apenas na API da Epic Games** inicialmente (pois é JSON estruturado e mais simples que fazer parse de HTML).
*   **Fase 3: Frontend Simples**
    *   Criar a listagem de jogos conectada à API do Backend.
*   **Fase 4: Sistema de Notificações**
    *   Implementar rota de inscrição.
    *   Configurar disparo de e-mails usando uma conta gratuita de serviço de email.
*   **Fase 5: Deploy**
    *   Instalar Docker e Caddy na VPS Oracle.
    *   Rodar os containers e vincular domínio.