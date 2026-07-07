# Relatórios Financeiros CETEL

Aplicação reorganizada em Backend FastAPI e Frontend Streamlit. O Streamlit atua apenas como interface e toda regra de negócio, importação SQL e acesso ao MySQL ficam no backend.

## Estrutura

```text
relatorios-financeiros/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── database/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── utils/
│   │   └── main.py
│   ├── tests/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── pages/
│   ├── components/
│   ├── services/
│   │   └── api_client.py
│   ├── utils/
│   ├── assets/
│   ├── app.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── database/
│   ├── init.sql
│   └── imports/
├── docker/
│   ├── mysql/
│   ├── backend/
│   └── frontend/
├── docker-compose.yml
└── README.md
```

## Executar sem Docker

Crie o banco MySQL 8 e copie os arquivos de ambiente:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Configure `backend/.env`:

```env
DATABASE_URL=mysql+pymysql://usuario:senha@localhost:3306/relatorios_financeiros?charset=utf8mb4
SECRET_KEY=sua-chave
ADMIN_NAME=Administrador
ADMIN_EMAIL=admin@cetel.local
ADMIN_PASSWORD=<senha-inicial>
ADMIN_RESET_PASSWORD_ON_STARTUP=false
JWT_SECRET_KEY=troque-esta-chave
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=480
```

Troque `JWT_SECRET_KEY` e a senha do admin antes de usar em produção.

Instale e execute o backend:

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Em outro terminal, execute o frontend:

```bash
cd frontend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Executar com Docker

O `docker-compose.yml` lê as variáveis do arquivo `.env` na raiz do projeto:

```env
MYSQL_ROOT_PASSWORD=root123
MYSQL_DATABASE=relatorios_financeiros
MYSQL_USER=relatorios_user
MYSQL_PASSWORD=relatorios123
DATABASE_URL=mysql+pymysql://relatorios_user:relatorios123@mysql:3306/relatorios_financeiros
API_URL=http://backend:8000
ADMIN_NAME=Administrador
ADMIN_EMAIL=admin@cetel.local
ADMIN_PASSWORD=<senha-inicial>
ADMIN_RESET_PASSWORD_ON_STARTUP=false
JWT_SECRET_KEY=troque-esta-chave
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=480
```

```bash
docker compose up --build
```

O frontend usa bind mount em `./frontend:/app/frontend`. Em desenvolvimento,
alterações em arquivos Python do frontend são refletidas no container sem
rebuild da imagem; o Streamlit roda com `server.runOnSave=true`.

Use rebuild sem cache quando mudar dependências, Dockerfile ou quiser recriar
todo o ambiente:

```bash
./scripts/rebuild.sh
```

Para verificar os arquivos efetivamente montados no container:

```bash
./scripts/check_frontend.sh
```

Scripts úteis:

- `./scripts/logs.sh`: acompanha logs do Streamlit.
- `./scripts/shell_frontend.sh`: abre shell no container do frontend.

Acessos:

- API: `http://localhost:8000`
- Documentação OpenAPI: `http://localhost:8000/docs`
- Streamlit: `http://localhost:8501`
- MySQL: `localhost:3306`

## Banco de Dados

O compose usa MySQL 8.4 e executa `database/init.sql` na primeira criação do volume. As tabelas da aplicação (`competences`, `import_batches`, `financial_entries`) são criadas pelo SQLAlchemy quando os serviços são usados.
Também é criada a tabela `users` para autenticação.
O RBAC cria ainda `roles`, `permissions`, `user_roles` e
`role_permissions`.

Para criar manualmente:

