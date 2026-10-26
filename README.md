# Show do Milhão em Pygame

Jogo de perguntas e respostas inspirado no formato de programas de conhecimento,
desenvolvido em Python com Pygame. O projeto possui três telas: abertura,
cadastro com histórico de partidas e jogo.

## Funcionalidades

- Perguntas fáceis, intermediárias e difíceis carregadas de `dados/perguntas.json`.
- Sorteio sem repetição dentro de cada partida.
- Premiação progressiva até R$ 1.000.000.
- Três ajudas, com até duas utilizações por ajuda:
  - eliminar duas alternativas;
  - ligar para um conhecido;
  - pular a pergunta.
- Efeitos sonoros em `assets/audios/`.
- Imagem de fundo em `assets/imagens/`.
- Histórico das últimas partidas em `dados/historico.json`.
- Compatibilidade futura com executável PyInstaller por meio de `sys._MEIPASS`.

## Estrutura

```text
.
├── main.py                 # Interface Pygame e eventos
├── complementos.py         # Regras, perguntas, áudio e histórico
├── build.py                # Geração do executável com PyInstaller
├── requirements.txt        # Dependências Python
├── assets/
│   ├── audios/
│   └── imagens/
├── dados/
│   ├── historico.json
│   └── perguntas.json
└── instalador_ambiente/
    ├── configurar_ambiente.bat
    └── configurar_ambiente.sh
```

## Instalação

### Windows

```bat
instalador_ambiente\configurar_ambiente.bat
```

### Linux ou macOS

```bash
chmod +x instalador_ambiente/configurar_ambiente.sh
./instalador_ambiente/configurar_ambiente.sh
```

Caso prefira configurar manualmente:

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows
python -m pip install -r requirements.txt
```

## Executar

Com o ambiente virtual ativado:

```bash
python main.py
```

## Gerar executável

Com o ambiente virtual ativado:

```bash
python -m pip install --upgrade pyinstaller
python build.py
```

O executável será criado em `dist/ShowDoMilhao` no Linux/macOS ou
`dist/ShowDoMilhao.exe` no Windows.

O build inclui automaticamente `assets/` e `dados/` no pacote usando
`--add-data`, com o separador adequado para cada sistema operacional.

## Controles

- `Enter` ou `Espaço`: avançar na tela inicial.
- Digitação: informar o nome do jogador.
- `Enter`: iniciar a partida após informar o nome.
- Teclas `1` a `4`: selecionar uma alternativa.
- Clique do mouse: navegar, responder e usar ajudas.
- `Esc`: voltar ou sair.

## Desenvolvimento

Os dois arquivos Python principais têm responsabilidades separadas:

- `main.py` cuida somente da interface, telas e captura de eventos.
- `complementos.py` concentra as regras, o banco de perguntas, os áudios e o
  histórico.

Para validar a sintaxe dos módulos:

```bash
python -m py_compile main.py complementos.py build.py
```
