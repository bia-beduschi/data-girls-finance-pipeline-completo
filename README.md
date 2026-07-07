# 💰 Data Girls Finance — Pipeline ETL de Credit Score

Pipeline de dados end-to-end que extrai, transforma e carrega o dataset
[Credit Score Classification](https://www.kaggle.com/datasets/parisrohan/credit-score-classification)
do Kaggle, orquestrado por Apache Airflow, com processamento em Python/Pandas e
armazenamento final em um Data Lake no Amazon S3.

Projeto final do Bootcamp [RE]Start — Trilha de Engenharia de Dados, para a
fintech fictícia **Data Girls Finance**.

---

## 🏗️ Arquitetura

```
Kaggle API / CSV local
        │  Task 1 — extrair_dados_kaggle
        ▼
   Raw Zone (data/raw/*.csv)
        │  Task 2 — transformar_dados_pandas
        │  (limpeza de 17 colunas sujas, remoção de PII,
        │   deduplicação, validação Fail-Fast)
        ▼
 Trusted Zone (Parquet particionado por Credit_Score)
        │  Task 3 — carregar_dados_s3
        ▼
   Amazon S3 (Data Lake)
```

Todo o fluxo é orquestrado por uma **DAG do Apache Airflow**, rodando em
containers Docker, com três tasks sequenciais e retries automáticos:

| Task | Responsabilidade | Módulo |
|---|---|---|
| `extrair_dados_kaggle` | Baixa via API do Kaggle (ou usa CSV local) | `scripts/extract/kaggle_extractor.py` |
| `transformar_dados_pandas` | Limpeza, padronização e validação de qualidade (Fail-Fast) | `scripts/transform/pandas_cleaning.py` |
| `carregar_dados_s3` | Upload do Parquet particionado para o Data Lake (S3) | `scripts/load/s3_uploader.py` |

## 🛠️ Stack Técnica

- **Extração**: Python + API oficial do Kaggle (com fallback para CSV local)
- **Transformação**: Python + Pandas + PyArrow
- **Orquestração**: Apache Airflow 2.9 (LocalExecutor)
- **Armazenamento**: Amazon S3 (Parquet, particionado por `Credit_Score`)
- **Containerização**: Docker + Docker Compose
- **Testes**: pytest, pytest-mock, moto (mock de AWS) — 30+ testes cobrindo as 3 tasks
- **Bônus**: dashboard HTML + CSVs prontos para Power BI (`docs/dashboard/`)

## 📁 Estrutura do Repositório

```
data-girls-finance-pipeline/
├── dags/
│   └── dag_credit_score_pipeline.py   # Orquestração das 3 tasks (Airflow)
├── scripts/
│   ├── extract/kaggle_extractor.py    # Task 1
│   ├── transform/pandas_cleaning.py   # Task 2
│   └── load/s3_uploader.py            # Task 3
├── tests/
│   ├── test_extract.py
│   ├── test_transform_pandas.py
│   └── test_load.py
├── docs/
│   ├── business_questions.md          # Respostas às perguntas norteadoras
│   └── dashboard/                     # Bônus: painel de métricas
├── data/raw/                          # train.csv / test.csv (não versionado)
├── Dockerfile
├── docker-compose.yaml
├── requirements.txt
├── pytest.ini
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```

## 🚀 Como Rodar

Veja o guia completo em **`COMO_RODAR.md`** — resumo rápido:

```bash
# 1. Testar a lógica localmente (sem Docker/Airflow), em segundos
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest -v

# 2. Rodar o pipeline completo automatizado (Airflow + Docker)
cp .env.example .env   # preencha com suas credenciais
docker compose up airflow-init
docker compose up -d
# Acesse http://localhost:8080 (login: admin / admin) e ative a DAG
```

## 📊 Sobre o Dataset

[Credit Score Classification](https://www.kaggle.com/datasets/parisrohan/credit-score-classification)
— dataset sintético com informações demográficas, financeiras e de
comportamento de pagamento de clientes, usado para prever a classe de
score de crédito (`Good`, `Standard`, `Poor`). O dataset bruto contém 17
colunas com inconsistências propositais (idades negativas, valores
numéricos com underscores, placeholders textuais), todas tratadas
explicitamente na Task 2.

## 📜 Respostas às Perguntas Norteadoras de Negócio

Ver [`docs/business_questions.md`](docs/business_questions.md).

## 🎁 Bônus — Painel de Métricas

Ver [`docs/dashboard/`](docs/dashboard/) — dashboard HTML pronto + dados
para Power BI, com total de clientes, distribuição por Credit_Score e
renda mensal por categoria.

## 👩‍💻 Autora

Beatriz Beduschi Tai-ao — Projeto final da Trilha de Engenharia de Dados, Bootcamp [RE]Start.
