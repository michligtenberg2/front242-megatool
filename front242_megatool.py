#!/usr/bin/env python3

import os
import subprocess
import threading
import random
import PySimpleGUI as sg
from yt_dlp import YoutubeDL
import librosa
import soundfile as sf
import numpy as np
from mutagen.easyid3 import EasyID3

# --- EBM Drum Pattern Presets ---
DRUM_PATTERNS = {
    'Classic EBM 1': {'tempo':125,'steps':{'kick':[1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0],'snare':[0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0],'hihat':[1]*16}},
    'Driving EBM':   {'tempo':130,'steps':{'kick':[1,0,1,0]*4,'snare':[0,0,1,0]*4,'hihat':[1,0]*8}},
    'Syncopated Pulse':{'tempo':120,'steps':{'kick':[1,0,0,1,0,1,0,0]*2,'snare':[0,0,1,0,0,1,0,1]*2,'hihat':[1,1,0,1,1,0,1,1]*2}},
    'Aggressive Fill':{'tempo':128,'steps':{'kick':[1,0,1,0,1,1,1,0]*2,'snare':[0,1,0,1]*4,'hihat':[1,0]*8}},
    'Breakbeat Variation':{'tempo':140,'steps':{'kick':[1,0,1,1,0,1,0,1]*2,'snare':[0,0,1,0,1,0,1,0]*2,'hihat':[1,1,0,0]*4}},
    'Kommando Remix': {'tempo':125,'steps':{'kick':[1,0,1,0]*4,'snare':[0,0,0,1]*4,'hihat':[1,0,1,0]*4}},
    'No Shuffle':     {'tempo':130,'steps':{'kick':[1,0,0,0,0,0,1,0]*2,'snare':[0,0,1,0,0,0,0,0]*2,'hihat':[1]*16}},
}

# --- Configuration ---
DEMUX_MODEL = 'mdx_extra'
DEFAULT_DOWNLOAD_DIR = 'tracks'
SEPARATED_DIR = 'separated'
SAMPLES_DIR = 'samples'
KEY_MAP = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']

# Ensure directories exist
for d in [DEFAULT_DOWNLOAD_DIR, SEPARATED_DIR]: os.makedirs(d, exist_ok=True)
for stem in ['drums','bass','other']:
    os.makedirs(os.path.join(SAMPLES_DIR, stem), exist_ok=True)

# --- Functions ---
def get_playlist_urls(url, window=None):
    if window: window.write_event_value('-STATUS-', f"Fetching playlist {url}")
    with YoutubeDL({'extract_flat':True,'skip_download':True,'quiet':True}) as ydl:
        info = ydl.extract_info(url, download=False)
        entries = info.get('entries',[]) or []
    urls = [f"https://www.youtube.com/watch?v={e['id']}" for e in entries if e.get('id')]
    if window: window.write_event_value('-LOG-', f"Found {len(urls)} links")
    return urls

def download_urls(urls, window, download_dir):
    opts={'outtmpl':os.path.join(download_dir,'%(title)s.%(ext)s'),'format':'bestaudio','quiet':True,
          'postprocessors':[{'key':'FFmpegExtractAudio','preferredcodec':'mp3','preferredquality':'192'}]}
    window.write_event_value('-LOG-', f"Downloading {len(urls)} URLs...")
    with YoutubeDL(opts) as ydl:
        for i,u in enumerate(urls,1):
            window.write_event_value('-STATUS-', f"Download {i}/{len(urls)}")
            window.write_event_value('-LOG-', f"DL: {u}")
            try: ydl.download([u])
            except Exception as e: window.write_event_value('-LOG-', f"Error: {e}")
            window.write_event_value('-PROGRESS-', (i, len(urls)))
    window.write_event_value('-STATUS-', 'Download complete')

def separate_all(window, source_dir):
    files=[f for f in os.listdir(source_dir) if f.lower().endswith('.mp3')]
    window.write_event_value('-LOG-', f"Separating {len(files)} files...")
    for i,f in enumerate(files,1):
        p=os.path.join(source_dir,f)
        window.write_event_value('-STATUS-', f"Separate {i}/{len(files)}")
        window.write_event_value('-LOG-', f"Sep: {f}")
        try: subprocess.run(['demucs','-n',DEMUX_MODEL,'--out',SEPARATED_DIR,p], check=True)
        except Exception as e: window.write_event_value('-LOG-', f"Err sep {f}: {e}")
        window.write_event_value('-PROGRESS-', (i, len(files)))
    window.write_event_value('-STATUS-', 'Separation complete')

