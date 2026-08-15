"""Testes offline: payloads no formato de cada API passam pelo pipeline inteiro.

Rodar:  python -m unittest discover -s testes -v
"""

from __future__ import annotations

import datetime as dt
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from garimpo import licencas
from garimpo.fontes.archive_org import ArchiveOrg, licenca_da_url
from garimpo.fontes.pexels import Pexels
from garimpo.fontes.pixabay import Pixabay
from garimpo.fontes.youtube_cc import YouTubeCC, iso_para_segundos
from garimpo.modelos import Video, duracao_legivel, numero_curto
from garimpo.relatorio import carregar_json, salvar_csv, salvar_html, salvar_json
from garimpo.scoring import pontuar

ONTEM = (dt.date.today() - dt.timedelta(days=10)).isoformat()


def item_youtube(**over) -> dict:
    base = {
        "id": "dQw4w9WgXcQ",
        "snippet": {
            "publishedAt": f"{ONTEM}T12:00:00Z",
            "channelId": "UC123",
            "channelTitle": "Canal Teste",
            "title": "Aula de surf em Itacaré",
            "thumbnails": {"medium": {"url": "https://i.ytimg.com/vi/x/mq.jpg"}},
            "tags": ["surf", "praia"],
        },
        "statistics": {"viewCount": "480000", "likeCount": "31000", "commentCount": "2200"},
        "contentDetails": {"duration": "PT12M31S", "definition": "hd", "licensedContent": False},
        "status": {"license": "creativeCommon", "embeddable": True},
    }
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            base[k] = {**base[k], **v}
        else:
            base[k] = v
    return base


class TestDuracaoISO(unittest.TestCase):
    def test_formatos(self):
        self.assertEqual(iso_para_segundos("PT12M31S"), 751)
        self.assertEqual(iso_para_segundos("PT1H2M3S"), 3723)
        self.assertEqual(iso_para_segundos("PT45S"), 45)
        self.assertEqual(iso_para_segundos("P1DT2H"), 93600)
        self.assertEqual(iso_para_segundos(""), 0)
        self.assertEqual(iso_para_segundos("lixo"), 0)


class TestYouTube(unittest.TestCase):
    def test_conversao(self):
        v = YouTubeCC()._converter(item_youtube())
        self.assertEqual(v.fonte, "youtube_cc")
        self.assertEqual(v.licenca, "cc-by")
        self.assertEqual(v.views, 480000)
        self.assertEqual(v.duracao_s, 751)
        self.assertEqual(v.autor, "Canal Teste")
        self.assertTrue(v.url.endswith("dQw4w9WgXcQ"))

    def test_licenca_padrao_vira_desconhecida(self):
        v = YouTubeCC()._converter(item_youtube(status={"license": "youtube"}))
        self.assertEqual(v.licenca, "desconhecida")
        licencas.avaliar(v)
        self.assertEqual(v.risco, "ALTO")

    def test_detalhar_descarta_nao_cc(self):
        fonte = YouTubeCC()
        convertidos = [fonte._converter(item_youtube()),
                       fonte._converter(item_youtube(id="outro", status={"license": "youtube"}))]
        sobreviventes = [v for v in convertidos if v.licenca == "cc-by"]
        self.assertEqual(len(sobreviventes), 1)

    def test_licensed_content_eleva_risco(self):
        v = YouTubeCC()._converter(item_youtube(contentDetails={"licensedContent": True}))
        licencas.avaliar(v)
        self.assertEqual(v.risco, "ALTO")
        self.assertTrue(any("licensedContent" in a for a in v.alertas))

    def test_cc_sem_reivindicacao_fica_medio(self):
        v = YouTubeCC()._converter(item_youtube())
        licencas.avaliar(v)
        self.assertEqual(v.risco, "MEDIO")
        self.assertTrue(any("trilha sonora" in a for a in v.alertas))


