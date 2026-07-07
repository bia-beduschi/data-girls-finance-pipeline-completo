import numpy as np
import pandas as pd
import pytest

from scripts.transform.pandas_cleaning import (
    DataQualityError,
    converter_credit_history_age,
    limpar_amount_invested_monthly,
    limpar_changed_credit_limit,
    limpar_contas_cartoes_e_juros,
    limpar_delay_from_due_date,
    limpar_idade,
    limpar_monthly_balance,
    limpar_num_credit_inquiries,
    limpar_num_of_delayed_payment,
    limpar_num_of_loan,
    limpar_outstanding_debt,
    limpar_renda_anual,
    limpar_total_emi_per_month,
    padronizar_categoricas_com_placeholder,
    padronizar_credit_score,
    padronizar_payment_of_min_amount,
    remover_colunas_pii,
    remover_duplicatas,
    validar_qualidade_dados,
)


class TestLimparIdade:
    def test_remove_underscore_e_converte(self):
        df = pd.DataFrame({"Age": ["25_", "30"]})
        resultado = limpar_idade(df)
        assert resultado["Age"].tolist() == [25.0, 30.0]

    def test_idade_fora_do_intervalo_vira_nan(self):
        df = pd.DataFrame({"Age": ["150", "-5", "40"]})
        resultado = limpar_idade(df)
        assert resultado["Age"].iloc[2] == 40.0
        assert pd.isna(resultado["Age"].iloc[0])
        assert pd.isna(resultado["Age"].iloc[1])


class TestLimparRendaAnual:
    def test_renda_negativa_vira_nan(self):
        df = pd.DataFrame({"Annual_Income": ["-1000", "50000_"]})
        resultado = limpar_renda_anual(df)
        assert pd.isna(resultado["Annual_Income"].iloc[0])
        assert resultado["Annual_Income"].iloc[1] == 50000.0


class TestLimparNumOfLoan:
    def test_intervalo_valido(self):
        df = pd.DataFrame({"Num_of_Loan": ["3", "-2", "100"]})
        resultado = limpar_num_of_loan(df)
        assert resultado["Num_of_Loan"].iloc[0] == 3.0
        assert pd.isna(resultado["Num_of_Loan"].iloc[1])
        assert pd.isna(resultado["Num_of_Loan"].iloc[2])


class TestLimparOutstandingDebt:
    def test_converte_e_remove_negativos(self):
        df = pd.DataFrame({"Outstanding_Debt": ["1500.5_", "-200"]})
        resultado = limpar_outstanding_debt(df)
        assert resultado["Outstanding_Debt"].iloc[0] == 1500.5
        assert pd.isna(resultado["Outstanding_Debt"].iloc[1])


class TestLimparContasCartoesEJuros:
    def test_remove_outliers_por_iqr(self):
        df = pd.DataFrame(
            {
                "Num_Bank_Accounts": [5, 9999],
                "Num_Credit_Card": [4, -1],
                "Interest_Rate": [15, 5000],
            }
        )
        resultado = limpar_contas_cartoes_e_juros(df)
        assert resultado["Num_Bank_Accounts"].iloc[0] == 5
        assert pd.isna(resultado["Num_Bank_Accounts"].iloc[1])
        assert pd.isna(resultado["Num_Credit_Card"].iloc[1])
        assert pd.isna(resultado["Interest_Rate"].iloc[1])


class TestLimparDelayFromDueDate:
    def test_clip_negativos_para_zero(self):
        df = pd.DataFrame({"Delay_from_due_date": [-5, 10]})
        resultado = limpar_delay_from_due_date(df)
        assert resultado["Delay_from_due_date"].tolist() == [0, 10]


class TestLimparNumOfDelayedPayment:
    def test_intervalo_valido(self):
        df = pd.DataFrame({"Num_of_Delayed_Payment": ["10_", "-3", "50"]})
        resultado = limpar_num_of_delayed_payment(df)
        assert resultado["Num_of_Delayed_Payment"].iloc[0] == 10.0
        assert pd.isna(resultado["Num_of_Delayed_Payment"].iloc[1])
        assert pd.isna(resultado["Num_of_Delayed_Payment"].iloc[2])


class TestLimparChangedCreditLimit:
    def test_remove_placeholder_e_arredonda(self):
        df = pd.DataFrame({"Changed_Credit_Limit": ["_", "12.345", "500"]})
        resultado = limpar_changed_credit_limit(df)
        assert pd.isna(resultado["Changed_Credit_Limit"].iloc[0])
        assert resultado["Changed_Credit_Limit"].iloc[1] == 12.35 or resultado["Changed_Credit_Limit"].iloc[1] == 12.34
        assert pd.isna(resultado["Changed_Credit_Limit"].iloc[2])


class TestLimparNumCreditInquiries:
    def test_intervalo_valido(self):
        df = pd.DataFrame({"Num_Credit_Inquiries": [5, -1, 999]})
        resultado = limpar_num_credit_inquiries(df)
        assert resultado["Num_Credit_Inquiries"].iloc[0] == 5
        assert pd.isna(resultado["Num_Credit_Inquiries"].iloc[1])
        assert pd.isna(resultado["Num_Credit_Inquiries"].iloc[2])


