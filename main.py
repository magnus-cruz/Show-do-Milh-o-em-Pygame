"""Aplicação Pygame do Show do Milhão."""

from __future__ import annotations

import sys
from pathlib import Path

import pygame

from complementos import GerenciadorAudios, Historico, Jogo, PREMIOS


def resource_path(relative_path: str | Path) -> Path:
    """Resolve recursos no código-fonte ou dentro do executável PyInstaller."""
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base_path / relative_path


BASE_DIR = resource_path("")
HISTORICO = Historico(resource_path("dados/historico.json"))
FUNDO_PATH = resource_path("assets/imagens/fundo.png")

BRANCO = (245, 248, 255)
AZUL_ESCURO = (8, 25, 70)
AZUL = (20, 70, 145)
AZUL_CLARO = (35, 110, 200)
DOURADO = (247, 195, 50)
VERDE = (35, 160, 91)
VERMELHO = (202, 57, 57)
CINZA = (125, 135, 155)


class Aplicacao:
    def __init__(self) -> None:
        pygame.init()
        self.tela = pygame.display.set_mode((1100, 700), pygame.RESIZABLE)
        pygame.display.set_caption("Show do Milhão")
        self.relogio = pygame.time.Clock()
        self.audio = GerenciadorAudios(BASE_DIR / "assets" / "audios")
        self.jogo = Jogo(resource_path("dados/perguntas.json"), self.audio.tocar)
        self.fundo = self._carregar_fundo()
        self.historico = HISTORICO.carregar()
        self.tela_atual = "inicial"
        self.nome = ""
        self.mensagem = ""

    def _carregar_fundo(self) -> pygame.Surface | None:
        try:
            return pygame.image.load(FUNDO_PATH).convert()
        except (pygame.error, OSError):
            return None

    def fonte(self, tamanho: int, negrito: bool = False) -> pygame.font.Font:
        return pygame.font.SysFont("arial", tamanho, bold=negrito)

    def texto(
        self,
        mensagem: str,
        posicao: tuple[int, int],
        tamanho: int = 20,
        cor=BRANCO,
        centralizado: bool = False,
        negrito: bool = False,
    ) -> pygame.Rect:
        imagem = self.fonte(tamanho, negrito).render(mensagem, True, cor)
        retangulo = imagem.get_rect()
        if centralizado:
            retangulo.center = posicao
        else:
            retangulo.topleft = posicao
        self.tela.blit(imagem, retangulo)
        return retangulo

    def botao(self, retangulo: pygame.Rect, legenda: str, cor=AZUL_CLARO) -> None:
        pygame.draw.rect(self.tela, cor, retangulo, border_radius=9)
        pygame.draw.rect(self.tela, DOURADO, retangulo, 2, border_radius=9)
        self.texto(legenda, retangulo.center, 19, centralizado=True, negrito=True)

    def painel(self, retangulo: pygame.Rect, alpha: int = 230) -> None:
        camada = pygame.Surface(retangulo.size, pygame.SRCALPHA)
        camada.fill((*AZUL_ESCURO, alpha))
        self.tela.blit(camada, retangulo.topleft)
        pygame.draw.rect(self.tela, DOURADO, retangulo, 2, border_radius=12)

    def desenhar_fundo(self) -> None:
        if self.fundo:
            imagem = pygame.transform.smoothscale(self.fundo, self.tela.get_size())
            self.tela.blit(imagem, (0, 0))
            sombra = pygame.Surface(self.tela.get_size(), pygame.SRCALPHA)
            sombra.fill((0, 10, 40, 115))
            self.tela.blit(sombra, (0, 0))
        else:
            self.tela.fill(AZUL_ESCURO)

    def desenhar_inicial(self) -> None:
        largura, altura = self.tela.get_size()
        self.texto("SHOW DO MILHÃO", (largura // 2, altura // 3), 54, DOURADO, True, True)
        self.texto("Conhecimentos, estratégia e muita emoção!", (largura // 2, altura // 3 + 65), 22, centralizado=True)
        self.botao(pygame.Rect(largura // 2 - 140, altura - 170, 280, 58), "COMEÇAR")
        self.texto("ENTER ou clique para continuar | ESC para sair", (largura // 2, altura - 90), 16, centralizado=True)

    def desenhar_cadastro(self) -> None:
        largura, altura = self.tela.get_size()
        painel = pygame.Rect(50, 35, largura - 100, altura - 70)
        self.painel(painel)
        self.texto("CADASTRO E HISTÓRICO", (largura // 2, 75), 32, DOURADO, True, True)
        self.texto("Nome do jogador:", (painel.left + 35, 130), 21, negrito=True)
        campo = pygame.Rect(painel.left + 35, 165, painel.width - 70, 52)
        pygame.draw.rect(self.tela, BRANCO, campo, border_radius=6)
        self.texto(self.nome or "Digite seu nome...", (campo.left + 12, campo.centery - 11), 20, AZUL_ESCURO)
        self.texto("Últimas partidas", (painel.left + 35, 260), 23, DOURADO, negrito=True)
        registros = self.historico[-6:][::-1]
        if not registros:
            self.texto("Nenhuma partida registrada.", (painel.left + 35, 300), 18, CINZA)
        for indice, registro in enumerate(registros):
            linha = f"{registro.get('nome', '?')} - {registro.get('resultado', '?')}"
            self.texto(linha, (painel.left + 35, 300 + indice * 28), 17)
        self.botao(pygame.Rect(painel.left + 35, painel.bottom - 70, 130, 46), "VOLTAR", VERMELHO)
        self.botao(pygame.Rect(painel.right - 205, painel.bottom - 70, 170, 46), "JOGAR")
        if self.mensagem:
            self.texto(self.mensagem, (largura // 2, painel.bottom - 100), 17, VERMELHO, True, True)

    def formatar_dinheiro(self, valor: int) -> str:
        return f"R$ {valor:,.0f}".replace(",", ".")

    def desenhar_jogo(self) -> None:
        largura, altura = self.tela.get_size()
        if self.jogo.encerrada:
            self.painel(pygame.Rect(150, 170, largura - 300, 300))
            titulo = "VOCÊ GANHOU!" if self.jogo.vencedor else "FIM DE JOGO"
            self.texto(titulo, (largura // 2, 235), 40, DOURADO, True, True)
            self.texto(self.mensagem, (largura // 2, 310), 21, centralizado=True)
            self.texto(f"Prêmio: {self.formatar_dinheiro(self.jogo.premio_atual)}", (largura // 2, 355), 26, centralizado=True)
            self.botao(pygame.Rect(largura // 2 - 120, 405, 240, 48), "NOVA PARTIDA")
            return

        pergunta = self.jogo.pergunta_atual
        self.texto(f"Jogador: {self.nome}", (25, 20), 18, negrito=True)
        self.texto(f"Nível {self.jogo.nivel} | {self.formatar_dinheiro(PREMIOS[self.jogo.indice])}", (largura - 330, 20), 21, DOURADO, negrito=True)
        caixa = pygame.Rect(35, 70, largura - 70, 125)
        self.painel(caixa)
        self.texto(pergunta.texto, caixa.center, 26, centralizado=True, negrito=True)
        largura_opcao = max(300, (largura - 110) // 2)
        for indice, opcao in enumerate(pergunta.opcoes):
            x = 35 if indice % 2 == 0 else largura - 35 - largura_opcao
            retangulo = pygame.Rect(x, 220 + (indice // 2) * 70, largura_opcao, 54)
            oculta = indice in self.jogo.opcoes_ocultas
            legenda = f"{'ABCD'[indice]}) {'ALTERNATIVA ELIMINADA' if oculta else opcao}"
            self.botao(retangulo, legenda, CINZA if oculta else AZUL)
        self.texto("AJUDAS (máximo 2 usos cada)", (35, 380), 18, negrito=True)
        for indice, nome in enumerate(("eliminar", "ligar", "pular")):
            usos = self.jogo.ajudas[nome]
            cor = CINZA if usos >= 2 else VERDE
            self.botao(pygame.Rect(35 + indice * 175, 410, 155, 48), f"{nome.upper()} ({usos}/2)", cor)
        self.texto(self.mensagem, (35, altura - 55), 18, DOURADO, negrito=True)

    def iniciar_partida(self) -> None:
        if not self.nome.strip():
            self.mensagem = "Digite seu nome antes de começar."
            return
        self.nome = self.nome.strip()
        self.jogo.iniciar()
        self.tela_atual = "jogo"
        self.mensagem = "Boa sorte!"

    def registrar_resultado(self) -> None:
        if not self.jogo.encerrada:
            return
        resultado = "Ganhou R$ 1.000.000" if self.jogo.vencedor else f"Parou com {self.formatar_dinheiro(self.jogo.premio_atual)}"
        HISTORICO.adicionar(self.nome, resultado)
        self.historico = HISTORICO.carregar()

    def responder(self, indice: int) -> None:
        try:
            resposta = self.jogo.responder(indice)
        except ValueError as erro:
            self.mensagem = str(erro)
            return
        self.mensagem = resposta.mensagem
        if resposta.encerrado:
            self.registrar_resultado()

    def usar_ajuda(self, nome: str) -> None:
        try:
            retorno = self.jogo.usar_ajuda(nome)
            self.mensagem = ", ".join(map(str, retorno)) if isinstance(retorno, list) else retorno
        except (RuntimeError, ValueError) as erro:
            self.mensagem = str(erro)

    def tratar_evento(self, evento: pygame.event.Event) -> bool:
        if evento.type == pygame.QUIT:
            return False
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_ESCAPE:
                if self.tela_atual == "inicial":
                    return False
                self.tela_atual = "cadastro" if self.tela_atual == "jogo" else "inicial"
                self.mensagem = ""
                return True
            if self.tela_atual == "inicial" and evento.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.tela_atual = "cadastro"
            elif self.tela_atual == "cadastro":
                if evento.key == pygame.K_BACKSPACE:
                    self.nome = self.nome[:-1]
                elif evento.key == pygame.K_RETURN:
                    self.iniciar_partida()
                elif evento.unicode.isprintable() and len(self.nome) < 28:
                    self.nome += evento.unicode
            elif self.tela_atual == "jogo" and not self.jogo.encerrada and pygame.K_1 <= evento.key <= pygame.K_4:
                self.responder(evento.key - pygame.K_1)
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            self.clique(evento.pos)
        return True

    def clique(self, posicao: tuple[int, int]) -> None:
        largura, altura = self.tela.get_size()
        if self.tela_atual == "inicial":
            self.tela_atual = "cadastro"
        elif self.tela_atual == "cadastro":
            painel = pygame.Rect(50, 35, largura - 100, altura - 70)
            if pygame.Rect(painel.left + 35, painel.bottom - 70, 130, 46).collidepoint(posicao):
                self.tela_atual = "inicial"
                self.mensagem = ""
            elif pygame.Rect(painel.right - 205, painel.bottom - 70, 170, 46).collidepoint(posicao):
                self.iniciar_partida()
        elif self.tela_atual == "jogo":
            if self.jogo.encerrada:
                self.tela_atual = "cadastro"
                self.historico = HISTORICO.carregar()
                self.mensagem = ""
            elif 220 <= posicao[1] <= 380:
                largura_opcao = max(300, (largura - 110) // 2)
                coluna = 0 if posicao[0] < largura // 2 else 1
                linha = 0 if posicao[1] < 290 else 1
                self.responder(linha * 2 + coluna)
            elif 410 <= posicao[1] <= 458:
                indice = min(2, max(0, (posicao[0] - 35) // 175))
                self.usar_ajuda(("eliminar", "ligar", "pular")[indice])

    def executar(self) -> None:
        rodando = True
        while rodando:
            for evento in pygame.event.get():
                rodando = self.tratar_evento(evento)
            self.desenhar_fundo()
            if self.tela_atual == "inicial":
                self.desenhar_inicial()
            elif self.tela_atual == "cadastro":
                self.desenhar_cadastro()
            else:
                self.desenhar_jogo()
            pygame.display.flip()
            self.relogio.tick(60)
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Aplicacao().executar()
