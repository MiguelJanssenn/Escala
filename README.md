# Plataforma de Organização de Escalas

## ⚠️ CONFIGURAÇÃO OBRIGATÓRIA - Google Sheets Service Account

**Antes de usar a aplicação, você DEVE configurar o Google Sheets com Service Account!**

Se você receber o erro: *"Public Spreadsheet cannot be written to, use Service Account authentication to enable CRUD methods on your Spreadsheets"*, isso significa que a autenticação com Service Account não foi configurada.

📖 **Siga o guia completo**: [GOOGLE_SHEETS_SETUP.md](GOOGLE_SHEETS_SETUP.md)

Este guia mostrará como:
1. Criar um Service Account no Google Cloud
2. Habilitar as APIs necessárias (Google Sheets e Drive)
3. Baixar as credenciais JSON
4. Configurar o arquivo `secrets.toml` do Streamlit
5. Compartilhar sua planilha com o Service Account

**Sem esta configuração, o aplicativo não conseguirá salvar ou ler dados!**

---

## Primeiro Acesso - Login do Administrador

### Como criar a conta de administrador:

1. **Acesse a aplicação** e vá para a aba "Registrar"

2. **Preencha o formulário de registro**:
   - Nome Completo: (seu nome)
   - Matrícula: (sua matrícula)
   - Email: **admin@email.com**
   - Senha: (escolha uma senha segura)
   - Confirmar Senha: (mesma senha)

3. **Clique em "Registrar"**

4. **Faça login**:
   - Acesse a aba "Login"
   - Email: **admin@email.com**
   - Senha: (a senha que você definiu)
   - Clique em "Entrar"
   - **OU** use "Login com Google" (se configurado)

### Credenciais padrão do administrador:

- **Email**: `admin@email.com`
- **Senha**: A que você definir no primeiro registro

**Importante**: 
- O administrador pode se registrar diretamente sem precisar estar na lista de emails permitidos
- Após o login, você terá acesso ao painel do administrador
- No menu "Gerenciar Emails Permitidos", você pode adicionar outros usuários à plataforma

### Para alterar o email do administrador:

Se desejar usar outro email como administrador, edite o arquivo `app.py` na linha 20:

```python
ADMIN_EMAIL = "seu-email@exemplo.com"  # Altere aqui
```

## Funcionalidades

- **Administrador**: Pode gerenciar escalas, configurar regras e controlar quem pode se cadastrar
- **Participantes**: Podem escolher horários, ver suas escalas e solicitar trocas de horários
- **Login com Google (Opcional)**: Permite login simplificado usando contas Google

## Métodos de Login

### Login Tradicional (Email/Senha)
- Usuários se registram com email, senha e matrícula
- Login usando email e senha cadastrados

### Login com Google OAuth (Opcional)
- **Simplicidade**: Login com um clique usando conta Google
- **Segurança**: Sem necessidade de criar senhas adicionais
- **Auto-registro**: Usuários autorizados são registrados automaticamente
- **Como habilitar**: Consulte [GOOGLE_OAUTH_SETUP.md](GOOGLE_OAUTH_SETUP.md)

## Documentação

- **🔧 Configuração do Google Sheets (OBRIGATÓRIO)**: [GOOGLE_SHEETS_SETUP.md](GOOGLE_SHEETS_SETUP.md)
- **Whitelist de Emails**: [WHITELIST_FEATURE.md](WHITELIST_FEATURE.md)
- **Configuração do Google OAuth (Opcional)**: [GOOGLE_OAUTH_SETUP.md](GOOGLE_OAUTH_SETUP.md)

## Estrutura de Arquivos

```
.
├── app.py                          # Aplicação principal
├── requirements.txt                # Dependências Python
├── .streamlit/
│   ├── secrets.toml.example       # Exemplo de configuração
│   └── secrets.toml               # Suas credenciais (não commitar!)
├── GOOGLE_SHEETS_SETUP.md         # Guia de configuração do Google Sheets
├── GOOGLE_OAUTH_SETUP.md          # Guia de configuração do OAuth
├── WHITELIST_FEATURE.md           # Documentação da whitelist
└── README.md                      # Este arquivo
```
