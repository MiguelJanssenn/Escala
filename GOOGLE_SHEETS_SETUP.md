# Configuração do Google Sheets com Service Account

## Problema: "Public Spreadsheet cannot be written to"

Se você está recebendo o erro **"Erro ao registrar: Public Spreadsheet cannot be written to, use Service Account authentication to enable CRUD methods on your Spreadsheets"**, isso significa que o aplicativo precisa de autenticação com Service Account do Google para poder criar, atualizar e deletar dados no Google Sheets.

## O que é um Service Account?

Um Service Account é uma conta especial do Google Cloud que permite que aplicações acessem e modifiquem recursos do Google (como Google Sheets) de forma programática, sem intervenção do usuário.

## Passo a Passo para Configurar

### Passo 1: Criar um Projeto no Google Cloud Console

1. **Acesse o Google Cloud Console**: https://console.cloud.google.com/

2. **Crie um novo projeto** (ou use um existente):
   - Clique em "Select a project" no topo da página
   - Clique em "New Project"
   - Nome do projeto: "Plataforma-Escalas" (ou outro nome de sua preferência)
   - Clique em "Create"

### Passo 2: Habilitar as APIs Necessárias

1. **No menu lateral**, vá em "APIs & Services" > "Library"

2. **Habilite a Google Sheets API**:
   - Pesquise por "Google Sheets API"
   - Clique nela
   - Clique em "Enable"

3. **Habilite a Google Drive API**:
   - Volte para "Library"
   - Pesquise por "Google Drive API"
   - Clique nela
   - Clique em "Enable"

### Passo 3: Criar um Service Account

1. **No menu lateral**, vá em "APIs & Services" > "Credentials"

2. **Clique em "Create Credentials"** > "Service Account"

3. **Preencha os detalhes**:
   - Service account name: "escalas-service-account" (ou outro nome)
   - Service account ID: será gerado automaticamente
   - Description: "Service account para gerenciar escalas no Google Sheets"
   - Clique em "Create and Continue"

4. **Permissões do Service Account** (Opcional - pode pular):
   - Clique em "Continue" (sem adicionar role)

5. **Conceder acesso aos usuários** (Opcional):
   - Clique em "Done"

### Passo 4: Criar e Baixar a Chave do Service Account

1. **Na lista de Service Accounts**, clique no service account que você acabou de criar

2. **Vá para a aba "Keys"**

3. **Clique em "Add Key"** > "Create new key"

4. **Selecione o tipo de chave**:
   - Escolha "JSON"
   - Clique em "Create"

5. **O arquivo JSON será baixado automaticamente**
   - Guarde este arquivo com segurança! Ele contém credenciais sensíveis
   - Exemplo de nome: `plataforma-escalas-xxxxx.json`

### Passo 5: Criar e Compartilhar o Google Sheets

1. **Acesse o Google Sheets**: https://sheets.google.com/

2. **Crie uma nova planilha** ou use uma existente

3. **Nomeie sua planilha**:
   - Por exemplo: "Escalas-Medicas"

4. **IMPORTANTE: Compartilhe a planilha com o Service Account**:
   - Clique em "Share" (Compartilhar) no canto superior direito
   - No arquivo JSON que você baixou, procure o campo `client_email`
   - Copie o email (algo como: `escalas-service-account@plataforma-escalas.iam.gserviceaccount.com`)
   - Cole este email no campo "Add people and groups"
   - Selecione "Editor" como permissão
   - Clique em "Send" (pode desmarcar "Notify people")

### Passo 6: Configurar o Streamlit Secrets

Agora você precisa copiar as credenciais do arquivo JSON para a configuração do Streamlit.

#### Para Streamlit Cloud (Produção):

1. **Acesse o Streamlit Cloud**: https://share.streamlit.io/

2. **Selecione sua aplicação**

3. **Vá em Settings** (ícone de engrenagem) > "Secrets"

4. **Copie o conteúdo do arquivo `.streamlit/secrets.toml.example`** e cole no editor

