"""TaskAnalyzer: análise de tarefas e métricas de produtividade.

Implementação do contrato definido em ``specs/task_analyzer_spec.md``, gerada com
assistente de IA sob as regras de ``CONTEXT_RULES.md`` e homologada manualmente.

O módulo é puro (RN-09): não lê nem escreve arquivos, não acessa rede e não
mantém estado entre chamadas.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, NoReturn

logger = logging.getLogger(__name__)

PRIORIDADES: tuple[str, ...] = ("baixa", "media", "alta")
STATUS_VALIDOS: tuple[str, ...] = ("concluida", "pendente", "cancelada")
STATUS_CONCLUIDA: str = "concluida"
CAMPOS_DATA: tuple[str, ...] = ("data_criacao", "prazo", "data_inicio", "data_conclusao")
CAMPOS_OBRIGATORIOS: tuple[str, ...] = (
    "id_tarefa",
    "data_criacao",
    "prazo",
    "prioridade",
    "status",
)


@dataclass(frozen=True)
class Tarefa:
    """Tarefa de entrada do analisador (todas as datas em UTC).

    Attributes:
        id_tarefa: Identificador único da tarefa (> 0).
        data_criacao: Data/hora de criação.
        prazo: Data/hora limite para conclusão.
        prioridade: ``"baixa"``, ``"media"`` ou ``"alta"``.
        status: ``"concluida"``, ``"pendente"`` ou ``"cancelada"``.
        data_inicio: Início da execução (obrigatório se concluída).
        data_conclusao: Conclusão (obrigatório se concluída).
    """

    id_tarefa: int
    data_criacao: datetime
    prazo: datetime
    prioridade: str
    status: str
    data_inicio: datetime | None = None
    data_conclusao: datetime | None = None


@dataclass(frozen=True)
class IndicadorPrioridade:
    """Métricas de um grupo de prioridade.

    Attributes:
        tempo_medio_conclusao_min: Tempo médio de conclusão em minutos.
        taxa_atraso_percentual: Percentual de tarefas concluídas após o prazo.
        quantidade_tarefas: Quantidade de tarefas consideradas no grupo.
    """

    tempo_medio_conclusao_min: float
    taxa_atraso_percentual: float
    quantidade_tarefas: int


@dataclass(frozen=True)
class RelatorioMetricas:
    """Resultado de ``analisar_tarefas``.

    Attributes:
        tempo_medio_conclusao_min: Tempo médio geral em minutos.
        taxa_atraso_percentual: Percentual geral de atraso.
        quantidade_tarefas: Total de tarefas concluídas válidas consideradas.
        indicadores_por_prioridade: Indicadores com chaves ``baixa``, ``media`` e ``alta``.
    """

    tempo_medio_conclusao_min: float
    taxa_atraso_percentual: float
    quantidade_tarefas: int
    indicadores_por_prioridade: dict[str, IndicadorPrioridade]


class TaskAnalyzerError(Exception):
    """Base de todas as exceções do módulo."""


class TaskValidationError(TaskAnalyzerError):
    """Entrada inválida (base dos erros de validação de tarefas)."""


class DatasInvalidasError(TaskValidationError):
    """Datas ausentes, naive (sem UTC) ou cronologicamente inconsistentes."""


class ValorEnumInvalidoError(TaskValidationError):
    """Prioridade ou status fora dos valores permitidos."""


class SemTarefasConcluidasError(TaskAnalyzerError):
    """Nenhuma tarefa concluída válida para calcular métricas (divisão por zero)."""


def _falhar(erro: TaskAnalyzerError) -> NoReturn:
    """Registra o erro em log (nível ERROR) e o dispara (RN-10).

    Args:
        erro: Exceção a ser registrada e disparada.

    Raises:
        TaskAnalyzerError: Sempre, a própria exceção recebida.
    """
    logger.error(str(erro))
    raise erro


def _formatar_data(valor: datetime) -> str:
    """Formata uma data UTC para mensagens de erro.

    Args:
        valor: Data/hora a ser formatada.

    Returns:
        Texto no formato ``AAAA-MM-DD HH:MM UTC``.
    """
    return f"{valor:%Y-%m-%d %H:%M} UTC"


def _validar_identificador(tarefa: Tarefa) -> None:
    """Garante que ``id_tarefa`` é um inteiro positivo.

    Args:
        tarefa: Tarefa a validar.

    Raises:
        TaskValidationError: Se o id não for inteiro maior que zero.
    """
    id_tarefa = tarefa.id_tarefa
    if isinstance(id_tarefa, bool) or not isinstance(id_tarefa, int) or id_tarefa <= 0:
        _falhar(TaskValidationError(f"Tarefa {id_tarefa!r}: id_tarefa deve ser inteiro > 0."))


def _validar_enums(tarefa: Tarefa) -> None:
    """Valida prioridade e status contra os valores permitidos (RN-08).

    Args:
        tarefa: Tarefa a validar.

    Raises:
        ValorEnumInvalidoError: Se prioridade ou status forem inválidos.
    """
    if tarefa.prioridade not in PRIORIDADES:
        _falhar(ValorEnumInvalidoError(
            f"Tarefa {tarefa.id_tarefa}: prioridade '{tarefa.prioridade}' inválida. "
            f"Valores aceitos: {', '.join(PRIORIDADES)}."
        ))
    if tarefa.status not in STATUS_VALIDOS:
        _falhar(ValorEnumInvalidoError(
            f"Tarefa {tarefa.id_tarefa}: status '{tarefa.status}' inválido. "
            f"Valores aceitos: {', '.join(STATUS_VALIDOS)}."
        ))


def _validar_fuso_utc(tarefa: Tarefa) -> None:
    """Garante que todas as datas informadas são timezone-aware em UTC (RN-06).

    Args:
        tarefa: Tarefa a validar.

    Raises:
        DatasInvalidasError: Se alguma data for naive ou não estiver em UTC.
    """
    for campo in CAMPOS_DATA:
        valor = getattr(tarefa, campo)
        if valor is None:
            continue
        if not isinstance(valor, datetime) or valor.utcoffset() != timedelta(0):
            _falhar(DatasInvalidasError(
                f"Tarefa {tarefa.id_tarefa}: {campo} ({valor}) deve ser datetime UTC timezone-aware."
            ))


def _validar_cronologia(tarefa: Tarefa) -> None:
    """Valida presença e ordem das datas de uma tarefa concluída (RN-04).

    Args:
        tarefa: Tarefa a validar. Tarefas não concluídas são ignoradas.

    Raises:
        DatasInvalidasError: Se início/conclusão faltarem ou estiverem fora de ordem.
    """
    if tarefa.status != STATUS_CONCLUIDA:
        return
    if tarefa.data_inicio is None or tarefa.data_conclusao is None:
        _falhar(DatasInvalidasError(
            f"Tarefa {tarefa.id_tarefa}: data_inicio e data_conclusao são obrigatórias "
            "para tarefas concluídas."
        ))
    pares = (
        ("data_conclusao", tarefa.data_conclusao, "data_criacao", tarefa.data_criacao),
        ("data_inicio", tarefa.data_inicio, "data_criacao", tarefa.data_criacao),
        ("data_conclusao", tarefa.data_conclusao, "data_inicio", tarefa.data_inicio),
    )
    for nome_posterior, posterior, nome_anterior, anterior in pares:
        if posterior < anterior:
            _falhar(DatasInvalidasError(
                f"Tarefa {tarefa.id_tarefa}: {nome_posterior} ({_formatar_data(posterior)}) "
                f"é anterior a {nome_anterior} ({_formatar_data(anterior)})."
            ))


def validar_tarefa(tarefa: Tarefa) -> None:
    """Valida uma tarefa contra o contrato SDD.

    Args:
        tarefa: Tarefa a validar.

    Raises:
        TaskValidationError: Se o id for inválido.
        ValorEnumInvalidoError: Se prioridade ou status forem inválidos.
        DatasInvalidasError: Se as datas forem naive ou inconsistentes.
    """
    _validar_identificador(tarefa)
    _validar_enums(tarefa)
    _validar_fuso_utc(tarefa)
    _validar_cronologia(tarefa)


def calcular_tempo_conclusao_min(tarefa: Tarefa) -> float:
    """Calcula o tempo de conclusão em minutos (RN-02).

    Args:
        tarefa: Tarefa concluída e já validada.

    Returns:
        Minutos entre ``data_inicio`` e ``data_conclusao``.

    Raises:
        DatasInvalidasError: Se início ou conclusão estiverem ausentes.
    """
    if tarefa.data_inicio is None or tarefa.data_conclusao is None:
        _falhar(DatasInvalidasError(
            f"Tarefa {tarefa.id_tarefa}: tempo de conclusão exige data_inicio e data_conclusao."
        ))
    return (tarefa.data_conclusao - tarefa.data_inicio).total_seconds() / 60


def esta_atrasada(tarefa: Tarefa) -> bool:
    """Indica se a tarefa foi concluída após o prazo (RN-03).

    Args:
        tarefa: Tarefa concluída e já validada.

    Returns:
        ``True`` se ``data_conclusao > prazo``; conclusão no prazo não é atraso.
    """
    return tarefa.data_conclusao is not None and tarefa.data_conclusao > tarefa.prazo


def _media(valores: list[float]) -> float:
    """Calcula a média arredondada, retornando 0.0 para lista vazia.

    Args:
        valores: Valores a serem agregados.

    Returns:
        Média com 2 casas decimais ou 0.0 se não houver valores.
    """
    return round(sum(valores) / len(valores), 2) if valores else 0.0


def _percentual(parte: int, total: int) -> float:
    """Calcula um percentual arredondado, retornando 0.0 se o total for zero.

    Args:
        parte: Quantidade de ocorrências.
        total: Quantidade total.

    Returns:
        Percentual com 2 casas decimais ou 0.0 se ``total`` for zero.
    """
    return round(parte / total * 100, 2) if total else 0.0


def _validar_ids_unicos(tarefas: list[Tarefa]) -> None:
    """Garante que não há ``id_tarefa`` duplicado.

    Args:
        tarefas: Tarefas recebidas.

    Raises:
        TaskValidationError: Se houver ids repetidos.
    """
    vistos: set[int] = set()
    for tarefa in tarefas:
        if tarefa.id_tarefa in vistos:
            _falhar(TaskValidationError(f"Tarefa {tarefa.id_tarefa}: id_tarefa duplicado."))
        vistos.add(tarefa.id_tarefa)


def _selecionar_concluidas_validas(
    tarefas: list[Tarefa],
    ignorar_inconsistentes: bool,
) -> list[Tarefa]:
    """Valida as tarefas e retorna apenas as concluídas com datas válidas.

    Args:
        tarefas: Tarefas recebidas.
        ignorar_inconsistentes: Se ``True``, descarta tarefas com cronologia
            inconsistente registrando WARNING em vez de disparar exceção.

    Returns:
        Tarefas concluídas aptas para o cálculo das métricas.

    Raises:
        TaskValidationError: Para entradas inválidas no modo padrão.
    """
    _validar_ids_unicos(tarefas)
    selecionadas: list[Tarefa] = []
    for tarefa in tarefas:
        _validar_identificador(tarefa)
        _validar_enums(tarefa)
        _validar_fuso_utc(tarefa)
        try:
            _validar_cronologia(tarefa)
        except DatasInvalidasError as erro:
            if not ignorar_inconsistentes:
                raise
            logger.warning("Tarefa %s descartada: %s", tarefa.id_tarefa, erro)
            continue
        if tarefa.status == STATUS_CONCLUIDA:
            selecionadas.append(tarefa)
    return selecionadas


def _construir_indicador(tarefas: list[Tarefa]) -> IndicadorPrioridade:
    """Agrega tempo médio, taxa de atraso e quantidade de um grupo de tarefas.

    Args:
        tarefas: Tarefas concluídas e válidas do grupo.

    Returns:
        Indicador do grupo (0.0, 0.0, 0 para grupo vazio).
    """
    tempos = [calcular_tempo_conclusao_min(tarefa) for tarefa in tarefas]
    atrasadas = sum(1 for tarefa in tarefas if esta_atrasada(tarefa))
    return IndicadorPrioridade(
        tempo_medio_conclusao_min=_media(tempos),
        taxa_atraso_percentual=_percentual(atrasadas, len(tarefas)),
        quantidade_tarefas=len(tarefas),
    )


def _montar_relatorio(concluidas: list[Tarefa]) -> RelatorioMetricas:
    """Monta o relatório geral e por prioridade a partir das tarefas válidas.

    Args:
        concluidas: Tarefas concluídas e válidas.

    Returns:
        Relatório de métricas com chaves fixas de prioridade.
    """
    geral = _construir_indicador(concluidas)
    por_prioridade = {
        prioridade: _construir_indicador(
            [tarefa for tarefa in concluidas if tarefa.prioridade == prioridade]
        )
        for prioridade in PRIORIDADES
    }
    return RelatorioMetricas(
        tempo_medio_conclusao_min=geral.tempo_medio_conclusao_min,
        taxa_atraso_percentual=geral.taxa_atraso_percentual,
        quantidade_tarefas=geral.quantidade_tarefas,
        indicadores_por_prioridade=por_prioridade,
    )


def analisar_tarefas(
    tarefas: list[Tarefa],
    ignorar_inconsistentes: bool = False,
) -> RelatorioMetricas:
    """Calcula as métricas de produtividade de uma lista de tarefas.

    Args:
        tarefas: Tarefas a analisar.
        ignorar_inconsistentes: Se ``True``, descarta tarefas com datas
            inconsistentes (com WARNING) em vez de disparar exceção (RN-04).

    Returns:
        Relatório com tempo médio, taxa de atraso e indicadores por prioridade.

    Raises:
        TaskValidationError: Se alguma tarefa for inválida.
        SemTarefasConcluidasError: Se não houver tarefa concluída válida (RN-05).
    """
    concluidas = _selecionar_concluidas_validas(tarefas, ignorar_inconsistentes)
    if not concluidas:
        _falhar(SemTarefasConcluidasError(
            "Nenhuma tarefa concluída válida para calcular métricas "
            f"(0 de {len(tarefas)} tarefas consideradas)."
        ))
    return _montar_relatorio(concluidas)


def _converter_data(valor: Any, campo: str, id_tarefa: Any) -> datetime | None:
    """Converte ``datetime`` ou texto ISO 8601 em ``datetime``.

    Args:
        valor: Valor recebido no dicionário da tarefa.
        campo: Nome do campo (para a mensagem de erro).
        id_tarefa: Identificador da tarefa (para a mensagem de erro).

    Returns:
        Data convertida ou ``None`` se o valor for ``None``.

    Raises:
        DatasInvalidasError: Se o valor não for data nem texto ISO 8601 válido.
    """
    if valor is None or isinstance(valor, datetime):
        return valor
    if isinstance(valor, str):
        try:
            return datetime.fromisoformat(valor.replace("Z", "+00:00"))
        except ValueError:
            pass
    _falhar(DatasInvalidasError(
        f"Tarefa {id_tarefa}: {campo} ({valor!r}) não é uma data ISO 8601 válida."
    ))


def _tarefa_de_dict(dados: dict[str, Any]) -> Tarefa:
    """Converte um dicionário de entrada em ``Tarefa``.

    Args:
        dados: Dicionário com as mesmas chaves da dataclass ``Tarefa``.

    Returns:
        Tarefa equivalente.

    Raises:
        TaskValidationError: Se faltar campo obrigatório ou alguma data for inválida.
    """
    id_tarefa = dados.get("id_tarefa")
    ausentes = [campo for campo in CAMPOS_OBRIGATORIOS if dados.get(campo) is None]
    if ausentes:
        _falhar(TaskValidationError(
            f"Tarefa {id_tarefa}: campos obrigatórios ausentes: {', '.join(ausentes)}."
        ))
    datas = {campo: _converter_data(dados.get(campo), campo, id_tarefa) for campo in CAMPOS_DATA}
    return Tarefa(
        id_tarefa=id_tarefa,
        prioridade=dados["prioridade"],
        status=dados["status"],
        **datas,
    )


def _metricas_em_horas(indicador: IndicadorPrioridade) -> dict[str, Any]:
    """Converte um indicador para o formato de dicionário da Fase 2.

    Args:
        indicador: Indicador calculado pelo núcleo do analisador.

    Returns:
        Dicionário com total de concluídas, tempo médio em horas e taxa de atraso.
    """
    return {
        "total_concluidas": indicador.quantidade_tarefas,
        "tempo_medio_conclusao_horas": round(indicador.tempo_medio_conclusao_min / 60, 2),
        "taxa_atraso_percentual": indicador.taxa_atraso_percentual,
    }


def analyze_tasks(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    """Analisa tarefas em formato de dicionário (interface exigida na Fase 2).

    Diferente de ``analisar_tarefas``, uma lista sem tarefas concluídas não
    dispara exceção: médias e taxas retornam 0.0 (prevenção de divisão por zero).

    Args:
        tasks: Tarefas como dicionários com as chaves da dataclass ``Tarefa``.

    Returns:
        Dicionário com totais, tempo médio (minutos e horas), taxa de atraso e
        ``metricas_por_prioridade``.

    Raises:
        TaskValidationError: Se alguma tarefa for inválida, inclusive quando
            ``data_conclusao`` for anterior a ``data_criacao``.
    """
    tarefas = [_tarefa_de_dict(dados) for dados in tasks]
    relatorio = _montar_relatorio(_selecionar_concluidas_validas(tarefas, False))
    contagem = {status: sum(1 for t in tarefas if t.status == status) for status in STATUS_VALIDOS}
    return {
        "total_tarefas": len(tarefas),
        "total_concluidas": contagem["concluida"],
        "total_pendentes": contagem["pendente"],
        "total_canceladas": contagem["cancelada"],
        "tempo_medio_conclusao_min": relatorio.tempo_medio_conclusao_min,
        "tempo_medio_conclusao_horas": round(relatorio.tempo_medio_conclusao_min / 60, 2),
        "taxa_atraso_percentual": relatorio.taxa_atraso_percentual,
        "metricas_por_prioridade": {
            prioridade: _metricas_em_horas(indicador)
            for prioridade, indicador in relatorio.indicadores_por_prioridade.items()
        },
    }
