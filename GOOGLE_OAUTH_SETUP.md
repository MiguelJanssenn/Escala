# Configuração do Login com Google OAuth

## O que é o Login com Google?

O login com Google permite que os usuários façam login na plataforma usando suas contas Google, eliminando a necessidade de criar e lembrar de senhas adicionais. Isso simplifica o processo de autenticação e melhora a experiência do usuário.

## Benefícios

- ✅ **Simplicidade**: Usuários fazem login com um clique usando suas contas Google
- ✅ **Segurança**: Não é necessário armazenar senhas, pois a autenticação é feita pelo Google
- ✅ **Conveniência**: Não é preciso lembrar de outra senha
- ✅ **Auto-registro**: Usuários autorizados são registrados automaticamente no primeiro login
- ✅ **Compatibilidade**: Funciona junto com o login tradicional por email/senha

## Como Habilitar o Login com Google

### Passo 1: Criar Credenciais OAuth no Google Cloud Console

1. **Acesse o Google Cloud Console**:
   - Vá para https://console.cloud.google.com/

2. **Crie um Novo Projeto** (ou selecione um existente):
   - Clique em "Select a project" no topo da página
   - Clique em "New Project"
   - Dê um nome ao projeto (ex: "Plataforma Escalas")
   - Clique em "Create"

3. **Habilite a Google+ API**:
   - No menu lateral, vá em "APIs & Services" > "Library"
   - Procure por "Google+ API"
   - Clique em "Enable"

4. **Configure a Tela de Consentimento OAuth**:
   - No menu lateral, vá em "APIs & Services" > "OAuth consent screen"
   - Selecione "External" (ou "Internal" se estiver usando Google Workspace)
   - Clique em "Create"
   - Preencha os campos obrigatórios:
     - App name: "Plataforma de Escalas"
     - User support email: seu email
     - Developer contact information: seu email
   - Clique em "Save and Continue"
   - Em "Scopes", clique em "Add or Remove Scopes"
   - Adicione os seguintes escopos:
     - `openid`
     - `email`
     - `profile`
   - Clique em "Save and Continue"
   - Clique em "Back to Dashboard"

5. **Crie as Credenciais OAuth**:
   - No menu lateral, vá em "APIs & Services" > "Credentials"
   - Clique em "Create Credentials" > "OAuth 2.0 Client ID"
   - Application type: "Web application"
   - Name: "Plataforma Escalas Web Client"
   - Authorized JavaScript origins: adicione a URL da sua aplicação Streamlit
     - Exemplo: `https://sua-app.streamlit.app`
     - Para desenvolvimento local: `http://localhost:8501`
   - Authorized redirect URIs: adicione a URL de redirecionamento
     - Exemplo: `https://sua-app.streamlit.app`
     - Para desenvolvimento local: `http://localhost:8501`
   - Clique em "Create"
   - **Importante**: Copie o "Client ID" e "Client Secret" que serão exibidos

### Passo 2: Configurar as Credenciais no Streamlit

#### Para Streamlit Cloud:

1. **Acesse suas configurações no Streamlit Cloud**:
   - Vá para https://share.streamlit.io/
   - Selecione sua aplicação
   - Clique em "Settings" (ícone de engrenagem)
   - Vá em "Secrets"

2. **Adicione as seguintes variáveis**:
   ```toml
   GOOGLE_CLIENT_ID = "seu-client-id.apps.googleusercontent.com"
   GOOGLE_CLIENT_SECRET = "seu-client-secret"
   GOOGLE_REDIRECT_URI = "https://sua-app.streamlit.app"
   ```

3. **Salve as alterações**

#### Para Desenvolvimento Local:

1. **Crie o arquivo `.streamlit/secrets.toml`** na raiz do projeto:
   ```bash
   mkdir -p .streamlit
   touch .streamlit/secrets.toml
   ```

2. **Adicione as credenciais ao arquivo**:
   ```toml
   GOOGLE_CLIENT_ID = "seu-client-id.apps.googleusercontent.com"
   GOOGLE_CLIENT_SECRET = "seu-client-secret"
   GOOGLE_REDIRECT_URI = "http://localhost:8501"
   ```

3. **Importante**: Certifique-se de que `.streamlit/secrets.toml` está no `.gitignore` para não commitar credenciais sensíveis!

### Passo 3: Verificar a Instalação

1. **Certifique-se de que as dependências estão instaladas**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Inicie a aplicação**:
   ```bash
   streamlit run app.py
   ```

3. **Teste o Login com Google**:
   - Acesse a aba "Login"
   - Você deverá ver a opção "Login com Google"
   - Clique no botão e siga o fluxo de autenticação do Google

## Como Funciona

### Para Usuários Novos (Primeiro Acesso com Google):

1. Usuário clica em "Login com Google"
2. É redirecionado para a página de autenticação do Google
3. Faz login com sua conta Google
4. O sistema verifica se o email está na lista de permitidos
5. Se estiver autorizado, o usuário é **automaticamente registrado** e logado
6. Se não estiver autorizado, recebe mensagem para contatar o administrador

### Para Usuários Existentes:

1. Usuário clica em "Login com Google"
2. É redirecionado para a página de autenticação do Google
3. Faz login com sua conta Google
4. O sistema identifica que o email já está cadastrado
5. Usuário é logado automaticamente

### Integração com Whitelist:

- A lista de emails permitidos funciona da mesma forma para login com Google
- O administrador precisa adicionar o email do usuário à lista de permitidos antes que ele possa se registrar
- O email do administrador (configurado em `ADMIN_EMAIL`) sempre pode se registrar

## Segurança

- ✅ As credenciais OAuth são armazenadas de forma segura no Streamlit Secrets
- ✅ A autenticação é feita pelo Google, que é altamente seguro
- ✅ Usuários OAuth são identificados com um marcador especial no banco de dados
- ✅ A whitelist de emails continua protegendo contra acessos não autorizados

## Problemas Comuns

### "Módulo streamlit-oauth não está disponível"

**Solução**: Execute `pip install -r requirements.txt` para instalar todas as dependências.

### "OAuth não está configurado"

**Solução**: Verifique se você adicionou as variáveis `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` e `GOOGLE_REDIRECT_URI` no Streamlit Secrets.

### "Redirect URI mismatch"

**Solução**: Certifique-se de que a URI de redirecionamento configurada no Google Cloud Console é exatamente igual à URI configurada no `GOOGLE_REDIRECT_URI` dos secrets.

### "Email não autorizado"

**Solução**: O administrador precisa adicionar o email do usuário à lista de emails permitidos através do menu "Gerenciar Emails Permitidos".

## Desabilitando o Login com Google

Se você não quiser usar o login com Google, simplesmente não configure as variáveis no Streamlit Secrets. A aplicação continuará funcionando normalmente com login tradicional por email/senha.

## Suporte

Para mais informações sobre OAuth 2.0 do Google, consulte:
- [Documentação Oficial do Google OAuth](https://developers.google.com/identity/protocols/oauth2)
- [Streamlit Secrets](https://docs.streamlit.io/streamlit-community-cloud/get-started/deploy-an-app/connect-to-data-sources/secrets-management)