```sql
CREATE DATABASE relatorios_financeiros
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

## Importação de Dados

Fluxo atual:

1. Acesse a página **Importação Mensal** no Streamlit.
2. Informe a competência no formato `YYYY-MM`.
3. Envie um arquivo `.sql` ou um arquivo bruto tabulado `.txt`, `.tsv`, `.csv`
   ou sem extensão.
4. O frontend chama `POST /api/importacoes`.
5. O backend salva o arquivo, registra o lote e processa via `POST /api/importacoes/{id}/processar`.
6. O backend escolhe o parser pelo tipo do arquivo:
   - `.sql`: extrai comandos `INSERT`.
   - texto bruto: detecta a seção `COLUNAS`, lê as linhas tabuladas e
     normaliza datas e valores brasileiros.
7. Os campos conhecidos são mapeados e gravados em `financial_entries`.

O Streamlit não acessa o banco diretamente.

Arquivo real validado:

```text
database/imports/relatorios_06_2026_mysql.sql
```

Resultado validado para a competência `2026-06`:

- 308 lançamentos
- Total de R$ 179.099,49
- 79 fornecedores
- 78 categorias
- 3 usuários

### Importação Bruta

Arquivos brutos como `Relatorios 05-2026 - Bruto` devem conter a seção
`COLUNAS` seguida por linhas tabuladas. O mapeamento aplicado é:

- `Lançamento` ou `Data` -> `entry_date`
- `Data` ou `Data Crédito` -> `payment_date`
- `Exec de Baixa` -> `created_at_source`
- `Número` -> `document_number`
- `Histórico` -> `transaction_type`, `service` e, quando aplicável, `description`
- `Classificador` -> `category` e `description`
- `Nome` -> `supplier`
- `Tipo Doc` -> `supplier_type`
- `Valor` -> `amount`
- `Usuários` -> `user_name`

Valores como `R$ 4.550,00` são gravados como `4550.00`. Datas nos formatos
`02/05/2026` e `02/05/2026 11:09:24` são aceitas.

## Endpoints Principais

- `GET /api/health`
- `GET /health`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/auth/logout`
- `GET /api/importacoes`
- `POST /api/importacoes`
- `GET /api/importacoes/{id}`
- `POST /api/importacoes/{id}/processar`
- `POST /api/importacoes/{id}/reprocessar`
- `DELETE /api/importacoes/{id}`
- `GET /api/lancamentos`
- `GET /api/lancamentos/paginado`
- `GET /api/lancamentos/competencias`
- `GET /api/lancamentos/competencias/{id}`
- `GET /api/fornecedores`
- `GET /api/categorias`
- `GET /api/dashboard`
- `GET /api/dashboard/financeiro`
- `GET /api/comparativo/mensal`
- `GET /api/usuarios`
- `GET /api/diagnostico/importacoes/{id}`

Os endpoints financeiros são protegidos por JWT Bearer token. Permanecem públicos:
`GET /health`, `GET /api/health`, `/docs`, `/openapi.json` e `POST /api/auth/login`.

### Autenticação

No startup do backend, o projeto garante automaticamente que exista um usuário
administrador ativo com papel `ADMIN`, usando `ADMIN_NAME`, `ADMIN_EMAIL` e
`ADMIN_PASSWORD`. Se `ADMIN_EMAIL` ou `ADMIN_PASSWORD` estiverem vazios, nenhum
usuário é criado e o backend registra apenas um aviso.

Quando o usuário já existe, o backend reaproveita o cadastro, garante
`is_active=true`, `is_admin=true` e associa o papel `ADMIN`. A senha não é
sobrescrita por padrão. Para redefinir a senha no startup, use
`ADMIN_RESET_PASSWORD_ON_STARTUP=true`.

As credenciais de desenvolvimento ficam documentadas apenas em
`backend/.env.example`.

No servidor, para garantir criação ou redefinição temporária do admin, configure
o `.env`:

```env
ADMIN_NAME=Administrador
ADMIN_EMAIL=admin@cetel.local
ADMIN_PASSWORD=admin123
ADMIN_RESET_PASSWORD_ON_STARTUP=true
```

Depois rode:

```bash
git pull
docker compose down
docker compose up -d --build
```

Após conseguir login, por segurança altere:

```env
ADMIN_RESET_PASSWORD_ON_STARTUP=false
```

E suba novamente:

```bash
docker compose up -d --build
```

Para testar na API docs:

1. Abra `http://localhost:8000/docs`.
2. Execute `POST /api/auth/login` com email e senha do admin.
3. Copie o `access_token`.
4. Clique em **Authorize** e informe `Bearer <access_token>`.
5. Execute um endpoint protegido, por exemplo `GET /api/dashboard/executivo`.

No frontend Streamlit, acessar `http://localhost:8501` sem token mostra apenas a
tela de login. Após o login, a sidebar exibe CETEL, Relatórios Financeiros, o
usuário logado e o botão **SAIR**, que limpa a sessão local.

### RBAC: Papéis e Permissões

O controle de acesso usa papéis e permissões granulares no formato
`modulo.acao`. As permissões ficam associadas aos papéis, e os usuários recebem
um ou mais papéis.

Papéis padrão criados automaticamente:

- `ADMIN`: acesso completo a todas as permissões.
- `FINANCEIRO`: acesso operacional financeiro, incluindo dashboard,
  comparativo, fornecedores, serviços, categorias, dados financeiros,
  importação, diagnóstico e exportações. Não gerencia usuários.
- `CONSULTA`: acesso somente de leitura a dashboard, comparativo,
  fornecedores, serviços, categorias e dados financeiros. Não importa, não
  exporta e não acessa diagnóstico.

Módulos disponíveis:

