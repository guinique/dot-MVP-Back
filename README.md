# dot-MVP-Back

Este repositório contém o backend para a plataforma de tutores personalizados.

## Requisitos do Backend (baseado no PRD)

### 4.1 Gestão de tutores

a) **Modelo de dados do tutor:** Pelo menos identificador, título, status (ativo/inativo), instruções de comportamento, e referência a uma ou mais “fontes” consumíveis pelo runtime (ex.: URLs HTTP públicas a texto ou JSON estático — não é obrigatório crawler completo; pode ser fetch simples com limites).
b) **API REST (ou equivalente claro):** Para as operações de gestão (CRUD de tutores), protegidas para o papel administrativo (JWT ou API key de admin — decisão documentada).

### 4.3 Conversação com o tutor

a) **Pipeline de resposta orquestrado por agente(s):** Usando LangChain ou Pydantic AI (escolha e justificação em "Decisões de arquitetura" no README).
b) **Agente de conhecimento:** Deve decidir como usar o conhecimento disponível (ex.: invocar ferramentas que buscam trechos, resumem, ou compilam contexto) em vez de depender de banco vetorial, índice vetorial externo ou embeddings como estratégia principal de RAG.
c) **Chamadas a modelos de linguagem:** Uso de variáveis de ambiente para chaves e endpoints; README com exemplo de .env.example sem segredos reais.

### 4.4 Persistência

a) **Persistir tutores e metadados necessários:** PostgreSQL, SQLite ou outro — justificar trade-off.
b) **Persistir histórico de conversas mínimo:** Últimas N mensagens por sessão ou por tutor para continuidade na sessão do iframe.

### 5. Requisitos não funcionais

a) **Segurança básica:** Não vazar stack traces em respostas de API; rate limit simples ou justificativa se omitido; CORS coerente com o cenário de iframe.
b) **Observabilidade mínima:** Logs estruturados ou legíveis para depurar falhas de ferramentas do agente.
c) **Qualidade:** Testes automatizados em pontos críticos (pelo menos serviço de tutor ou rota de chat); linter/formatador configurados.
d) **Documentação:** README com como subir localmente, variáveis de ambiente, e fluxo embed ponta a ponta.

## Decisões de Arquitetura

### Stack
- **Framework:** FastAPI — async-ready, OpenAPI automático, integração nativa com Pydantic
- **ORM:** SQLAlchemy 2.x — flexível para SQLite (dev) e PostgreSQL (prod)
- **Auth:** JWT com `python-jose` + bcrypt — stateless, adequado para API REST e iframe embed
- **Agente de IA:** LangChain com tools + Groq (tier gratuito, modelo `llama-3.3-70b-versatile`)
- **Estratégia de conhecimento:** agente decide quando buscar fontes via HTTP (sem vector DB/embeddings)

### Autenticação
- Registro e login via `/api/v1/auth/register` e `/api/v1/auth/login`
- Token Bearer JWT com expiração configurável
- Papéis: `user` (padrão) e `admin` (proteção de rotas administrativas via `get_current_admin`)
- Rotas protegidas usam dependency injection (`get_current_user`)

## Como rodar localmente

### Pré-requisitos
- Python 3.10+

### Setup

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate

pip install -e ".[dev]"
cp .env.example .env
# Edite .env e defina SECRET_KEY com um valor seguro
```

### Executar

```bash
uvicorn app.main:app --reload
```

API disponível em `http://localhost:8000` — documentação em `/docs`.

### Testes

```bash
pytest
```

### Endpoints de autenticação

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/api/v1/auth/register` | Registrar usuário |
| POST | `/api/v1/auth/login` | Login (form: username=email, password) |
| GET | `/api/v1/auth/me` | Dados do usuário autenticado |

### Endpoints de gestão de usuários (admin)

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/v1/users` | Listar usuários |
| POST | `/api/v1/users` | Criar usuário (com papel e status) |
| GET | `/api/v1/users/{id}` | Obter usuário por ID |
| PATCH | `/api/v1/users/{id}` | Atualizar usuário |
| DELETE | `/api/v1/users/{id}` | Remover usuário |

Todas as rotas acima exigem JWT com papel `admin`.

### Endpoints de gestão de tutores (admin)

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/v1/tutors` | Listar tutores |
| POST | `/api/v1/tutors` | Criar tutor |
| GET | `/api/v1/tutors/{id}` | Obter tutor |
| PATCH | `/api/v1/tutors/{id}` | Atualizar tutor |
| POST | `/api/v1/tutors/{id}/deactivate` | Desativar tutor |
| DELETE | `/api/v1/tutors/{id}` | Remover tutor |

### Endpoints de chat (embed)

Requer header `X-Embed-Token` com valor de `EMBED_API_KEY`.

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/api/v1/chat/sessions` | Criar sessão de conversa |
| POST | `/api/v1/chat/tutors/{id}/messages` | Enviar mensagem e receber resposta do agente |

### Agente de IA (Groq — gratuito)

1. Crie uma conta em [console.groq.com](https://console.groq.com)
2. Gere uma API key e defina `GROQ_API_KEY` no `.env`
3. Para dev/testes sem API: `LLM_PROVIDER=mock`

O agente usa ferramentas LangChain para listar e buscar conteúdo das fontes configuradas no tutor.

### Observabilidade (LangSmith — opcional)

Para inspecionar cada conversa do agente (prompts, tools chamadas, latência, erros):

1. Crie conta em [smith.langchain.com](https://smith.langchain.com)
2. Gere uma API key
3. No `.env`:

```env
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_pt_...
LANGSMITH_PROJECT=dot-mvp
```

4. Reinicie o backend e converse no embed — os traces aparecem em **Tracing** no [LangSmith](https://smith.langchain.com)

Conforme a [documentação oficial](https://docs.langchain.com/langsmith/trace-with-langchain), nenhum código extra é necessário no LangChain — os `invoke()` do agente são rastreados automaticamente.

Cada run inclui tags `tutor:{id}` e metadata `session_key` para filtrar conversas.

> Este código foi produzido com auxílio de agentes de codificação (Cursor AI), conforme exigido pelo PRD.

---

## Próximos Passos (para evolução do produto em produção)

---
