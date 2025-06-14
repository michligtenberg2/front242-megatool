# Front242 Megatool

## Overzicht
Deze tool biedt een alles-in-één GUI voor:
- YouTube → MP3 downloaden  
- Stems scheiden met Demucs  
- Drum hits & loops extraheren  
- Audio preprocessing (normalisatie, fades)  
- Timing humanizen  
- Key detectie & ID3-tagging  
- BPM/maat matchen van samples  
- EBM/Front-242 drum-patronen

## Installatie
1. Clone deze repo  
2. `python -m venv venv && source venv/bin/activate`  
3. `pip install -r requirements.txt`  
4. Installeer PyTorch CPU-only (véél kleiner dan GPU-versie):
   ```bash
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

