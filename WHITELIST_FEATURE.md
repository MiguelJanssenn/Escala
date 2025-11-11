# Email Whitelist Feature

## Descrição

Esta funcionalidade permite que o administrador controle quais emails podem se cadastrar na plataforma. Apenas usuários com emails previamente autorizados pelo administrador poderão completar o registro.

## Como Funciona

### Para Administradores

1. **Fazer login como administrador** usando o email definido em `ADMIN_EMAIL` (padrão: `admin@email.com`)

2. **Acessar o gerenciamento de emails**:
   - No menu lateral, selecione "Gerenciar Emails Permitidos"

3. **Adicionar emails autorizados**:
   - Digite o email que deseja autorizar no campo "Email para permitir cadastro"
   - Clique em "Adicionar Email"
   - O email será normalizado (convertido para minúsculas e removidos espaços)

4. **Visualizar emails autorizados**:
   - A lista completa de emails autorizados é exibida em uma tabela

5. **Remover emails autorizados**:
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

## Benefícios

- ✅ Controle completo sobre quem pode acessar a plataforma
- ✅ Previne registros não autorizados
- ✅ Interface simples para gerenciamento
- ✅ Validação automática durante o registro
- ✅ Mensagens claras para usuários não autorizados
