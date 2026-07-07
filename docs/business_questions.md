# Respostas às Perguntas Norteadoras de Negócio

## 1. Como garantir que os dados cadastrais e financeiros dos clientes estejam sempre atualizados e prontos para utilização pelas equipes de negócio?

A DAG `dag_credit_score_pipeline` roda com `schedule="@daily"` no Airflow,
executando as 3 tasks (extração → transformação → carga) automaticamente
todos os dias, sem intervenção manual. Cada execução:

- Extrai a versão mais recente do dataset (via API do Kaggle, com fallback
  para CSV local já validado).
- Reprocessa a limpeza do zero (não incrementalmente), garantindo que
  qualquer correção nas regras de negócio se propague para todo o
  histórico, não só para dados novos.
- Sobrescreve a camada Trusted no S3 de forma determinística (mesmo
  prefixo sempre), então as equipes de Analytics/Crédito sempre consultam
  o caminho mais atual sem precisar saber qual execução gerou o dado.

## 2. Quais validações de qualidade dos dados devem ser realizadas antes que as informações sejam disponibilizadas para análises e modelos de score de crédito?

A função `validar_qualidade_dados()` (Task 2) aplica checagens **Fail-Fast**
— se qualquer uma falhar, o pipeline é interrompido antes de gravar
qualquer dado no S3:

- **Completude:** `Customer_ID` não pode ser nulo (chave de negócio).
- **Conformidade (LGPD):** nenhuma coluna de dado pessoal identificável
  (`Name`, `SSN`) pode estar presente na camada Trusted.
- **Consistência de domínio:** `Annual_Income` não pode ser negativo após
  a limpeza (indicaria falha na etapa anterior).
- **Unicidade:** não pode haver mais de um registro para o mesmo
  `Customer_ID` + `Month` (evita double counting em relatórios).
- **Volume mínimo:** o dataset resultante não pode estar vazio.

Além disso, todas as 17 colunas numéricas/categóricas sujas do dataset
bruto (underscores, placeholders como `"_______"`, outliers extremos como
juros > 5000%) são tratadas antes da validação — os valores corrompidos
viram `NULL` em vez de serem silenciosamente aceitos ou de descartar a
linha inteira, preservando o registro para as equipes decidirem a
estratégia de imputação mais adequada ao caso de uso (analytics vs.
modelo preditivo).

## 3. Como estruturar um pipeline que permita atualizações periódicas dos dados sem duplicar registros e preservando sua consistência?

Duas camadas de proteção, ambas em código (não só na arquitetura):

1. **Idempotência na gravação:** a Task 2 grava com `mode="overwrite"` e
   um prefixo fixo e determinístico no S3 (`credit_score_clean/`, sem
   timestamp). Reprocessamentos substituem o dado anterior em vez de
   acumular versões órfãs.
2. **Deduplicação explícita:** `remover_duplicatas()` aplica
   `drop_duplicates(subset=["Customer_ID", "Month"])` antes da gravação, e
   `validar_qualidade_dados()` re-confirma a ausência de duplicatas como
   regra Fail-Fast.

## 4. Como organizar e armazenar os dados para facilitar consultas analíticas e alimentar dashboards ou modelos preditivos de classificação de crédito?

- **Particionamento por `Credit_Score`:** os arquivos Parquet são
  particionados pela própria variável-alvo, o que acelera drasticamente
  consultas analíticas típicas ("qual o perfil dos clientes `Poor`?") por
  permitir *partition pruning* — o motor de consulta lê só a partição
  relevante, sem varrer o dataset inteiro.
- **Formato colunar (Parquet):** leitura muito mais eficiente que CSV para
  ferramentas analíticas (Athena, Spark, Power BI), com compressão nativa.
- **Colunas derivadas prontas para consumo:** `Credit_History_Age_Months`
  (convertida de texto para número) elimina a necessidade de qualquer
  parsing adicional por quem for consumir o dado.
- **Painel de métricas (bônus):** ver `docs/dashboard/` — total de
  clientes, distribuição por Credit_Score e renda mensal por categoria,
  prontos tanto como dashboard HTML quanto como CSVs para importar no
  Power BI.
