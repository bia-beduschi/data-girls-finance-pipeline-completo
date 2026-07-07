import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

KAGGLE_DATASET_SLUG = "parisrohan/credit-score-classification"
ARQUIVOS_ESPERADOS = ["train.csv", "test.csv"]


class KaggleExtractionError(Exception):
    """Erro customizado para falhas na etapa de extração."""


def _validar_credenciais_kaggle() -> bool:
    """Verifica se as credenciais do Kaggle estão presentes no ambiente."""
    username = os.getenv("KAGGLE_USERNAME")
    key = os.getenv("KAGGLE_KEY")
    return bool(username and key)


def _arquivos_ja_presentes(diretorio_destino: str) -> bool:
    """Verifica se train.csv e test.csv já existem e não estão vazios."""
    destino = Path(diretorio_destino)
    if not destino.exists():
        return False
    for nome_arquivo in ARQUIVOS_ESPERADOS:
        caminho = destino / nome_arquivo
        if not caminho.exists() or caminho.stat().st_size == 0:
            return False
    return True


def _baixar_via_api_kaggle(diretorio_destino: str) -> None:
    """Autentica e baixa o dataset via API oficial do Kaggle."""
    from kaggle.api.kaggle_api_extended import KaggleApi

    try:
        api = KaggleApi()
        api.authenticate()
    except Exception as erro:
        raise KaggleExtractionError(f"Falha na autenticação com o Kaggle: {erro}") from erro

    os.makedirs(diretorio_destino, exist_ok=True)

    try:
        logger.info("Baixando dataset '%s' do Kaggle...", KAGGLE_DATASET_SLUG)
        api.dataset_download_files(
            dataset=KAGGLE_DATASET_SLUG,
            path=diretorio_destino,
            unzip=True,
            quiet=False,
        )
    except Exception as erro:
        raise KaggleExtractionError(
            f"Falha ao baixar o dataset '{KAGGLE_DATASET_SLUG}': {erro}"
        ) from erro


def extrair_dataset_kaggle(diretorio_destino: str) -> str:
    """Função de entrada da Task 1, chamada pelo PythonOperator do Airflow."""
    logger.info("=== Iniciando Task 1: Extração ===")
    credenciais_ok = _validar_credenciais_kaggle()

    if credenciais_ok:
        _baixar_via_api_kaggle(diretorio_destino)
    elif _arquivos_ja_presentes(diretorio_destino):
        logger.warning(
            "Credenciais do Kaggle ausentes — usando CSVs já presentes em '%s' "
            "(fallback local permitido pelo edital do bootcamp).",
            diretorio_destino,
        )
    else:
        raise KaggleExtractionError(
            "Credenciais do Kaggle ausentes (KAGGLE_USERNAME/KAGGLE_KEY) e nenhum "
            f"CSV local encontrado em '{diretorio_destino}'. Configure as "
            "credenciais ou copie train.csv/test.csv manualmente para essa pasta."
        )

    _validar_arquivos_baixados(diretorio_destino)
    logger.info("=== Task 1 finalizada com sucesso ===")
    return diretorio_destino


def _validar_arquivos_baixados(diretorio_destino: str) -> None:
    """Confere que os arquivos essenciais existem e não estão vazios (porta de qualidade)."""
    destino = Path(diretorio_destino)
    for nome_arquivo in ARQUIVOS_ESPERADOS:
        caminho = destino / nome_arquivo
        if not caminho.exists():
            raise KaggleExtractionError(f"Arquivo esperado não encontrado: {caminho}")
        if caminho.stat().st_size == 0:
            raise KaggleExtractionError(f"Arquivo baixado está vazio: {caminho}")
        logger.info("Validado: %s (%.2f MB)", nome_arquivo, caminho.stat().st_size / (1024 * 1024))


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    extrair_dataset_kaggle(diretorio_destino=os.getenv("RAW_DATA_DIR", "./data/raw"))
