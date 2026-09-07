"""Painel do METODO 2 - tesoura inteligente por Dijkstra.

Usa a mesma interface minima com a janela
principal e nao conhece o painel de segmentacao.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import numpy as np

from core import tesoura, efeito
from gui import pintura, tarefa


class PainelTesoura(ttk.Frame):
    def __init__(self, pai, app) -> None:
        super().__init__(pai, padding=10)
        self.app = app
        self.pontos: list[tuple[int, int]] = []
        self.resultado = None
        self._custo_pixel = None

        self.reforco = tk.StringVar(value="1.0")
        self.fechar = tk.BooleanVar(value=False)
        self.ver_custo = tk.BooleanVar(value=False)

        ttk.Label(self, text="Clique ao redor do objeto. Cada trecho entre dois "
                             "cliques e um Dijkstra que segue as bordas.",
                  wraplength=300, justify="left",
                  foreground="#3c4a58").pack(anchor="w")

        parametros = ttk.LabelFrame(self, text="Parametros", padding=8)
        parametros.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(parametros, text="reforco da borda").grid(row=0, column=0, sticky="w")
        ttk.Entry(parametros, textvariable=self.reforco, width=8).grid(row=0, column=1, sticky="e")
        parametros.columnconfigure(0, weight=1)
        ttk.Checkbutton(parametros, text="Fechar o contorno (necessario para selecionar area)",
                        variable=self.fechar, command=self.recalcular).grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(6, 0))
        ttk.Checkbutton(parametros, text="Ver o mapa de custo",
                        variable=self.ver_custo, command=self.redesenhar).grid(
            row=2, column=0, columnspan=2, sticky="w")

        acoes = ttk.Frame(self)
        acoes.pack(fill=tk.X, pady=8)
        ttk.Button(acoes, text="Desfazer ponto", command=self.desfazer).pack(
            side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        ttk.Button(acoes, text="Limpar", command=self.limpar).pack(
            side=tk.LEFT, expand=True, fill=tk.X, padx=1)

        self.estatisticas = ttk.Label(self, text="Nenhum ponto marcado.",
                                      wraplength=300, justify="left")
        self.estatisticas.pack(anchor="w", pady=(10, 0))

    # ------------------------------------------------------------------ #
    def custo_pixel(self):
        """Mapa de custo em cache: so recalcula se o reforco mudar."""
        try:
            reforco = float(self.reforco.get().replace(",", "."))
        except ValueError:
            reforco = 1.0
        chave = (id(self.app.grafo), reforco)
        if self._custo_pixel is None or self._custo_pixel[0] != chave:
            self._custo_pixel = (chave, tesoura.mapa_de_custo(self.app.grafo, reforco))
        return self._custo_pixel[1]

    def ao_clicar(self, linha: int, coluna: int) -> None:
        if self.app.grafo is None:
            return
        self.pontos.append((linha, coluna))
        if len(self.pontos) < 2:
            self.estatisticas.configure(text="Ponto inicial marcado. Clique no proximo.")
            self.redesenhar()
            return
        self.recalcular()

    def recalcular(self) -> None:
        if len(self.pontos) < 2:
            self.redesenhar()
            return
        pontos = list(self.pontos)
        fechar = self.fechar.get()
        custo = self.custo_pixel()
        self.app.ocupado("Tracando o contorno...")
        tarefa.executar(
            self.app,
            lambda: tesoura.tracar_poligonal(self.app.grafo, pontos, custo, fechar),
            ao_terminar=self._concluir,
            ao_falhar=self._falhar)

    def _concluir(self, resultado) -> None:
        self.app.ocupado(None)
        self.resultado = resultado
        texto = f"{len(self.pontos)} pontos\n{resultado.resumo}"
        if self.fechar.get():
            area = self.mascara_atual()
            if area is None or not area.any():
                texto += "\nContorno sem area interna: adicione mais pontos."
            else:
                texto += f"\narea selecionada: {int(area.sum())} px"
        self.estatisticas.configure(text=texto)
        self.redesenhar()

    def _falhar(self, erro: Exception) -> None:
        self.app.ocupado(None)
        self.app.avisar(f"Falha ao tracar: {erro}")

    def desfazer(self) -> None:
        if self.pontos:
            self.pontos.pop()
        self.resultado = None
        if len(self.pontos) >= 2:
            self.recalcular()
        else:
            self.estatisticas.configure(text="Nenhum ponto marcado."
                                        if not self.pontos else "Ponto inicial marcado.")
            self.redesenhar()

    def limpar(self) -> None:
        self.pontos.clear()
        self.resultado = None
        self.app.ocupado(None)   # descarta o aviso de uma tarefa abandonada
        self.estatisticas.configure(text="Nenhum ponto marcado.")
        self.redesenhar()

    def mascara_atual(self):
        """Contrato com a barra de efeitos.

        Com o contorno fechado, devolve o INTERIOR da area contornada - o
        preenchimento e feito por flood fill a partir das bordas da imagem,
        usando o contorno como parede. Sem fechar, devolve apenas o traco
        engrossado, que ainda serve para riscar sobre a imagem.
        """
        if self.resultado is None or not self.resultado.sucesso:
            return None
        if not self.fechar.get():
            marca = np.zeros((self.app.grafo.altura, self.app.grafo.largura), dtype=bool)
            for linha, coluna in self.resultado.caminho:
                marca[linha, coluna] = True
            return efeito.engrossar(marca, 2)
        return efeito.interior_do_contorno(
            self.resultado.caminho, self.app.grafo.altura, self.app.grafo.largura)

    def redesenhar(self) -> None:
        if self.app.imagem is None:
            return
        if self.ver_custo.get() and self.app.grafo is not None:
            custo = self.custo_pixel()
            # np.ptp em vez do metodo ndarray.ptp, removido no numpy 2
            normal = (custo - custo.min()) / (float(np.ptp(custo)) or 1.0)
            quadro = np.repeat((normal * 255).astype("uint8")[:, :, None], 3, axis=2)
        else:
            quadro = self.app.imagem
        if self.resultado is not None and self.resultado.sucesso:
            if self.fechar.get():
                area = self.mascara_atual()
                if area is not None and area.any():
                    quadro = pintura.marcar(quadro, area, pintura.TURQUESA, 0.4)
            quadro = pintura.pintar_caminho(quadro, self.resultado.caminho)
        for ponto in self.pontos:
            quadro = pintura.marcar_ponto(quadro, ponto)
        self.app.mostrar(quadro)

    def ao_ativar(self) -> None:
        self.redesenhar()

    def ao_trocar_imagem(self) -> None:
        self._custo_pixel = None
        self.limpar()
