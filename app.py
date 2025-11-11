import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from passlib.context import CryptContext # Biblioteca de senha mais confiável
import time
import uuid
import random # Para sortear a ordem
from fpdf import FPDF
import io

# --- Configuração da Página ---
st.set_page_config(page_title="Plataforma de Escalas", layout="wide")
st.title("Plataforma de Organização de Escalas 🩺")

# !!! IMPORTANTE: Mude para o seu email de admin.
# Este email DEVE estar na aba 'convidados' da sua planilha.
ADMIN_EMAIL = "admin@email.com" 

# --- Conexão com Google Sheets ---
# Usa os segredos (Secrets) do Streamlit Cloud
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("Erro ao conectar com o Google Sheets. Verifique seus 'Secrets' no Streamlit Cloud.")
    st.error(e)
    st.stop()


# --- Funções de Hash de Senha (usando passlib) ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password):
    """Criptografa a senha."""
    return pwd_context.hash(password)

def check_password(password, hashed):
    """Verifica a senha com o hash."""
    try:
        return pwd_context.verify(password, hashed)
    except (ValueError, TypeError):
        return False

# --- Funções de Banco de Dados (Google Sheets) ---

def is_email_invited(email):
    """Verifica se um email está na lista de convidados (aba 'convidados')."""
    try:
        df_invited = conn.read(worksheet="convidados", usecols=[0], ttl=5)
        df_invited['email'] = df_invited['email'].astype(str).str.strip().str.lower()
        allowed_emails = df_invited['email'].tolist()
        
        if email.strip().lower() in allowed_emails:
            return True
    except Exception as e:
        # Se a aba 'convidados' não existir, nega por padrão
        st.error("Erro ao verificar lista de convidados. A aba 'convidados' existe e tem uma coluna 'email'?")
        return False
    return False

def get_user_data(email):
    """Busca os dados do usuário pelo email."""
    try:
        df_users = conn.read(worksheet="usuarios", usecols=[0, 1, 2, 3], ttl=5)
        df_users['email'] = df_users['email'].astype(str).str.strip()
        user_data = df_users[df_users['email'].str.lower() == email.lower().strip()]
        if not user_data.empty:
            return user_data.iloc[0]
    except Exception as e:
        st.error(f"Erro ao ler dados de usuários: {e}")
    return None

def register_user(name, matricula, email, password):
    """Registra um novo usuário na planilha."""
    
    # 1. Verifica se o email está na lista de permissão
    if not is_email_invited(email):
        return False, "Este email não está autorizado a se registrar. Contate o administrador."

    # 2. Verifica se o email já foi registrado
    if get_user_data(email) is not None:
        return False, "E-mail já cadastrado."
    
    # 3. Se passou, cria o usuário
    hashed_pw = hash_password(password)
    new_user_data = pd.DataFrame([{
        "nome": name,
        "matricula": matricula,
        "email": email.strip().lower(),
        "senha_hash": hashed_pw
    }])
    
    try:
        df_users = conn.read(worksheet="usuarios")
        conn.update(worksheet="usuarios", data=new_user_data, offset_rows=len(df_users))
        return True, "Usuário registrado com sucesso!"
    except Exception as e:
        return False, f"Erro ao registrar: {e}"

def add_atividade(escala_nome, tipo, data, horario, vagas):
    """Adiciona uma nova atividade ao banco de dados."""
    atividade_id = str(uuid.uuid4()) # Gera um ID único
    new_atividade = pd.DataFrame([{
        "escala_nome": escala_nome,
        "tipo": tipo,
        "data": str(data),
        "horario": horario,
        "vagas": vagas,
        "id_atividade": atividade_id
    }])
    
    try:
        df_atividades = conn.read(worksheet="atividades")
        conn.update(worksheet="atividades", data=new_atividade, offset_rows=len(df_atividades))
        return True
    except Exception as e:
        st.error(f"Erro ao adicionar atividade: {e}")
        return False

