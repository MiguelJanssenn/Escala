import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import bcrypt
import time
import uuid

try:
    from streamlit_oauth import OAuth2Component
    OAUTH_AVAILABLE = True
except ImportError:
    OAUTH_AVAILABLE = False
    st.warning("Módulo streamlit-oauth não está disponível. Login com Google está desabilitado.")

# --- Configuração da Página ---
st.set_page_config(page_title="Plataforma de Escalas", layout="wide")
st.title("Plataforma de Organização de Escalas 🩺")

# Email que define quem é o administrador
ADMIN_EMAIL = "admin@email.com" # Mude para o seu email de admin

# --- Configuração do Google OAuth (Opcional) ---
# Para habilitar login com Google, adicione as seguintes variáveis em .streamlit/secrets.toml:
# GOOGLE_CLIENT_ID = "seu-client-id.apps.googleusercontent.com"
# GOOGLE_CLIENT_SECRET = "seu-client-secret"
# GOOGLE_REDIRECT_URI = "https://sua-app.streamlit.app"

def get_google_oauth_config():
    """Retorna a configuração do Google OAuth se disponível."""
    if not OAUTH_AVAILABLE:
        return None
    
    try:
        client_id = st.secrets.get("GOOGLE_CLIENT_ID")
        client_secret = st.secrets.get("GOOGLE_CLIENT_SECRET")
        redirect_uri = st.secrets.get("GOOGLE_REDIRECT_URI")
        
        if client_id and client_secret and redirect_uri:
            return {
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "authorize_endpoint": "https://accounts.google.com/o/oauth2/v2/auth",
                "token_endpoint": "https://oauth2.googleapis.com/token",
                "userinfo_endpoint": "https://www.googleapis.com/oauth2/v1/userinfo",
                "scope": "openid email profile"
            }
    except:
        pass
    
    return None

# --- Conexão com Google Sheets ---
# Usa os segredos (Secrets) do Streamlit Cloud
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Verifica se está usando Service Account (necessário para write operations)
    if not hasattr(st, 'secrets') or 'connections' not in st.secrets or 'gsheets' not in st.secrets['connections']:
        st.error("⚠️ **ERRO DE CONFIGURAÇÃO**: Google Sheets não está configurado!")
        st.error("Você precisa configurar o Service Account para usar esta aplicação.")
        st.info("📖 **Consulte o guia completo**: [GOOGLE_SHEETS_SETUP.md](https://github.com/MiguelJanssenn/Escala/blob/main/GOOGLE_SHEETS_SETUP.md)")
        st.stop()
    
    # Verifica se está usando service account
    gsheets_config = st.secrets['connections']['gsheets']
    if 'type' not in gsheets_config or gsheets_config['type'] != 'service_account':
        st.error("⚠️ **ERRO DE AUTENTICAÇÃO**: Service Account não configurado!")
        st.warning("""
        O erro **"Public Spreadsheet cannot be written to"** ocorre porque você está tentando 
        usar uma planilha pública (somente leitura) em vez de autenticação com Service Account.
        
        **Para corrigir este problema:**
        1. Crie um Service Account no Google Cloud Console
        2. Configure o arquivo `.streamlit/secrets.toml` com as credenciais do Service Account
        3. Compartilhe sua planilha Google Sheets com o email do Service Account
        """)
        st.info("📖 **Guia completo de configuração**: [GOOGLE_SHEETS_SETUP.md](https://github.com/MiguelJanssenn/Escala/blob/main/GOOGLE_SHEETS_SETUP.md)")
        st.stop()
        
