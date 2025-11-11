import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import bcrypt
import time
import uuid

# --- Configuração da Página ---
st.set_page_config(page_title="Plataforma de Escalas", layout="wide")
st.title("Plataforma de Organização de Escalas 🩺")

# Email que define quem é o administrador
ADMIN_EMAIL = "admin@email.com" # Mude para o seu email de admin

# --- Conexão com Google Sheets ---
# Usa os segredos (Secrets) do Streamlit Cloud
conn = st.connection("gsheets", type=GSheetsConnection)

# --- Funções de Hash de Senha ---
def hash_password(password):
    """Criptografa a senha."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    """Verifica a senha com o hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# --- Funções de Banco de Dados (Google Sheets) ---

def get_allowed_emails():
    """Busca a lista de emails permitidos para cadastro."""
    try:
        df_emails = conn.read(worksheet="emails_permitidos", usecols=[0], ttl=5)
        if not df_emails.empty:
            return df_emails['email'].tolist()
        return []
    except Exception as e:
        # Se a planilha não existir ainda, retorna lista vazia
        return []

def add_allowed_email(email):
    """Adiciona um email à lista de permitidos."""
    try:
        # Verifica se o email já existe
        allowed_emails = get_allowed_emails()
        if email in allowed_emails:
            return False, "Email já está na lista de permitidos."
        
        new_email_data = pd.DataFrame([{"email": email}])
        
        # Lê a planilha atual e adiciona o novo email
        try:
            df_emails = conn.read(worksheet="emails_permitidos")
            conn.update(worksheet="emails_permitidos", data=new_email_data, offset_rows=len(df_emails))
        except:
            # Se a planilha não existir, cria com o primeiro email
            conn.update(worksheet="emails_permitidos", data=new_email_data)
        
        return True, "Email adicionado à lista de permitidos!"
    except Exception as e:
        return False, f"Erro ao adicionar email: {e}"

def remove_allowed_email(email):
    """Remove um email da lista de permitidos."""
    try:
        df_emails = conn.read(worksheet="emails_permitidos")
        df_emails_filtered = df_emails[df_emails['email'] != email]
        
        if len(df_emails_filtered) == len(df_emails):
            return False, "Email não encontrado na lista."
        
        conn.update(worksheet="emails_permitidos", data=df_emails_filtered)
        return True, "Email removido da lista de permitidos!"
    except Exception as e:
        return False, f"Erro ao remover email: {e}"

def get_user_data(email):
    """Busca os dados do usuário pelo email."""
    try:
        df_users = conn.read(worksheet="usuarios", usecols=[0, 1, 2, 3], ttl=5)
        user_data = df_users[df_users['email'] == email]
        if not user_data.empty:
            return user_data.iloc[0]
    except Exception as e:
        st.error(f"Erro ao ler dados de usuários: {e}")
    return None

def register_user(name, matricula, email, password):
    """Registra um novo usuário na planilha."""
    if get_user_data(email) is not None:
        return False, "E-mail já cadastrado."
    
    # Verifica se o email está na lista de permitidos
    allowed_emails = get_allowed_emails()
    if email not in allowed_emails:
        return False, "E-mail não autorizado. Entre em contato com o administrador para solicitar acesso."
    
    hashed_pw = hash_password(password)
    new_user_data = pd.DataFrame([{
        "nome": name,
        "matricula": matricula,
        "email": email,
        "senha_hash": hashed_pw
    }])
    
    try:
        # Lê a planilha de usuários para encontrar a próxima linha vazia
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


# --- Funções de Exportação (Mantidas como estavam) ---
from fpdf import FPDF
import io

def dataframe_to_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    
    # Cabeçalhos
    col_widths = [30, 25, 30, 15, 80] # Ajuste as larguras das colunas
    for i, col in enumerate(df.columns):
        pdf.cell(col_widths[i], 10, col, 1, 0, 'C')
    pdf.ln()
    
    # Dados
    for index, row in df.iterrows():
        for i, item in enumerate(row):
            pdf.multi_cell(col_widths[i], 10, str(item), 1, 'L')
        pdf.ln()
    
    return pdf.output(dest='S').encode('latin-1')

def dataframe_to_excel(df):
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Escala')
    writer.close()
    processed_data = output.getvalue()
    return processed_data

# --- Lógica de Login e Registro (Novo) ---

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
                    st.session_state['is_admin'] = (user_data['email'] == ADMIN_EMAIL)
                    st.rerun() # Recarrega a página para o estado "logado"
                else:
                    st.error("Email ou senha incorretos.")

    with tab_register:
        with st.form("register_form"):
            name = st.text_input("Nome Completo")
            matricula = st.text_input("Matrícula")
            email = st.text_input("Email (o admin deve usar o email: " + ADMIN_EMAIL + ")")
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
            del st.session_state[key] # Limpa a sessão
        st.rerun()

    # --- Visão do Administrador ---
    if st.session_state['is_admin']:
        st.sidebar.title("Painel do Administrador")
        menu_admin = st.sidebar.radio("Selecione:", ["Criar/Ver Escala", "Gerenciar Emails Permitidos", "Configurar Regras", "Histórico"])

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

        elif menu_admin == "Gerenciar Emails Permitidos":
            st.header("Gerenciar Emails Permitidos para Cadastro 📧")
            
            # Adicionar novo email
            with st.form("form_add_email", clear_on_submit=True):
                st.subheader("Adicionar Email à Lista de Permitidos")
                new_email = st.text_input("Email para permitir cadastro:")
                add_email_button = st.form_submit_button("Adicionar Email")
                
                if add_email_button:
                    if new_email:
                        success, message = add_allowed_email(new_email.strip().lower())
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.warning("Por favor, digite um email válido.")
            
            # Mostrar lista de emails permitidos
            st.subheader("Lista de Emails Autorizados")
            allowed_emails = get_allowed_emails()
            
            if allowed_emails:
                df_allowed = pd.DataFrame(allowed_emails, columns=["Email"])
                st.dataframe(df_allowed, use_container_width=True)
                
                # Remover email
                st.subheader("Remover Email da Lista")
                email_to_remove = st.selectbox("Selecione o email para remover:", allowed_emails)
                if st.button("Remover Email Selecionado"):
                    success, message = remove_allowed_email(email_to_remove)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
            else:
                st.info("Nenhum email cadastrado na lista de permitidos. Adicione emails acima para permitir novos cadastros.")

        elif menu_admin == "Configurar Regras":
            st.header("Configuração de Regras (Em Desenvolvimento) ⚙️")
            # ... (Lógica das regras) ...
            
        elif menu_admin == "Histórico":
            st.header("Histórico de Escalas (Em Desenvolvimento) 📚")
            # ... (Lógica do histórico) ...

    # --- Visão do Participante ---
    else:
        st.sidebar.title("Menu do Participante")
        menu_user = st.sidebar.radio("Selecione:", ["Escolher Horário", "Minha Escala", "Trocar Horário"])

        if menu_user == "Escolher Horário":
            st.header("Rodada de Escolha de Horários 🕒")
            st.info("Funcionalidade de sorteio e escolha em rodadas em desenvolvimento.")
            # ... (Lógica da escolha) ...

        elif menu_user == "Minha Escala":
            st.header("Minha Escala Pessoal")
            st.info("Funcionalidade em desenvolvimento.")

        elif menu_user == "Trocar Horário":
            st.header("Solicitar Troca de Horários 🔄")
            st.info("Funcionalidade em desenvolvimento.")
