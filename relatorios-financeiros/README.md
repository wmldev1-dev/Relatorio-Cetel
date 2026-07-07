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
```

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
