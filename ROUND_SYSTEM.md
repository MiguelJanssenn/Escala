# Sistema de Rodadas - Guia de Uso

## Visão Geral

O sistema de rodadas permite que os participantes escolham suas atividades de forma justa, com ordem aleatória em cada rodada. Este guia explica como usar as novas funcionalidades.

## Para Administradores

### 1. Adicionar Atividades (Nova Interface)

Agora você pode adicionar múltiplas atividades de uma vez usando a interface de planilha:

1. **Acesse**: Menu Admin → "Criar/Ver Escala"
2. **Digite o nome da escala**: Ex: "Dezembro/2025"
3. **Use a planilha interativa**:
   - Clique nas células para editar
   - Adicione novas linhas clicando no botão "+"
   - Preencha: Tipo, Data (AAAA-MM-DD), Horário, Vagas
4. **Salve**: Clique em "💾 Salvar Atividades"

**Dica**: Todas as atividades são automaticamente ordenadas cronologicamente para os participantes!

### 2. Iniciar uma Rodada

Após adicionar as atividades:

1. Role até a seção "Gerenciar Rodadas de Escolha"
2. Clique em "🎲 Iniciar Primeira Rodada"
3. O sistema irá:
   - Buscar todos os participantes cadastrados
   - Embaralhar a ordem aleatoriamente
   - Criar uma nova rodada

### 3. Acompanhar o Progresso

A interface mostra:
- **Rodada atual**: Número da rodada em andamento
- **Ordem de escolha**: Lista de participantes com status
  - ⏳ Aguardando: Ainda não escolheu
  - ✅ Escolheu: Já fez a escolha

### 4. Iniciar Nova Rodada

Quando todos os participantes escolherem:
1. Aparecerá uma mensagem "✅ Todos os participantes já escolheram"
2. Clique em "🔄 Iniciar Nova Rodada"
3. A ordem será embaralhada novamente

## Para Participantes

### 1. Escolher uma Atividade

1. **Acesse**: Menu → "Escolher Horário"
2. **Digite o nome da escala**: Ex: "Dezembro/2025"
3. **Visualize**:
   - Rodada atual
   - Ordem de escolha
   - Seu status

### 2. Quando For Sua Vez

Quando aparecer "🎯 É a sua vez de escolher!":

1. Veja as atividades disponíveis (em ordem cronológica)
2. Cada linha mostra:
   - Tipo de atividade
   - Data
   - Horário
   - Vagas disponíveis
3. Selecione uma atividade no menu dropdown
4. Clique em "✅ Confirmar Escolha"

### 3. Aguardar Sua Vez

Se não for sua vez:
- Você verá: "⏳ Aguarde sua vez. Escolhendo agora: [Nome]"
- Pode visualizar as atividades disponíveis no menu expansível
- Aguarde até ser sua vez

### 4. Ver Sua Escala Pessoal

1. **Acesse**: Menu → "Minha Escala"
2. **Digite o nome da escala**
3. Veja todas as suas escolhas em **ordem cronológica**

## Estrutura de Dados

### Planilha "rodadas" (Nova)

Esta planilha será criada automaticamente quando você iniciar a primeira rodada.

| Coluna | Descrição |
|--------|-----------|
| escala_nome | Nome da escala (ex: "Dezembro/2025") |
| numero_rodada | Número da rodada (1, 2, 3, ...) |
| posicao | Posição na ordem de escolha (1, 2, 3, ...) |
| email_participante | Email do participante |
| ja_escolheu | True/False - indica se já escolheu |

## Fluxo Completo de Uso

### Configuração Inicial (Admin)

1. ✅ Configure o Google Sheets com Service Account
2. ✅ Registre-se como administrador (admin@email.com)
3. ✅ Adicione emails permitidos para participantes
4. ✅ Participantes se registram

### Criação da Escala (Admin)

1. 📝 Escolha um nome para a escala
2. 📊 Adicione atividades usando a planilha
3. 💾 Salve as atividades
4. 🎲 Inicie a primeira rodada

### Rodada de Escolhas (Participantes)

1. 👤 Cada participante aguarda sua vez (ordem aleatória)
2. 🎯 Quando for sua vez, escolha uma atividade disponível
3. ✅ Confirme a escolha
4. ⏳ Aguarde todos escolherem

### Próximas Rodadas (Admin)

1. 📊 Verifique que todos escolheram
2. 🔄 Inicie nova rodada (ordem será embaralhada)
3. 🔁 Repita até preencher todas as vagas

## Perguntas Frequentes

### Como funciona a ordem aleatória?

A cada rodada, o sistema:
1. Busca todos os participantes cadastrados (exceto admin)
2. Embaralha a lista usando algoritmo aleatório
3. Atribui posições sequenciais (1, 2, 3, ...)

### Posso ver as atividades antes da minha vez?

Sim! Use o menu expansível "👁️ Ver Atividades Disponíveis" na tela de escolha.

### O que acontece se alguém não escolher?

O sistema aguarda indefinidamente. O participante pode escolher quando quiser, mas isso bloqueia os próximos na fila.

**Solução**: O admin pode comunicar com o participante para fazer a escolha.

### As atividades ficam em ordem cronológica?

Sim! Sempre que as atividades são exibidas (para admin ou participantes), elas são automaticamente ordenadas por:
1. Data (mais antiga primeiro)
2. Horário de início (mais cedo primeiro)

### Como sei quantas vagas restam?

As atividades disponíveis sempre mostram "Vagas Disponíveis". Atividades sem vagas não aparecem na lista de escolha.

## Resolução de Problemas

### "Nenhuma rodada foi iniciada"

**Solução**: O administrador precisa clicar em "Iniciar Primeira Rodada" no painel de admin.

### "Nenhum participante cadastrado"

**Solução**: 
1. Admin deve adicionar emails permitidos
2. Participantes devem se registrar
3. Depois o admin pode iniciar a rodada

### "Erro ao buscar rodada"

**Solução**: Verifique:
1. Nome da escala está correto (exatamente igual)
2. Service Account está configurado
3. Planilha "rodadas" tem permissões corretas

## Suporte Técnico

Para problemas técnicos:
1. Verifique a configuração do Google Sheets
2. Consulte [GOOGLE_SHEETS_SETUP.md](GOOGLE_SHEETS_SETUP.md)
3. Verifique que todas as planilhas necessárias existem
4. Confirme que o Service Account tem acesso de escrita