class TestPexels(unittest.TestCase):
    PAYLOAD = {
        "id": 8765,
        "url": "https://www.pexels.com/video/ondas-8765/",
        "alt": "Ondas quebrando ao amanhecer",
        "duration": 24,
        "width": 1920, "height": 1080,
        "image": "https://images.pexels.com/videos/8765/thumb.jpg",
        "user": {"name": "Fulano", "url": "https://www.pexels.com/@fulano"},
        "video_files": [
            {"quality": "sd", "width": 640, "height": 360, "link": "https://player.vimeo.com/sd.mp4"},
            {"quality": "hd", "width": 1920, "height": 1080, "link": "https://player.vimeo.com/hd.mp4"},
        ],
    }

    def test_escolhe_maior_arquivo(self):
        v = Pexels()._converter(self.PAYLOAD, pos=0, total=10)
        self.assertEqual(v.download_url, "https://player.vimeo.com/hd.mp4")
        self.assertEqual(v.altura, 1080)
        self.assertEqual(v.licenca, "pexels")
        self.assertTrue(v.extra["sem_metricas"])

    def test_sem_metricas_usa_rank(self):
        primeiro = pontuar(Pexels()._converter(self.PAYLOAD, pos=0, total=10))
        ultimo = pontuar(Pexels()._converter(self.PAYLOAD, pos=9, total=10))
        self.assertGreater(primeiro.score, ultimo.score)
        self.assertGreater(primeiro.score, 0)

    def test_risco_baixo_e_alerta_de_imagem(self):
        v = licencas.avaliar(Pexels()._converter(self.PAYLOAD, pos=0, total=10))
        self.assertEqual(v.risco, "BAIXO")
        self.assertTrue(any("identificáveis" in a for a in v.alertas))


class TestPixabay(unittest.TestCase):
    PAYLOAD = {
        "id": 4321, "pageURL": "https://pixabay.com/videos/id-4321/",
        "duration": 18, "views": 90000, "downloads": 12000, "likes": 800, "comments": 40,
        "user": "Beltrano", "user_id": 77, "tags": "praia, mar, verão",
        "videos": {"large": {"url": "https://cdn.pixabay.com/large.mp4",
                             "width": 1920, "height": 1080,
                             "thumbnail": "https://cdn.pixabay.com/thumb.jpg"}},
    }

    def test_conversao(self):
        v = Pixabay()._converter(self.PAYLOAD)
        self.assertEqual(v.views, 90000)
        self.assertEqual(v.tags, ["praia", "mar", "verão"])
        self.assertEqual(v.download_url, "https://cdn.pixabay.com/large.mp4")
        self.assertEqual(v.licenca, "pixabay")

    def test_cai_para_qualidade_menor(self):
        payload = dict(self.PAYLOAD, videos={"small": {"url": "https://cdn/small.mp4",
                                                       "width": 640, "height": 360}})
        self.assertEqual(Pixabay()._converter(payload).download_url, "https://cdn/small.mp4")


class TestArchive(unittest.TestCase):
    def test_mapeamento_de_licenca(self):
        casos = {
            "https://creativecommons.org/licenses/by/4.0/": "cc-by",
            "https://creativecommons.org/licenses/by-sa/3.0/": "cc-by-sa",
            "https://creativecommons.org/licenses/by-nc-sa/4.0/": "cc-nc",
            "https://creativecommons.org/licenses/by-nd/4.0/": "cc-nd",
            "https://creativecommons.org/publicdomain/zero/1.0/": "cc0",
            "https://creativecommons.org/publicdomain/mark/1.0/": "dominio-publico",
            "": "desconhecida",
        }
        for url, esperado in casos.items():
            self.assertEqual(licenca_da_url(url), esperado, url)

    def test_conversao_e_creator_em_lista(self):
        doc = {"identifier": "surf_1962", "title": "Surfing 1962",
               "creator": ["Prelinger", "Arquivo"], "downloads": 52000,
               "licenseurl": "https://creativecommons.org/publicdomain/mark/1.0/",
               "publicdate": "2011-03-04T00:00:00Z", "subject": "surf"}
        v = ArchiveOrg()._converter(doc)
        self.assertEqual(v.autor, "Prelinger, Arquivo")
        self.assertEqual(v.licenca, "dominio-publico")
        self.assertEqual(v.views, 52000)
        self.assertEqual(v.publicado, dt.date(2011, 3, 4))
        licencas.avaliar(v)
        self.assertEqual(v.risco, "BAIXO")


