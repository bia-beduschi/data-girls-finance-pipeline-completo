import logging
import os
import re

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

PII_COLUMNS = ["Name", "SSN"]


class DataQualityError(Exception):
    """Erro customizado levantado quando uma regra critica de qualidade falha."""


def _strip_underscore_to_numeric(serie: pd.Series) -> pd.Series:
    """Remove underscores de uma coluna string e converte para numerico (NaN se invalido)."""
    return pd.to_numeric(serie.astype(str).str.replace("_", "", regex=False), errors="coerce")


def limpar_idade(df: pd.DataFrame) -> pd.DataFrame:
    """Idade valida: entre 1 e 100 anos. Fora disso vira NaN."""
    df["Age"] = _strip_underscore_to_numeric(df["Age"])
    df.loc[(df["Age"] < 1) | (df["Age"] > 100), "Age"] = np.nan
    return df


def limpar_renda_anual(df: pd.DataFrame) -> pd.DataFrame:
    """Converte Annual_Income para numerico e remove valores negativos."""
    df["Annual_Income"] = _strip_underscore_to_numeric(df["Annual_Income"])
    df.loc[df["Annual_Income"] < 0, "Annual_Income"] = np.nan
    return df


def limpar_num_of_loan(df: pd.DataFrame) -> pd.DataFrame:
    """Numero de emprestimos valido: entre 0 e 10."""
    df["Num_of_Loan"] = _strip_underscore_to_numeric(df["Num_of_Loan"])
    df.loc[(df["Num_of_Loan"] < 0) | (df["Num_of_Loan"] > 10), "Num_of_Loan"] = np.nan
    return df


def limpar_outstanding_debt(df: pd.DataFrame) -> pd.DataFrame:
    """Converte Outstanding_Debt para numerico; divida negativa nao faz sentido."""
    df["Outstanding_Debt"] = _strip_underscore_to_numeric(df["Outstanding_Debt"])
    df.loc[df["Outstanding_Debt"] < 0, "Outstanding_Debt"] = np.nan
    return df


def limpar_contas_cartoes_e_juros(df: pd.DataFrame) -> pd.DataFrame:
    """
    Num_Bank_Accounts, Num_Credit_Card e Interest_Rate chegam como numero,
    mas contem outliers extremos (ex: milhares de contas, juros > 5000%).
    Limites superiores derivados por IQR (Q3 + 1.5*IQR) na analise
    exploratoria do dataset real.
    """
    limites_superiores = {"Num_Bank_Accounts": 10, "Num_Credit_Card": 11, "Interest_Rate": 34}
    for coluna, limite in limites_superiores.items():
        df[coluna] = pd.to_numeric(df[coluna], errors="coerce")
        df.loc[(df[coluna] < 0) | (df[coluna] > limite), coluna] = np.nan
    return df


def limpar_delay_from_due_date(df: pd.DataFrame) -> pd.DataFrame:
    """Atrasos negativos nao fazem sentido de negocio; viram 0 (clip)."""
    df["Delay_from_due_date"] = pd.to_numeric(df["Delay_from_due_date"], errors="coerce")
    df["Delay_from_due_date"] = df["Delay_from_due_date"].clip(lower=0)
    return df


def limpar_num_of_delayed_payment(df: pd.DataFrame) -> pd.DataFrame:
    """Contagem valida de pagamentos atrasados: entre 0 e 30."""
    df["Num_of_Delayed_Payment"] = _strip_underscore_to_numeric(df["Num_of_Delayed_Payment"])
    df.loc[
        (df["Num_of_Delayed_Payment"] < 0) | (df["Num_of_Delayed_Payment"] > 30),
        "Num_of_Delayed_Payment",
    ] = np.nan
    return df


def limpar_changed_credit_limit(df: pd.DataFrame) -> pd.DataFrame:
    """Remove placeholder '_', converte, arredonda e descarta valores > 100."""
    df["Changed_Credit_Limit"] = _strip_underscore_to_numeric(df["Changed_Credit_Limit"]).round(2)
    df.loc[df["Changed_Credit_Limit"] > 100, "Changed_Credit_Limit"] = np.nan
    return df