- `dashboard`
- `comparativo`
- `fornecedores`
- `servicos`
- `categorias`
- `dados_financeiros`
- `importacao`
- `diagnostico`
- `usuarios`
- `configuracoes`

Ações disponíveis em cada módulo:

- `view`
- `create`
- `update`
- `delete`
- `export`

Exemplos de permissões:

- `dashboard.view`
- `dashboard.export`
- `fornecedores.export`
- `importacao.create`
- `usuarios.update`

Endpoint para consultar as permissões do usuário autenticado:

```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/auth/permissions
```

Resposta:

```json
{
  "roles": [
    {"name": "ADMIN", "description": "Acesso administrativo completo.", "is_system": true}
  ],
  "permissions": [
    {"module": "dashboard", "action": "view", "code": "dashboard.view"}
  ]
}
```

Para adicionar um novo módulo, inclua o nome em `MODULES` em
`backend/app/services/rbac_service.py`. O seed cria automaticamente as cinco
ações padrão para o módulo.

Para adicionar uma nova permissão a um papel padrão, ajuste
`ROLE_DEFINITIONS` em `backend/app/services/rbac_service.py`. O seed é
idempotente e reaplica as associações no startup.

No backend, proteja endpoints com:

```python
from fastapi import Depends
from app.core.permissions import require_permission

@router.get("/exemplo", dependencies=[Depends(require_permission("dashboard.view"))])
def exemplo():
    ...
```

No frontend, use os helpers de `frontend/components/permissions.py`:

```python
from components.permissions import can, can_any, protected_component
```

A navegação do Streamlit é montada dinamicamente por permissão. Botões e ações
como exportação e importação também são ocultados quando o usuário não possui a
permissão exigida.

### Painel Administrativo

O menu **ADMINISTRAÇÃO** aparece somente para usuários com `usuarios.view`.
Nesta sprint, o módulo completo é **Usuários**. Os demais itens ficam
preparados como placeholders:

- Usuários
- Papéis
- Permissões
- Auditoria
- Configurações

Permissões usadas pela Gestão de Usuários:

- `usuarios.view`: listar, filtrar e consultar usuários.
- `usuarios.create`: criar novo usuário.
- `usuarios.update`: editar dados, papéis, status e senha.
- `usuarios.delete`: exclusão lógica.

Endpoints administrativos:

- `GET /api/users`
- `GET /api/users/{id}`
- `POST /api/users`
- `PUT /api/users/{id}`
- `PATCH /api/users/{id}/password`
- `DELETE /api/users/{id}`

Filtros de listagem:

- `nome`
- `email`
- `ativo`
- `papel`
- `page`
- `page_size`
- `order_by`: `nome`, `email` ou `created_at`

Regras aplicadas:

- Senhas nunca são retornadas.
- Senha mínima de 8 caracteres.
- Email único.
- Exclusão é lógica (`is_active=False`).
- Não é permitido desativar ou remover a si mesmo.
- Não é permitido remover ou desativar o último `ADMIN`.
- Usuários podem ter múltiplos papéis entre `ADMIN`, `FINANCEIRO` e `CONSULTA`.

Campos administrativos preparados:

- `last_login_at`
- `created_by_id`
- `updated_by_id`
- `failed_login_attempts`
- `first_failed_login_at`
- `locked_until`
- tabela `user_audit_logs`

O login atualiza `last_login_at` e bloqueia temporariamente usuário existente
após 5 tentativas inválidas dentro de 15 minutos.

Exemplo de paginação:

```bash
curl "http://localhost:8000/api/lancamentos/paginado?limit=100&offset=0"
```

## Comparativo Mensal

A tela **Comparativo Mensal** permite comparar duas competências, por exemplo
`2026-06` x `2026-07`, exibindo totais, diferença em reais, diferença
percentual e rankings por fornecedor, serviço e categoria.

Endpoint:

```bash
curl "http://localhost:8000/api/comparativo/mensal?competencia_base=2026-06&competencia_comparacao=2026-07"
```

Campos principais retornados:

- `total_base`
- `total_comparacao`
- `diferenca_valor`
- `diferenca_percentual`
- `status`: `aumento`, `reducao` ou `estavel`
- `total_lancamentos_base`
- `total_lancamentos_comparacao`
- `fornecedores_maior_aumento`
- `fornecedores_maior_reducao`
- `servicos_maior_aumento`
- `servicos_maior_reducao`
- `categorias_maior_aumento`
- `categorias_maior_reducao`

Cada item dos rankings contém `nome`, `valor_base`, `valor_comparacao`,
`diferenca_valor`, `diferenca_percentual` e `status`.

## Desenvolvimento

Backend:

```bash
cd backend
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
streamlit run app.py
```

Variáveis do frontend:

```env
API_URL=http://localhost:8000
```
