# app.py

import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import pandas as pd
from fpdf import FPDF
import io

# Importar funções do banco de dados
import database as db

# --- Configuração da Página ---
st.set_page_config(page_title="Plataforma de Escalas", layout="wide")

# --- Autenticação ---
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
    # O parâmetro 'preauthorized' foi removido daqui
)

st.title("Plataforma de Organização de Escalas 🩺")

name, authentication_status, username = authenticator.login()

# --- Funções de Utilidade ---
def dataframe_to_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Cabeçalhos
    for col in df.columns:
        pdf.cell(40, 10, col, 1, 0, 'C')
    pdf.ln()
    
    # Dados
    for index, row in df.iterrows():
        for item in row:
            pdf.cell(40, 10, str(item), 1, 0, 'L')
        pdf.ln()
    
    return pdf.output(dest='S').encode('latin-1')

def dataframe_to_excel(df):
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Escala')
    writer.close()
    processed_data = output.getvalue()
    return processed_data

# --- Lógica da Aplicação ---
if authentication_status:
    st.sidebar.write(f'Bem-vindo(a) *{name}*')
    authenticator.logout('Logout', 'sidebar')

    # --- Visão do Administrador ---
    if username == 'admin':
        st.sidebar.title("Painel do Administrador")
        menu_admin = st.sidebar.radio("Selecione uma opção:", ["Criar/Ver Escala", "Configurar Regras", "Histórico"])

        if menu_admin == "Criar/Ver Escala":
            st.header("Gerenciador de Escalas 🗓️")
            escala_nome = st.text_input("Digite o nome da nova escala (ex: 'Dezembro/2025'):")

            with st.form("form_add_atividade", clear_on_submit=True):
                st.subheader("Adicionar Nova Atividade")
                tipo = st.selectbox("Tipo de Atividade", ["Plantão", "Ambulatório", "Enfermaria"])
                data = st.date_input("Data")
                horario = st.text_input("Horário (ex: 07:00-19:00)")
                vagas = st.number_input("Número de Vagas", min_value=1, value=1)
                submitted = st.form_submit_button("Adicionar Atividade")

                if submitted and escala_nome:
                    db.adicionar_atividade(escala_nome, tipo, str(data), horario, vagas)
                    st.success(f"Atividade '{tipo}' em {data} adicionada à escala '{escala_nome}'!")
                elif submitted:
                    st.warning("Por favor, defina um nome para a escala antes de adicionar atividades.")
            
            st.header(f"Escala Atual: {escala_nome or 'Nenhuma selecionada'}")
            if escala_nome:
                df_escala_completa = db.buscar_escala_completa(escala_nome)
                st.dataframe(df_escala_completa, use_container_width=True)

                # Botões de Exportação
                col1, col2 = st.columns(2)
                with col1:
                    pdf_data = dataframe_to_pdf(df_escala_completa)
                    st.download_button(
                        label="📥 Exportar para PDF",
                        data=pdf_data,
                        file_name=f"escala_{escala_nome.replace('/', '_')}.pdf",
                        mime="application/pdf",
                    )
                with col2:
                    excel_data = dataframe_to_excel(df_escala_completa)
                    st.download_button(
                        label="📥 Exportar para Excel",
                        data=excel_data,
                        file_name=f"escala_{escala_nome.replace('/', '_')}.xlsx",
                        mime="application/vnd.ms-excel"
                    )


        elif menu_admin == "Configurar Regras":
            st.header("Configuração de Regras (Em Desenvolvimento) ⚙️")
            st.info("Esta seção permitirá ativar/desativar regras para a escolha.")
            st.checkbox("Todos devem fazer pelo menos um plantão em fim de semana.")
            st.number_input("Número total de atividades por pessoa:", min_value=1)
            st.checkbox("Exigir que todas as datas sejam preenchidas antes de dobrar vagas.")
            
        elif menu_admin == "Histórico":
            st.header("Histórico de Escalas (Em Desenvolvimento) 📚")
            st.info("Aqui você poderá visualizar as escalas finalizadas de meses anteriores.")

    # --- Visão do Participante ---
    else:
        st.sidebar.title("Menu do Participante")
        menu_user = st.sidebar.radio("Selecione:", ["Escolher Horário", "Minha Escala", "Trocar Horário"])

        if menu_user == "Escolher Horário":
            st.header("Rodada de Escolha de Horários 🕒")
            st.info("Funcionalidade de sorteio e escolha em rodadas em desenvolvimento.")
            
            # Placeholder para a lógica de rodadas
            if 'ordem_escolha' not in st.session_state:
                st.session_state.ordem_escolha = ["Participante 2", "Participante 1", "Admin"] # Exemplo
            
            st.write(f"**Ordem da rodada atual:** {', '.join(st.session_state.ordem_escolha)}")
            st.write(f"**É a vez de:** {st.session_state.ordem_escolha[0]}")
            
            escala_vigente = "Dezembro/2025" # Deveria ser dinâmico
            df_atividades = db.buscar_atividades(escala_vigente)
            st.dataframe(df_atividades)

        elif menu_user == "Minha Escala":
            st.header("Minha Escala Pessoal")
            st.info("Funcionalidade em desenvolvimento.")

        elif menu_user == "Trocar Horário":
            st.header("Solicitar Troca de Horários 🔄")
            st.info("Funcionalidade em desenvolvimento.")


elif authentication_status is False:
    st.error('Usuário/senha está incorreto')
elif authentication_status is None:
    st.warning('Por favor, insira seu usuário e senha')
