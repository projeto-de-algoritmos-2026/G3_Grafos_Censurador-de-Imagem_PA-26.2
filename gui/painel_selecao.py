"""Painel do EXTRA - flood fill.

Nao e um dos metodos avaliados; serve de contraste com os outros dois.
Painel pequeno de proposito.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from core import selecao
from gui import pintura


class PainelSelecao(ttk.Frame):
    def __init__(self, pai, app) -> None:
        super().__init__(pai, padding=10)
        self.app = app
        self.resultado = None
        self.semente: tuple[int, int] | None = None
        self.tolerancia = tk.StringVar(value="40")

        ttk.Label(self, text="Clique em um ponto para selecionar a regiao conectada "
                             "de cor parecida. Busca em largura, sem custo acumulado.",
                  wraplength=300, justify="left", foreground="#3c4a58").pack(anchor="w")

        parametros = ttk.LabelFrame(self, text="Parametros", padding=8)
        parametros.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(parametros, text="tolerancia de cor").grid(row=0, column=0, sticky="w")
        entrada = ttk.Entry(parametros, textvariable=self.tolerancia, width=8)
        entrada.grid(row=0, column=1, sticky="e")
        entrada.bind("<Return>", lambda e: self.recalcular())
        parametros.columnconfigure(0, weight=1)
        ttk.Button(parametros, text="Recalcular", command=self.recalcular).grid(
            row=1, column=0, columnspan=2, sticky="ew", pady=(6, 0))

        self.estatisticas = ttk.Label(self, text="Nenhuma selecao.", wraplength=300,
                                      justify="left")
        self.estatisticas.pack(anchor="w", pady=(10, 0))

    def ao_clicar(self, linha: int, coluna: int) -> None:
        self.semente = (linha, coluna)
        self.recalcular()

    def recalcular(self) -> None:
        if self.semente is None or self.app.grafo is None:
            return
        try:
            tolerancia = float(self.tolerancia.get().replace(",", "."))
        except ValueError:
            self.app.avisar("A tolerancia precisa ser numerica.")
            return
        self.resultado = selecao.preencher(self.app.grafo, *self.semente, tolerancia)
        self.estatisticas.configure(text=self.resultado.resumo)
        self.redesenhar()

    def mascara_atual(self):
        """Contrato com a barra de efeitos."""
        if self.resultado is None or not self.resultado.mascara.any():
            return None
        return self.resultado.mascara

    def redesenhar(self) -> None:
        if self.app.imagem is None:
            return
        quadro = self.app.imagem
        if self.resultado is not None:
            quadro = pintura.marcar(quadro, self.resultado.mascara, pintura.TURQUESA)
        if self.semente is not None:
            quadro = pintura.marcar_ponto(quadro, self.semente, 3, pintura.LARANJA)
        self.app.mostrar(quadro)

    def ao_ativar(self) -> None:
        self.redesenhar()

    def ao_trocar_imagem(self) -> None:
        self.resultado = None
        self.semente = None
        self.estatisticas.configure(text="Nenhuma selecao.")
