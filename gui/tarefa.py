"""Execucao em segundo plano.

A segmentacao leva alguns segundos em imagens grandes; se
rodasse na thread da interface, a janela congelaria e o usuario acharia que o
programa travou. Aqui a funcao pesada roda em uma thread separada e a
interface consulta o resultado periodicamente com after(), que e a forma
segura de voltar para o Tkinter (widgets nao podem ser tocados de outra
thread).
"""

from __future__ import annotations

import threading
import traceback
from typing import Callable

INTERVALO_MS = 80


def executar(janela, funcao: Callable, ao_terminar: Callable,
             ao_falhar: Callable | None = None) -> None:
    """Roda funcao() em outra thread e entrega o retorno a ao_terminar()."""
    deposito: dict = {}

    def trabalho():
        try:
            deposito["valor"] = funcao()
        except Exception as erro:           # noqa: BLE001 - repassado a interface
            deposito["erro"] = erro
            deposito["rastro"] = traceback.format_exc()

    thread = threading.Thread(target=trabalho, daemon=True)
    thread.start()

    def verificar():
        if thread.is_alive():
            janela.after(INTERVALO_MS, verificar)
            return
        if "erro" in deposito:
            if ao_falhar:
                ao_falhar(deposito["erro"])
            else:
                raise deposito["erro"]
        else:
            ao_terminar(deposito["valor"])

    janela.after(INTERVALO_MS, verificar)
