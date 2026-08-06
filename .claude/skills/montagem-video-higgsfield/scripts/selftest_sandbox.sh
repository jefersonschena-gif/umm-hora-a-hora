# selftest_sandbox.sh — autoteste do QC no sandbox, sem gastar credito de geracao.
# Monta um video sintetico (3 blocos x 5 cortes), tomadas de voz, sidecar, manifesto
# e .srt, e roda o qc_video.py em cima. Uso, em UM comando so':
#   python3 push_scripts.py --pacote qc --append "$(cat scripts/selftest_sandbox.sh)"
set -e
mkdir -p work/blocks work/voices work/output
for b in 1 2 3; do
: > /tmp/l$b.txt
for c in 1 2 3 4 5; do
ffmpeg -y -v error -f lavfi -i "testsrc2=s=1920x1080:r=30:d=2" -vf "hue=h=$((b*60+c*47))" -c:v libx264 -preset ultrafast -crf 26 -pix_fmt yuv420p /tmp/s$b$c.mp4
echo "file '/tmp/s$b$c.mp4'" >> /tmp/l$b.txt
done
ffmpeg -y -v error -f concat -safe 0 -i /tmp/l$b.txt -c copy work/blocks/block0$b.mp4
ffmpeg -y -v error -f lavfi -i "sine=f=180:d=9" -af "volume=0.6,adelay=500|500,apad=pad_dur=0.5" -t 10 work/voices/voice0$b.wav
done
printf "file 'work/blocks/block01.mp4'\nfile 'work/blocks/block02.mp4'\nfile 'work/blocks/block03.mp4'\n" > /tmp/all.txt
ffmpeg -y -v error -f concat -safe 0 -i /tmp/all.txt -c copy /tmp/v.mp4
ffmpeg -y -v error -i work/voices/voice01.wav -i work/voices/voice02.wav -i work/voices/voice03.wav -filter_complex "[0:a][1:a][2:a]concat=n=3:v=0:a=1[a]" -map "[a]" /tmp/a.wav
ffmpeg -y -v error -i /tmp/v.mp4 -i /tmp/a.wav -af loudnorm=I=-16:TP=-1.5:LRA=11 -c:v copy -c:a aac -b:a 192k -shortest work/output/final.mp4
python3 - <<'PY'
import json
pb=[{"n":i+1,"clip":f"block0{i+1}.mp4","voice":f"voice0{i+1}.wav","voice_norm":f"voice0{i+1}.wav","clip_s":10.0,"speech_s":9.0,"speech_abs_s":i*10+0.5,"lead_silence_s":0.5,"internal_pauses":0} for i in range(3)]
json.dump({"script":"assemble_final.sh","out":"final.mp4","blocks":3,"clip_seconds":10,"width":1920,"height":1080,"fps":"30/1","per_block":pb},open("work/output/final.mp4.assembly.json","w"))
linhas=[("Existe um relogio parado no centro da cidade","e ninguem lembra quem cuidava dele"),("A familia responsavel manteve os ponteiros girando","por tres geracoes seguidas sem falhar"),("Uma adolescente subiu duzentos degraus","e a cidade voltou a marcar o proprio tempo")]
json.dump({"blocks":[{"n":i+1,"vo_line":a+", "+b,"visual_proposition":["relogio parado na torre","oficina com engrenagens antigas","menina no alto da torre"][i],"key_visual":["torre","oficina","cume"][i]} for i,(a,b) in enumerate(linhas)]},open("script_manifest.json","w"),ensure_ascii=False)
def ts(t):
    h=int(t//3600); m=int(t%3600//60); s=t-h*3600-m*60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".",",")
cues=[]
for i,(a,b) in enumerate(linhas):
    cues.append((i*10+0.5, i*10+5.0, a))
    cues.append((i*10+5.0, i*10+9.5, b))
with open("work/output/final.srt","w") as f:
    for n,(ini,fim,tx) in enumerate(cues,1):
        f.write(f"{n}\n{ts(ini)} --> {ts(fim)}\n{tx}\n\n")
print("fixtures ok")
PY
ffmpeg -y -v error -ss 3 -i work/output/final.mp4 -frames:v 1 -vf scale=1920:1080 /tmp/bg.jpg
if [ -f qc/thumb_text.sh ]; then
bash qc/thumb_text.sh --in /tmp/bg.jpg --out work/output/thumb.jpg --text 'O RELOGIO\\nPAROU' --pos left --color '#FFE100'
else
cp /tmp/bg.jpg work/output/thumb.jpg
fi
python3 qc/qc_video.py --video work/output/final.mp4 --sidecar work/output/final.mp4.assembly.json --srt work/output/final.srt --script script_manifest.json --voice-dir work/voices --thumb work/output/thumb.jpg --thumb-text 'O RELOGIO PAROU' --aspect 16:9 --sem-whisper --json work/output/qc_report.json
