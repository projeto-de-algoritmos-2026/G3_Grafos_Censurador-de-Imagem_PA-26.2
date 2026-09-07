"""Ponto de entrada.

    python main.py                abre a interface com a imagem de exemplo
    python main.py foto.jpg       abre a interface com uma imagem escolhida
    python main.py --demo         gera um painel comparativo em resultado.png
    python main.py --benchmark    mede tempo por numero de pixels
"""

import sys
from pathlib import Path

EXEMPLO = Path(__file__).parent / "dados" / "exemplo.png"


def main() -> None:
    argumentos = sys.argv[1:]
    opcoes = {a for a in argumentos if a.startswith("--")}
    arquivos = [a for a in argumentos if not a.startswith("--")]
    caminho = arquivos[0] if arquivos else EXEMPLO

    if "--benchmark" in opcoes:
        from benchmark import executar

        executar(caminho)
        return

    if "--demo" in opcoes:
        from demo import executar

        executar(caminho)
        return

    from gui.app import executar

    executar(caminho)


if __name__ == "__main__":
    main()
