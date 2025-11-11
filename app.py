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
        
        # Lê a planilha atual e adiciona o novo email
        try:
            df_emails = conn.read(worksheet="emails_permitidos")
            # Append the new email to the existing dataframe
            new_email_data = pd.DataFrame([{"email": email}])
            updated_emails = pd.concat([df_emails, new_email_data], ignore_index=True)
            conn.update(worksheet="emails_permitidos", data=updated_emails)
        except:
            # Se a planilha não existir, cria com o primeiro email
            new_email_data = pd.DataFrame([{"email": email}])
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
            # Append the new user to the existing dataframe
            updated_users = pd.concat([df_users, new_user_data], ignore_index=True)
            conn.update(worksheet="usuarios", data=updated_users)
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
            # Append the new user to the existing dataframe
            updated_users = pd.concat([df_users, new_user_data], ignore_index=True)
            conn.update(worksheet="usuarios", data=updated_users)
        except:
            # Se a planilha não existir, cria com o primeiro usuário
            conn.update(worksheet="usuarios", data=new_user_data)
        return True, "Usuário registrado com sucesso via Google!"
    except Exception as e:
        error_msg = str(e)
        if "Public Spreadsheet cannot be written to" in error_msg:
            return False, "⚠️ ERRO DE CONFIGURAÇÃO: O Google Sheets não está configurado com Service Account. Consulte GOOGLE_SHEETS_SETUP.md para instruções."
        return False, f"Erro ao registrar: {error_msg}"

def add_atividades_bulk(escala_nome, df_new_atividades):
    """Adiciona múltiplas atividades ao banco de dados."""
    if df_new_atividades.empty:
        return False, "Nenhuma atividade para adicionar."
    
    # Adiciona IDs únicos e nome da escala
    df_new_atividades['id_atividade'] = [str(uuid.uuid4()) for _ in range(len(df_new_atividades))]
    df_new_atividades['escala_nome'] = escala_nome
    
    try:
        try:
            df_atividades = conn.read(worksheet="atividades")
            updated_atividades = pd.concat([df_atividades, df_new_atividades], ignore_index=True)
            conn.update(worksheet="atividades", data=updated_atividades)
        except:
            # Se a planilha não existir, cria com as novas atividades
            conn.update(worksheet="atividades", data=df_new_atividades)
        return True, f"{len(df_new_atividades)} atividade(s) adicionada(s) com sucesso!"
    except Exception as e:
        return False, f"Erro ao adicionar atividades: {e}"

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
        # Append the new activity to the existing dataframe
        updated_atividades = pd.concat([df_atividades, new_atividade], ignore_index=True)
        conn.update(worksheet="atividades", data=updated_atividades)
        return True
    except Exception as e:
        st.error(f"Erro ao adicionar atividade: {e}")
        return False

def get_escala_completa(escala_nome, sort_chronologically=True):
    """Busca a escala com os nomes dos participantes."""
    try:
        df_atividades = conn.read(worksheet="atividades", ttl=5)
        df_escolhas = conn.read(worksheet="escolhas", ttl=5)
        
        atividades_escala = df_atividades[df_atividades['escala_nome'] == escala_nome]
        if atividades_escala.empty:
            return pd.DataFrame(columns=['Tipo', 'Data', 'Horário', 'Vagas', 'Participantes', 'Observações'])
        
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
        
        # Inclui observações se existir, senão cria coluna vazia
        if 'observacoes' in df_final.columns:
            df_final = df_final[['tipo', 'data', 'horario', 'vagas', 'Participantes', 'observacoes']]
            df_final.columns = ['Tipo', 'Data', 'Horário', 'Vagas', 'Participantes', 'Observações']
        else:
            df_final = df_final[['tipo', 'data', 'horario', 'vagas', 'Participantes']]
            df_final.columns = ['Tipo', 'Data', 'Horário', 'Vagas', 'Participantes']
            df_final['Observações'] = ''
        
        # Formata a data para dd/mm/YYYY
        try:
            df_final['data_temp'] = pd.to_datetime(df_final['Data'], format='%d/%m/%Y', errors='coerce')
            if df_final['data_temp'].isna().all():
                # Se falhou, tenta formato YYYY-MM-DD
                df_final['data_temp'] = pd.to_datetime(df_final['Data'], format='%Y-%m-%d', errors='coerce')
            # Converte para dd/mm/YYYY
            df_final['Data'] = df_final['data_temp'].dt.strftime('%d/%m/%Y')
        except:
            pass  # Mantém o formato original se falhar
        
        # Ordena cronologicamente se solicitado
        if sort_chronologically:
            try:
                df_final['data_sort'] = pd.to_datetime(df_final['Data'], format='%d/%m/%Y', errors='coerce')
                if df_final['data_sort'].isna().all():
                    # Se falhou, tenta formato YYYY-MM-DD
                    df_final['data_sort'] = pd.to_datetime(df_final['Data'], format='%Y-%m-%d', errors='coerce')
            except:
                df_final['data_sort'] = pd.to_datetime(df_final['Data'], errors='coerce')
            
            # Extrai o horário inicial para ordenação (ex: "07:00-19:00" -> "07:00")
            df_final['horario_sort'] = df_final['Horário'].str.split('-').str[0].str.strip()
            df_final = df_final.sort_values(['data_sort', 'horario_sort'])
            df_final = df_final.drop(['data_sort', 'horario_sort'], axis=1)
        
        # Remove a coluna temporária se existir
        if 'data_temp' in df_final.columns:
            df_final = df_final.drop('data_temp', axis=1)
        
        return df_final
    except Exception as e:
        st.error(f"Erro ao buscar escala: {e}")
        return pd.DataFrame(columns=['Tipo', 'Data', 'Horário', 'Vagas', 'Participantes', 'Observações'])


