# Plataforma de Organização de Escalas

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

### Credenciais padrão do administrador:

- **Email**: `admin@email.com`
- **Senha**: A que você definir no primeiro registro

**Importante**: 
- O administrador pode se registrar diretamente sem precisar estar na lista de emails permitidos
- Após o login, você terá acesso ao painel do administrador
- No menu "Gerenciar Emails Permitidos", você pode adicionar outros usuários à plataforma

### Para alterar o email do administrador:

Se desejar usar outro email como administrador, edite o arquivo `app.py` na linha 13:

```python
ADMIN_EMAIL = "seu-email@exemplo.com"  # Altere aqui
```

## Funcionalidades

- **Administrador**: Pode gerenciar escalas, configurar regras e controlar quem pode se cadastrar
- **Participantes**: Podem escolher horários, ver suas escalas e solicitar trocas de horários

## Documentação

Para mais detalhes sobre a funcionalidade de whitelist de emails, veja [WHITELIST_FEATURE.md](WHITELIST_FEATURE.md)
