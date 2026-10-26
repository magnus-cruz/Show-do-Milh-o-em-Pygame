#!/usr/bin/env bash

set -euo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."

PYTHON_CMD=""

selecionar_python() {
    local candidato
    for candidato in python3 python; do
        if command -v "$candidato" >/dev/null 2>&1 &&
            "$candidato" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 8) else 1)' >/dev/null 2>&1; then
            PYTHON_CMD="$candidato"
            return 0
        fi
    done
    return 1
}

if ! selecionar_python; then
    case "$(uname -s)" in
        Linux)
            if ! command -v apt-get >/dev/null 2>&1; then
                printf '\033[31m[ERRO]\033[0m apt/apt-get nao foi encontrado.\n'
                printf 'Instale Python 3.8+ e python3-venv manualmente.\n'
                exit 1
            fi
            printf 'Python 3.8+ nao encontrado. Instalando pelo apt...\n'
            if [[ "$EUID" -eq 0 ]]; then
                apt-get update
                apt-get install -y python3 python3-pip python3-venv
            elif command -v sudo >/dev/null 2>&1; then
                sudo apt-get update
                sudo apt-get install -y python3 python3-pip python3-venv
            else
                printf '\033[31m[ERRO]\033[0m sudo nao foi encontrado. Execute como root.\n'
                exit 1
            fi
            ;;
        Darwin)
            if ! command -v brew >/dev/null 2>&1; then
                printf '\033[31m[ERRO]\033[0m Homebrew nao foi encontrado.\n'
                printf 'Instale-o em: https://brew.sh/\n'
                printf 'Depois, execute este script novamente.\n'
                exit 1
            fi
            printf 'Python 3.8+ nao encontrado. Instalando pelo Homebrew...\n'
            brew install python
            ;;
        *)
            printf '\033[31m[ERRO]\033[0m Sistema operacional nao suportado: %s\n' "$(uname -s)"
            exit 1
            ;;
    esac

    selecionar_python || {
        printf '\033[31m[ERRO]\033[0m Python 3.8+ ainda nao esta disponivel no PATH.\n'
        printf 'Reabra o terminal e execute este script novamente.\n'
        exit 1
    }
fi

printf 'Python compativel encontrado: %s\n' "$PYTHON_CMD"

if [[ ! -x ".venv/bin/python" ]]; then
    printf 'Criando o ambiente virtual em .venv...\n'
    "$PYTHON_CMD" -m venv .venv
fi

source ".venv/bin/activate"

# Escrever sempre o arquivo torna a configuracao repetivel quando ele for removido.
printf '%s\n' 'pygame' > requirements.txt

printf 'Atualizando o pip...\n'
python -m pip install --upgrade pip
printf 'Instalando as dependencias...\n'
python -m pip install -r requirements.txt

printf '\n\033[32m========================================\033[0m\n'
printf '\033[32m Ambiente configurado com sucesso!\033[0m\n'
printf '\033[32m========================================\033[0m\n\n'
printf 'Ative o ambiente neste terminal com:\n'
printf '    source .venv/bin/activate\n\n'
printf 'Depois, inicie o jogo com:\n'
printf '    python main.py\n'
