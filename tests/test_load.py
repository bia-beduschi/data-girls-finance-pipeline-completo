import os

import boto3
import pytest
from moto import mock_aws

from scripts.load.s3_uploader import (
    S3UploadError,
    _validar_credenciais_aws,
    enviar_diretorio_para_s3,
)

BUCKET_TESTE = "data-girls-finance-bucket-teste"


@pytest.fixture(autouse=True)
def credenciais_aws_fake(monkeypatch):
    """Garante credenciais AWS fake para todos os testes (nunca reais)."""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "fake-access-key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "fake-secret-key")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")


class TestValidarCredenciaisAws:
    def test_falha_quando_credenciais_ausentes(self, monkeypatch):
        monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
        monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)
        with pytest.raises(S3UploadError, match="Credenciais AWS"):
            _validar_credenciais_aws()

    def test_nao_falha_quando_credenciais_presentes(self):
        _validar_credenciais_aws()  # não deve lançar


class TestEnviarDiretorioParaS3:
    def _criar_parquet_fake(self, diretorio) -> None:
        pasta_particao = diretorio / "Credit_Score=GOOD"
        pasta_particao.mkdir(parents=True)
        (pasta_particao / "parte-0000.parquet").write_bytes(b"conteudo-parquet-fake")

    @mock_aws
    def test_envia_arquivos_e_cria_bucket_se_nao_existir(self, tmp_path):
        self._criar_parquet_fake(tmp_path)

        total_enviado = enviar_diretorio_para_s3(
            caminho_local=str(tmp_path),
            nome_bucket=BUCKET_TESTE,
        )

        assert total_enviado == 1

        cliente = boto3.client("s3", region_name="us-east-1")
        objetos = cliente.list_objects_v2(Bucket=BUCKET_TESTE)
        chaves = [obj["Key"] for obj in objetos.get("Contents", [])]
        assert "credit_score_clean/Credit_Score=GOOD/parte-0000.parquet" in chaves

    @mock_aws
    def test_falha_quando_diretorio_local_nao_existe(self, tmp_path):
        with pytest.raises(S3UploadError, match="não encontrado"):
            enviar_diretorio_para_s3(
                caminho_local=str(tmp_path / "nao_existe"),
                nome_bucket=BUCKET_TESTE,
            )

    @mock_aws
    def test_falha_quando_nenhum_parquet_encontrado(self, tmp_path):
        (tmp_path / "arquivo.txt").write_text("nao eh parquet")
        with pytest.raises(S3UploadError, match="Nenhum arquivo .parquet"):
            enviar_diretorio_para_s3(
                caminho_local=str(tmp_path),
                nome_bucket=BUCKET_TESTE,
            )

    @mock_aws
    def test_usa_bucket_existente_sem_recriar(self, tmp_path):
        cliente = boto3.client("s3", region_name="us-east-1")
        cliente.create_bucket(Bucket=BUCKET_TESTE)

        self._criar_parquet_fake(tmp_path)
        total_enviado = enviar_diretorio_para_s3(caminho_local=str(tmp_path), nome_bucket=BUCKET_TESTE)
        assert total_enviado == 1