class TestLimparTotalEmiPerMonth:
    def test_intervalo_valido(self):
        df = pd.DataFrame({"Total_EMI_per_month": [100, -5, 999999]})
        resultado = limpar_total_emi_per_month(df)
        assert resultado["Total_EMI_per_month"].iloc[0] == 100
        assert pd.isna(resultado["Total_EMI_per_month"].iloc[1])
        assert pd.isna(resultado["Total_EMI_per_month"].iloc[2])


class TestLimparAmountInvestedMonthly:
    def test_remove_negativos(self):
        df = pd.DataFrame({"Amount_invested_monthly": ["100_", "-50"]})
        resultado = limpar_amount_invested_monthly(df)
        assert resultado["Amount_invested_monthly"].iloc[0] == 100.0
        assert pd.isna(resultado["Amount_invested_monthly"].iloc[1])


class TestLimparMonthlyBalance:
    def test_remove_valores_absurdos(self):
        df = pd.DataFrame({"Monthly_Balance": ["300.5", "-3.3e26"]})
        resultado = limpar_monthly_balance(df)
        assert resultado["Monthly_Balance"].iloc[0] == 300.5
        assert pd.isna(resultado["Monthly_Balance"].iloc[1])


class TestConverterCreditHistoryAge:
    def test_converte_para_meses(self):
        df = pd.DataFrame({"Credit_History_Age": ["5 Years and 3 Months", "0 Years and 8 Months"]})
        resultado = converter_credit_history_age(df)
        assert "Credit_History_Age" not in resultado.columns
        assert resultado["Credit_History_Age_Months"].tolist() == [63, 8]

    def test_valor_nulo_vira_nan(self):
        df = pd.DataFrame({"Credit_History_Age": [np.nan]})
        resultado = converter_credit_history_age(df)
        assert pd.isna(resultado["Credit_History_Age_Months"].iloc[0])


class TestPadronizarCategoricasComPlaceholder:
    def test_substitui_placeholders_conhecidos(self):
        df = pd.DataFrame(
            {
                "Occupation": ["_______", "Engineer"],
                "Credit_Mix": ["_", "Good"],
                "Payment_Behaviour": ["!@9#%8", "High_spent_Large_value_payments"],
            }
        )
        resultado = padronizar_categoricas_com_placeholder(df)
        assert resultado["Occupation"].iloc[0] == "Unknown"
        assert resultado["Credit_Mix"].iloc[0] == "Unknown"
        assert resultado["Payment_Behaviour"].iloc[0] == "Unknown"


class TestPadronizarPaymentOfMinAmount:
    def test_nm_vira_no(self):
        df = pd.DataFrame({"Payment_of_Min_Amount": ["NM", "Yes", "No"]})
        resultado = padronizar_payment_of_min_amount(df)
        assert resultado["Payment_of_Min_Amount"].tolist() == ["No", "Yes", "No"]


class TestPadronizarCreditScore:
    def test_normaliza_caixa_e_espacos(self):
        df = pd.DataFrame({"Credit_Score": [" good ", "Standard", "poor"]})
        resultado = padronizar_credit_score(df)
        assert resultado["Credit_Score"].tolist() == ["GOOD", "STANDARD", "POOR"]


class TestRemoverColunasPii:
    def test_remove_name_e_ssn(self):
        df = pd.DataFrame({"Name": ["Joao"], "SSN": ["123-45-6789"], "Age": [30]})
        resultado = remover_colunas_pii(df)
        assert "Name" not in resultado.columns
        assert "SSN" not in resultado.columns
        assert "Age" in resultado.columns

    def test_nao_falha_se_colunas_ja_ausentes(self):
        df = pd.DataFrame({"Age": [30]})
        resultado = remover_colunas_pii(df)
        assert list(resultado.columns) == ["Age"]


class TestRemoverDuplicatas:
    def test_remove_linha_duplicada_por_cliente_e_mes(self):
        df = pd.DataFrame(
            {
                "Customer_ID": ["C1", "C1", "C2"],
                "Month": ["January", "January", "January"],
                "Age": [25, 25, 40],
            }
        )
        resultado = remover_duplicatas(df)
        assert len(resultado) == 2


class TestValidarQualidadeDados:
    def _df_valido(self):
        return pd.DataFrame(
            {
                "Customer_ID": ["C1", "C2"],
                "Month": ["January", "February"],
                "Annual_Income": [50000.0, 60000.0],
                "Credit_Score": ["GOOD", "POOR"],
            }
        )

    def test_dataset_valido_nao_levanta_erro(self):
        validar_qualidade_dados(self._df_valido())

    def test_dataset_vazio_levanta_erro(self):
        with pytest.raises(DataQualityError):
            validar_qualidade_dados(self._df_valido().iloc[0:0])

    def test_customer_id_nulo_levanta_erro(self):
        df = self._df_valido()
        df.loc[0, "Customer_ID"] = np.nan
        with pytest.raises(DataQualityError):
            validar_qualidade_dados(df)

    def test_renda_negativa_levanta_erro(self):
        df = self._df_valido()
        df.loc[0, "Annual_Income"] = -100
        with pytest.raises(DataQualityError):
            validar_qualidade_dados(df)

    def test_pii_presente_levanta_erro(self):
        df = self._df_valido()
        df["Name"] = ["Joao", "Maria"]
        with pytest.raises(DataQualityError):
            validar_qualidade_dados(df)

    def test_duplicata_levanta_erro(self):
        df = self._df_valido()
        df = pd.concat([df, df.iloc[[0]]], ignore_index=True)
        with pytest.raises(DataQualityError):
            validar_qualidade_dados(df)
