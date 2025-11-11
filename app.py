import streamlit as st
import json
import gspread
import pandas as pd
from datetime import datetime
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

st.set_page_config(page_title="Gerenciador de Escalas", layout="wide")

# --- Conexão ao Google Sheets via st.secrets ---
# Espera-se que .streamlit/secrets.toml contenha:
# gspread_service_account = '''{ ... }'''
# SHEET_ID = "1AbCdE..."
creds_json_str = st.secrets.get("gspread_service_account", None)
sheet_id = st.secrets.get("SHEET_ID", None)

if creds_json_str is None or sheet_id is None:
    st.error("Credenciais do Google Sheets ou SHEET_ID não encontradas em st.secrets. Verifique .streamlit/secrets.toml.")
    st.stop()

creds_dict = json.loads(creds_json_str)
gc = gspread.service_account_from_dict(creds_dict)
sh = gc.open_by_key(sheet_id)

# Helper: ler aba como DataFrame (preserva cabeçalho)
def read_sheet_df(sheet_name):
    try:
        ws = sh.worksheet(sheet_name)
        data = ws.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        # Se a aba não existir ou estiver vazia, retorna DataFrame vazio com colunas
        return pd.DataFrame()

# Helper: append linha (dict) para uma aba
def append_row(sheet_name, row_dict):
    ws = sh.worksheet(sheet_name)
    # Garantir que cabeçalhos existam
    headers = ws.row_values(1)
    if not headers:
        # cria cabeçalho baseado nas chaves
        ws.append_row(list(row_dict.keys()))
    # append valores na ordem dos headers (preenchendo campos faltantes)
    headers = ws.row_values(1)
    values = [row_dict.get(h, "") for h in headers]
    ws.append_row(values)

# --- Autenticação (streamlit-authenticator) ---
# Opcional: ler config.yaml local para credenciais de login do app
# (Você pode continuar usando config.yaml com users ou migrar usuarios para Google Sheet)
try:
    with open('config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)
except FileNotFoundError:
    config = None

if config:
    authenticator = stauth.Authenticate(
        config['credentials'],
        config.get('cookie', {}).get('name', 'cookie-name'),
        config.get('cookie', {}).get('key', 'some-key'),
        config.get('cookie', {}).get('expiry_days', 30),
        config.get('preauthorized', {})
    )
    name, authentication_status, username = authenticator.login('Login', 'main')
else:
    st.info("Arquivo config.yaml não encontrado. A aplicação continuará sem login de usuários (somente testes).")
    name = "Visitante"
    authentication_status = True
    username = "guest"

if authentication_status:
    if config:
        authenticator.logout('Logout', 'main', key='logout')
    st.write(f"Bem-vindo(a), {name}!")

    # Página admin (simples check pelo username 'admin' — customize conforme seu sistema)
    is_admin = (username == 'admin')

    if is_admin:
        st.header("Painel do Administrador")

        # Mostrar atividades atuais
        st.subheader("Atividades cadastradas")
        df_atividades = read_sheet_df("atividades")
        if df_atividades.empty:
            st.info("Nenhuma atividade cadastrada.")
        else:
            st.dataframe(df_atividades)

        # Form para cadastrar atividade (append à aba 'atividades')
        with st.form("form_add_activity", clear_on_submit=True):
            tipo = st.selectbox("Tipo de Atividade", ["Plantão", "Ambulatório", "Enfermaria"])
            data_atividade = st.date_input("Data")
            horario = st.time_input("Horário")
            vagas = st.number_input("Vagas", min_value=1, step=1)
            submitted = st.form_submit_button("Cadastrar")
            if submitted:
                row = {
                    "Tipo": tipo,
                    "Data": data_atividade.strftime("%Y-%m-%d"),
                    "Horario": horario.strftime("%H:%M"),
                    "Vagas": int(vagas)
                }
                # Se a aba não existir, cria-la com headers
                try:
                    append_row("atividades", row)
                    st.success("Atividade cadastrada e enviada ao Google Sheets.")
                except Exception as e:
                    st.error(f"Erro ao cadastrar atividade: {e}")

        st.divider()
        st.subheader("Finalizar e arquivar escala atual")
        st.write("Isto copia as linhas de 'escolhas_atuais' para 'historico' e adiciona DataArquivamento, depois limpa 'escolhas_atuais'.")

        if st.button("Finalizar e Arquivar Escala"):
            try:
                df_escolhas = read_sheet_df("escolhas_atuais")
                if df_escolhas.empty:
                    st.warning("Não há escolhas atuais para arquivar.")
                else:
                    # Adiciona coluna DataArquivamento e append a historico linha a linha
                    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                    # Garante que aba historico exista; se não, cria cabecalho
                    try:
                        ws_hist = sh.worksheet("historico")
                    except gspread.exceptions.WorksheetNotFound:
                        # criar worksheet com cabeçalho = colunas de df_escolhas + DataArquivamento
                        header = list(df_escolhas.columns) + ["DataArquivamento"]
                        sh.add_worksheet(title="historico", rows="1000", cols=str(len(header)))
                        ws_hist = sh.worksheet("historico")
                        ws_hist.append_row(header)

                    # Append cada linha ao historico
                    for _, row in df_escolhas.iterrows():
                        row_dict = row.to_dict()
                        row_dict["DataArquivamento"] = timestamp
                        append_row("historico", row_dict)

                    # Limpar escolhas_atuais: sobrescrever com apenas a linha de cabeçalho (vazias)
                    try:
                        ws_escolhas = sh.worksheet("escolhas_atuais")
                        headers = ws_escolhas.row_values(1)
                        if headers:
                            ws_escolhas.clear()
                            ws_escolhas.append_row(headers)
                        else:
                            ws_escolhas.clear()
                    except Exception:
                        pass

                    st.success(f"Escala arquivada com sucesso em {timestamp} e histórico atualizado.")
            except Exception as e:
                st.error(f"Erro ao arquivar: {e}")

        st.divider()
        st.subheader("Visualizar Histórico")
        df_hist = read_sheet_df("historico")
        if df_hist.empty:
            st.info("Histórico vazio.")
        else:
            st.dataframe(df_hist)

    else:
        # Página do usuário comum
        st.header("Área do Usuário")
        st.write("Aqui você verá suas escolhas e poderá marcar/selecionar atividades (a implementar).")
        # Exemplo: mostrar atividades disponíveis
        df_atividades = read_sheet_df("atividades")
        st.subheader("Atividades disponíveis")
        if df_atividades.empty:
            st.info("Nenhuma atividade disponível.")
        else:
            st.dataframe(df_atividades)

else:
    st.error("Falha na autenticação. Verifique usuário/senha.")
