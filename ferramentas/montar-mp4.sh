#!/bin/sh
# montar-mp4.sh — converte o que sai do UMM Studio em MP4 pronto para postar.
# Só usa ffmpeg, que é livre e gratuito (https://ffmpeg.org).
#
#   ./ferramentas/montar-mp4.sh video.webm                  # converte para MP4
#   ./ferramentas/montar-mp4.sh video.webm narracao.wav     # converte e cola o áudio
#   ./ferramentas/montar-mp4.sh pasta-de-quadros/           # monta a partir dos PNGs
#
# O resultado sai em H.264 + AAC, yuv420p, que é o que Instagram, TikTok,
# YouTube e WhatsApp aceitam sem reprocessar demais.

set -e

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ffmpeg não encontrado."
  echo "  Ubuntu/Debian: sudo apt install ffmpeg"
  echo "  macOS:         brew install ffmpeg"
  echo "  Windows:       winget install Gyan.FFmpeg"
  exit 1
fi

ENTRADA="$1"
AUDIO="$2"
SAIDA="${SAIDA:-video.mp4}"
FPS="${FPS:-30}"

if [ -z "$ENTRADA" ]; then
  echo "Uso: $0 <video.webm | pasta-de-quadros> [narracao.wav]"
  exit 1
fi

if [ -d "$ENTRADA" ]; then
  # Sequência de quadros exportada pelo Studio.
  QUADROS="$ENTRADA/quadro_%05d.png"
  [ -z "$AUDIO" ] && [ -f "$ENTRADA/narracao.wav" ] && AUDIO="$ENTRADA/narracao.wav"
  if [ -n "$AUDIO" ]; then
    ffmpeg -y -framerate "$FPS" -i "$QUADROS" -i "$AUDIO" \
      -c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p \
      -c:a aac -b:a 192k -shortest -movflags +faststart "$SAIDA"
  else
    ffmpeg -y -framerate "$FPS" -i "$QUADROS" \
      -c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p -movflags +faststart "$SAIDA"
  fi
else
  # Arquivo de vídeo (webm do "Exportar exato" ou do "Gravar").
  if [ -n "$AUDIO" ]; then
    ffmpeg -y -i "$ENTRADA" -i "$AUDIO" -map 0:v:0 -map 1:a:0 \
      -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p \
      -c:a aac -b:a 192k -shortest -movflags +faststart "$SAIDA"
  else
    ffmpeg -y -i "$ENTRADA" \
      -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p \
      -c:a aac -b:a 192k -movflags +faststart "$SAIDA"
  fi
fi

echo ""
echo "Pronto: $SAIDA"
echo "Para gravar a legenda .srt dentro da imagem (útil onde a plataforma não legenda):"
echo "  ffmpeg -i $SAIDA -vf \"subtitles=legendas.srt:force_style='FontSize=16'\" -c:a copy com-legenda.mp4"