def get_current_round(escala_nome):
    """Busca a rodada atual da escala."""
    try:
        df_rounds = conn.read(worksheet="rodadas", ttl=5)
        rounds_escala = df_rounds[df_rounds['escala_nome'] == escala_nome]
        if rounds_escala.empty:
            return None
        # Retorna a rodada com maior número (rodada atual)
        return rounds_escala.loc[rounds_escala['numero_rodada'].idxmax()]
    except:
        return None

def create_new_round(escala_nome):
    """Cria uma nova rodada com ordem aleatória dos participantes."""
    try:
        # Busca todos os usuários (exceto admin)
        df_users = conn.read(worksheet="usuarios", ttl=5)
        participants = df_users[df_users['email'] != ADMIN_EMAIL]['email'].tolist()
        
        if not participants:
            return False, "Nenhum participante cadastrado."
        
        # Embaralha a ordem dos participantes
        import random
        random.shuffle(participants)
        
        # Determina o número da nova rodada
        current_round = get_current_round(escala_nome)
        new_round_number = 1 if current_round is None else int(current_round['numero_rodada']) + 1
        
        # Cria registros para a nova rodada
        round_data = []
        for position, email in enumerate(participants, start=1):
            round_data.append({
                "escala_nome": escala_nome,
                "numero_rodada": new_round_number,
                "posicao": position,
                "email_participante": email,
                "ja_escolheu": False
            })
        
        new_round_df = pd.DataFrame(round_data)
        
        # Salva a nova rodada
        try:
            df_rounds = conn.read(worksheet="rodadas")
            updated_rounds = pd.concat([df_rounds, new_round_df], ignore_index=True)
            conn.update(worksheet="rodadas", data=updated_rounds)
        except:
            # Se a planilha não existir, cria com a nova rodada
            conn.update(worksheet="rodadas", data=new_round_df)
        
        return True, f"Rodada {new_round_number} criada com {len(participants)} participantes!"
    except Exception as e:
        return False, f"Erro ao criar rodada: {e}"

def get_round_order(escala_nome):
    """Retorna a ordem de escolha da rodada atual."""
    try:
        df_rounds = conn.read(worksheet="rodadas", ttl=5)
        current_round = get_current_round(escala_nome)
        
        if current_round is None:
            return pd.DataFrame(columns=['Posição', 'Participante', 'Email', 'Status'])
        
        round_number = current_round['numero_rodada']
        round_data = df_rounds[
            (df_rounds['escala_nome'] == escala_nome) & 
            (df_rounds['numero_rodada'] == round_number)
        ].sort_values('posicao')
        
        # Busca os nomes dos participantes
        df_users = conn.read(worksheet="usuarios", ttl=5)
        round_data = round_data.merge(
            df_users[['email', 'nome']], 
            left_on='email_participante', 
            right_on='email', 
            how='left'
        )
        
        round_data['Status'] = round_data['ja_escolheu'].apply(lambda x: '✅ Escolheu' if x else '⏳ Aguardando')
        
        result = round_data[['posicao', 'nome', 'email_participante', 'Status']]
        result.columns = ['Posição', 'Participante', 'Email', 'Status']
        
        return result
    except Exception as e:
        st.error(f"Erro ao buscar ordem da rodada: {e}")
        return pd.DataFrame(columns=['Posição', 'Participante', 'Email', 'Status'])

