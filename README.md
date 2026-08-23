# cobranca-api

API de cobrança construída com FastAPI, SQLAlchemy 2.0, PostgreSQL e Clean Architecture.

## Status

Em desenvolvimento avançado. A fundação de identidade, autenticação JWT, RBAC, administração de usuários, roles e permissions, migrations, Docker/Compose e testes automatizados já está implementada.

## Stack

- Python 3.12
- FastAPI
- Pydantic v2
- SQLAlchemy 2.0
- Alembic
- PostgreSQL 17
- Docker e Docker Compose
- JWT access/refresh

## Arquitetura

O projeto mantém separação explícita de responsabilidades:

- `app/models`: entidades e regras de domínio.
- `app/repositories`: acesso e persistência no banco.
- `app/services`: casos de uso e regras de aplicação, sem `HTTPException`.
- `app/routers`: camada HTTP, sem regras de negócio.
- `app/schemas`: contratos Pydantic de entrada e saída.
- `app/core`: configuração, segurança, JWT e logging.
- `app/database`: sessão SQLAlchemy e migrations Alembic.
- `app/dependencies.py`: composição de dependências e DI.

A persistência usa Repository Pattern e Unit of Work. O schema do banco é gerenciado exclusivamente por Alembic; a aplicação não usa `create_all()`.

## Configuração

Crie o arquivo `.env` a partir do exemplo:

```bash
cp .env.example .env
```

Configure pelo menos as credenciais do PostgreSQL e uma chave JWT segura.

## Executar com Docker Compose

```bash
docker compose up --build
```

A API ficará disponível em `http://localhost:8000`.

No startup, o container da API aguarda o PostgreSQL ficar saudável, executa `alembic upgrade head` e inicia o Uvicorn.

### Criar o administrador inicial

Depois que a API e o PostgreSQL estiverem em execução, inicialize o primeiro administrador pelo próprio container da API:

```bash
docker compose exec api python -m app.cli.bootstrap_admin \
  --email admin@example.com \
  --password 'troque-por-uma-senha-segura'
```

O comando é idempotente: pode ser executado novamente para completar as associações RBAC já existentes. Ele cria ou reutiliza o usuário informado, o role `admin` e as permissões administrativas atuais de usuários, roles e permissions.

Em execução local, fora do Docker, use o mesmo CLI após aplicar as migrations e configurar o `.env`:

```bash
python -m app.cli.bootstrap_admin \
  --email admin@example.com \
  --password 'troque-por-uma-senha-segura'
```

Após o bootstrap, use esse usuário em `POST /api/v1/auth/login` para obter os tokens JWT.

Health check:

```text
GET /api/v1/health
```

Documentação OpenAPI:

```text
GET /docs
```

## Principais endpoints

### Autenticação

```text
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
```

### Usuários

```text
GET    /api/v1/users/me
GET    /api/v1/users
POST   /api/v1/users
GET    /api/v1/users/{user_id}
PATCH  /api/v1/users/{user_id}
DELETE /api/v1/users/{user_id}
GET    /api/v1/users/{user_id}/roles
POST   /api/v1/users/{user_id}/roles/{role_id}
DELETE /api/v1/users/{user_id}/roles/{role_id}
```

### Roles

```text
GET    /api/v1/roles
POST   /api/v1/roles
GET    /api/v1/roles/{role_id}
PATCH  /api/v1/roles/{role_id}
DELETE /api/v1/roles/{role_id}
GET    /api/v1/roles/{role_id}/permissions
PUT    /api/v1/roles/{role_id}/permissions/{permission_id}
DELETE /api/v1/roles/{role_id}/permissions/{permission_id}
```

### Permissions

```text
GET    /api/v1/permissions
POST   /api/v1/permissions
GET    /api/v1/permissions/{permission_id}
PATCH  /api/v1/permissions/{permission_id}
DELETE /api/v1/permissions/{permission_id}
```

Os endpoints administrativos são protegidos por autenticação Bearer e permissões RBAC.

## Testes

Instale as dependências:

```bash
python -m pip install -r requirements.txt
```

Execute a suíte:

```bash
python -m unittest discover -v
```

Para validar sintaxe/importação:

```bash
python -m compileall -q app tests
```

Os testes de integração dependem de PostgreSQL com as migrations aplicadas. O workflow de testes do GitHub Actions provisiona PostgreSQL 17 e executa `alembic upgrade head` antes da suíte.

## Migrations

Aplicar todas as migrations:

```bash
alembic upgrade head
```

Validar se os models estão sincronizados com as migrations:

```bash
alembic check
```

O workflow de migration valida automaticamente o ciclo completo:

```text
upgrade head -> downgrade base -> upgrade head -> alembic check
```

## Segurança

- Senhas são armazenadas somente como hash com salt aleatório.
- Autenticação usa access e refresh tokens JWT.
- Logout persiste a revogação do `jti` do token.
- Tokens revogados não podem ser reutilizados.
- Usuários inativos não podem autenticar ou renovar tokens.
- Autorização administrativa é controlada por RBAC.
- Respostas de usuário não expõem `password_hash`.

## Convenções

- PEP8 e type hints.
- Conventional Commits.
- Regras de domínio em models/services conforme responsabilidade.
- Banco acessado somente através de repositories.
- Services independentes de HTTP.
- Routers finos, responsáveis apenas pela camada HTTP.
