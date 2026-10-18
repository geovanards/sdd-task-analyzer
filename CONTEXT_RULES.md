# CONTEXT_RULES — TaskAnalyzer (SDD)

Você é um assistente de codificação. A fonte da verdade é `specs/task_analyzer_spec.md`.
Estas regras foram transpostas da Fase 1 (seção 3 da Especificação SDD) e devem ser
fornecidas ao agente de IA no início de **toda** sessão.

## Obrigatório

- Python 3.11+; type hints em tudo; PEP 8; SRP; docstrings Google style.
- Exceções específicas: `DatasInvalidasError`, `SemTarefasConcluidasError`, `ValorEnumInvalidoError`
  (todas derivadas de `TaskAnalyzerError`; erros de entrada derivam de `TaskValidationError`).
- Logging com o módulo `logging` (WARNING para descartes, ERROR antes de exceções).
- Datas sempre `datetime` UTC timezone-aware; arredondar com `round(x, 2)`.

## Proibido

- Bibliotecas externas; persistência; alterar assinaturas públicas; alterar testes;
  alterar a estrutura de pastas; assumir comportamento não especificado; usar `print`.

## Fluxo

1. Leia a spec. 2. Resuma as regras. 3. Gere código + testes. 4. Rode `pytest -q`.
5. Explique decisões. 6. Aguarde homologação humana antes de qualquer commit.

---

## 1. Diretrizes Arquiteturais (Obrigatórias)

| ID | Diretriz |
|----|----------|
| DA-01 | Python 3.11 ou superior como versão mínima obrigatória (uso de `X \| None` e `dataclasses`). |
| DA-02 | Type hints em todas as funções, métodos, parâmetros e retornos. |
| DA-03 | Seguir o princípio Single Responsibility (SRP) e código limpo conforme PEP 8. |
| DA-04 | Docstrings no padrão Google style para módulo, classes, funções e parâmetros. |
| DA-05 | Funções pequenas, coesas e com um único propósito (máximo sugerido: 25 linhas). |
| DA-06 | Tratamento de exceções específico, com hierarquia própria e mensagens claras (spec, seção 1.3.4). |
| DA-07 | Logs estruturados com o módulo padrão `logging` (nunca `print`). |
| DA-08 | Código legível, com nomes descritivos em português para o domínio (ex.: `calcular_tempo_conclusao_min`). |
| DA-09 | Apenas biblioteca padrão do Python em `src/`. Em `tests/`, apenas `pytest` (e `pytest-cov`, se autorizado). |
| DA-10 | Separar responsabilidades: validação, cálculo por tarefa e agregação em funções distintas. |

## 2. Proibições Explícitas (Regras Restritivas)

| ID | Proibição |
|----|-----------|
| PR-01 | Não utilizar bibliotecas externas não autorizadas (pandas, numpy, dateutil, etc.). |
| PR-02 | Não alterar, remover ou adaptar os cenários de teste fornecidos. |
| PR-03 | Não modificar a estrutura de pastas definida na spec (seção 4.1). |
| PR-04 | Não persistir dados em arquivos ou bancos de dados. |
| PR-05 | Não alterar a assinatura (nome e parâmetros) das funções públicas sem autorização. |
| PR-06 | Não gerar código sem testes correspondentes para as novas funcionalidades. |
| PR-07 | Não inserir código duplicado ou sem necessidade. |
| PR-08 | Não assumir comportamentos não especificados no contrato de negócio. |
| PR-09 | Não comentar código em excesso (apenas o necessário); a docstring é a documentação. |
| PR-10 | Não retornar valores diferentes do contrato definido (ex.: `dict` no lugar de `RelatorioMetricas`). |
| PR-11 | Não usar `datetime.now()` ou qualquer fonte de tempo do sistema dentro do módulo. |

## 3. Regras de Interação com a IA

| ID | Regra |
|----|-------|
| RI-01 | Fornecer sempre o contexto completo (spec e este arquivo) antes de qualquer solicitação. |
| RI-02 | Validar se a IA compreendeu o contrato antes de gerar código (pedir um resumo das regras). |
| RI-03 | Solicitar explicações e justificativas quando houver dúvidas na solução gerada. |
| RI-04 | Revisar criticamente todo código gerado; a IA é executora, o desenvolvedor é o homologador. |
| RI-05 | Rejeitar respostas que violem as proibições ou o contrato e registrar o motivo no PR. |
| RI-06 | Registrar no `README.md` quais trechos foram gerados por IA e quais foram revisados/ajustados. |
