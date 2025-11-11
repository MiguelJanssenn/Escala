# Diagrama do Fluxo de Rodadas

## Fluxo Administrativo

```
┌─────────────────────────────────────────────────────────┐
│ ADMINISTRADOR                                           │
└─────────────────────────────────────────────────────────┘

1. Criar Escala
   ├── Digite nome da escala (ex: "Dezembro/2025")
   └── Use planilha interativa para adicionar atividades
       ├── Tipo: Plantão/Ambulatório/Enfermaria
       ├── Data: AAAA-MM-DD
       ├── Horário: HH:MM-HH:MM
       └── Vagas: número
   
2. Salvar Atividades
   └── Clique "💾 Salvar Atividades"
       └── Sistema ordena cronologicamente

3. Iniciar Rodada
   └── Clique "🎲 Iniciar Primeira Rodada"
       ├── Sistema busca participantes
       ├── Embaralha ordem aleatoriamente
       └── Cria rodada #1

4. Acompanhar Progresso
   └── Visualize tabela de participantes
       ├── Posição
       ├── Nome
       └── Status (⏳ Aguardando / ✅ Escolheu)

5. Nova Rodada (quando todos escolherem)
   └── Clique "🔄 Iniciar Nova Rodada"
       └── Sistema embaralha novamente
```

## Fluxo do Participante

```
┌─────────────────────────────────────────────────────────┐
│ PARTICIPANTE                                            │
└─────────────────────────────────────────────────────────┘

1. Acessar Escolha
   ├── Menu → "Escolher Horário"
   └── Digite nome da escala

2. Visualizar Rodada
   ├── Número da rodada atual
   ├── Ordem de escolha
   └── Seu status

3. Aguardar Vez
   ├── SE não é sua vez
   │   ├── Ver quem está escolhendo
   │   └── Ver atividades disponíveis (apenas visualização)
   │
   └── SE é sua vez
       ├── Ver "🎯 É a sua vez de escolher!"
       ├── Ver atividades disponíveis (cronologicamente)
       ├── Selecionar uma atividade
       └── Confirmar escolha

4. Ver Minha Escala
   └── Menu → "Minha Escala"
       └── Ver todas escolhas em ordem cronológica
```

## Ordenação Cronológica

```
Atividades são SEMPRE ordenadas por:

1º Critério: Data (AAAA-MM-DD)
   ├── 2025-12-01
   ├── 2025-12-02
   └── 2025-12-03

2º Critério: Horário de Início
   ├── 07:00-19:00
   ├── 13:00-18:00
   └── 19:00-07:00

Exemplo de ordenação:
┌────────────┬──────────────┬───────────────┐
│ Data       │ Horário      │ Tipo          │
├────────────┼──────────────┼───────────────┤
│ 2025-12-01 │ 07:00-19:00  │ Plantão       │ ← Primeiro
│ 2025-12-01 │ 19:00-07:00  │ Plantão       │
│ 2025-12-02 │ 08:00-12:00  │ Ambulatório   │
│ 2025-12-03 │ 13:00-18:00  │ Enfermaria    │ ← Último
└────────────┴──────────────┴───────────────┘
```

## Sistema de Vagas

```
Cada atividade tem:
├── Vagas Totais: definido pelo admin
├── Vagas Ocupadas: contadas automaticamente
└── Vagas Disponíveis: Totais - Ocupadas

Exemplo:
┌────────────┬───────┬──────────┬────────────┐
│ Atividade  │ Total │ Ocupadas │ Disponível │
├────────────┼───────┼──────────┼────────────┤
│ Plantão A  │   3   │    2     │      1     │ ✓ Aparece
│ Plantão B  │   2   │    2     │      0     │ ✗ Não aparece
│ Ambulat. C │   1   │    0     │      1     │ ✓ Aparece
└────────────┴───────┴──────────┴────────────┘

Participantes só veem atividades com Disponível > 0
```

## Estrutura de Dados

```
┌──────────────────────────────────────────────────────────┐
│ PLANILHA: atividades                                     │
├──────────────────────────────────────────────────────────┤
│ Campos:                                                  │
│  - escala_nome: "Dezembro/2025"                         │
│  - tipo: "Plantão" / "Ambulatório" / "Enfermaria"       │
│  - data: "2025-12-01"                                   │
│  - horario: "07:00-19:00"                               │
│  - vagas: 2                                             │
│  - id_atividade: UUID único                             │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│ PLANILHA: rodadas (NOVA!)                                │
├──────────────────────────────────────────────────────────┤
│ Campos:                                                  │
│  - escala_nome: "Dezembro/2025"                         │
│  - numero_rodada: 1, 2, 3, ...                          │
│  - posicao: 1, 2, 3, ...                                │
│  - email_participante: "user@email.com"                 │
│  - ja_escolheu: True / False                            │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│ PLANILHA: escolhas                                       │
├──────────────────────────────────────────────────────────┤
│ Campos:                                                  │
│  - escala_nome: "Dezembro/2025"                         │
│  - id_atividade: UUID da atividade                      │
│  - email_participante: "user@email.com"                 │
│  - nome_participante: "Nome Completo"                   │
└──────────────────────────────────────────────────────────┘
```

## Exemplo Completo de Uso

```
PASSO 1: Admin cria escala "Dezembro/2025"
   └── Adiciona 10 atividades via planilha

PASSO 2: Admin inicia Rodada #1
   └── Sistema embaralha 10 participantes
       Ordem: [João(1), Maria(2), Pedro(3), ...]

PASSO 3: João escolhe (posição 1)
   └── Vê 10 atividades disponíveis
   └── Escolhe "Plantão - 2025-12-01 - 07:00-19:00"
   └── Marca: ja_escolheu = True

PASSO 4: Maria escolhe (posição 2)
   └── Vê 10 atividades disponíveis (Plantão tem 1 vaga restante)
   └── Escolhe "Ambulatório - 2025-12-02 - 08:00-12:00"
   └── Marca: ja_escolheu = True

PASSO 5: ... todos os 10 participantes escolhem

PASSO 6: Admin inicia Rodada #2
   └── Sistema embaralha novamente
       Nova ordem: [Pedro(1), Ana(2), João(3), ...]
   
PASSO 7: Pedro escolhe primeiro agora
   └── Processo se repete

CONTINUA ATÉ: Todas as vagas serem preenchidas
```