def limpar_num_credit_inquiries(df: pd.DataFrame) -> pd.DataFrame:
    """Numero de consultas de credito valido: entre 0 e 25."""
    df["Num_Credit_Inquiries"] = pd.to_numeric(df["Num_Credit_Inquiries"], errors="coerce")
    df.loc[
        (df["Num_Credit_Inquiries"] < 0) | (df["Num_Credit_Inquiries"] > 25), "Num_Credit_Inquiries"
    ] = np.nan
    return df


def limpar_total_emi_per_month(df: pd.DataFrame) -> pd.DataFrame:
    """EMI mensal valido: entre 0 e 10.000."""
    df["Total_EMI_per_month"] = pd.to_numeric(df["Total_EMI_per_month"], errors="coerce")
    df.loc[
        (df["Total_EMI_per_month"] < 0) | (df["Total_EMI_per_month"] > 10000), "Total_EMI_per_month"
    ] = np.nan
    return df


def limpar_amount_invested_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """Investimento mensal negativo nao faz sentido de negocio."""
    df["Amount_invested_monthly"] = _strip_underscore_to_numeric(df["Amount_invested_monthly"])
    df.loc[df["Amount_invested_monthly"] < 0, "Amount_invested_monthly"] = np.nan
    return df


def limpar_monthly_balance(df: pd.DataFrame) -> pd.DataFrame:
    """Remove valores absurdos (ex: -3.3e26)."""
    df["Monthly_Balance"] = _strip_underscore_to_numeric(df["Monthly_Balance"])
    df.loc[df["Monthly_Balance"] < -10000, "Monthly_Balance"] = np.nan
    return df


def limpar_monthly_inhand_salary(df: pd.DataFrame) -> pd.DataFrame:
    """Converte para numerico; ausencias ficam NaN para tratamento posterior."""
    df["Monthly_Inhand_Salary"] = pd.to_numeric(df["Monthly_Inhand_Salary"], errors="coerce")
    return df


def limpar_credit_utilization_ratio(df: pd.DataFrame) -> pd.DataFrame:
    """Converte para numerico (coluna ja numericamente consistente no dataset bruto)."""
    df["Credit_Utilization_Ratio"] = pd.to_numeric(df["Credit_Utilization_Ratio"], errors="coerce")
    return df


