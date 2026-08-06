#!/usr/bin/env bash
# thumb_text.sh — aplica o texto da thumbnail POR COMPOSICAO (ImageMagick),
# nunca deixando o modelo de imagem "escrever". Texto gerado por modelo erra
# acento e letra; texto composto aqui e' sempre exato.
#
# Roda no sandbox do Higgsfield (convert + fontes Montserrat/Metropolis).
#
#   bash thumb_text.sh --in fundo.jpg --out thumb.jpg \
#        --text "ELE VOLTOU\nDEPOIS DE 40 ANOS" --pos right --color '#FFE100'
#
# Grava tambem <out>.textbox.json (caixa do texto + cor) — e' o que o
# qc_video.py usa para medir contraste WCAG e legibilidade a 168 px.
set -euo pipefail

IN=""; OUT=""; TEXT=""; POS="left"; COLOR="#FFE100"; STROKE="#000000"
FONT="/usr/share/fonts/truetype/higgsfield/Montserrat-ExtraBold.ttf"
SAFE="0.055"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --in) IN="$2"; shift 2 ;;
    --out) OUT="$2"; shift 2 ;;
    --text) TEXT="$2"; shift 2 ;;
    --pos) POS="$2"; shift 2 ;;              # left | right | top | bottom
    --color) COLOR="$2"; shift 2 ;;
    --stroke) STROKE="$2"; shift 2 ;;
    --font-file) FONT="$2"; shift 2 ;;
    --safe) SAFE="$2"; shift 2 ;;
    -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "flag desconhecida: $1" >&2; exit 2 ;;
  esac
done
[[ -f "$IN" ]] || { echo "ERRO: --in nao encontrado: $IN" >&2; exit 1; }
[[ -n "$OUT" && -n "$TEXT" ]] || { echo "ERRO: --out e --text sao obrigatorios" >&2; exit 1; }
[[ -f "$FONT" ]] || { echo "ERRO: fonte nao encontrada: $FONT" >&2; exit 1; }

PALAVRAS=$(printf '%s' "$TEXT" | tr '\\n' ' ' | wc -w)
if [[ "$PALAVRAS" -gt 5 ]]; then
  echo "ERRO: $PALAVRAS palavras na thumbnail (maximo 5 — a miniatura e' lida em 0,3s)" >&2
  exit 1
fi

W=$(identify -format '%w' "$IN"); H=$(identify -format '%h' "$IN")
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
printf '%b' "$TEXT" > "$TMP/t.txt"     # interpreta \n como quebra real

case "$POS" in
  left|right) BW=$(( W * 44 / 100 )); BH=$(( H * 36 / 100 )) ;;
  top|bottom) BW=$(( W * 86 / 100 )); BH=$(( H * 26 / 100 )) ;;
  *) echo "ERRO: --pos deve ser left|right|top|bottom" >&2; exit 2 ;;
esac

# 1) camada de texto ajustada a caixa (o label: escolhe o corpo sozinho)
convert -background none -fill "$COLOR" -font "$FONT" -size "${BW}x${BH}" \
        -gravity center "label:@$TMP/t.txt" -trim +repage "$TMP/fill.png"
convert -background none -fill none -stroke "$STROKE" -strokewidth 14 \
        -font "$FONT" -size "${BW}x${BH}" -gravity center "label:@$TMP/t.txt" \
        -trim +repage "$TMP/stroke.png"

TW=$(identify -format '%w' "$TMP/fill.png"); TH=$(identify -format '%h' "$TMP/fill.png")

# 2) contorno + sombra projetada, para o texto sobreviver a qualquer fundo
convert "$TMP/stroke.png" "$TMP/fill.png" -gravity center -composite "$TMP/txt.png"
convert "$TMP/txt.png" \( +clone -background black -shadow 90x10+0+10 \) \
        +swap -background none -layers merge +repage "$TMP/txt_sh.png"

# 3) posicao respeitando margem de seguranca
MX=$(awk -v w="$W" -v s="$SAFE" 'BEGIN{printf "%d", w*s}')
MY=$(awk -v h="$H" -v s="$SAFE" 'BEGIN{printf "%d", h*s}')
case "$POS" in
  left)   X=$MX;                       Y=$(( (H - TH) / 2 )) ;;
  right)  X=$(( W - TW - MX ));        Y=$(( (H - TH) / 2 )) ;;
  top)    X=$(( (W - TW) / 2 ));       Y=$MY ;;
  bottom) X=$(( (W - TW) / 2 ));       Y=$(( H - TH - MY )) ;;
esac

convert "$IN" "$TMP/txt_sh.png" -geometry "+${X}+${Y}" -composite -quality 92 "$OUT"

RGB=$(printf '%d,%d,%d' "0x${COLOR:1:2}" "0x${COLOR:3:2}" "0x${COLOR:5:2}" 2>/dev/null \
      || echo "255,255,255")
cat > "${OUT%.*}.textbox.json" <<JSON
{"box":[$X,$Y,$((X+TW)),$((Y+TH))],
 "rgb":[${RGB%%,*},$(echo "$RGB"|cut -d, -f2),${RGB##*,}],
 "cor":"$COLOR","fonte":"$(basename "$FONT")","pos":"$POS",
 "texto":$(python3 -c 'import json,sys;print(json.dumps(open(sys.argv[1]).read().strip()))' "$TMP/t.txt"),
 "imagem":[$W,$H],"altura_texto_pct":$(awk -v t="$TH" -v h="$H" 'BEGIN{printf "%.3f", t/h}')}
JSON

echo "THUMB: $OUT  (${W}x${H}, texto ${TW}x${TH} em +${X}+${Y}, ${PALAVRAS} palavra(s))" >&2
echo "TEXTBOX: ${OUT%.*}.textbox.json" >&2
