"""Compila o Show do Milhão como um executável standalone com PyInstaller.

Instalação:
    python -m pip install --upgrade pyinstaller

Execução:
    python build.py

Em um executável criado com --onefile, os recursos são extraídos
temporariamente. A função resource_path abaixo é o padrão usado pelo
main.py para localizar esses recursos:

    def resource_path(relative_path: str) -> Path:
        base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
        return base_path / relative_path

Exemplo:
    FUNDO_PATH = resource_path("assets/imagens/fundo.png")
    perguntas_path = resource_path("dados/perguntas.json")
"""

from __future__ import annotations

import platform
import subprocess
import sys
from importlib.util import find_spec
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
MAIN_FILE = PROJECT_ROOT / "main.py"
ASSETS_DIR = PROJECT_ROOT / "assets"
DATA_DIR = PROJECT_ROOT / "dados"


def build() -> None:
    """Valida o projeto e executa o PyInstaller com as opções do jogo."""
    operating_system = platform.system()
    if operating_system not in {"Windows", "Linux", "Darwin"}:
        raise RuntimeError(
            f"Sistema operacional não suportado automaticamente: {operating_system}"
        )

    for required_path in (MAIN_FILE, ASSETS_DIR, DATA_DIR):
        if not required_path.exists():
            raise FileNotFoundError(f"Recurso obrigatório não encontrado: {required_path}")

    if find_spec("PyInstaller") is None:
        raise RuntimeError(
            "PyInstaller não está instalado no ambiente Python atual. "
            "Execute: python -m pip install --upgrade pyinstaller"
        )

    # O separador separa a origem e o destino dentro do pacote.
    data_separator = ";" if operating_system == "Windows" else ":"
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        "--onefile",
        "--noconsole",
        "--name",
        "ShowDoMilhao",
        "--distpath",
        str(PROJECT_ROOT / "dist"),
        "--workpath",
        str(PROJECT_ROOT / "build"),
        "--specpath",
        str(PROJECT_ROOT),
        "--add-data",
        f"{ASSETS_DIR}{data_separator}assets",
        "--add-data",
        f"{DATA_DIR}{data_separator}dados",
        str(MAIN_FILE),
    ]

    print(f"Sistema detectado: {operating_system}")
    print("Iniciando compilação com PyInstaller...")
    print(" ".join(f'"{argument}"' if " " in argument else argument for argument in command))

    try:
        subprocess.run(command, cwd=PROJECT_ROOT, check=True)
    except FileNotFoundError as error:
        raise RuntimeError(
            "PyInstaller não está instalado no ambiente Python atual. "
            "Execute: python -m pip install --upgrade pyinstaller"
        ) from error
    except subprocess.CalledProcessError as error:
        raise RuntimeError(
            f"A compilação falhou com código de saída {error.returncode}."
        ) from error

    executable_name = "ShowDoMilhao.exe" if operating_system == "Windows" else "ShowDoMilhao"
    print(f"\nCompilação concluída. Executável: {PROJECT_ROOT / 'dist' / executable_name}")


if __name__ == "__main__":
    try:
        build()
    except (FileNotFoundError, RuntimeError) as error:
        print(f"\nERRO: {error}", file=sys.stderr)
        raise SystemExit(1) from error
