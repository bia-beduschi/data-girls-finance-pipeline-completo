import logging
import os
from pathlib import Path

import boto3
from botocore.exceptions import ClientError, NoCredentialsError, ParamValidationError

logger = logging.getLogger(__name__)


class S3UploadError(Exception):
    """Erro customizado para falhas na etapa de carga (Load) para o S3."""


def _validar_credenciais_aws() -> None:
    """Valida se as credenciais AWS estão configuradas no ambiente."""
    if not os.getenv("AWS_ACCESS_KEY_ID") or not os.getenv("AWS_SECRET_ACCESS_KEY"):
        raise S3UploadError(
            "Credenciais AWS não encontradas. Defina AWS_ACCESS_KEY_ID e "
            "AWS_SECRET_ACCESS_KEY como variáveis de ambiente (ou configure "
            "uma Connection do Airflow do tipo 'aws_default' em produção)."
        )


def _criar_cliente_s3():
    _validar_credenciais_aws()
    try:
        return boto3.client("s3", region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
    except Exception as erro:
        raise S3UploadError(f"Falha ao inicializar cliente S3: {erro}") from erro


def _bucket_existe(cliente_s3, nome_bucket: str) -> bool:
    try:
        cliente_s3.head_bucket(Bucket=nome_bucket)
        return True
    except ClientError as erro:
        codigo = erro.response.get("Error", {}).get("Code", "")
        if codigo in ("404", "NoSuchBucket"):
            return False
        raise S3UploadError(f"Erro ao verificar o bucket '{nome_bucket}': {erro}") from erro


def _garantir_bucket(cliente_s3, nome_bucket: str, regiao: str) -> None:
    """Cria o bucket se ele ainda não existir."""
    if _bucket_existe(cliente_s3, nome_bucket):
        logger.info("Bucket '%s' já existe.", nome_bucket)
        return

    logger.info("Bucket '%s' não encontrado. Criando...", nome_bucket)
    try:
        if regiao == "us-east-1":
            cliente_s3.create_bucket(Bucket=nome_bucket)
        else:
            cliente_s3.create_bucket(
                Bucket=nome_bucket,
                CreateBucketConfiguration={"LocationConstraint": regiao},
            )
    except ClientError as erro:
        raise S3UploadError(f"Falha ao criar o bucket '{nome_bucket}': {erro}") from erro


def enviar_diretorio_para_s3(caminho_local: str, nome_bucket: str, prefixo_s3: str = "credit_score_clean") -> int:
    """Envia recursivamente os arquivos Parquet de um diretório local para o S3."""
    logger.info("=== Iniciando Task 3: Carga no S3 ===")

    if not os.path.exists(caminho_local):
        raise S3UploadError(f"Diretório local não encontrado: {caminho_local}")

    cliente_s3 = _criar_cliente_s3()
    regiao = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

    try:
        _garantir_bucket(cliente_s3, nome_bucket, regiao)
    except NoCredentialsError as erro:
        raise S3UploadError("Credenciais AWS rejeitadas pelo boto3.") from erro

    enviados = 0
    falhas = []

    for raiz, _, arquivos in os.walk(caminho_local):
        for nome_arquivo in arquivos:
            if not nome_arquivo.endswith(".parquet"):
                continue
            caminho_completo = os.path.join(raiz, nome_arquivo)
            caminho_relativo = Path(caminho_completo).relative_to(caminho_local)
            chave_s3 = f"{prefixo_s3}/{caminho_relativo.as_posix()}"

            try:
                cliente_s3.upload_file(caminho_completo, nome_bucket, chave_s3)
                logger.info("Enviado: s3://%s/%s", nome_bucket, chave_s3)
                enviados += 1
            except (ClientError, ParamValidationError) as erro:
                logger.error("Falha ao enviar '%s': %s", chave_s3, erro)
                falhas.append(chave_s3)

    if enviados == 0:
        raise S3UploadError(f"Nenhum arquivo .parquet encontrado em '{caminho_local}'.")
    if falhas:
        raise S3UploadError(f"{len(falhas)} arquivo(s) não enviados: {falhas}")

    logger.info("=== Task 3 finalizada com sucesso: %d arquivo(s) enviados ===", enviados)
    return enviados


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    enviar_diretorio_para_s3(
        caminho_local=os.getenv("TRUSTED_DATA_DIR", "./data/processed/credit_score_clean"),
        nome_bucket=os.getenv("S3_BUCKET_NAME", "data-girls-finance-trusted-bucket"),
    )
