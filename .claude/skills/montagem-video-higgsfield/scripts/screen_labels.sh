#!/usr/bin/env bash
# screen_labels.sh — aplica o ROTULO DE TELA de um bloco sobre o clipe dele.
#
# Existe por causa da leitura MUDA: metafora visual carrega clima e arco, mas
# nao carrega fato. Quem assiste sem som precisa ler "CARENCIA MINIMA: 6 MESES"
# em algum lugar — e esse texto NAO pode sair do modelo de imagem, que erra
# letra e acento. Entao ele e' composto aqui, com fonte propria, igual ao texto
# da thumbnail.
#
# NAO E' LEGENDA e nao substitui legenda:
#   - roda sobre o CLIPE do bloco, ANTES da montagem — o montador e o passo de
#     legenda continuam intocados (nunca rode isto no final.mp4);
#   - fica no TERCO SUPERIOR; a legenda vive nos 12% de baixo. Nunca colidem;
#   - o texto e' renderizado como PNG pelo ImageMagick e sobreposto com
#     `overlay`. Nenhum filtro drawtext/subtitles/ass e' usado aqui.
#
#   bash screen_labels.sh --in work/blocks/block08.mp4 \
#        --out work/blocks/block08_lab.mp4 --text 'CARÊNCIA MÍNIMA: 6 MESES'
#
# Grava <out>.label.json com a caixa e a cor — e' o que o qc_video.py le para
# medir contraste e legibilidade do rotulo.
set -euo pipefail

IN=""; OUT=""; TEXT=""; COLOR="#FFFFFF"; STROKE="#000000"; POS="topo"
FONT="/usr/share/fonts/truetype/higgsfield/Montserrat-ExtraBold.ttf"
FADE="0.35"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --in) IN="$2"; shift 2 ;;
    --out) OUT="$2"; shift 2 ;;
    --text) TEXT="$2"; shift 2 ;;
    --color) COLOR="$2"; shift 2 ;;
    --stroke) STROKE="$2"; shift 2 ;;
    --pos) POS="$2"; shift 2 ;;          # topo | meio
    --font-file) FONT="$2"; shift 2 ;;
    --fade) FADE="$2"; shift 2 ;;
    -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "flag desconhecida: $1" >&2; exit 2 ;;
  esac
done
[[ -f "$IN" ]] || { echo "ERRO: --in nao encontrado: $IN" >&2; exit 1; }
[[ -n "$OUT" && -n "$TEXT" ]] || { echo "ERRO: --out e --text sao obrigatorios" >&2; exit 1; }
[[ -f "$FONT" ]] || { echo "ERRO: fonte nao encontrada: $FONT" >&2; exit 1; }
case "$OUT" in
  *final.mp4|*final_*.mp4)
    echo "ERRO: rotulo NAO se aplica ao arquivo final — rode sobre o clipe do bloco." >&2
    exit 1 ;;
esac

PALAVRAS=$(printf '%s' "$TEXT" | wc -w)
if [[ "$PALAVRAS" -gt 6 ]]; then
  echo "ERRO: $PALAVRAS palavras no rotulo (maximo 6 — rotulo e' leitura de relance)" >&2
  exit 1
fi

W=$(ffprobe -v error -select_streams v:0 -show_entries stream=width -of csv=p=0 "$IN")
H=$(ffprobe -v error -select_streams v:0 -show_entries stream=height -of csv=p=0 "$IN")
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
printf '%s' "$TEXT" > "$TMP/t.txt"

# caixa do rotulo: largura util de 84%, altura de 11% do quadro
BW=$(( W * 84 / 100 )); BH=$(( H * 11 / 100 ))
convert -background none -fill "$COLOR" -font "$FONT" -size "${BW}x${BH}" \
        -gravity center "label:@$TMP/t.txt" -trim +repage "$TMP/fill.png"
convert -background none -fill none -stroke "$STROKE" -strokewidth 10 \
        -font "$FONT" -size "${BW}x${BH}" -gravity center "label:@$TMP/t.txt" \
        -trim +repage "$TMP/stroke.png"
TW=$(identify -format '%w' "$TMP/fill.png"); TH=$(identify -format '%h' "$TMP/fill.png")
convert "$TMP/stroke.png" "$TMP/fill.png" -gravity center -composite \
        \( +clone -background black -shadow 85x8+0+6 \) +swap \
        -background none -layers merge +repage "$TMP/lab.png"

X=$(( (W - TW) / 2 ))
if [[ "$POS" == "meio" ]]; then Y=$(( (H - TH) / 2 )); else Y=$(( H * 9 / 100 )); fi

# overlay puro + fade de entrada. Sem drawtext, sem subtitles, sem ass.
ffmpeg -y -loglevel error -i "$IN" -i "$TMP/lab.png" \
  -filter_complex "[1:v]format=rgba,fade=t=in:st=0:d=${FADE}:alpha=1[l];[0:v][l]overlay=${X}:${Y}:format=auto[v]" \
  -map "[v]" -map 0:a? -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -c:a copy "$OUT"

RGB=$(printf '%d,%d,%d' "0x${COLOR:1:2}" "0x${COLOR:3:2}" "0x${COLOR:5:2}" 2>/dev/null || echo "255,255,255")
cat > "${OUT%.*}.label.json" <<JSON
{"box":[$X,$Y,$((X+TW)),$((Y+TH))],
 "rgb":[${RGB%%,*},$(echo "$RGB"|cut -d, -f2),${RGB##*,}],
 "cor":"$COLOR","fonte":"$(basename "$FONT")","pos":"$POS",
 "texto":$(python3 -c 'import json,sys;print(json.dumps(open(sys.argv[1]).read().strip()))' "$TMP/t.txt"),
 "quadro":[$W,$H],"altura_texto_pct":$(awk -v t="$TH" -v h="$H" 'BEGIN{printf "%.3f", t/h}'),
 "composto":true}
JSON

echo "ROTULO: $OUT  (${TW}x${TH} em +${X}+${Y}, ${PALAVRAS} palavra(s))" >&2
