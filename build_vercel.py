"""Publish only public assets; never expose server code or private data."""
from pathlib import Path
from shutil import copy2, rmtree
root = Path(__file__).resolve().parent
out = root / 'public'
if out.exists():
    rmtree(out)
out.mkdir()
copy2(root / 'index.html', out / 'index.html')
(out / 'assets').mkdir()
for name in ('boutiquepilot-accueil.mp4', 'boutiquepilot-accueil-mobile.mp4', 'boutiquepilot-titre-anime.mp4'):
    copy2(root / 'assets' / name, out / 'assets' / name)
