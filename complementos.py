"""Lógica, dados e serviços do jogo Show do Milhão.

Este módulo não depende da interface Pygame. A interface em ``main.py`` usa
as classes daqui para controlar a partida, o áudio e o histórico.
"""

from __future__ import annotations

import json
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Final


def resource_path(relative_path: str | Path) -> Path:
    """Resolve recursos tanto no código-fonte quanto no executável PyInstaller."""
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base_path / relative_path


# 1k..10k; 40k, 70k, 100k; 200k..1M em passos de 100k.
PREMIOS: Final[tuple[int, ...]] = (
    *range(1_000, 10_001, 1_000),
    40_000,
    70_000,
    100_000,
    *range(200_000, 1_000_001, 100_000),
)


@dataclass(frozen=True)
class Pergunta:
    id: str
    texto: str
    opcoes: tuple[str, str, str, str]
    correta: int


@dataclass(frozen=True)
class ResultadoResposta:
    correta: bool
    encerrado: bool
    premio: int
    mensagem: str


class BancoPerguntas:
    """Carrega perguntas categorizadas e sorteia sem repetição na partida."""

    CATEGORIAS: Final[tuple[str, ...]] = ("faceis", "intermediarias", "dificeis")

    def __init__(self, caminho: str | Path) -> None:
        self.caminho = Path(caminho)
        self.dados = self._carregar()

    def _carregar(self) -> dict[str, list[dict[str, Any]]]:
        try:
            dados = json.loads(self.caminho.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeError(f"Falha ao carregar o banco de perguntas: {self.caminho}") from error
        if not isinstance(dados, dict) or any(
            not isinstance(dados.get(categoria), list) for categoria in self.CATEGORIAS
        ):
            raise ValueError("O banco deve conter as listas faceis, intermediarias e dificieis.")
        return dados

    def sortear_partida(self, rng: random.Random) -> list[Pergunta]:
        quantidades = {
            "faceis": 10,
            "intermediarias": 3,
            "dificeis": len(PREMIOS) - 13,
        }
        perguntas: list[Pergunta] = []
        for categoria in self.CATEGORIAS:
            itens = self.dados[categoria]
            quantidade = quantidades[categoria]
            if len(itens) < quantidade:
                raise ValueError(
                    f"A categoria {categoria} precisa de pelo menos {quantidade} perguntas."
                )
            for item in rng.sample(itens, quantidade):
                opcoes = item.get("opcoes")
                correta = item.get("correta")
                if (
                    not isinstance(item.get("id"), str)
                    or not isinstance(item.get("pergunta"), str)
                    or not isinstance(opcoes, list)
                    or len(opcoes) != 4
                    or not all(isinstance(opcao, str) for opcao in opcoes)
                    or not isinstance(correta, int)
                    or correta not in range(4)
                ):
                    raise ValueError(f"Pergunta inválida: {item.get('id', '?')}.")
                perguntas.append(
                    Pergunta(item["id"], item["pergunta"], tuple(opcoes), correta)
                )
        return perguntas


class GerenciadorAudios:
    """Carrega e reproduz os efeitos sonoros disponíveis no jogo."""

    ARQUIVOS: Final[dict[str, str]] = {
        "bem_vindo": "bem_vindo.mp3",
        "acerto": "acertou.mp3",
        "erro": "errou.mp3",
        "milhao": "ganhou_milhao.mp3",
        "ajuda_eliminar": "ajuda_cartas.mp3",
        "ajuda_ligar": "ajuda_ligacao.mp3",
        "ajuda_pular": "ajuda_pular.mp3",
    }

    def __init__(self, pasta: str | Path) -> None:
        self.pasta = Path(pasta)
        self._sons: dict[str, Any] = {}
        self._pygame: Any = None
        self._carregado = False

    def carregar(self) -> None:
        if self._carregado:
            return
        try:
            import pygame

            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except (ImportError, RuntimeError) as error:
            raise RuntimeError("Não foi possível inicializar o mixer do Pygame.") from error

        self._pygame = pygame
        for nome, arquivo in self.ARQUIVOS.items():
            caminho = self.pasta / arquivo
            if caminho.exists():
                try:
                    self._sons[nome] = pygame.mixer.Sound(str(caminho))
                except pygame.error:
                    continue
        self._carregado = True

    def tocar(self, nome: str) -> bool:
        if nome not in self.ARQUIVOS:
            raise KeyError(f"Áudio não cadastrado: {nome}")
        self.carregar()
        som = self._sons.get(nome)
        if som is None:
            return False
        som.play()
        return True

    def parar_tudo(self) -> None:
        if self._pygame is not None:
            self._pygame.mixer.stop()


class Historico:
    """Persiste as últimas partidas em JSON."""

    def __init__(self, caminho: str | Path) -> None:
        self.caminho = Path(caminho)

    def carregar(self) -> list[dict[str, str]]:
        try:
            dados = json.loads(self.caminho.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        return dados if isinstance(dados, list) else []

    def adicionar(self, nome: str, resultado: str) -> None:
        registros = self.carregar()
        registros.append({"nome": nome, "resultado": resultado})
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        self.caminho.write_text(
            json.dumps(registros[-20:], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


class Jogo:
    """Controla uma partida completa, sem conhecer a interface gráfica."""

    AJUDAS: Final[tuple[str, ...]] = ("eliminar", "ligar", "pular")

    def __init__(
        self,
        caminho_perguntas: str | Path,
        tocar_audio: Callable[[str], Any] | None = None,
        rng: random.Random | None = None,
    ) -> None:
        self.banco = BancoPerguntas(caminho_perguntas)
        self.tocar_audio = tocar_audio
        self.rng = rng or random.Random()
        self.perguntas: list[Pergunta] = []
        self.indice = 0
        self.premio_atual = 0
        self.ajudas = {nome: 0 for nome in self.AJUDAS}
        self.opcoes_ocultas: set[int] = set()
        self.iniciada = False
        self.encerrada = False
        self.vencedor = False

    @property
    def pergunta_atual(self) -> Pergunta:
        if not self.iniciada or self.encerrada:
            raise RuntimeError("A partida não está em uma pergunta ativa.")
        return self.perguntas[self.indice]

    @property
    def nivel(self) -> int:
        return self.indice + 1

    @property
    def premio_da_pergunta(self) -> int:
        return PREMIOS[self.indice]

    def iniciar(self) -> None:
        self.perguntas = self.banco.sortear_partida(self.rng)
        self.indice = 0
        self.premio_atual = 0
        self.ajudas = {nome: 0 for nome in self.AJUDAS}
        self.opcoes_ocultas = set()
        self.iniciada = True
        self.encerrada = False
        self.vencedor = False
        self._audio("bem_vindo")

    def _audio(self, nome: str) -> None:
        if self.tocar_audio is not None:
            self.tocar_audio(nome)

    def responder(self, indice: int) -> ResultadoResposta:
        if indice not in range(4) or indice in self.opcoes_ocultas:
            raise ValueError("Alternativa inválida ou eliminada.")
        pergunta = self.pergunta_atual
        if indice != pergunta.correta:
            self.encerrada = True
            self._audio("erro")
            return ResultadoResposta(
                False,
                True,
                self.premio_atual,
                f"Resposta incorreta. A correta era {pergunta.opcoes[pergunta.correta]}.",
            )

        self.premio_atual = self.premio_da_pergunta
        ultimo = self.indice == len(self.perguntas) - 1
        self._audio("milhao" if ultimo else "acerto")
        if ultimo:
            self.encerrada = True
            self.vencedor = True
            return ResultadoResposta(True, True, self.premio_atual, "Parabéns! Você ganhou R$ 1.000.000!")
        self._avancar()
        return ResultadoResposta(True, False, self.premio_atual, "Resposta correta!")

    def _avancar(self) -> None:
        self.indice += 1
        self.opcoes_ocultas.clear()

    def usar_ajuda(self, nome: str) -> str | list[int]:
        if nome not in self.AJUDAS:
            raise ValueError(f"Ajuda desconhecida: {nome}")
        if self.ajudas[nome] >= 2:
            raise RuntimeError(f"A ajuda '{nome}' já foi usada duas vezes.")
        if nome == "pular" and self.indice == len(PREMIOS) - 1:
            raise RuntimeError("Não é possível pular a pergunta de 1 milhão.")

        self.ajudas[nome] += 1
        if nome == "eliminar":
            erradas = [
                indice
                for indice in range(4)
                if indice != self.pergunta_atual.correta
                and indice not in self.opcoes_ocultas
            ]
            eliminadas = self.rng.sample(erradas, min(2, len(erradas)))
            self.opcoes_ocultas.update(eliminadas)
            self._audio("ajuda_eliminar")
            return eliminadas
        if nome == "ligar":
            pergunta = self.pergunta_atual
            opcoes_visiveis = [
                opcao for indice, opcao in enumerate(pergunta.opcoes)
                if indice not in self.opcoes_ocultas
            ]
            palpite = (
                pergunta.opcoes[pergunta.correta]
                if self.rng.random() < 0.75
                else self.rng.choice(opcoes_visiveis)
            )
            self._audio("ajuda_ligar")
            return f"Seu conhecido acha que a resposta é: {palpite}."

        self._audio("ajuda_pular")
        self._avancar()
        return "Pergunta pulada. A próxima pergunta é do mesmo nível de dificuldade."