def get_escala_completa(escala_nome):
    """Busca a escala com os nomes dos participantes."""
    try:
        df_atividades = conn.read(worksheet="atividades", ttl=5)
        df_escolhas = conn.read(worksheet="escolhas", ttl=5)
        
        atividades_escala = df_atividades[df_atividades['escala_nome'] == escala_nome]
        if atividades_escala.empty:
            return pd.DataFrame(columns=['Tipo', 'Data', 'Horário', 'Vagas', 'Participantes'])
        
        # Agrupa os participantes por atividade
        escolhas_agrupadas = df_escolhas.groupby('id_atividade')['nome_participante'].apply(lambda x: ', '.join(x)).reset_index()
        
        # Junta atividades com escolhas
        df_final = pd.merge(
            atividades_escala,
            escolhas_agrupadas,
            on="id_atividade",
            how="left"
        )
        
        df_final['Participantes'] = df_final['nome_participante'].fillna('')
        df_final = df_final[['tipo', 'data', 'horario', 'vagas', 'Participantes']]
        df_final.columns = ['Tipo', 'Data', 'Horário', 'Vagas', 'Participantes']
        
        return df_final
    except Exception as e:
        st.error(f"Erro ao buscar escala: {e}")
        return pd.DataFrame(columns=['Tipo', 'Data', 'Horário', 'Vagas', 'Participantes'])

def get_todos_usuarios():
    """Busca todos os usuários, exceto o admin."""
    try:
        df_users = conn.read(worksheet="usuarios", usecols=[0, 1, 2], ttl=5)
        df_users['email'] = df_users['email'].astype(str).str.strip()
        participantes = df_users[df_users['email'].str.lower() != ADMIN_EMAIL.lower().strip()]
        return participantes['nome'].tolist()
    except Exception as e:
        st.error(f"Erro ao buscar lista de participantes: {e}")
    return []

def get_atividades_disponiveis(escala_nome):
    """Busca atividades e quantas vagas já foram preenchidas."""
    try:
        df_atividades = conn.read(worksheet="atividades", ttl=5)
        df_escolhas = conn.read(worksheet="escolhas", ttl=5)

        atividades_escala = df_atividades[df_atividades['escala_nome'] == escala_nome].copy()
        if atividades_escala.empty:
            return pd.DataFrame() # Retorna DF vazio se não houver atividades

        # Conta quantas escolhas cada atividade já tem
        escolhas_count = df_escolhas['id_atividade'].value_counts().reset_index()
        escolhas_count.columns = ['id_atividade', 'preenchidas']
        
        df_final = pd.merge(
            atividades_escala,
            escolhas_count,
            on="id_atividade",
            how="left"
        )
        
        df_final['preenchidas'] = df_final['preenchidas'].fillna(0).astype(int)
        df_final['vagas'] = df_final['vagas'].astype(int)
        df_final['vagas_restantes'] = df_final['vagas'] - df_final['preenchidas']
        
        df_disponiveis = df_final[df_final['vagas_restantes'] > 0].copy()
        
        # Cria uma coluna de "label" para o selectbox
        df_disponiveis['label'] = df_disponiveis.apply(
            lambda row: f"{row['tipo']} - {row['data']} ({row['horario']}) - {row['vagas_restantes']} vagas",
            axis=1
        )
        return df_disponiveis[['id_atividade', 'label']]

    except Exception as e:
        st.error(f"Erro ao buscar atividades disponíveis: {e}")
    return pd.DataFrame()

def salvar_escolha(escala_nome, atividade_id, user_email, user_name):
    """Salva a escolha do participante na planilha 'escolhas'."""
    try:
        df_escolhas = conn.read(worksheet="escolhas", ttl=5)
        
        # Idealmente, verificaríamos regras aqui (ex: já escolheu nessa rodada? etc.)
        
        new_escolha = pd.DataFrame([{
            "id_atividade": atividade_id,
            "email_participante": user_email,
            "nome_participante": user_name
        }])
        
        conn.update(worksheet="escolhas", data=new_escolha, offset_rows=len(df_escolhas))
        return True
    except Exception as e:
        st.error(f"Erro ao salvar escolha: {e}")
        return False

