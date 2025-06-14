DRUM_PATTERNS = {
    'Classic EBM 1': {'tempo':125, 'steps': {
        'kick':  [1,0,0,0]*4,
        'snare': [0,0,1,0]*4,
        'hihat': [1]*16
    }},
    'Driving EBM':   {'tempo':130, 'steps': {
        'kick':  [1,0,1,0]*4,
        'snare': [0,0,1,0]*4,
        'hihat': [1,0]*8
    }},
    'Syncopated Pulse': {'tempo':120, 'steps': {
        'kick':  [1,0,0,1,0,1,0,0]*2,
        'snare': [0,0,1,0,0,1,0,1]*2,
        'hihat': [1,1,0,1,1,0,1,1]*2
    }},
    'Kommando Remix':   {'tempo':125, 'steps': {
        'kick':  [1,0,1,0]*4,
        'snare': [0,0,0,1]*4,
        'hihat': [1,0,1,0]*4
    }},
    'No Shuffle':       {'tempo':130, 'steps': {
        'kick':  [1,0,0,0,0,0,1,0]*2,
        'snare': [0,0,1,0,0,0,0,0]*2,
        'hihat': [1]*16
    }},
}