class TestScoring(unittest.TestCase):
    def _video(self, **kw):
        base = dict(fonte="youtube_cc", id="x", titulo="t", url="u", licenca="cc-by",
                    views=100000, likes=5000, comentarios=200, duracao_s=300,
                    publicado=dt.date.today() - dt.timedelta(days=10))
        base.update(kw)
        return pontuar(Video(**base))

    def test_viral_ganha_de_video_velho(self):
        novo = self._video(publicado=dt.date.today() - dt.timedelta(days=2))
        velho = self._video(publicado=dt.date.today() - dt.timedelta(days=400))
        self.assertGreater(novo.score, velho.score)
        self.assertGreater(novo.velocidade_dia, velho.velocidade_dia)

    def test_engajamento_pesa(self):
        alto = self._video(likes=9000, comentarios=1000)
        baixo = self._video(likes=10, comentarios=0)
        self.assertGreater(alto.score, baixo.score)

    def test_duracao_ideal_ganha_de_novela(self):
        ideal = self._video(duracao_s=8 * 60)
        novela = self._video(duracao_s=3 * 3600)
        self.assertGreater(ideal.score, novela.score)

    def test_vertical_recebe_bonus(self):
        vertical = self._video(largura=1080, altura=1920)
        horizontal = self._video(largura=1920, altura=1080)
        self.assertGreater(vertical.score, horizontal.score)

    def test_score_dentro_da_faixa(self):
        for v in (self._video(views=0, likes=0, comentarios=0),
                  self._video(views=10**9, likes=10**8, comentarios=10**7)):
            self.assertGreaterEqual(v.score, 0)
            self.assertLessEqual(v.score, 100)

    def test_sem_data_nao_quebra(self):
        v = self._video(publicado=None)
        self.assertGreater(v.score, 0)


class TestLicencas(unittest.TestCase):
    def _v(self, lic):
        return licencas.avaliar(Video(fonte="archive", id="i", titulo="T", url="U",
                                      licenca=lic, autor="A"))

    def test_nd_e_nc_sao_alto_risco(self):
        self.assertEqual(self._v("cc-nd").risco, "ALTO")
        self.assertEqual(self._v("cc-nc").risco, "ALTO")
        self.assertEqual(self._v("desconhecida").risco, "ALTO")

    def test_dominio_publico_e_baixo(self):
        self.assertEqual(self._v("dominio-publico").risco, "BAIXO")
        self.assertEqual(self._v("cc0").risco, "BAIXO")

    def test_credito_cita_licenca_e_fonte(self):
        v = self._v("cc-by")
        texto = licencas.texto_credito(v, editor="Meu Canal")
        self.assertIn("A", texto)
        self.assertIn("Creative Commons", texto)
        self.assertIn("U", texto)
        self.assertIn("Meu Canal", texto)

    def test_credito_sem_exigencia_ainda_cita_origem(self):
        texto = licencas.texto_credito(self._v("cc0"))
        self.assertIn("U", texto)


class TestRelatorio(unittest.TestCase):
    def setUp(self):
        self.videos = [licencas.avaliar(pontuar(YouTubeCC()._converter(item_youtube()))),
                       licencas.avaliar(pontuar(Pixabay()._converter(TestPixabay.PAYLOAD)))]
        self.dir = tempfile.mkdtemp()

    def test_json_ida_e_volta(self):
        caminho = salvar_json(self.videos, os.path.join(self.dir, "r.json"))
        de_volta = carregar_json(caminho)
        self.assertEqual(len(de_volta), 2)
        self.assertEqual(de_volta[0].id, self.videos[0].id)
        self.assertEqual(de_volta[0].publicado, self.videos[0].publicado)
        self.assertEqual(de_volta[0].score, self.videos[0].score)
        self.assertEqual(de_volta[0].risco, self.videos[0].risco)

    def test_csv_tem_cabecalho_e_linhas(self):
        caminho = salvar_csv(self.videos, os.path.join(self.dir, "r.csv"))
        with open(caminho, encoding="utf-8-sig") as f:
            linhas = f.read().strip().splitlines()
        self.assertEqual(len(linhas), 3)
        self.assertIn("credito", linhas[0])

    def test_html_embute_dados_validos(self):
        caminho = salvar_html(self.videos, os.path.join(self.dir, "r.html"), tema="surf")
        with open(caminho, encoding="utf-8") as f:
            html = f.read()
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("Aula de surf em Itacaré", html)
        bruto = html.split("const dados = ", 1)[1].split(";\n", 1)[0]
        dados = json.loads(bruto)
        self.assertEqual(len(dados), 2)
        self.assertIn("licenca_nome", dados[0])


class TestFormatacao(unittest.TestCase):
    def test_numero_curto(self):
        self.assertEqual(numero_curto(999), "999")
        self.assertEqual(numero_curto(1500), "1.5k")
        self.assertEqual(numero_curto(2_000_000), "2M")

    def test_duracao_legivel(self):
        self.assertEqual(duracao_legivel(0), "—")
        self.assertEqual(duracao_legivel(75), "1:15")
        self.assertEqual(duracao_legivel(3725), "1:02:05")


if __name__ == "__main__":
    unittest.main()