def extract_samples(window):
    base=os.path.join(SEPARATED_DIR,'separated')
    items=[]
    if os.path.isdir(base):
        for d in os.listdir(base):
            sd=os.path.join(base,d,'stems')
            if os.path.isdir(sd):
                for f in os.listdir(sd): items.append((d,sd,f))
    window.write_event_value('-LOG-', f"Extracting {len(items)} stems...")
    for i,(d,sd,f) in enumerate(items,1):
        p=os.path.join(sd,f)
        if 'drum' in f.lower(): extract_hits(p,d,window)
        else: extract_loops(p,d,'bass' if 'bass' in f.lower() else 'other',window)
        window.write_event_value('-PROGRESS-', (i, len(items)))
    window.write_event_value('-STATUS-', 'Extraction complete')

def extract_hits(path, track, window):
    y,sr=librosa.load(path,sr=None)
    onsets=librosa.onset.onset_detect(y=y,sr=sr,backtrack=True)
    times=librosa.frames_to_time(onsets,sr=sr)
    window.write_event_value('-LOG-', f"Hits {len(times)} @ {track}")
    for i,t in enumerate(times):
        seg=y[int((t-0.01)*sr):int((t+0.2)*sr)]
        sf.write(os.path.join(SAMPLES_DIR,'drums',f"{track}_drum_{i:03d}.wav"), seg, sr)

