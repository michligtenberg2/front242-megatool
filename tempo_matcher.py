import os
import argparse
import librosa
import soundfile as sf
import numpy as np

def match_tempo(input_path, output_path, target_bpm, beats_per_bar=4):
    y, sr = librosa.load(input_path, sr=None)
    orig_bpm, _ = librosa.beat.beat_track(y, sr=sr)
    rate = orig_bpm / target_bpm
    y_stretched = librosa.effects.time_stretch(y, rate)
    spb = sr * 60 / target_bpm
    spbar = int(spb * beats_per_bar)
    total = len(y_stretched)
    bars = max(1, round(total / spbar))
    target_len = bars * spbar
    if total > target_len:
        aligned = y_stretched[:target_len]
    else:
        aligned = np.pad(y_stretched, (0, target_len-total))
    sf.write(output_path, aligned, sr)
    print(f"{os.path.basename(input_path)}: {orig_bpm:.1f}→{target_bpm} BPM, {bars} bars")

def batch_process_root(root_in, root_out, bpm, bars):
    os.makedirs(root_out, exist_ok=True)
    for sub in os.listdir(root_in):
        in_sub = os.path.join(root_in, sub)
        if not os.path.isdir(in_sub): continue
        out_sub = os.path.join(root_out, sub)
        os.makedirs(out_sub, exist_ok=True)
        for f in os.listdir(in_sub):
            if f.lower().endswith(('.wav','.mp3','.flac')):
                inp = os.path.join(in_sub, f)
                out = os.path.join(out_sub, f"{os.path.splitext(f)[0]}_{bpm}bpm.wav")
                match_tempo(inp, out, bpm, bars)

if __name__=='__main__':
    p = argparse.ArgumentParser()
    p.add_argument('-i','--root-input', required=True)
    p.add_argument('-o','--root-output', required=True)
    p.add_argument('-b','--bpm', type=float, required=True)
    p.add_argument('-p','--beats-per-bar', type=int, default=4)
    args = p.parse_args()
    batch_process_root(args.root_input, args.root_output, args.bpm, args.beats_per_bar)