def get_current_turn(escala_nome):
    """Retorna o email do participante cuja vez é de escolher."""
    try:
        df_rounds = conn.read(worksheet="rodadas", ttl=5)
        current_round = get_current_round(escala_nome)
        
        if current_round is None:
            return None
        
        round_number = current_round['numero_rodada']
        round_data = df_rounds[
            (df_rounds['escala_nome'] == escala_nome) & 
            (df_rounds['numero_rodada'] == round_number) &
            (df_rounds['ja_escolheu'] == False)
        ].sort_values('posicao')
        
        if round_data.empty:
            return None  # Todos já escolheram
        
        return round_data.iloc[0]['email_participante']
    except:
        return None

def mark_choice_made(escala_nome, email):
    """Marca que um participante já fez sua escolha na rodada atual."""
    try:
        df_rounds = conn.read(worksheet="rodadas")
        current_round = get_current_round(escala_nome)
        
        if current_round is None:
            return False
        
        round_number = current_round['numero_rodada']
        
        # Atualiza o status de ja_escolheu para True
        df_rounds.loc[
            (df_rounds['escala_nome'] == escala_nome) & 
            (df_rounds['numero_rodada'] == round_number) &
            (df_rounds['email_participante'] == email),
            'ja_escolheu'
        ] = True
        
        conn.update(worksheet="rodadas", data=df_rounds)
        return True
    except Exception as e:
        st.error(f"Erro ao marcar escolha: {e}")
        return False

def get_available_activities(escala_nome):
    """Retorna atividades disponíveis (com vagas) ordenadas cronologicamente."""
    try:
        df_atividades = conn.read(worksheet="atividades", ttl=5)
        
        # Filtra pela escala
        atividades_escala = df_atividades[df_atividades['escala_nome'] == escala_nome].copy()
        
        if atividades_escala.empty:
            return pd.DataFrame()
        
        # Conta quantas escolhas já foram feitas para cada atividade
        try:
            df_escolhas = conn.read(worksheet="escolhas", ttl=5)
            escolhas_count = df_escolhas.groupby('id_atividade').size().reset_index(name='ocupadas')
            atividades_escala = atividades_escala.merge(escolhas_count, on='id_atividade', how='left')
            atividades_escala['ocupadas'] = atividades_escala['ocupadas'].fillna(0).astype(int)
        except:
            atividades_escala['ocupadas'] = 0
        
        # Calcula vagas disponíveis
        atividades_escala['vagas_disponiveis'] = atividades_escala['vagas'].astype(int) - atividades_escala['ocupadas']
        
        # Filtra apenas atividades com vagas disponíveis
        atividades_disponiveis = atividades_escala[atividades_escala['vagas_disponiveis'] > 0].copy()
        
        # Ordena cronologicamente
        atividades_disponiveis['data_sort'] = pd.to_datetime(atividades_disponiveis['data'], format='%d/%m/%Y', errors='coerce')
        if atividades_disponiveis['data_sort'].isna().all():
            # Se falhou, tenta formato YYYY-MM-DD
            atividades_disponiveis['data_sort'] = pd.to_datetime(atividades_disponiveis['data'], format='%Y-%m-%d', errors='coerce')
        atividades_disponiveis['horario_sort'] = atividades_disponiveis['horario'].str.split('-').str[0].str.strip()
        atividades_disponiveis = atividades_disponiveis.sort_values(['data_sort', 'horario_sort'])
        
        # Inclui observações se disponível
        if 'observacoes' in atividades_disponiveis.columns:
            return atividades_disponiveis[['id_atividade', 'tipo', 'data', 'horario', 'vagas_disponiveis', 'observacoes']]
        else:
            return atividades_disponiveis[['id_atividade', 'tipo', 'data', 'horario', 'vagas_disponiveis']]
    except Exception as e:
        st.error(f"Erro ao buscar atividades disponíveis: {e}")
        return pd.DataFrame()