5. **Substitua os valores** com os valores do seu arquivo JSON:
   
   Abra o arquivo JSON que você baixou e copie os valores:
   
   ```toml
   [connections.gsheets]
   spreadsheet = "Nome-da-sua-planilha"  # Use o nome exato da planilha
   
   type = "service_account"
   project_id = "seu-project-id"  # Do JSON
   private_key_id = "sua-private-key-id"  # Do JSON
   private_key = """-----BEGIN PRIVATE KEY-----
   Sua chave privada aqui (copie do JSON, incluindo as quebras de linha)
   -----END PRIVATE KEY-----
   """
   client_email = "seu-service-account@seu-projeto.iam.gserviceaccount.com"  # Do JSON
   client_id = "seu-client-id"  # Do JSON
   auth_uri = "https://accounts.google.com/o/oauth2/auth"
   token_uri = "https://oauth2.googleapis.com/token"
   auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
   client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."  # Do JSON
   ```

6. **Clique em "Save"**

7. **Reinicie a aplicação** se necessário

#### Para Desenvolvimento Local:

1. **Crie o arquivo `.streamlit/secrets.toml`** na raiz do projeto:
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```

2. **Edite o arquivo** e substitua os valores conforme explicado acima

3. **IMPORTANTE**: Este arquivo está no `.gitignore` e não será commitado. Nunca faça commit de credenciais!

### Passo 7: Testar a Configuração

1. **Execute a aplicação**:
   ```bash
   streamlit run app.py
   ```

2. **Tente fazer o registro**:
   - Vá para a aba "Registrar"
   - Preencha os campos com o email do administrador: `admin@email.com`
   - Complete o registro
   - Se tudo estiver configurado corretamente, você não verá mais o erro!

## Estrutura das Planilhas

O aplicativo criará automaticamente as seguintes abas (worksheets) na sua planilha:

1. **usuarios**: Armazena os dados dos usuários registrados
   - Colunas: nome, matricula, email, senha_hash

2. **emails_permitidos**: Lista de emails autorizados para cadastro
   - Colunas: email

3. **atividades**: Atividades/plantões da escala
   - Colunas: escala_nome, tipo, data, horario, vagas, id_atividade

4. **escolhas**: Escolhas dos participantes
   - Colunas: id_atividade, nome_participante

Não é necessário criar essas abas manualmente. O aplicativo as criará quando necessário.

## Segurança

⚠️ **IMPORTANTE**:
- **NUNCA** compartilhe o arquivo JSON do Service Account publicamente
- **NUNCA** faça commit do arquivo JSON ou do `secrets.toml` no Git
- O arquivo `.gitignore` já está configurado para ignorar `.streamlit/secrets.toml`
- No Streamlit Cloud, os secrets são armazenados de forma segura e criptografada
- Somente compartilhe a planilha Google Sheets com o email do Service Account

## Solução de Problemas

### Erro: "Permission denied" ou "Spreadsheet not found"

**Solução**: Certifique-se de que você compartilhou a planilha Google Sheets com o email do Service Account (client_email do JSON).

### Erro: "Invalid credentials"

**Solução**: Verifique se você copiou todos os valores corretamente do JSON para o secrets.toml, especialmente a `private_key` (incluindo `-----BEGIN PRIVATE KEY-----` e `-----END PRIVATE KEY-----`).

### Erro: "API has not been used in project"

**Solução**: Certifique-se de que você habilitou tanto a Google Sheets API quanto a Google Drive API no Google Cloud Console.

### A private_key tem caracteres especiais

**Solução**: Use aspas triplas (""") para valores multi-linha no TOML, como mostrado no exemplo acima para `private_key`.

## Diferença entre Service Account e Public Spreadsheet

| Aspecto | Public Spreadsheet | Service Account |
|---------|-------------------|-----------------|
| Acesso | Somente leitura | Leitura e escrita |
| Configuração | Simples (apenas URL) | Requer credenciais |
| Segurança | Qualquer um com link pode ler | Acesso controlado |
| Use quando | Apenas ler dados públicos | Aplicação precisa modificar dados |

## Próximos Passos

Após configurar o Service Account com sucesso:

1. ✅ Faça o primeiro registro como administrador usando o email `admin@email.com`
2. ✅ Gerencie emails permitidos no menu de administrador
3. ✅ Crie escalas e atividades
4. ✅ (Opcional) Configure o Google OAuth para login com Google - veja [GOOGLE_OAUTH_SETUP.md](GOOGLE_OAUTH_SETUP.md)

## Referências

- [Documentação do Google Service Accounts](https://cloud.google.com/iam/docs/service-accounts)
- [Documentação do gspread (biblioteca usada)](https://docs.gspread.org/en/latest/oauth2.html)
- [Streamlit Secrets Management](https://docs.streamlit.io/streamlit-community-cloud/get-started/deploy-an-app/connect-to-data-sources/secrets-management)
