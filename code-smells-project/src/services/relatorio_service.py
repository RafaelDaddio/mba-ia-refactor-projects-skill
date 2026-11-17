"""Relatório de vendas."""
from src.services.pedido_service import STATUS_APROVADO, STATUS_CANCELADO, STATUS_PENDENTE

# (faturamento mínimo, desconto), da maior faixa para a menor
FAIXAS_DESCONTO = ((10_000, 0.10), (5_000, 0.05), (1_000, 0.02))


def desconto_para(faturamento):
    for minimo, percentual in FAIXAS_DESCONTO:
        if faturamento > minimo:
            return faturamento * percentual
    return 0


class RelatorioService:
    def __init__(self, pedidos):
        self.pedidos = pedidos

    def vendas(self):
        resumo = self.pedidos.resumo_por_status()

        def quantidade(status):
            return resumo.get(status, {}).get("quantidade", 0)

        total_pedidos = sum(grupo["quantidade"] for grupo in resumo.values())
        cancelados = quantidade(STATUS_CANCELADO)
        # Pedidos cancelados não entram no faturamento nem no ticket médio.
        faturamento = sum(
            grupo["total"] for status, grupo in resumo.items() if status != STATUS_CANCELADO
        )
        pedidos_faturados = total_pedidos - cancelados
        desconto = desconto_para(faturamento)

        return {
            "total_pedidos": total_pedidos,
            "faturamento_bruto": round(faturamento, 2),
            "desconto_aplicavel": round(desconto, 2),
            "faturamento_liquido": round(faturamento - desconto, 2),
            "pedidos_pendentes": quantidade(STATUS_PENDENTE),
            "pedidos_aprovados": quantidade(STATUS_APROVADO),
            "pedidos_cancelados": cancelados,
            "ticket_medio": round(faturamento / pedidos_faturados, 2) if pedidos_faturados > 0 else 0,
        }