except Exception as e:
    st.error("⚠️ **ERRO ao conectar com Google Sheets**")
    st.error(f"Detalhes do erro: {str(e)}")
    
    if "Public Spreadsheet cannot be written to" in str(e):
        st.warning("""
        **Este erro significa que você está tentando usar uma planilha pública (somente leitura).**
        
        Para usar esta aplicação, você precisa:
        1. Criar um Service Account no Google Cloud
        2. Configurar as credenciais no arquivo `.streamlit/secrets.toml`
        3. Compartilhar sua planilha com o email do Service Account
        """)
    
    st.info("📖 **Consulte o guia completo**: [GOOGLE_SHEETS_SETUP.md](https://github.com/MiguelJanssenn/Escala/blob/main/GOOGLE_SHEETS_SETUP.md)")
    st.info("💡 **Exemplo de configuração**: Veja o arquivo `.streamlit/secrets.toml.example`")
    st.stop()

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
            df_combined = pd.concat([df_emails, new_email_data], ignore_index=True)
            conn.update(worksheet="emails_permitidos", data=df_combined)
        except:
            # Se a planilha não existir, cria com o primeiro email
            conn.update(worksheet="emails_permitidos", data=new_email_data)
        
        return True, "Email adicionado à lista de permitidos!"
    except Exception as e:
        error_msg = str(e)
        if "Public Spreadsheet cannot be written to" in error_msg:
            return False, "⚠️ ERRO DE CONFIGURAÇÃO: O Google Sheets não está configurado com Service Account. Consulte GOOGLE_SHEETS_SETUP.md para instruções."
        return False, f"Erro ao adicionar email: {error_msg}"

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
        error_msg = str(e)
        if "Public Spreadsheet cannot be written to" in error_msg:
            return False, "⚠️ ERRO DE CONFIGURAÇÃO: O Google Sheets não está configurado com Service Account. Consulte GOOGLE_SHEETS_SETUP.md para instruções."
        return False, f"Erro ao remover email: {error_msg}"

def get_user_data(email):
    """Busca os dados do usuário pelo email."""
    try:
        df_users = conn.read(worksheet="usuarios", usecols=[0, 1, 2, 3], ttl=5)
        if not df_users.empty:
            user_data = df_users[df_users['email'] == email]
            if not user_data.empty:
                return user_data.iloc[0]
    except Exception as e:
        # Se a planilha não existir ainda ou houver erro de autenticação, retorna None
        # O erro será tratado no contexto de uso
        pass
    return None

def register_user(name, matricula, email, password):
    """Registra um novo usuário na planilha."""
    if get_user_data(email) is not None:
        return False, "E-mail já cadastrado."
    
    # Verifica se o email está na lista de permitidos
    # O email do administrador sempre pode se registrar
    allowed_emails = get_allowed_emails()
    if email != ADMIN_EMAIL and email not in allowed_emails:
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
        try:
            df_users = conn.read(worksheet="usuarios")
            df_combined = pd.concat([df_users, new_user_data], ignore_index=True)
            conn.update(worksheet="usuarios", data=df_combined)
        except:
            # Se a planilha não existir, cria com o primeiro usuário
            conn.update(worksheet="usuarios", data=new_user_data)
        return True, "Usuário registrado com sucesso!"
    except Exception as e:
        error_msg = str(e)
        if "Public Spreadsheet cannot be written to" in error_msg:
            return False, "⚠️ ERRO DE CONFIGURAÇÃO: O Google Sheets não está configurado com Service Account. Consulte GOOGLE_SHEETS_SETUP.md para instruções."
        return False, f"Erro ao registrar: {error_msg}"

