# Email Whitelist Feature

## Descrição

Esta funcionalidade permite que o administrador controle quais emails podem se cadastrar na plataforma. Apenas usuários com emails previamente autorizados pelo administrador poderão completar o registro.

## Como Funciona

### Configuração Inicial do Administrador

**Importante:** O administrador pode se registrar diretamente sem precisar estar na lista de emails permitidos.

1. **Primeiro Acesso - Registro do Administrador**:
   - Acesse a aba "Registrar"
   - Preencha os campos:
     - Nome Completo
     - Matrícula
     - Email: **admin@email.com** (este é o email definido no código)
     - Senha (escolha uma senha segura)
   - Clique em "Registrar"
   - O administrador será registrado automaticamente, mesmo sem estar na lista de emails permitidos

2. **Login como Administrador**:
   - Acesse a aba "Login"
   - Email: **admin@email.com**
   - Senha: (a senha que você definiu no registro)
   - Clique em "Entrar"

3. **Alterar o Email do Administrador** (opcional):
   - Se desejar usar outro email como administrador, edite a linha 13 do arquivo `app.py`:
   - Altere `ADMIN_EMAIL = "admin@email.com"` para seu email desejado
   - Depois, registre-se usando esse email

### Para Administradores

1. **Acessar o gerenciamento de emails**:
   - Após fazer login como administrador, no menu lateral selecione "Gerenciar Emails Permitidos"

2. **Adicionar emails autorizados**:
   - Digite o email que deseja autorizar no campo "Email para permitir cadastro"
   - Clique em "Adicionar Email"
   - O email será normalizado (convertido para minúsculas e removidos espaços)

3. **Visualizar emails autorizados**:
   - A lista completa de emails autorizados é exibida em uma tabela

4. **Remover emails autorizados**:
   - Selecione o email no dropdown
   - Clique em "Remover Email Selecionado"

### Para Usuários

1. **Solicitar autorização**:
   - Entre em contato com o administrador para que seu email seja adicionado à lista de permitidos

2. **Realizar cadastro**:
   - Acesse a aba "Registrar"
   - Preencha todos os campos (Nome, Matrícula, Email, Senha)
   - **Importante**: Use o email exatamente como foi autorizado pelo administrador
   - Clique em "Registrar"

3. **Mensagens possíveis**:
   - ✅ "Usuário registrado com sucesso!" - Cadastro aprovado
   - ❌ "E-mail não autorizado. Entre em contato com o administrador para solicitar acesso." - Email não está na lista de permitidos
   - ❌ "E-mail já cadastrado." - Este email já possui uma conta

## Estrutura Técnica

### Nova Planilha no Google Sheets

É necessário criar uma nova planilha (worksheet) chamada **"emails_permitidos"** com a seguinte estrutura:

| email |
|-------|
| usuario1@example.com |
| usuario2@example.com |

A planilha será criada automaticamente quando o administrador adicionar o primeiro email.

### Funções Adicionadas

- `get_allowed_emails()`: Busca a lista de emails permitidos
- `add_allowed_email(email)`: Adiciona um email à lista
- `remove_allowed_email(email)`: Remove um email da lista

### Modificações no Registro

A função `register_user()` foi modificada para validar se o email está na lista de permitidos antes de criar a conta. 

**Exceção importante:** O email do administrador (definido em `ADMIN_EMAIL`) pode se registrar sem estar na lista de permitidos, garantindo que o administrador possa fazer o primeiro acesso e configurar a plataforma.

## Benefícios

- ✅ Controle completo sobre quem pode acessar a plataforma
- ✅ Previne registros não autorizados
- ✅ Interface simples para gerenciamento
- ✅ Validação automática durante o registro
- ✅ Mensagens claras para usuários não autorizados
