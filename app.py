# Exemplo de como a conexão e a leitura seriam feitas

from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Criar a conexão (usando os Secrets do Streamlit)
conn = st.connection("gsheets", type=GSheetsConnection)

# --- Para ler atividades ---
df_atividades = conn.read(
    worksheet="atividades",
    usecols=[0, 1, 2, 3] # Colunas Tipo, Data, Horario, Vagas
)

# --- Para adicionar uma nova atividade ---
nova_atividade = pd.DataFrame([
    {
        'Tipo': tipo_atividade,
        'Data': data_atividade.strftime('%Y-%m-%d'),
        'Horario': horario_atividade.strftime('%H:%M'),
        'Vagas': vagas
    }
])
# Concatena o dataframe existente com a nova linha
df_atualizado = pd.concat([df_atividades, nova_atividade])
# Escreve o dataframe completo de volta na planilha
conn.update(worksheet="atividades", data=df_atualizado)
