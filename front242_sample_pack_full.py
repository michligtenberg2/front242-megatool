#!/usr/bin/env python3

import os
import subprocess
import threading
import PySimpleGUI as sg
from yt_dlp import YoutubeDL
import librosa
import soundfile as sf

# --- Configuratie ---
DEMUX_MODEL = 'mdx_extra'
DOWNLOAD_DIR = 'tracks'
SEPARATED_DIR = 'separated'
SAMPLES_DIR = 'samples'

# Zorg dat mappen bestaan
for d in (DOWNLOAD_DIR, SEPARATED_DIR, SAMPLES_DIR):
    os.makedirs(d, exist_ok=True)
    for stem in ('drums','bass','other'):
        os.makedirs(os.path.join(SAMPLES_DIR, stem), exist_ok=True)

# --- Helper functies ---

def get_playlist_urls(playlist_url, window=None):
    ydl_opts = {'extract_flat': True, 'skip_download': True, 'quiet': True}
    if window: window.write_event_value('-STATUS-', f"Fetching {playlist_url}")
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(playlist_url, download=False)
    urls = [f"https://www.youtube.com/watch?v={e['id']}"
            for e in info.get('entries',[]) or []]
    if window: window.write_event_value('-LOG-', f"Found {len(urls)} links")
    return urls

def download_urls(urls, window):
    ydl_opts = {
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
        'format': 'bestaudio', 'quiet': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192'
        }]
    }
    total = len(urls)
    for i,url in enumerate(urls,1):
        if window:
            window.write_event_value('-STATUS-', f"Downloading {i}/{total}")
            window.write_event_value('-LOG-', url)
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        if window: window.write_event_value('-PROGRESS-', (i, total))

def separate_all(window):
    tracks = [f for f in os.listdir(DOWNLOAD_DIR) if f.endswith('.mp3')]
    total = len(tracks)
    for i,track in enumerate(tracks,1):
        path = os.path.join(DOWNLOAD_DIR, track)
        if window:
            window.write_event_value('-STATUS-', f"Separating {i}/{total}")
            window.write_event_value('-LOG-', track)
        subprocess.run(['demucs','-n',DEMUX_MODEL,'--out',SEPARATED_DIR, path], check=True)
        if window: window.write_event_value('-PROGRESS-', (i, total))

def extract_samples(window):
    base = os.path.join(SEPARATED_DIR, 'separated')
    stems = []
    for d in os.listdir(base):
        stemdir = os.path.join(base, d, 'stems')
        if os.path.isdir(stemdir):
            for f in os.listdir(stemdir):
                stems.append((d, os.path.join(stemdir, f)))
    total = len(stems)
    for i,(track, path) in enumerate(stems,1):
        name = os.path.basename(path).lower()
        if 'drum' in name:
            # drum hits
            y, sr = librosa.load(path, sr=None)
            onsets = librosa.onset.onset_detect(y, sr=sr, backtrack=True)
            times = librosa.frames_to_time(onsets, sr=sr)
            for j,t in enumerate(times):
                seg = y[int((t-0.01)*sr):int((t+0.2)*sr)]
                sf.write(os.path.join(SAMPLES_DIR,'drums', f"{track}_hit_{j:03d}.wav"), seg, sr)
        else:
            # loops of bass/other
            y, sr = librosa.load(path, sr=None)
            _, beats = librosa.beat.beat_track(y, sr=sr)
            times = librosa.frames_to_time(beats, sr=sr)
            for j in range(0, len(times)-4, 4):
                seg = y[int(times[j]*sr):int(times[j+4]*sr)]
                stem = 'bass' if 'bass' in name else 'other'
                sf.write(os.path.join(SAMPLES_DIR, stem, f"{track}_{stem}_{j//4:03d}.wav"), seg, sr)
        if window: window.write_event_value('-PROGRESS-', (i, total))

# GUI (kort gehouden, copy/paste jouw frontend hier)
sg.theme('DarkBlue3')
layout = [
    [sg.Text('Sample Pack Pipeline')],
    [sg.Button('Download'), sg.Button('Separate'), sg.Button('Extract')],
    [sg.ProgressBar(1, orientation='h', size=(40, 10), key='-P-')],
    [sg.Multiline(size=(60,10), key='-LOG-', disabled=True)]
]
win = sg.Window('Sample Pack', layout)
while True:
    ev, vals = win.read()
    if ev in (sg.WIN_CLOSED, 'Exit'): break
    if ev == 'Download':
        # lees URL's van clipboard of input…
        urls = []  # TODO vullen
        threading.Thread(target=download_urls, args=(urls,win), daemon=True).start()
    if ev == 'Separate':
        win['-P-'].update(0, len(os.listdir(DOWNLOAD_DIR)))
        threading.Thread(target=separate_all, args=(win,), daemon=True).start()
    if ev == 'Extract':
        # count stems
        win['-P-'].update(0,1)
        threading.Thread(target=extract_samples, args=(win,), daemon=True).start()

win.close()