def register_user_oauth(name, email):
    """Registra um novo usuário via OAuth (sem senha)."""
    if get_user_data(email) is not None:
        return False, "E-mail já cadastrado."
    
    # Verifica se o email está na lista de permitidos
    # O email do administrador sempre pode se registrar
    allowed_emails = get_allowed_emails()
    if email != ADMIN_EMAIL and email not in allowed_emails:
        return False, "E-mail não autorizado. Entre em contato com o administrador para solicitar acesso."
    
    # Para usuários OAuth, não há senha (usa hash vazio como marcador)
    new_user_data = pd.DataFrame([{
        "nome": name,
        "matricula": "OAUTH",  # Matrícula padrão para usuários OAuth
        "email": email,
        "senha_hash": "OAUTH_USER"  # Marcador para identificar usuários OAuth
    }])
    
    try:
        # Lê a planilha de usuários para encontrar a próxima linha vazia
        try:
            df_users = conn.read(worksheet="usuarios")
            df_combined = pd.concat([df_users, new_user_data], ignore_index=True)
            conn.update(worksheet="usuarios", data=df_combined)
        except:
            # Se a planilha não existir, cria com o primeiro usuário
            conn.update(worksheet="usuarios", data=new_user_data)
        return True, "Usuário registrado com sucesso via Google!"
    except Exception as e:
        error_msg = str(e)
        if "Public Spreadsheet cannot be written to" in error_msg:
            return False, "⚠️ ERRO DE CONFIGURAÇÃO: O Google Sheets não está configurado com Service Account. Consulte GOOGLE_SHEETS_SETUP.md para instruções."
        return False, f"Erro ao registrar: {error_msg}"

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
        df_combined = pd.concat([df_atividades, new_atividade], ignore_index=True)
        conn.update(worksheet="atividades", data=df_combined)
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
        st.subheader("Login com Email e Senha")
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Senha", type="password")
            login_button = st.form_submit_button("Entrar")
            
            if login_button:
                user_data = get_user_data(email)
                if user_data is not None:
                    # Verifica se é usuário OAuth ou tradicional
                    if user_data['senha_hash'] == "OAUTH_USER":
                        st.error("Esta conta foi criada com Google. Use 'Login com Google' abaixo.")
                    elif check_password(password, user_data['senha_hash']):
                        st.session_state['logged_in'] = True
                        st.session_state['user_name'] = user_data['nome']
                        st.session_state['user_email'] = user_data['email']
                        st.session_state['is_admin'] = (user_data['email'] == ADMIN_EMAIL)
                        st.rerun() # Recarrega a página para o estado "logado"
                    else:
                        st.error("Email ou senha incorretos.")
                else:
                    st.error("Email ou senha incorretos.")
        
        # Adiciona opção de login com Google se estiver configurado
        oauth_config = get_google_oauth_config()
        if oauth_config:
            st.divider()
            st.subheader("Ou faça login com Google")
            
            oauth2 = OAuth2Component(
                oauth_config["client_id"],
                oauth_config["client_secret"],
                oauth_config["authorize_endpoint"],
                oauth_config["token_endpoint"],
                oauth_config["token_endpoint"],
                None
            )
            
            result = oauth2.authorize_button(
                name="Login com Google",
                redirect_uri=oauth_config["redirect_uri"],
                scope=oauth_config["scope"],
                key="google_oauth",
                extras_params={"access_type": "offline", "prompt": "consent"}
            )
            
            if result and 'token' in result:
                # Busca informações do usuário
                import requests
                headers = {"Authorization": f"Bearer {result['token']['access_token']}"}
                response = requests.get(oauth_config["userinfo_endpoint"], headers=headers)
                
                if response.status_code == 200:
                    user_info = response.json()
                    email = user_info.get('email', '').lower()
                    name = user_info.get('name', '')
                    
                    # Verifica se o usuário existe
                    user_data = get_user_data(email)
                    
                    if user_data is not None:
                        # Usuário já existe, faz login
                        st.session_state['logged_in'] = True
                        st.session_state['user_name'] = user_data['nome']
                        st.session_state['user_email'] = user_data['email']
                        st.session_state['is_admin'] = (user_data['email'] == ADMIN_EMAIL)
                        st.rerun()
                    else:
                        # Usuário não existe, tenta registrar automaticamente
                        success, message = register_user_oauth(name, email)
                        if success:
                            # Registrou com sucesso, faz login automaticamente
                            st.session_state['logged_in'] = True
                            st.session_state['user_name'] = name
                            st.session_state['user_email'] = email
                            st.session_state['is_admin'] = (email == ADMIN_EMAIL)
                            st.success(message)
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(message)
                else:
                    st.error("Erro ao obter informações do usuário do Google.")
        else:
            st.info("💡 **Dica:** O administrador pode habilitar o login com Google configurando as credenciais OAuth no Streamlit Secrets.")

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
