"""Janela principal.
Cuida do que e comum aos dois metodos: carregar a imagem,
desenhar no canvas, converter clique de tela em coordenada de pixel e hospedar
as abas. Cada aba e um painel independente, com o contrato:

    ao_clicar(linha, coluna)   clique sobre a imagem
    ao_ativar()                a aba ganhou foco
    ao_trocar_imagem()         uma nova imagem foi carregada
    redesenhar()               refaz a exibicao
    mascara_atual()            mascara booleana da selecao, ou None

O ultimo metodo e o que unifica o programa: os tres algoritmos produzem coisas
diferentes, mas todos sabem reduzir sua selecao a uma mascara. A barra de
efeitos consome essa mascara sem saber qual algoritmo a gerou.

Adicionar um metodo novo e escrever um painel com esses quatro metodos e
registra-lo em _montar_abas. Nenhum painel importa o outro.
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog, messagebox

import numpy as np
from PIL import Image, ImageTk

from core import grafo_imagem, efeito
from gui.painel_segmentacao import PainelSegmentacao
from gui.painel_tesoura import PainelTesoura
from gui.painel_selecao import PainelSelecao

EXEMPLO = Path(__file__).resolve().parents[1] / "dados" / "exemplo.png"
FUNDO = "#eef1f4"


class Aplicacao(tk.Tk):
    def __init__(self, caminho: str | Path | None = None) -> None:
        super().__init__()
        self.title("Segmentador - algoritmos de grafo sobre imagens")
        self.geometry("1100x700")
        self.minsize(900, 600)

        self.imagem: np.ndarray | None = None
        self.grafo: grafo_imagem.GrafoImagem | None = None
        self._foto: ImageTk.PhotoImage | None = None
        self._historico: list[np.ndarray] = []   # pilha para desfazer
        self.efeito = tk.StringVar(value="achatar")
        self.intensidade = tk.StringVar(value="10")

        self._montar_widgets()
        self.carregar(caminho or EXEMPLO)

    # ================================================================== #
    def _montar_widgets(self) -> None:
        barra = ttk.Frame(self, padding=(10, 8))
        barra.pack(side=tk.TOP, fill=tk.X)
        ttk.Button(barra, text="Abrir imagem", command=self.escolher_arquivo).pack(side=tk.LEFT)
        ttk.Button(barra, text="Exemplo", command=lambda: self.carregar(EXEMPLO)).pack(
            side=tk.LEFT, padx=4)
        self.rotulo_arquivo = ttk.Label(barra, text="")
        self.rotulo_arquivo.pack(side=tk.LEFT, padx=12)
        self.rotulo_estado = ttk.Label(barra, text="", foreground="#a65a22")
        self.rotulo_estado.pack(side=tk.RIGHT)

        corpo = ttk.Frame(self)
        corpo.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(corpo, bg=FUNDO, highlightthickness=0, cursor="crosshair")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self._clique)
        self.canvas.bind("<Configure>", lambda e: self._redesenhar_aba())

        self._montar_barra_efeitos()

        self.abas = ttk.Notebook(corpo, width=340)
        self.abas.pack(side=tk.RIGHT, fill=tk.Y)
        self.abas.pack_propagate(False)
        self._montar_abas()
        self.abas.bind("<<NotebookTabChanged>>", lambda e: self._redesenhar_aba())

    def _montar_barra_efeitos(self) -> None:
        """Barra inferior: aplica um efeito a mascara do painel ativo."""
        barra = ttk.LabelFrame(self, text="Efeito sobre a selecao", padding=8)
        barra.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 8))

        for valor, texto in (("achatar", "Achatar (Kruskal)"), ("borrar", "Borrar"),
                             ("pixelizar", "Pixelizar"), ("tarjar", "Tarja preta")):
            ttk.Radiobutton(barra, text=texto, value=valor,
                            variable=self.efeito).pack(side=tk.LEFT, padx=(0, 8))

        ttk.Label(barra, text="intensidade").pack(side=tk.LEFT, padx=(10, 4))
        ttk.Entry(barra, textvariable=self.intensidade, width=6).pack(side=tk.LEFT)

        ttk.Button(barra, text="Aplicar", command=self.aplicar_efeito).pack(
            side=tk.LEFT, padx=10)
        self.bt_desfazer = ttk.Button(barra, text="Desfazer", command=self.desfazer,
                                      state=tk.DISABLED)
        self.bt_desfazer.pack(side=tk.LEFT)
        ttk.Button(barra, text="Salvar imagem", command=self.salvar).pack(
            side=tk.RIGHT)

    # ------------------------------------------------------------------ #
    def aplicar_efeito(self) -> None:
        """Pega a mascara do painel ativo e aplica o efeito escolhido."""
        if self.imagem is None:
            return
        painel = self.painel_ativo
        mascara = painel.mascara_atual()
        if mascara is None or not mascara.any():
            self.avisar("Nenhuma area selecionada nesta aba.\n\n"
                        "Kruskal: segmente e clique nas regioes.\n"
                        "Dijkstra: marque os pontos com 'Fechar o contorno' ligado.\n"
                        "Flood fill: clique em um ponto da imagem.")
            return
        try:
            intensidade = float(self.intensidade.get().replace(",", "."))
        except ValueError:
            self.avisar("A intensidade precisa ser numerica.")
            return

        try:
            nova = efeito.aplicar(self.efeito.get(), self.imagem, mascara, intensidade)
        except ValueError as erro:
            self.avisar(str(erro))
            return

        self._historico.append(self.imagem)
        self.bt_desfazer.configure(state=tk.NORMAL)
        self._trocar_imagem_editada(nova)

    def desfazer(self) -> None:
        if not self._historico:
            return
        self._trocar_imagem_editada(self._historico.pop())
        if not self._historico:
            self.bt_desfazer.configure(state=tk.DISABLED)

    def _trocar_imagem_editada(self, nova: np.ndarray) -> None:
        """Troca a imagem em edicao e reconstroi o grafo.

        O grafo precisa ser refeito porque os pixels mudaram: uma segmentacao
        ou um contorno calculados depois do efeito devem enxergar a imagem
        como ela esta agora.
        """
        self.imagem = nova
        self.grafo = grafo_imagem.construir(nova)
        for painel, _ in self.paineis:
            painel.ao_trocar_imagem()
        self.painel_ativo.redesenhar()

    def salvar(self) -> None:
        if self.imagem is None:
            return
        caminho = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg")])
        if caminho:
            Image.fromarray(self.imagem).save(caminho)

    def _montar_abas(self) -> None:
        self.paineis = [
            (PainelSegmentacao(self.abas, self), " Kruskal "),
            (PainelTesoura(self.abas, self), " Dijkstra "),
            (PainelSelecao(self.abas, self), " Flood fill "),
        ]
        for painel, titulo in self.paineis:
            self.abas.add(painel, text=titulo)

    @property
    def painel_ativo(self):
        indice = self.abas.index(self.abas.select())
        return self.paineis[indice][0]

    # ================================================================== #
    # imagem
    # ================================================================== #
    def escolher_arquivo(self) -> None:
        caminho = filedialog.askopenfilename(
            filetypes=[("Imagens", "*.png *.jpg *.jpeg *.bmp *.gif"), ("Todos", "*.*")])
        if caminho:
            self.carregar(caminho)

    def carregar(self, caminho: str | Path) -> None:
        try:
            self.imagem = grafo_imagem.carregar(caminho)
            self.grafo = grafo_imagem.construir(self.imagem)
        except Exception as erro:  # arquivo invalido, formato nao suportado
            self.avisar(f"Nao foi possivel abrir a imagem: {erro}")
            return
        self.rotulo_arquivo.configure(
            text=f"{Path(caminho).name} - {self.grafo.largura}x{self.grafo.altura} px, "
                 f"{self.grafo.total_vertices:,} vertices, "
                 f"{self.grafo.total_arestas:,} arestas".replace(",", "."))
        self._historico.clear()
        self.bt_desfazer.configure(state=tk.DISABLED)
        for painel, _ in self.paineis:
            painel.ao_trocar_imagem()
        self.mostrar(self.imagem)

    # ================================================================== #
    # desenho e coordenadas
    # ================================================================== #
    def _geometria(self) -> tuple[float, int, int]:
        """Escala de exibicao e deslocamento da imagem dentro do canvas."""
        largura = self.canvas.winfo_width() or 700
        altura = self.canvas.winfo_height() or 600
        escala = min(largura / self.grafo.largura, altura / self.grafo.altura, 1.0)
        largura_final = self.grafo.largura * escala
        altura_final = self.grafo.altura * escala
        return escala, int((largura - largura_final) / 2), int((altura - altura_final) / 2)

    def mostrar(self, quadro: np.ndarray) -> None:
        """Exibe um quadro RGB no canvas, ajustado ao espaco disponivel."""
        if self.grafo is None:
            return
        escala, x, y = self._geometria()
        figura = Image.fromarray(np.ascontiguousarray(quadro, dtype=np.uint8))
        if escala < 1.0:
            figura = figura.resize(
                (max(1, int(figura.width * escala)), max(1, int(figura.height * escala))),
                Image.NEAREST)
        self._foto = ImageTk.PhotoImage(figura)  # referencia viva evita coleta
        self.canvas.delete("all")
        self.canvas.create_image(x, y, image=self._foto, anchor="nw")

    def _clique(self, evento) -> None:
        if self.grafo is None:
            return
        escala, x, y = self._geometria()
        coluna = int((evento.x - x) / escala)
        linha = int((evento.y - y) / escala)
        if self.grafo.dentro(linha, coluna):
            self.painel_ativo.ao_clicar(linha, coluna)

    def _redesenhar_aba(self) -> None:
        if self.grafo is not None:
            self.painel_ativo.ao_ativar()

    # ================================================================== #
    # avisos
    # ================================================================== #
    def ocupado(self, mensagem: str | None) -> None:
        self.rotulo_estado.configure(text=mensagem or "")
        self.configure(cursor="watch" if mensagem else "")
        self.update_idletasks()

    def avisar(self, mensagem: str) -> None:
        messagebox.showinfo("Segmentador", mensagem, parent=self)


def executar(caminho: str | Path | None = None) -> None:
    Aplicacao(caminho).mainloop()
