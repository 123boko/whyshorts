#!/usr/bin/env python3
"""Mix voice over + sound effects + ambience beds onto a rendered video.

usage: mix_audio.py <video.mp4> <scene-dir> <out.mp4>
The scene dir holds audio/<vo>.mp3, audio/*_vo_timing.json, audio/sfx/*.mp3 and sfx_cues.py,
which defines cues(w, wend, B) -> (events, beds):
  events: [(sfx_name, time_s, gain_db), ...]
  beds:   [(sfx_name_or_'wind', start_s, end_s, gain_db), ...]
"""
import glob, json, os, re, runpy, subprocess, sys

video, scene, out = sys.argv[1:4]
timing = json.load(open(glob.glob(os.path.join(scene, 'audio', '*_vo_timing.json'))[0]))
words = timing['words']
norm = lambda s: re.sub(r"[^a-z0-9'-]", '', s.lower())


def _find(word, n, key):
    k = 0
    for x in words:
        if norm(x['text']) == norm(word):
            k += 1
            if k == n:
                return x[key]
    raise KeyError(f'{word} #{n}')


w = lambda word, n=1: _find(word, n, 'start')
wend = lambda word, n=1: _find(word, n, 'end')
B = lambda n: timing['beats'][n - 1]['start']
events, beds = runpy.run_path(os.path.join(scene, 'sfx_cues.py'))['cues'](w, wend, B)

dur = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', video]))
sfx = os.path.join(scene, 'audio', 'sfx')
inputs = ['-i', video, '-i', os.path.join(scene, 'audio', timing['audio'])]
parts, labels = [], []
idx = 2  # next input index
lab = 0
for name, t, db in events:
    inputs += ['-i', os.path.join(sfx, name + '.mp3')]
    # peak-normalise each effect, then set its level and drop it at its time
    parts.append(f'[{idx}:a]aformat=sample_rates=48000:channel_layouts=stereo,dynaudnorm=f=150:g=3,volume={db}dB,adelay={int(t * 1000)}:all=1[e{lab}]')
    labels.append(f'[e{lab}]'); idx += 1; lab += 1
for name, t0, t1, db in beds:
    length = t1 - t0
    if name == 'wind':  # synthetic wind: filtered brown noise with slow gusts, seamless for any length
        src = f'anoisesrc=color=brown:amplitude=0.6:duration={length:.2f}:sample_rate=48000,lowpass=f=900,highpass=f=60,tremolo=f=0.18:d=0.6,aformat=channel_layouts=stereo'
        parts.append(f'{src},volume={db}dB,afade=t=in:d=0.8,afade=t=out:st={max(length - 0.8, 0):.2f}:d=0.8,adelay={int(t0 * 1000)}:all=1[e{lab}]')
    else:
        inputs += ['-stream_loop', '-1', '-i', os.path.join(sfx, name + '.mp3')]
        parts.append(f'[{idx}:a]aformat=sample_rates=48000:channel_layouts=stereo,dynaudnorm=f=150:g=3,atrim=0:{length:.2f},volume={db}dB,afade=t=in:d=0.6,afade=t=out:st={max(length - 0.6, 0):.2f}:d=0.6,adelay={int(t0 * 1000)}:all=1[e{lab}]')
        idx += 1
    labels.append(f'[e{lab}]'); lab += 1
parts.append('[1:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=3dB,asplit=2[vo][vosc]')
fx_mix = ''.join(labels) + f'amix=inputs={len(labels)}:normalize=0:duration=longest[fx]'
parts.append(fx_mix)
# duck effects under the voice, then sum and limit
parts.append('[fx][vosc]sidechaincompress=threshold=0.12:ratio=2:attack=15:release=250[fxd]')
parts.append(f'[vo][fxd]amix=inputs=2:normalize=0:duration=first,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,atrim=0:{dur:.3f}[mix]')
tmp = out.replace('.mp4', '.part.mp4')
cmd = ['ffmpeg', '-v', 'error', '-y', *inputs, '-filter_complex', ';'.join(parts), '-map', '0:v', '-map', '[mix]',
       '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', tmp]
subprocess.run(cmd, check=True)
os.replace(tmp, out)
print('mixed', len(events), 'effects and', len(beds), 'beds ->', out)
