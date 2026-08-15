"""Testes da montagem.

O planejamento é puro e roda sempre. Os testes que chamam ffmpeg de verdade
são pulados quando o binário não está instalado.

Rodar:  python -m unittest discover -s testes -v
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from garimpo.montagem import (ClipeBroll, ErroFFmpeg, achar_binario, escrever_creditos,
                              ffmpeg_disponivel, montar_insercao, montar_split,
                              planejar_insercoes, sondar)

TEM_FFMPEG = ffmpeg_disponivel()
precisa_ffmpeg = unittest.skipUnless(TEM_FFMPEG, "ffmpeg/ffprobe não instalados")


def clipes(*duracoes: float) -> list[ClipeBroll]:
    return [ClipeBroll(caminho=f"/tmp/c{i}.mp4", duracao=d, titulo=f"c{i}")
            for i, d in enumerate(duracoes)]


# --------------------------------------------------------------------------- #
# planejamento (sem ffmpeg)
# --------------------------------------------------------------------------- #

class TestPlanejamento(unittest.TestCase):
    def test_poupa_o_gancho(self):
        plano = planejar_insercoes(60, clipes(10), intervalo=8, duracao=2)
        self.assertEqual(plano[0].inicio, 8.0)

    def test_passo_conta_a_propria_insercao(self):
        # 8s de base + 2s de inserção = próxima entra em 18s, não em 16s
        plano = planejar_insercoes(60, clipes(10), intervalo=8, duracao=2)
        self.assertEqual([i.inicio for i in plano[:3]], [8.0, 18.0, 28.0])

    def test_respeita_a_margem_final(self):
        plano = planejar_insercoes(30, clipes(10), intervalo=8, duracao=2, margem_final=1.5)
        self.assertTrue(all(i.fim <= 28.5 for i in plano), [i.fim for i in plano])

    def test_corte_curto_nao_gera_plano(self):
        self.assertEqual(planejar_insercoes(6, clipes(10), intervalo=30, duracao=2), [])

    def test_sem_clipes_nao_gera_plano(self):
        self.assertEqual(planejar_insercoes(60, [], intervalo=8, duracao=2), [])

    def test_semente_reproduz_o_mesmo_plano(self):
        a = planejar_insercoes(120, clipes(10, 12, 8), semente=7)
        b = planejar_insercoes(120, clipes(10, 12, 8), semente=7)
        self.assertEqual([(i.inicio, i.clipe.caminho, i.offset) for i in a],
                         [(i.inicio, i.clipe.caminho, i.offset) for i in b])

    def test_sementes_diferentes_mudam_a_ordem(self):
        a = [i.clipe.caminho for i in planejar_insercoes(300, clipes(10, 12, 8, 15), semente=1)]
        b = [i.clipe.caminho for i in planejar_insercoes(300, clipes(10, 12, 8, 15), semente=99)]
        self.assertNotEqual(a, b)

    def test_offset_cabe_dentro_do_clipe(self):
        plano = planejar_insercoes(300, clipes(5, 6, 4), intervalo=5, duracao=2, semente=3)
        for ins in plano:
            self.assertLessEqual(ins.offset + ins.duracao, ins.clipe.duracao + 1e-6)
            self.assertGreaterEqual(ins.offset, 0)

    def test_clipe_curto_encolhe_a_insercao(self):
        plano = planejar_insercoes(60, clipes(1.2), intervalo=8, duracao=3)
        self.assertAlmostEqual(plano[0].duracao, 1.2, places=2)

    def test_maximo_limita(self):
        plano = planejar_insercoes(10_000, clipes(10), intervalo=5, duracao=2, maximo=6)
        self.assertEqual(len(plano), 6)

    def test_primeiro_explicito(self):
        plano = planejar_insercoes(60, clipes(10), intervalo=8, duracao=2, primeiro=3)
        self.assertEqual(plano[0].inicio, 3.0)

    def test_todos_os_clipes_entram_em_rodizio(self):
        plano = planejar_insercoes(300, clipes(10, 10, 10), intervalo=5, duracao=2, semente=5)
        self.assertEqual(len({i.clipe.caminho for i in plano}), 3)


class TestCreditos(unittest.TestCase):
    def test_lista_clipes_e_momentos(self):
        plano = planejar_insercoes(60, clipes(10, 10), intervalo=8, duracao=2, semente=1)
        for ins in plano:
            ins.clipe.credito = f"Crédito de {ins.clipe.titulo}"
        from garimpo.montagem import Resultado
        resultado = Resultado(saida="x.mp4", modo="insercao", insercoes=plano,
                              clipes_usados=list({i.clipe.caminho: i.clipe for i in plano}.values()))
        with tempfile.TemporaryDirectory() as d:
            caminho = escrever_creditos(resultado, os.path.join(d, "c.txt"),
                                        credito_base="Base por Fulano (CC BY)",
                                        editor="Canal X")
            with open(caminho, encoding="utf-8") as f:
                texto = f.read()
        self.assertIn("Base por Fulano (CC BY)", texto)
        self.assertIn("Canal X", texto)
        self.assertIn("Crédito de c0", texto)
        self.assertIn("aparece em:", texto)
        self.assertIn("áudio dos clipes de B-roll foi descartado", texto)

    def test_avisa_quando_falta_credito_da_base(self):
        from garimpo.montagem import Resultado
        with tempfile.TemporaryDirectory() as d:
            caminho = escrever_creditos(Resultado(saida="x.mp4", modo="split"),
                                        os.path.join(d, "c.txt"))
            with open(caminho, encoding="utf-8") as f:
                self.assertIn("[preencha aqui", f.read())


# --------------------------------------------------------------------------- #
# integração (chama ffmpeg de verdade)
# --------------------------------------------------------------------------- #

def gerar_video(caminho: str, cor: str = "", segundos: float = 4, largura: int = 320,
                altura: int = 240, fps: int = 25, com_audio: bool = False) -> str:
    fonte = (f"color=c={cor}:size={largura}x{altura}:rate={fps}:duration={segundos}" if cor
             else f"testsrc=size={largura}x{altura}:rate={fps}:duration={segundos}")
    args = [achar_binario("ffmpeg"), "-y", "-loglevel", "error", "-f", "lavfi", "-i", fonte]
    if com_audio:
        args += ["-f", "lavfi", "-i", f"sine=frequency=440:duration={segundos}"]
    args += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "ultrafast"]
    if com_audio:
        args += ["-c:a", "aac", "-shortest"]
    args.append(caminho)
    subprocess.run(args, check=True, capture_output=True)
    return caminho


def cor_em(caminho: str, segundo: float, recorte: str = "") -> tuple[int, int, int]:
    """Cor média do quadro naquele instante — prova que a cena certa está lá."""
    vf = (recorte + "," if recorte else "") + "scale=1:1"
    proc = subprocess.run(
        [achar_binario("ffmpeg"), "-v", "error", "-ss", str(segundo), "-i", caminho,
         "-frames:v", "1", "-vf", vf, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        capture_output=True, check=True)
    b = proc.stdout[:3]
    return (b[0], b[1], b[2])


@precisa_ffmpeg
class TestSondagem(unittest.TestCase):
    def test_le_duracao_resolucao_e_audio(self):
        with tempfile.TemporaryDirectory() as d:
            caminho = gerar_video(os.path.join(d, "v.mp4"), segundos=3,
                                  largura=640, altura=360, fps=30, com_audio=True)
            m = sondar(caminho)
            self.assertAlmostEqual(m.duracao, 3.0, delta=0.2)
            self.assertEqual((m.largura, m.altura), (640, 360))
            self.assertAlmostEqual(m.fps, 30, delta=0.5)
            self.assertTrue(m.tem_audio)

    def test_detecta_ausencia_de_audio(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertFalse(sondar(gerar_video(os.path.join(d, "v.mp4"))).tem_audio)

    def test_arquivo_inexistente(self):
        with self.assertRaises(ErroFFmpeg):
            sondar("/nao/existe.mp4")


@precisa_ffmpeg
class TestMontagemInsercao(unittest.TestCase):
    def test_cena_entra_na_hora_certa_e_o_resto_fica_intacto(self):
        with tempfile.TemporaryDirectory() as d:
            base = gerar_video(os.path.join(d, "base.mp4"), segundos=20,
                               largura=320, altura=240, com_audio=True)
            verde = ClipeBroll(gerar_video(os.path.join(d, "verde.mp4"), "green", 5), 5.0,
                               credito="Verde por Fulano")
            saida = os.path.join(d, "out.mp4")
            plano = planejar_insercoes(20, [verde], intervalo=6, duracao=2)
            resultado = montar_insercao(base, plano, saida, preset="ultrafast", crf=30)

            self.assertEqual(len(plano), 2)          # 6s e 14s
            self.assertTrue(os.path.isfile(saida))

            # dentro da janela: verde puro
            for ins in plano:
                r, g, b = cor_em(saida, ins.inicio + 1)
                self.assertGreater(g, 100, f"t={ins.inicio + 1}")
                self.assertLess(r, 60)
                self.assertLess(b, 60)
            # fora da janela: barras do testsrc, nunca verde puro
            for t in (3, 10, 18):
                r, g, b = cor_em(saida, t)
                self.assertFalse(g > 100 and r < 60 and b < 60, f"t={t} virou verde")

            self.assertEqual(len(resultado.clipes_usados), 1)

    def test_duracao_e_audio_preservados(self):
        with tempfile.TemporaryDirectory() as d:
            base = gerar_video(os.path.join(d, "base.mp4"), segundos=20, com_audio=True)
            clipe = ClipeBroll(gerar_video(os.path.join(d, "b.mp4"), "red", 5), 5.0)
            saida = os.path.join(d, "out.mp4")
            montar_insercao(base, planejar_insercoes(20, [clipe], intervalo=6, duracao=2),
                            saida, preset="ultrafast", crf=30)
            final = sondar(saida)
            self.assertAlmostEqual(final.duracao, 20.0, delta=0.3)
            self.assertTrue(final.tem_audio)

    def test_base_sem_audio_nao_quebra(self):
        with tempfile.TemporaryDirectory() as d:
            base = gerar_video(os.path.join(d, "base.mp4"), segundos=20, com_audio=False)
            clipe = ClipeBroll(gerar_video(os.path.join(d, "b.mp4"), "red", 5), 5.0)
            saida = os.path.join(d, "out.mp4")
            montar_insercao(base, planejar_insercoes(20, [clipe], intervalo=6, duracao=2),
                            saida, preset="ultrafast", crf=30)
            self.assertFalse(sondar(saida).tem_audio)

    def test_resolucao_forcada(self):
        with tempfile.TemporaryDirectory() as d:
            base = gerar_video(os.path.join(d, "base.mp4"), segundos=12, largura=640, altura=360)
            clipe = ClipeBroll(gerar_video(os.path.join(d, "b.mp4"), "red", 5), 5.0)
            saida = os.path.join(d, "out.mp4")
            montar_insercao(base, planejar_insercoes(12, [clipe], intervalo=4, duracao=2),
                            saida, largura=270, altura=480, preset="ultrafast", crf=30)
            final = sondar(saida)
            self.assertEqual((final.largura, final.altura), (270, 480))

    def test_plano_vazio_da_erro_claro(self):
        with tempfile.TemporaryDirectory() as d:
            base = gerar_video(os.path.join(d, "base.mp4"), segundos=5)
            with self.assertRaises(ErroFFmpeg):
                montar_insercao(base, [], os.path.join(d, "out.mp4"))


@precisa_ffmpeg
class TestMontagemSplit(unittest.TestCase):
    def test_empilha_base_em_cima_e_broll_embaixo(self):
        with tempfile.TemporaryDirectory() as d:
            base = gerar_video(os.path.join(d, "base.mp4"), segundos=12,
                               largura=320, altura=240, com_audio=True)
            azul = ClipeBroll(gerar_video(os.path.join(d, "azul.mp4"), "blue", 3), 3.0)
            saida = os.path.join(d, "out.mp4")
            montar_split(base, [azul], saida, largura=180, altura=320,
                         fps=15, preset="ultrafast", crf=30)

            final = sondar(saida)
            self.assertEqual((final.largura, final.altura), (180, 320))
            self.assertAlmostEqual(final.duracao, 12.0, delta=0.4)
            self.assertTrue(final.tem_audio)

            # t=10s > 3s do clipe: só aparece azul embaixo se o loop funcionou
            r, g, b = cor_em(saida, 10, recorte="crop=180:160:0:160")
            self.assertGreater(b, 150)
            self.assertLess(r, 60)

    def test_limpa_o_arquivo_temporario(self):
        with tempfile.TemporaryDirectory() as d:
            base = gerar_video(os.path.join(d, "base.mp4"), segundos=6)
            clipe = ClipeBroll(gerar_video(os.path.join(d, "b.mp4"), "blue", 3), 3.0)
            montar_split(base, [clipe], os.path.join(d, "out.mp4"), largura=180, altura=320,
                         fps=15, preset="ultrafast", crf=30)
            self.assertEqual([f for f in os.listdir(d) if "faixa-broll" in f], [])

    def test_varios_clipes_entram_na_faixa(self):
        with tempfile.TemporaryDirectory() as d:
            base = gerar_video(os.path.join(d, "base.mp4"), segundos=8)
            lista = [ClipeBroll(gerar_video(os.path.join(d, "b1.mp4"), "blue", 2), 2.0),
                     ClipeBroll(gerar_video(os.path.join(d, "b2.mp4"), "red", 2), 2.0)]
            saida = os.path.join(d, "out.mp4")
            resultado = montar_split(base, lista, saida, largura=180, altura=320,
                                     fps=15, preset="ultrafast", crf=30)
            self.assertEqual(len(resultado.clipes_usados), 2)
            # primeiro clipe (azul) no começo, segundo (vermelho) logo depois
            self.assertGreater(cor_em(saida, 1, "crop=180:160:0:160")[2], 150)
            self.assertGreater(cor_em(saida, 3, "crop=180:160:0:160")[0], 150)

    def test_sem_clipes_da_erro_claro(self):
        with tempfile.TemporaryDirectory() as d:
            base = gerar_video(os.path.join(d, "base.mp4"), segundos=5)
            with self.assertRaises(ErroFFmpeg):
                montar_split(base, [], os.path.join(d, "out.mp4"))


if __name__ == "__main__":
    unittest.main()
