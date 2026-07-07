from unittest.mock import MagicMock, patch

import pytest

from scripts.extract.kaggle_extractor import (
    KaggleExtractionError,
    _arquivos_ja_presentes,
    _validar_credenciais_kaggle,
    extrair_dataset_kaggle,
)


class TestValidarCredenciaisKaggle:
    def test_retorna_false_quando_credenciais_ausentes(self, monkeypatch):
        monkeypatch.delenv("KAGGLE_USERNAME", raising=False)
        monkeypatch.delenv("KAGGLE_KEY", raising=False)
        assert _validar_credenciais_kaggle() is False

    def test_retorna_true_quando_credenciais_presentes(self, monkeypatch):
        monkeypatch.setenv("KAGGLE_USERNAME", "usuario_teste")
        monkeypatch.setenv("KAGGLE_KEY", "chave_teste")
        assert _validar_credenciais_kaggle() is True


class TestArquivosJaPresentes:
    def test_retorna_false_quando_diretorio_nao_existe(self, tmp_path):
        assert _arquivos_ja_presentes(str(tmp_path / "nao_existe")) is False

    def test_retorna_false_quando_arquivo_esta_vazio(self, tmp_path):
        (tmp_path / "train.csv").write_text("")
        (tmp_path / "test.csv").write_text("conteudo")
        assert _arquivos_ja_presentes(str(tmp_path)) is False

    def test_retorna_true_quando_ambos_arquivos_existem_e_tem_conteudo(self, tmp_path):
        (tmp_path / "train.csv").write_text("ID,Age\n1,25")
        (tmp_path / "test.csv").write_text("ID,Age\n1,30")
        assert _arquivos_ja_presentes(str(tmp_path)) is True


class TestExtrairDatasetKaggle:
    def test_usa_fallback_local_quando_sem_credenciais_e_csv_presente(self, tmp_path, monkeypatch):
        monkeypatch.delenv("KAGGLE_USERNAME", raising=False)
        monkeypatch.delenv("KAGGLE_KEY", raising=False)
        (tmp_path / "train.csv").write_text("ID,Age\n1,25")
        (tmp_path / "test.csv").write_text("ID,Age\n1,30")

        resultado = extrair_dataset_kaggle(diretorio_destino=str(tmp_path))
        assert resultado == str(tmp_path)

    def test_falha_quando_sem_credenciais_e_sem_csv_local(self, tmp_path, monkeypatch):
        monkeypatch.delenv("KAGGLE_USERNAME", raising=False)
        monkeypatch.delenv("KAGGLE_KEY", raising=False)

        with pytest.raises(KaggleExtractionError, match="Credenciais do Kaggle ausentes"):
            extrair_dataset_kaggle(diretorio_destino=str(tmp_path))

    @patch("kaggle.api.kaggle_api_extended.KaggleApi")
    def test_falha_quando_autenticacao_da_api_quebra(self, mock_kaggle_api_classe, tmp_path, monkeypatch):
        monkeypatch.setenv("KAGGLE_USERNAME", "usuario_teste")
        monkeypatch.setenv("KAGGLE_KEY", "chave_teste")

        instancia_mock = MagicMock()
        instancia_mock.authenticate.side_effect = Exception("Token inválido")
        mock_kaggle_api_classe.return_value = instancia_mock

        with pytest.raises(KaggleExtractionError, match="Falha na autenticação"):
            extrair_dataset_kaggle(diretorio_destino=str(tmp_path))

    @patch("kaggle.api.kaggle_api_extended.KaggleApi")
    def test_falha_quando_download_nao_produz_arquivos(self, mock_kaggle_api_classe, tmp_path, monkeypatch):
        monkeypatch.setenv("KAGGLE_USERNAME", "usuario_teste")
        monkeypatch.setenv("KAGGLE_KEY", "chave_teste")

        instancia_mock = MagicMock()
        instancia_mock.authenticate.return_value = None
        instancia_mock.dataset_download_files.return_value = None
        mock_kaggle_api_classe.return_value = instancia_mock

        with pytest.raises(KaggleExtractionError, match="não encontrado"):
            extrair_dataset_kaggle(diretorio_destino=str(tmp_path))
