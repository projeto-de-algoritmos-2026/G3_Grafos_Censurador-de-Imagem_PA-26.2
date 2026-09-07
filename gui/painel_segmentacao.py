"""Painel do METODO 1 - segmentacao por Kruskal.

Conversa com a janela principal por uma
interface minima: le `app.grafo`, chama `app.mostrar(imagem)` para exibir e
`app.ocupado(...)` para sinalizar processamento. Nao conhece o outro painel.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import numpy as np

from core import segmentacao
from gui import pintura, tarefa


class PainelSegmentacao(ttk.Frame):
    def __init__(self, pai, app) -> None:
        super().__init__(pai, padding=10)
        self.app = app
        self.resultado = None
        self.regioes_marcadas: set[int] = set()

        self.k = tk.StringVar(value="600")
        self.tamanho_minimo = tk.StringVar(value="80")
        self.exibicao = tk.StringVar(value="contornos")

        ttk.Label(self, text="Agrupa pixels em regioes de cor coerente. "
                             "Kruskal com criterio de fusao por escala. "
                             "Depois de segmentar, clique nas regioes para marca-las.",
                  wraplength=300, justify="left",
                  foreground="#3c4a58").pack(anchor="w")

        parametros = ttk.LabelFrame(self, text="Parametros", padding=8)
        parametros.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(parametros, text="k (escala das regioes)").grid(row=0, column=0, sticky="w")
        ttk.Entry(parametros, textvariable=self.k, width=8).grid(row=0, column=1, sticky="e")
        ttk.Label(parametros, text="tamanho minimo (px)").grid(row=1, column=0, sticky="w", pady=(4, 0))
        ttk.Entry(parametros, textvariable=self.tamanho_minimo, width=8).grid(
            row=1, column=1, sticky="e", pady=(4, 0))
        parametros.columnconfigure(0, weight=1)
        ttk.Label(parametros, text="k maior produz regioes maiores.",
                  foreground="#5a6b7a").grid(row=2, column=0, columnspan=2,
                                             sticky="w", pady=(6, 0))

        self.botao = ttk.Button(self, text="Segmentar", command=self.executar)
        self.botao.pack(fill=tk.X, pady=8)

        exibir = ttk.LabelFrame(self, text="Exibicao", padding=8)
        exibir.pack(fill=tk.X)
        for valor, texto in (("contornos", "Contornos sobre a foto"),
                             ("media", "Regioes pela cor media"),
                             ("original", "Imagem original")):
            ttk.Radiobutton(exibir, text=texto, value=valor, variable=self.exibicao,
                            command=self.redesenhar).pack(anchor="w")

        self.estatisticas = ttk.Label(self, text="", wraplength=300, justify="left")
        self.estatisticas.pack(anchor="w", pady=(10, 0))

    # ------------------------------------------------------------------ #
    def executar(self) -> None:
        grafo = self.app.grafo
        if grafo is None:
            self.app.avisar("Carregue uma imagem primeiro.")
            return
        try:
            k = float(self.k.get().replace(",", "."))
            minimo = int(self.tamanho_minimo.get())
        except ValueError:
            self.app.avisar("k e tamanho minimo precisam ser numericos.")
            return

        self.botao.configure(state=tk.DISABLED)
        self.app.ocupado(f"Segmentando {grafo.total_arestas:,} arestas...".replace(",", "."))

        tarefa.executar(
            self.app,
            lambda: segmentacao.segmentar(grafo, k=k, tamanho_minimo=minimo),
            ao_terminar=self._concluir,
            ao_falhar=self._falhar)

    def _concluir(self, resultado) -> None:
        self.resultado = resultado
        self.regioes_marcadas.clear()
        self.botao.configure(state=tk.NORMAL)
        self.app.ocupado(None)
        self.estatisticas.configure(text=resultado.resumo.replace(" | ", "\n"))
        self.redesenhar()

    def _falhar(self, erro: Exception) -> None:
        self.botao.configure(state=tk.NORMAL)
        self.app.ocupado(None)
        self.app.avisar(f"Falha na segmentacao: {erro}")

    def redesenhar(self) -> None:
        if self.app.imagem is None:
            return
        if self.resultado is None or self.exibicao.get() == "original":
            self.app.mostrar(self.app.imagem)
            return
        if self.exibicao.get() == "media":
            quadro = segmentacao.cor_media(self.app.imagem, self.resultado.rotulos)
        else:
            quadro = pintura.pintar_contornos(
                self.app.imagem, segmentacao.contornos(self.resultado.rotulos))

        mascara = self.mascara_atual()
        if mascara is not None:
            quadro = pintura.marcar(quadro, mascara, pintura.TURQUESA, 0.5)
            self.estatisticas.configure(
                text=f"{self.resultado.resumo}\n{len(self.regioes_marcadas)} regiao(oes) "
                     f"marcada(s): {int(mascara.sum())} px")
        self.app.mostrar(quadro)

    def ao_ativar(self) -> None:
        """Chamado quando a aba ganha foco."""
        self.redesenhar()

    def ao_clicar(self, linha: int, coluna: int) -> None:
        """Clique sobre a imagem: marca ou desmarca a regiao daquele pixel."""
        if self.resultado is None:
            self.app.avisar("Rode a segmentacao antes de selecionar regioes.")
            return
        rotulo = int(self.resultado.rotulos[linha, coluna])
        if rotulo in self.regioes_marcadas:
            self.regioes_marcadas.discard(rotulo)
        else:
            self.regioes_marcadas.add(rotulo)
        self.redesenhar()

    def mascara_atual(self):
        """Contrato com a barra de efeitos: uniao das regioes marcadas."""
        if self.resultado is None or not self.regioes_marcadas:
            return None
        return np.isin(self.resultado.rotulos, list(self.regioes_marcadas))

    def ao_trocar_imagem(self) -> None:
        self.resultado = None
        self.regioes_marcadas.clear()
        self.estatisticas.configure(text="")