def converter_credit_history_age(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converte 'X Years and Y Months' em uma coluna numerica unica
    (Credit_History_Age_Months). A coluna textual original e removida.
    """

    def _parse(valor):
        if pd.isna(valor):
            return np.nan
        anos = re.search(r"(\d+)\s+Years", str(valor))
        meses = re.search(r"(\d+)\s+Months", str(valor))
        total = (int(anos.group(1)) if anos else 0) * 12 + (int(meses.group(1)) if meses else 0)
        return total

    df["Credit_History_Age_Months"] = df["Credit_History_Age"].apply(_parse)
    df = df.drop(columns=["Credit_History_Age"])
    return df


def padronizar_categoricas_com_placeholder(df: pd.DataFrame) -> pd.DataFrame:
    """Substitui placeholders conhecidos (identificados na EDA) por 'Unknown'."""
    mapeamentos = {"Occupation": "_______", "Credit_Mix": "_", "Payment_Behaviour": "!@9#%8"}
    for coluna, placeholder in mapeamentos.items():
        df[coluna] = df[coluna].replace(placeholder, "Unknown")
    return df


def padronizar_payment_of_min_amount(df: pd.DataFrame) -> pd.DataFrame:
    """'NM' ("Not Mentioned") e tratado como equivalente a 'No'."""
    df["Payment_of_Min_Amount"] = df["Payment_of_Min_Amount"].replace("NM", "No")
    return df


def padronizar_credit_score(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza a coluna target: remove espacos e uniformiza caixa alta."""
    df["Credit_Score"] = df["Credit_Score"].astype(str).str.strip().str.upper()
    return df


def remover_colunas_pii(df: pd.DataFrame) -> pd.DataFrame:
    """Remove colunas de dado pessoal identificavel (Name, SSN) - conformidade LGPD."""
    colunas_existentes = [c for c in PII_COLUMNS if c in df.columns]
    if colunas_existentes:
        logger.info("Removendo colunas de PII: %s", colunas_existentes)
        df = df.drop(columns=colunas_existentes)
    return df


def remover_duplicatas(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicatas de Customer_ID + Month (salvaguarda defensiva de idempotencia)."""
    linhas_antes = len(df)
    df = df.drop_duplicates(subset=["Customer_ID", "Month"])
    removidas = linhas_antes - len(df)
    if removidas > 0:
        logger.warning("Removidas %d linha(s) duplicada(s) (Customer_ID + Month).", removidas)
    return df


def validar_qualidade_dados(df: pd.DataFrame) -> None:
    """Executa checagens criticas de qualidade (Fail-Fast) antes da gravacao."""
    if len(df) == 0:
        raise DataQualityError("Dataset resultante esta vazio. Abortando pipeline.")

    ids_nulos = int(df["Customer_ID"].isna().sum())
    logger.info("Customer_ID nulos encontrados: %d", ids_nulos)
    if ids_nulos > 0:
        raise DataQualityError(f"Falha critica de qualidade: {ids_nulos} registros com Customer_ID nulo.")

    rendas_negativas = int((df["Annual_Income"] < 0).sum())
    if rendas_negativas > 0:
        raise DataQualityError(
            f"Falha critica de qualidade: {rendas_negativas} registros com renda negativa residual."
        )

    colunas_pii_presentes = [c for c in PII_COLUMNS if c in df.columns]
    if colunas_pii_presentes:
        raise DataQualityError(
            f"Falha critica de conformidade (LGPD): colunas de PII ainda presentes: {colunas_pii_presentes}."
        )

    duplicatas = int(df.duplicated(subset=["Customer_ID", "Month"]).sum())
    if duplicatas > 0:
        raise DataQualityError(
            f"Falha critica de qualidade: {duplicatas} combinacao(oes) de Customer_ID+Month duplicada(s)."
        )

    scores_invalidos = int((~df["Credit_Score"].isin(["GOOD", "STANDARD", "POOR"])).sum())
    logger.info("Registros com Credit_Score fora do dominio esperado: %d", scores_invalidos)

    logger.info("Validacao de qualidade concluida com sucesso. Total de linhas: %d", len(df))


def transformar_dados_credit_score(caminho_raw: str, caminho_trusted: str) -> str:
    """
    Funcao principal da Task 2: le o CSV bruto, aplica todas as regras de
    limpeza, remove PII, deduplica, valida qualidade e persiste em Parquet
    particionado por Credit_Score.
    """
    logger.info("Iniciando Task 2 - Transformacao e Validacao (Pandas + PyArrow)")

    caminho_arquivo = os.path.join(caminho_raw, "train.csv")
    if not os.path.exists(caminho_arquivo):
        raise FileNotFoundError(f"Arquivo nao encontrado: {caminho_arquivo}")

    df = pd.read_csv(caminho_arquivo, low_memory=False)

    logger.info("Aplicando regras de limpeza em todas as colunas sujas conhecidas...")
    df = limpar_idade(df)
    df = limpar_renda_anual(df)
    df = limpar_monthly_inhand_salary(df)
    df = limpar_contas_cartoes_e_juros(df)
    df = limpar_num_of_loan(df)
    df = limpar_delay_from_due_date(df)
    df = limpar_num_of_delayed_payment(df)
    df = limpar_changed_credit_limit(df)
    df = limpar_num_credit_inquiries(df)
    df = limpar_outstanding_debt(df)
    df = limpar_credit_utilization_ratio(df)
    df = limpar_total_emi_per_month(df)
    df = limpar_amount_invested_monthly(df)
    df = limpar_monthly_balance(df)
    df = converter_credit_history_age(df)
    df = padronizar_categoricas_com_placeholder(df)
    df = padronizar_payment_of_min_amount(df)
    df = padronizar_credit_score(df)

    logger.info("Removendo colunas de PII (LGPD)...")
    df = remover_colunas_pii(df)

    logger.info("Aplicando salvaguarda de deduplicacao...")
    df = remover_duplicatas(df)

    logger.info("Executando validacao de qualidade (Fail-Fast)...")
    validar_qualidade_dados(df)

    logger.info("Gravando dados trusted em Parquet particionado em: %s", caminho_trusted)
    os.makedirs(caminho_trusted, exist_ok=True)
    df.to_parquet(
        caminho_trusted,
        engine="pyarrow",
        partition_cols=["Credit_Score"],
        index=False,
    )

    logger.info("Task 2 concluida com sucesso.")
    return caminho_trusted


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    transformar_dados_credit_score(
        caminho_raw="./data/raw",
        caminho_trusted="./data/processed/credit_score_clean",
    )