# --- Funções de Exportação ---
def dataframe_to_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    
    col_widths = [30, 25, 30, 15, 80] 
    for i, col in enumerate(df.columns):
        pdf.cell(col_widths[i], 10, col, 1, 0, 'C')
    pdf.ln()
    
    for index, row in df.iterrows():
        y_before = pdf.get_y()
        pdf.multi_cell(col_widths[0], 10, str(row.iloc[0]), 1, 'L')
        y_after_col1 = pdf.get_y()
        pdf.set_y(y_before) 
        pdf.set_x(pdf.get_x() + col_widths[0]) 
        
        pdf.multi_cell(col_widths[1], 10, str(row.iloc[1]), 1, 'L')
        y_after_col2 = pdf.get_y()
        pdf.set_y(y_before)
        pdf.set_x(pdf.get_x() + col_widths[0] + col_widths[1])
        
        pdf.multi_cell(col_widths[2], 10, str(row.iloc[2]), 1, 'L')
        y_after_col3 = pdf.get_y()
        pdf.set_y(y_before)
        pdf.set_x(pdf.get_x() + col_widths[0] + col_widths[1] + col_widths[2])

        pdf.multi_cell(col_widths[3], 10, str(row.iloc[3]), 1, 'L')
        y_after_col4 = pdf.get_y()
        pdf.set_y(y_before)
        pdf.set_x(pdf.get_x() + col_widths[0] + col_widths[1] + col_widths[2] + col_widths[3])

        pdf.multi_cell(col_widths[4], 10, str(row.iloc[4]), 1, 'L')
        y_after_col5 = pdf.get_y()

        pdf.set_y(max(y_after_col1, y_after_col2, y_after_col3, y_after_col4, y_after_col5))

    return pdf.output(dest='S').encode('latin-1')

def dataframe_to_excel(df):
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Escala')
    
    worksheet = writer.sheets['Escala']
    for i, col in enumerate(df.columns):
        column_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
        worksheet.set_column(i, i, column_len)
        
    writer.close()
    processed_data = output.getvalue()
    return processed_data

# --- Lógica de Login e Registro ---

# Inicializa o estado da sessão
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_name'] = None
    st.session_state['user_email'] = None
    st.session_state['is_admin'] = False

# Se não estiver logado, mostra o formulário de login/registro
if not st.session_state['logged_in']:
    
    tab_login, tab_register = st.tabs(["Login", "Registrar"])
    
    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Senha", type="password")
            login_button = st.form_submit_button("Entrar")
            
            if login_button:
                user_data = get_user_data(email)
                
                if user_data is not None and check_password(password, user_data['senha_hash']):
                    st.session_state['logged_in'] = True
                    st.session_state['user_name'] = user_data['nome']
                    st.session_state['user_email'] = user_data['email']
                    st.session_state['is_admin'] = (user_data['email'] == ADMIN_EMAIL.lower().strip())
                    st.rerun() 
                else:
                    st.error("Email ou senha incorretos.")

    with tab_register:
        with st.form("register_form"):
            name = st.text_input("Nome Completo")
            matricula = st.text_input("Matrícula")
            email = st.text_input("Email")
            password = st.text_input("Senha", type="password")
            confirm_password = st.text_input("Confirmar Senha", type="password")
            register_button = st.form_submit_button("Registrar")
            
            if register_button:
                if password != confirm_password:
                    st.error("As senhas não coincidem.")
                elif not all([name, matricula, email, password]):
                    st.error("Por favor, preencha todos os campos.")
                else:
                    success, message = register_user(name, matricula, email, password)
                    if success:
                        st.success(message + " Agora você pode fazer o login.")
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(message)