def extract_loops(path, track, stem, window):
    y,sr=librosa.load(path,sr=None)
    _,b=librosa.beat.beat_track(y=y,sr=sr)
    tms=librosa.frames_to_time(b,sr=sr)
    c=max(0,(len(tms)-4)//4)
    window.write_event_value('-LOG-', f"Loops {c} @ {stem}/{track}")
    for i in range(c):
        seg=y[int(tms[i*4]*sr):int(tms[i*4+4]*sr)]
        sf.write(os.path.join(SAMPLES_DIR,stem,f"{track}_{stem}_{i:03d}.wav"), seg, sr)

def humanize_samples(stems,off,prob,window):
    window.write_event_value('-LOG-', f"Humanize ±{off}ms @ {prob*100}%")
    for stem in stems:
        fld=os.path.join(SAMPLES_DIR,stem)
        for f in os.listdir(fld):
            if random.random()<=prob:
                p=os.path.join(fld,f);y,sr=librosa.load(p,sr=None)
                o=int(random.uniform(-off,off)/1000*sr)
                y2=np.roll(y,o)
                y2[:o if o>0 else None]=0
                y2[o if o<0 else None:]=0
                sf.write(p,y2,sr)
    window.write_event_value('-LOG-','Humanize done')

def normalize_audio(y,dbfs):
    r=np.sqrt(np.mean(y**2));tlin=10**(dbfs/20)
    return y*(tlin/r) if r>0 else y

def apply_fade(y,sr,fi,fo):
    fi_s=int(sr*fi/1000);fo_s=int(sr*fo/1000)
    if fi_s>0: y[:fi_s]*=np.linspace(0,1,fi_s)
    if fo_s>0: y[-fo_s:]*=np.linspace(1,0,fo_s)
    return y

def preprocess_samples(window,norm,dbfs,fi,fo):
    window.write_event_value('-LOG-','Preprocess start')
    for stem in ['drums','bass','other']:
        for f in os.listdir(os.path.join(SAMPLES_DIR,stem)):
            p=os.path.join(SAMPLES_DIR,stem,f);y,sr=librosa.load(p,sr=None)
            if norm: y=normalize_audio(y,dbfs)
            if fi>0 or fo>0: y=apply_fade(y,sr,fi,fo)
            sf.write(p,y,sr)
            window.write_event_value('-LOG-',f"Preprocessed {stem}/{f}")
    window.write_event_value('-LOG-','Preprocess done')

def detect_key(path):
    y,sr=librosa.load(path,sr=None)
    c=np.mean(librosa.feature.chroma_cqt(y=y,sr=sr),axis=1)
    return KEY_MAP[int(np.argmax(c))]

def tag_keys(window):
    window.write_event_value('-LOG-','Tag keys start')
    for stem in ['drums','bass','other']:
        for f in os.listdir(os.path.join(SAMPLES_DIR,stem)):
            p=os.path.join(SAMPLES_DIR,stem,f);k=detect_key(p)
            try: a=EasyID3(p);a['key']=k;a.save();window.write_event_value('-LOG-',f"Tagged {stem}/{f}={k}")
            except: window.write_event_value('-LOG-',f"No tag for {f}")
    window.write_event_value('-LOG-','Tag keys done')

# --- GUI ---
sg.theme('DarkBlue3')
layout=[
  [sg.Frame('Input',[[sg.Text('YouTube URLs/Playlists:')],[sg.Multiline(key='-URLS-',size=(60,3))],[sg.Text('Local folder:'),sg.Input(key='-FOLDER-'),sg.FolderBrowse()]])],
  [sg.Frame('Options',[[
      sg.Checkbox('Normalize',key='-NORM-'),sg.Text('dBFS'),sg.Input('-14',key='-DBFS-',size=(5,1)),
      sg.Text('FadeIn'),sg.Input('10',key='-FI-',size=(5,1)),sg.Text('FadeOut'),sg.Input('20',key='-FO-',size=(5,1)),
      sg.Checkbox('Humanize',key='-HUM-'),sg.Text('±ms'),sg.Input('15',key='-OFF-',size=(5,1)),sg.Text('%'),sg.Input('50',key='-CHANCE-',size=(4,1))
  ]])],
  [sg.Frame('Actions',[[sg.Button('Get Links'),sg.Button('Download'),sg.Button('Separate'),sg.Button('Extract'),sg.Button('Preprocess'),sg.Button('Tag Keys'),sg.Button('Humanize'),sg.Button('Run All')]])],
  [sg.Frame('Progress',[[sg.Text('Status:'),sg.Text('',key='-STATUS-')],[sg.ProgressBar(1,orientation='h',size=(50,10),key='-PROGRESS-')]])],
  [sg.Frame('Log',[[sg.Multiline(key='-LOGBOX-',size=(80,15),disabled=True)]])]
]
win=sg.Window('Front242 Megatool',layout,finalize=True)
while True:
    ev,vals=win.read()
    if ev in (sg.WIN_CLOSED,'Exit'): break
    dl=vals['-FOLDER-'] or DEFAULT_DOWNLOAD_DIR
    if ev=='Get Links':
        us=[]
        for l in vals['-URLS-'].splitlines(): u=l.strip();
        if 'list=' in u: us+=get_playlist_urls(u,win)
        elif u: us.append(u)
        win['-URLS-'].update("\n".join(us))
    elif ev=='Download':
        arr=[u for u in vals['-URLS-'].splitlines() if u]
        win['-PROGRESS-'].update(0,len(arr))
        threading.Thread(target=download_urls,args=(arr,win,dl),daemon=True).start()
    elif ev=='Separate':
        tr=[f for f in os.listdir(dl) if f.endswith('.mp3')]
        win['-PROGRESS-'].update(0,len(tr))
        threading.Thread(target=separate_all,args=(win,dl),daemon=True).start()
    elif ev=='Extract': threading.Thread(target=lambda: extract_samples(win),daemon=True).start()
    elif ev=='Preprocess': threading.Thread(target=preprocess_samples,args=(win,vals['-NORM-'],float(vals['-DBFS-']),int(vals['-FI-']),int(vals['-FO-'])),daemon=True).start()
    elif ev=='Tag Keys': threading.Thread(target=tag_keys,args=(win,),daemon=True).start()
    elif ev=='Humanize': threading.Thread(target=humanize_samples,args=(['drums','bass','other'],int(vals['-OFF-']),float(vals['-CHANCE-'])/100,win),daemon=True).start()
    elif ev=='Run All': threading.Thread(target=lambda: (download_urls([u for u in vals['-URLS-'].splitlines() if u],win,dl), separate_all(win,dl), extract_samples(win), preprocess_samples(win,vals['-NORM-'],float(vals['-DBFS-']),int(vals['-FI-']),int(vals['-FO-'])), tag_keys(win), humanize_samples(['drums','bass','other'],int(vals['-OFF-']),float(vals['-CHANCE-'])/100,win)),daemon=True).start()
    elif ev=='-PROGRESS-':c,t=vals['-PROGRESS-'];win['-PROGRESS-'].update(c,t)
    elif ev=='-STATUS-':win['-STATUS-'].update(vals['-STATUS-'])
    elif ev=='-LOG-':win['-LOGBOX-'].print(vals['-LOG-'])
win.close()