def make_choice(escala_nome, email_participante, nome_participante, id_atividade):
    """Registra a escolha de um participante."""
    try:
        # Cria o registro da escolha
        new_choice = pd.DataFrame([{
            "escala_nome": escala_nome,
            "id_atividade": id_atividade,
            "email_participante": email_participante,
            "nome_participante": nome_participante
        }])
        
        # Salva a escolha
        try:
            df_escolhas = conn.read(worksheet="escolhas")
            updated_escolhas = pd.concat([df_escolhas, new_choice], ignore_index=True)
            conn.update(worksheet="escolhas", data=updated_escolhas)
        except:
            # Se a planilha não existir, cria com a primeira escolha
            conn.update(worksheet="escolhas", data=new_choice)
        
        # Marca que o participante já escolheu nesta rodada
        mark_choice_made(escala_nome, email_participante)
        
        return True, "Escolha registrada com sucesso!"
    except Exception as e:
        return False, f"Erro ao registrar escolha: {e}"


# --- Funções de Exportação (Mantidas como estavam) ---
from fpdf import FPDF
import io

def dataframe_to_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    
    # Cabeçalhos - ajusta larguras dinamicamente baseado no número de colunas
    num_cols = len(df.columns)
    if num_cols == 6:
        # Com Observações: Tipo, Data, Horário, Vagas, Participantes, Observações
        col_widths = [25, 20, 25, 12, 60, 38]
    else:
        # Sem Observações
        col_widths = [30, 25, 30, 15, 80]
    
    for i, col in enumerate(df.columns):
        if i < len(col_widths):
            pdf.cell(col_widths[i], 10, col, 1, 0, 'C')
    pdf.ln()
    
    # Dados
    for index, row in df.iterrows():
        for i, item in enumerate(row):
            if i < len(col_widths):
                pdf.multi_cell(col_widths[i], 10, str(item), 1, 'L')
        pdf.ln()
    
    # fpdf2 returns bytearray, convert to bytes for streamlit compatibility
    return bytes(pdf.output())

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
                oauth_config["token_endpoint"],  # refresh_token_endpoint
                None  # revoke_token_endpoint
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

            # Formulário de adição de atividades via planilha
            if escala_nome:
                st.subheader("Adicionar Atividades")
                st.info("💡 Edite a tabela abaixo para adicionar múltiplas atividades de uma vez. As atividades serão ordenadas cronologicamente automaticamente.")
                
                # Inicializa a planilha de edição se não existir
                if 'df_new_activities' not in st.session_state:
                    st.session_state.df_new_activities = pd.DataFrame({
                        'Tipo': ['Plantão', 'Ambulatório', 'Enfermaria'],
                        'Data': ['01/12/2025', '02/12/2025', '03/12/2025'],
                        'Horário': ['07:00-19:00', '08:00-12:00', '13:00-18:00'],
                        'Vagas': [2, 1, 1],
                        'Observações': ['', '', '']
                    })
                
                # Editor de dados
                edited_df = st.data_editor(
                    st.session_state.df_new_activities,
                    num_rows="dynamic",
                    column_config={
                        "Tipo": st.column_config.SelectboxColumn(
                            "Tipo de Atividade",
                            options=["Plantão", "Ambulatório", "Enfermaria"],
                            required=True
                        ),
                        "Data": st.column_config.TextColumn(
                            "Data (dd/mm/AAAA)",
                            required=True
                        ),
                        "Horário": st.column_config.TextColumn(
                            "Horário (ex: 07:00-19:00)",
                            required=True
                        ),
                        "Vagas": st.column_config.NumberColumn(
                            "Número de Vagas",
                            min_value=1,
                            required=True
                        ),
                        "Observações": st.column_config.TextColumn(
                            "Observações",
                            required=False
                        )
                    },
                    hide_index=True,
                    use_container_width=True
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 Salvar Atividades", type="primary"):
                        # Valida e prepara os dados
                        if not edited_df.empty:
                            # Remove linhas vazias
                            edited_df = edited_df.dropna(how='all')
                            
                            if not edited_df.empty:
                                # Converte para o formato esperado
                                df_to_save = edited_df.copy()
                                df_to_save.columns = ['tipo', 'data', 'horario', 'vagas', 'observacoes']
                                
                                # Salva as atividades
                                success, message = add_atividades_bulk(escala_nome, df_to_save)
                                if success:
                                    st.success(message)
                                    # Limpa a planilha de edição
                                    st.session_state.df_new_activities = pd.DataFrame({
                                        'Tipo': [''],
                                        'Data': [''],
                                        'Horário': [''],
                                        'Vagas': [1],
                                        'Observações': ['']
                                    })
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error(message)
                            else:
                                st.warning("Nenhuma atividade para salvar.")
                        else:
                            st.warning("Nenhuma atividade para salvar.")
                
                with col2:
                    if st.button("🗑️ Limpar Planilha"):
                        st.session_state.df_new_activities = pd.DataFrame({
                            'Tipo': [''],
                            'Data': [''],
                            'Horário': [''],
                            'Vagas': [1],
                            'Observações': ['']
                        })
                        st.rerun()
                
                st.divider()
            
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
                
                st.divider()
                
                # Gerenciamento de rodadas
                st.subheader("Gerenciar Rodadas de Escolha")
                
                current_round = get_current_round(escala_nome)
                if current_round is not None:
                    st.info(f"📍 Rodada atual: **{int(current_round['numero_rodada'])}**")
                    
                    # Mostra a ordem da rodada
                    df_order = get_round_order(escala_nome)
                    st.dataframe(df_order, use_container_width=True)
                    
                    # Verifica se todos já escolheram
                    all_chosen = (df_order['Status'] == '✅ Escolheu').all()
                    if all_chosen:
                        st.success("✅ Todos os participantes já escolheram nesta rodada!")
                        if st.button("🔄 Iniciar Nova Rodada"):
                            success, message = create_new_round(escala_nome)
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
                else:
                    st.warning("Nenhuma rodada iniciada para esta escala.")
                    if st.button("🎲 Iniciar Primeira Rodada"):
                        success, message = create_new_round(escala_nome)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)

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
            
            # Seletor de escala
            escala_nome = st.text_input("Digite o nome da escala (ex: 'Dezembro/2025'):")
            
            if escala_nome:
                # Verifica se existe uma rodada ativa
                current_round = get_current_round(escala_nome)
                
                if current_round is None:
                    st.warning("⏳ Nenhuma rodada foi iniciada ainda para esta escala. Aguarde o administrador iniciar a primeira rodada.")
                else:
                    round_number = int(current_round['numero_rodada'])
                    st.info(f"📍 Rodada atual: **{round_number}**")
                    
                    # Mostra a ordem da rodada
                    st.subheader("Ordem de Escolha")
                    df_order = get_round_order(escala_nome)
                    st.dataframe(df_order, use_container_width=True)
                    
                    # Verifica de quem é a vez
                    current_turn = get_current_turn(escala_nome)
                    user_email = st.session_state['user_email']
                    
                    if current_turn is None:
                        st.success("✅ Todos os participantes já escolheram nesta rodada! Aguarde o administrador iniciar a próxima rodada.")
                    elif current_turn == user_email:
                        st.success("🎯 É a sua vez de escolher!")
                        
                        # Mostra atividades disponíveis
                        st.subheader("Atividades Disponíveis (Ordenadas Cronologicamente)")
                        df_available = get_available_activities(escala_nome)
                        
                        if df_available.empty:
                            st.warning("Nenhuma atividade disponível no momento.")
                        else:
                            # Prepara dados para exibição
                            df_display = df_available.copy()
                            if len(df_display.columns) == 6:
                                # Com observações
                                df_display.columns = ['ID', 'Tipo', 'Data', 'Horário', 'Vagas Disponíveis', 'Observações']
                                df_display = df_display[['Tipo', 'Data', 'Horário', 'Vagas Disponíveis', 'Observações']]
                            else:
                                # Sem observações
                                df_display.columns = ['ID', 'Tipo', 'Data', 'Horário', 'Vagas Disponíveis']
                                df_display = df_display[['Tipo', 'Data', 'Horário', 'Vagas Disponíveis']]
                            
                            st.dataframe(df_display, use_container_width=True)
                            
                            # Formulário de escolha
                            with st.form("form_escolha"):
                                st.write("**Selecione uma atividade:**")
                                
                                # Cria opções para o selectbox
                                options = []
                                for idx, row in df_available.iterrows():
                                    option_text = f"{row['tipo']} - {row['data']} - {row['horario']} ({int(row['vagas_disponiveis'])} vaga(s))"
                                    options.append((option_text, row['id_atividade']))
                                
                                selected = st.selectbox(
                                    "Escolha:",
                                    options=range(len(options)),
                                    format_func=lambda x: options[x][0]
                                )
                                
                                submit = st.form_submit_button("✅ Confirmar Escolha", type="primary")
                                
                                if submit:
                                    selected_id = options[selected][1]
                                    success, message = make_choice(
                                        escala_nome, 
                                        user_email, 
                                        st.session_state['user_name'],
                                        selected_id
                                    )
                                    
                                    if success:
                                        st.success(message)
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error(message)
                    else:
                        # Mostra quem está escolhendo no momento
                        try:
                            df_users = conn.read(worksheet="usuarios", ttl=5)
                            current_user = df_users[df_users['email'] == current_turn]
                            if not current_user.empty:
                                current_name = current_user.iloc[0]['nome']
                                st.info(f"⏳ Aguarde sua vez. Escolhendo agora: **{current_name}**")
                            else:
                                st.info(f"⏳ Aguarde sua vez.")
                        except:
                            st.info(f"⏳ Aguarde sua vez.")
                        
                        # Mostra atividades disponíveis (apenas visualização)
                        with st.expander("👁️ Ver Atividades Disponíveis"):
                            df_available = get_available_activities(escala_nome)
                            if not df_available.empty:
                                df_display = df_available.copy()
                                if len(df_display.columns) == 6:
                                    # Com observações
                                    df_display.columns = ['ID', 'Tipo', 'Data', 'Horário', 'Vagas Disponíveis', 'Observações']
                                    df_display = df_display[['Tipo', 'Data', 'Horário', 'Vagas Disponíveis', 'Observações']]
                                else:
                                    # Sem observações
                                    df_display.columns = ['ID', 'Tipo', 'Data', 'Horário', 'Vagas Disponíveis']
                                    df_display = df_display[['Tipo', 'Data', 'Horário', 'Vagas Disponíveis']]
                                st.dataframe(df_display, use_container_width=True)

        elif menu_user == "Minha Escala":
            st.header("Minha Escala Pessoal")
            
            escala_nome = st.text_input("Digite o nome da escala (ex: 'Dezembro/2025'):")
            
            if escala_nome:
                try:
                    df_escolhas = conn.read(worksheet="escolhas", ttl=5)
                    df_atividades = conn.read(worksheet="atividades", ttl=5)
                    
                    # Filtra escolhas do usuário
                    user_email = st.session_state['user_email']
                    minhas_escolhas = df_escolhas[
                        (df_escolhas['email_participante'] == user_email) &
                        (df_escolhas['escala_nome'] == escala_nome)
                    ]
                    
                    if minhas_escolhas.empty:
                        st.info("Você ainda não escolheu nenhuma atividade nesta escala.")
                    else:
                        # Junta com informações das atividades
                        minhas_atividades = minhas_escolhas.merge(
                            df_atividades,
                            on='id_atividade',
                            how='left'
                        )
                        
                        # Prepara dados para exibição
                        if 'observacoes' in minhas_atividades.columns:
                            df_display = minhas_atividades[['tipo', 'data', 'horario', 'observacoes']].copy()
                            df_display.columns = ['Tipo', 'Data', 'Horário', 'Observações']
                        else:
                            df_display = minhas_atividades[['tipo', 'data', 'horario']].copy()
                            df_display.columns = ['Tipo', 'Data', 'Horário']
                        
                        # Ordena cronologicamente
                        df_display['data_sort'] = pd.to_datetime(df_display['Data'], format='%d/%m/%Y', errors='coerce')
                        if df_display['data_sort'].isna().all():
                            # Se falhou, tenta formato YYYY-MM-DD
                            df_display['data_sort'] = pd.to_datetime(df_display['Data'], format='%Y-%m-%d', errors='coerce')
                        df_display['horario_sort'] = df_display['Horário'].str.split('-').str[0].str.strip()
                        df_display = df_display.sort_values(['data_sort', 'horario_sort'])
                        
                        # Remove colunas de ordenação
                        if 'observacoes' in minhas_atividades.columns:
                            df_display = df_display[['Tipo', 'Data', 'Horário', 'Observações']]
                        else:
                            df_display = df_display[['Tipo', 'Data', 'Horário']]
                        
                        st.dataframe(df_display, use_container_width=True)
                        
                        st.success(f"✅ Total de atividades escolhidas: {len(df_display)}")
                except Exception as e:
                    st.error(f"Erro ao carregar suas escolhas: {e}")

        elif menu_user == "Trocar Horário":
            st.header("Solicitar Troca de Horários 🔄")
            st.info("Funcionalidade em desenvolvimento.")
