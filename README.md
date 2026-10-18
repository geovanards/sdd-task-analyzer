# sdd-task-analyzer — TaskAnalyzer
> **Bootcamp III** — Fase 2: Implementação com IA, Test Harness e Versionamento no GitHub
> **Aluno:** Geovana Rodrigues Paz Cruz
> **Curso:** Ciência da Computação


## Visão geral

O **TaskAnalyzer** é um módulo Python desenvolvido com **SDD (Spec-Driven Development)**.
Ele recebe uma lista de tarefas (datas, prazo, prioridade e status) e calcula, sem persistência:

- tempo médio de conclusão (minutos e horas), geral e por prioridade;
- taxa de atraso percentual, geral e por prioridade;
- totais de tarefas, concluídas, pendentes e canceladas.

O código foi gerado com assistente de IA guiado por `CONTEXT_RULES.md` e pelo contrato
`specs/task_analyzer_spec.md`, e validado pelo Test Harness em `tests/test_harness.py`.

## Estrutura do repositório

```
sdd-task-analyzer/
├── README.md                 # Este arquivo: visão geral, execução e status do build
├── CONTEXT_RULES.md          # Regras de governança da IA (transpostas da Fase 1)
├── .gitignore                # __pycache__/, .pytest_cache/, venv/ etc.
├── requirements.txt          # Dependências autorizadas (pytest)
├── specs/
│   └── task_analyzer_spec.md # Contrato SDD (Fase 1 + adendo Fase 2)
├── tests/
│   └── test_harness.py       # Test Harness com pytest (Cenários 1, 2 e casos de borda)
└── src/
    └── task_analyzer.py      # Código gerado via IA e homologado
```

## Como executar

Pré-requisitos: Python 3.11+ e Git.

```bash
git clone https://github.com/geovanards/sdd-task-analyzer.git
cd sdd-task-analyzer
python -m pip install -r requirements.txt
python -m pytest -v
```

Resultado esperado: `13 passed` (100 % de aprovação).

## Exemplo de uso

```python
from src.task_analyzer import analyze_tasks

resultado = analyze_tasks([
    {
        "id_tarefa": 1,
        "prioridade": "alta",
        "status": "concluida",
        "data_criacao": "2026-09-01T07:00:00Z",
        "data_inicio": "2026-09-01T08:00:00Z",
        "data_conclusao": "2026-09-01T10:00:00Z",
        "prazo": "2026-09-01T12:00:00Z",
    },
])
# {'total_tarefas': 1, 'total_concluidas': 1, 'total_pendentes': 0, ...,
#  'tempo_medio_conclusao_horas': 2.0, 'taxa_atraso_percentual': 0.0, ...}
```

Também está disponível a API tipada do contrato da Fase 1: `analisar_tarefas(list[Tarefa]) -> RelatorioMetricas`.

## Cobertura do Test Harness

| Cenário | O que é validado | Testes |
|---------|------------------|--------|
| Cenário 1 (sucesso) | `total_tarefas`, `total_concluidas`, `total_pendentes`, tempo médio (geral e por prioridade) e `taxa_atraso_percentual` | `test_metricas_corretas_com_tarefas_validas`, `test_analyze_tasks_cenario_1_sucesso` |
| Cenário 2 (erro) | `data_conclusao` < `data_criacao`/`data_inicio` dispara `TaskValidationError` / `DatasInvalidasError` | `test_datas_inconsistentes_disparam_excecao`, `test_analyze_tasks_conclusao_anterior_a_criacao` |
| Casos de borda | Lista vazia ou só pendentes: retorno `0.0` em `analyze_tasks`; `SemTarefasConcluidasError` em `analisar_tarefas` | `test_analyze_tasks_casos_de_borda_retornam_zero`, `test_sem_tarefas_concluidas_dispara_excecao` |
| C3 a C7 | Conclusão no prazo, modo tolerante com log, prioridade inválida, datetime naive, prioridade sem tarefas | demais testes |

## Governança de IA e rastreabilidade (RI-06)

| Arquivo | Origem | Revisão humana |
|---------|--------|----------------|
| `specs/task_analyzer_spec.md` | Humano (Fase 1), com adendo da Fase 2 | — |
| `CONTEXT_RULES.md` | Humano (Fase 1) | — |
| `src/task_analyzer.py` | Gerado por IA a partir da spec + CONTEXT_RULES | Conferência de assinaturas, tipos, exceções, arredondamento e logging |
| `tests/test_harness.py` | Cenários definidos pelo humano; código de teste sugerido pela IA | Conferência 1:1 com a seção 2 da spec (PR-02) |

Pontos da homologação:

- **Contrato preservado (PR-05/PR-10):** `analisar_tarefas` continua retornando `RelatorioMetricas`.
  A função `analyze_tasks` exigida pela Fase 2 foi adicionada como fachada, sem alterar a API original.
- **Hierarquia de exceções:** `TaskValidationError` é a base dos erros de entrada; `DatasInvalidasError`
  e `ValorEnumInvalidoError` derivam dela, então a mesma falha atende aos dois contratos.
- **Divisão por zero:** `analyze_tasks` retorna `0.0`; `analisar_tarefas` mantém o fail-fast da RN-05.
- **Sem dependências externas (PR-01)** e **sem `datetime.now()` (PR-11)**; logs via `logging` (DA-07).

## Fluxo de versionamento

`feature/*` → Pull Request → `develop` → Pull Request → `main` (tag `v0.1.0`).
Commits no padrão Conventional Commits.
