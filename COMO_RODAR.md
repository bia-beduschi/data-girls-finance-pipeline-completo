# Como Rodar — Guia Rápido

Duas formas de rodar, da mais simples para a mais completa.

## Opção A — Rodar a lógica localmente (sem Docker)

```bash
cd data-girls-finance-pipeline-completo
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac

pip install -r requirements.txt
pytest -v
```

Para rodar a transformação em cima do `train.csv` já presente em `data/raw/`:

```bash
python scripts/transform/pandas_cleaning.py
```

O resultado (Parquet particionado por `Credit_Score`) aparece em
`data/processed/credit_score_clean/`.

## Opção B — Pipeline completo automatizado (Airflow + Docker)

### Pré-requisitos
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado e aberto.
- Conta no [Kaggle](https://www.kaggle.com/) com API Token (opcional — sem
  isso o pipeline usa o CSV já presente em `data/raw/`).
- Conta AWS com um bucket S3 e um usuário IAM com permissão de leitura/escrita.

### Passo a passo

1. Configure as variáveis de ambiente:
   ```bash
   cp .env.example .env
   ```
   Preencha o `.env` com suas credenciais AWS (obrigatórias para a Task 3) e,
   opcionalmente, do Kaggle.

2. Suba o ambiente:
   ```bash
   docker compose up airflow-init
   docker compose up -d
   ```

3. Acesse `http://localhost:8080` (login `admin` / `admin`).

4. Ative a DAG `dag_credit_score_pipeline` e dispare manualmente, ou espere
   o agendamento diário (`@daily`).

5. Confira as 3 tasks (`extrair_dados_kaggle` → `transformar_dados_pandas` →
   `carregar_dados_s3`) ficarem verdes na aba Graph/Grid.

6. Confira o resultado no console da AWS → S3 → bucket configurado → pasta
   `credit_score_clean/` com subpastas `Credit_Score=GOOD/`,
   `Credit_Score=STANDARD/`, `Credit_Score=POOR/`.

### Para parar tudo

```bash
docker compose down
```

## Bônus — dashboard

Dê duplo clique em `docs/dashboard/dashboard_credit_score.html` para abrir no
navegador. O arquivo `docs/dashboard/Dashboard_Credit_Score_PowerBI.pbix` tem
o mesmo painel montado no Power BI Desktop.

## Problemas comuns

- **`ModuleNotFoundError`**: confirme que o ambiente virtual está ativado
  antes de rodar `pip install` e `pytest`.
- **Erro de credenciais AWS/Kaggle ao rodar localmente**: os testes usam
  `moto` (S3 simulado) e o extrator cai para o CSV local em `data/raw/`,
  então isso não impede rodar `pytest -v`.
- **Porta 8080 já em uso**: pare o serviço que está usando a porta ou altere
  o mapeamento em `docker-compose.yaml`.
