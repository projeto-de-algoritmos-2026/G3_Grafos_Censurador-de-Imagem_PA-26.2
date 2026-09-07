"""Efeitos aplicados a uma regiao selecionada.

BASE COMPARTILHADA. Os tres algoritmos do projeto produzem coisas diferentes -
rotulos, contorno, regiao conectada - mas todos podem ser reduzidos a uma
MASCARA booleana do mesmo tamanho da imagem. Este modulo recebe imagem e
mascara e nao precisa saber qual algoritmo gerou a selecao.

E o que transforma o trabalho em ferramenta: borrar ou pixelizar exatamente a
area escolhida e o que fazem as ferramentas de censura de imagem (rosto,
placa, documento).
"""

from __future__ import annotations

from collections import deque

import numpy as np
from PIL import Image, ImageFilter

TARJA = np.array([12, 12, 12], dtype=np.uint8)


# ===================================================================== #
# da selecao a mascara
# ===================================================================== #
def interior_do_contorno(caminho: list[tuple[int, int]], altura: int,
                         largura: int) -> np.ndarray:
    """Preenche o interior de um contorno fechado.

    Usa o flood fill de forma invertida: em vez de inundar a regiao desejada,
    inunda tudo o que esta FORA dela, partindo das bordas da imagem e tratando
    o contorno como parede. O que a inundacao nao alcancou e o interior.

    E a mesma tecnica que os editores usam para transformar um traco fechado
    em selecao, e resolve o caso em que o interior nao e de cor uniforme -
    nenhuma comparacao de cor acontece aqui, so conectividade.

    Retorna mascara vazia se o contorno nao estiver fechado: nesse caso a
    inundacao contorna o traco, alcanca os dois lados dele e nao sobra
    interior algum alem da propria parede.
    """
    parede = np.zeros((altura, largura), dtype=bool)
    for linha, coluna in caminho:
        if 0 <= linha < altura and 0 <= coluna < largura:
            parede[linha, coluna] = True

    fora = np.zeros((altura, largura), dtype=bool)
    fila: deque[tuple[int, int]] = deque()
    for linha in range(altura):
        for coluna in (0, largura - 1):
            if not parede[linha, coluna] and not fora[linha, coluna]:
                fora[linha, coluna] = True
                fila.append((linha, coluna))
    for coluna in range(largura):
        for linha in (0, altura - 1):
            if not parede[linha, coluna] and not fora[linha, coluna]:
                fora[linha, coluna] = True
                fila.append((linha, coluna))

    while fila:
        linha, coluna = fila.popleft()
        for dl, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nl, nc = linha + dl, coluna + dc
            if (0 <= nl < altura and 0 <= nc < largura
                    and not parede[nl, nc] and not fora[nl, nc]):
                fora[nl, nc] = True
                fila.append((nl, nc))

    # o que a inundacao nao alcancou, descontando a propria parede
    interior_livre = ~fora & ~parede
    if not interior_livre.any():
        # a inundacao contornou o traco e chegou aos dois lados dele: o
        # contorno esta aberto e nao delimita area nenhuma
        return np.zeros((altura, largura), dtype=bool)
    return ~fora  # interior, incluindo o proprio contorno


def engrossar(mascara: np.ndarray, raio: int = 1) -> np.ndarray:
    """Dilata a mascara. Util para transformar um traco fino em faixa."""
    if raio <= 0:
        return mascara
    saida = mascara.copy()
    for _ in range(raio):
        crescida = saida.copy()
        crescida[1:, :] |= saida[:-1, :]
        crescida[:-1, :] |= saida[1:, :]
        crescida[:, 1:] |= saida[:, :-1]
        crescida[:, :-1] |= saida[:, 1:]
        saida = crescida
    return saida


# ===================================================================== #
# efeitos
# ===================================================================== #
def borrar(imagem: np.ndarray, mascara: np.ndarray, raio: float = 8.0) -> np.ndarray:
    """Desfoque gaussiano restrito a mascara.

    O desfoque e calculado na imagem inteira e depois recortado pela mascara.
    Fazer o contrario - borrar apenas os pixels selecionados - deixaria a
    borda da selecao dura e denunciaria o recorte.
    """
    if raio <= 0:
        raise ValueError("O raio precisa ser maior que zero")
    desfocada = np.asarray(
        Image.fromarray(imagem).filter(ImageFilter.GaussianBlur(radius=raio)),
        dtype=np.uint8)
    saida = imagem.copy()
    saida[mascara] = desfocada[mascara]
    return saida


def pixelizar(imagem: np.ndarray, mascara: np.ndarray, bloco: int = 12) -> np.ndarray:
    """Mosaico: substitui cada bloco pela sua cor media.

    E a censura mais usada em rosto e documento, e mais dificil de reverter
    que o desfoque - o desfoque preserva parte da informacao de alta
    frequencia e pode ser parcialmente desfeito.
    """
    if bloco < 2:
        raise ValueError("O bloco precisa ter ao menos 2 pixels")
    altura, largura = imagem.shape[:2]
    reduzida = Image.fromarray(imagem).resize(
        (max(1, largura // bloco), max(1, altura // bloco)), Image.BILINEAR)
    mosaico = np.asarray(reduzida.resize((largura, altura), Image.NEAREST), dtype=np.uint8)
    saida = imagem.copy()
    saida[mascara] = mosaico[mascara]
    return saida


def tarjar(imagem: np.ndarray, mascara: np.ndarray) -> np.ndarray:
    """Tarja preta sobre a area selecionada."""
    saida = imagem.copy()
    saida[mascara] = TARJA
    return saida


def achatar(imagem: np.ndarray, mascara: np.ndarray, k: float = 1500.0) -> np.ndarray:
    """Achatamento por segmentacao

    Unico ponto em que este modulo depende de um dos metodos, e por isso o
    import e local: mantem core/segmentacao.py livre para ser editado sem quebrar a barra de efeitos.
    """
    from .segmentacao import achatar as _achatar

    return _achatar(imagem, mascara, k=k, tamanho_minimo=max(20, int(k / 20)))


EFEITOS = {
    "achatar": achatar,
    "borrar": borrar,
    "pixelizar": pixelizar,
    "tarjar": tarjar,
}


def aplicar(nome: str, imagem: np.ndarray, mascara: np.ndarray,
            intensidade: float | None = None) -> np.ndarray:
    """Despacha para o efeito escolhido. Ignora selecao vazia."""
    if nome not in EFEITOS:
        raise ValueError(f"Efeito desconhecido: {nome}")
    if not mascara.any():
        return imagem.copy()
    if nome == "tarjar":
        return tarjar(imagem, mascara)
    if nome == "pixelizar":
        return pixelizar(imagem, mascara, int(intensidade or 12))
    if nome == "achatar":
        # a intensidade da interface vira a escala k da segmentacao
        return achatar(imagem, mascara, k=max(50.0, float(intensidade or 10) * 150))
    return borrar(imagem, mascara, float(intensidade or 8.0))
