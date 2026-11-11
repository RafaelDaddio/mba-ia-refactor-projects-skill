from src.services.pedido_service import STATUS_APROVADO, STATUS_CANCELADO, STATUS_PENDENTE

# (faturamento mínimo, percentual de desconto), da faixa mais alta para a mais baixa.
FAIXAS_DE_DESCONTO = ((10000, 0.1), (5000, 0.05), (1000, 0.02))


def calcular_desconto(faturamento):
    for minimo, percentual in FAIXAS_DE_DESCONTO:
        if faturamento > minimo:
            return faturamento * percentual
    return 0


class RelatorioService:
    def __init__(self, pedidos):
        self.pedidos = pedidos

    def vendas(self):
        resumo = {linha["status"]: linha for linha in self.pedidos.resumo_por_status()}

        def quantidade(status):
            return resumo[status]["quantidade"] if status in resumo else 0

        total_pedidos = sum(linha["quantidade"] for linha in resumo.values())
        cancelados = quantidade(STATUS_CANCELADO)
        # Pedidos cancelados não são venda: ficam fora do faturamento e do ticket médio.
        faturamento = sum(
            linha["soma"] for status, linha in resumo.items() if status != STATUS_CANCELADO
        )
        pedidos_faturados = total_pedidos - cancelados
        desconto = calcular_desconto(faturamento)

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