# --- Aplicação Principal (Se estiver logado) ---
else:
    st.sidebar.write(f"Bem-vindo(a), **{st.session_state['user_name']}**!")
    if st.sidebar.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key] 
        st.rerun()

    # --- Visão do Administrador ---
    if st.session_state['is_admin']:
        st.sidebar.title("Painel do Administrador")
        menu_admin = st.sidebar.radio("Selecione:", ["Criar/Ver Escala", "Configurar Regras", "Histórico"])

        if menu_admin == "Criar/Ver Escala":
            st.header("Gerenciador de Escalas 🗓️")
            escala_nome = st.text_input("Digite o nome da escala (ex: 'Dezembro/2025'):")

            with st.form("form_add_atividade", clear_on_submit=True):
                st.subheader("Adicionar Nova Atividade")
                tipo = st.selectbox("Tipo de Atividade", ["Plantão", "Ambulatório", "Enfermaria"])
                data = st.date_input("Data")
                horario = st.text_input("Horário (ex: 07:00-19:00)")
                vagas = st.number_input("Número de Vagas", min_value=1, value=1)
                submitted = st.form_submit_button("Adicionar Atividade")

                if submitted and escala_nome:
                    if add_atividade(escala_nome, tipo, data, horario, vagas):
                        st.success(f"Atividade '{tipo}' em {data} adicionada à escala '{escala_nome}'!")
                    else:
                        st.error("Falha ao adicionar atividade.")
                elif submitted:
                    st.warning("Por favor, defina um nome para a escala antes de adicionar atividades.")
            
            st.header(f"Escala Atual: {escala_nome or 'Nenhuma selecionada'}")
            if escala_nome:
                df_escala_completa = get_escala_completa(escala_nome)
                st.dataframe(df_escala_completa, use_container_width=True)

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
            st.checkbox("Todos devem fazer pelo menos um plantão em fim de semana.")
            st.number_input("Número total de atividades por pessoa:", min_value=1)
            
        elif menu_admin == "Histórico":
            st.header("Histórico de Escalas (Em Desenvolvimento) 📚")
            st.info("Aqui você poderá visualizar as escalas finalizadas.")

    # --- Visão do Participante ---
    else:
        st.sidebar.title("Menu do Participante")
        menu_user = st.sidebar.radio("Selecione:", ["Escolher Horário", "Minha Escala", "Trocar Horário"])

        if menu_user == "Escolher Horário":
            st.header("Rodada de Escolha de Horários 🕒")
            
            # Define a escala ativa (idealmente o admin definiria isso)
            escala_ativa = "Dezembro/2025" # Mude para a escala que você criou
            st.subheader(f"Escala ativa: {escala_ativa}")

            # --- Lógica da Rodada ---
            if 'ordem_escolha' not in st.session_state:
                st.session_state.ordem_escolha = []
                st.session_state.indice_atual = 0

            if not st.session_state.ordem_escolha:
                if st.button("Iniciar Nova Rodada (Sortear Ordem)"):
                    participantes = get_todos_usuarios()
                    random.shuffle(participantes)
                    st.session_state.ordem_escolha = participantes
                    st.session_state.indice_atual = 0
                    st.rerun()
            else:
                # Se a rodada já começou
                ordem = st.session_state.ordem_escolha
                indice = st.session_state.indice_atual

                if indice >= len(ordem):
                    st.success("Todos os participantes escolheram nesta rodada!")
                    if st.button("Iniciar Próxima Rodada"):
                        st.session_state.ordem_escolha = [] # Limpa a ordem para o próximo sorteio
                        st.rerun()
                    st.stop()

                pessoa_da_vez = ordem[indice]
                st.info(f"Ordem da rodada: {', '.join(ordem)}")
                st.subheader(f"É a vez de: **{pessoa_da_vez}**")

                # Se for a vez do usuário logado
                if st.session_state['user_name'] == pessoa_da_vez:
                    df_atividades = get_atividades_disponiveis(escala_ativa)
                    if df_atividades.empty:
                        st.warning("Não há mais atividades com vagas disponíveis.")
                        st.stop()

                    opcoes = pd.Series(df_atividades.id_atividade.values, index=df_atividades.label).to_dict()
                    escolha = st.selectbox("Selecione sua atividade:", options=opcoes.keys())
                    
                    if st.button("Confirmar Escolha"):
                        id_atividade_escolhida = opcoes[escolha]
                        
                        sucesso = salvar_escolha(
                            escala_ativa, 
                            id_atividade_escolhida, 
                            st.session_state['user_email'], 
                            st.session_state['user_name']
                        )
                        
                        if sucesso:
                            st.success(f"Você escolheu: {escolha}")
                            # Avança para o próximo da fila
                            st.session_state.indice_atual += 1
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Não foi possível salvar sua escolha.")
                
                else:
                    st.info("Aguardando o colega escolher...")
                    # Botão para o admin forçar a passagem de vez (útil se alguém travar)
                    if st.session_state['is_admin'] and st.button("Pular vez (Admin)"):
                         st.session_state.indice_atual += 1
                         st.rerun()


        elif menu_user == "Minha Escala":
            st.header("Minha Escala Pessoal (Em Desenvolvimento)")
            st.info("Aqui você verá apenas as atividades que você escolheu.")

        elif menu_user == "Trocar Horário":
            st.header("Solicitar Troca de Horários (Em Desenvolvimento) 🔄")
            st.info("Aqui você poderá solicitar trocas com colegas.")
