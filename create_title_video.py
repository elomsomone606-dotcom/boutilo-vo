"""Render the animated replacement for the homepage headline (8s, silent H.264).
Optional build dependencies: Pillow, imageio-ffmpeg. No runtime dependencies.
"""
from pathlib import Path
from functools import lru_cache
import subprocess, math
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
ROOT=Path(__file__).resolve().parent
W,H,FPS,SECONDS=960,480,24,8
@lru_cache(None)
def font(weight=750):
    f=ImageFont.truetype(str(ROOT/'assets/manrope.ttf'),112)
    f.set_variation_by_axes([weight])
    return f

def ease(x):
    x=max(0,min(1,x))
    return 1-(1-x)**3

def line(text,y,t,start,color,weight=750,x=12):
    p=ease((t-start)/.85)
    layer=Image.new('RGBA',(W,H))
    d=ImageDraw.Draw(layer)
    d.text((x,y+int(27*(1-p))),text,font=font(weight),fill=(*color,int(255*p)),stroke_width=0)
    return layer

def frame(t):
    im=Image.new('RGBA',(W,H),(248,249,243,255))
    im.alpha_composite(line('Votre boutique',0,t,-.35,(30,56,44)))
    im.alpha_composite(line('mérite mieux',126,t,.65,(30,56,44)))
    im.alpha_composite(line('qu’un ',252,t,1.45,(30,56,44)))
    prefix=12+font().getlength('qu’un ')
    im.alpha_composite(line('cahier.',252,t,1.75,(123,150,91),650,prefix))
    # A soft hand-drawn underline, then an almost imperceptible breathing glow.
    p=ease((t-2.4)/1.05)
    end=prefix+font(650).getlength('cahier.')
    overlay=Image.new('RGBA',(W,H))
    d=ImageDraw.Draw(overlay)
    if p>0:
        right=prefix+(end-prefix)*p
        d.polygon([(prefix,407),(right,393),(right,405),(prefix,417)],fill=(211,230,171,195))
        d.line([(prefix,414),(right,401)],fill=(210,228,170,100),width=5)
    im.alpha_composite(overlay)
    return im.convert('RGB')

if __name__=='__main__':
    target=ROOT/'assets/boutiquepilot-titre-anime.mp4'
    cmd=[imageio_ffmpeg.get_ffmpeg_exe(),'-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart','-metadata','title=Votre boutique mérite mieux qu’un cahier — BoutiquePilot',str(target)]
    process=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for n in range(FPS*SECONDS):process.stdin.write(frame(n/FPS).tobytes())
        process.stdin.close()
        if process.wait():raise RuntimeError('FFmpeg failed')
    except BaseException:
        process.kill();process.wait();raise
    frame(5).save(target.with_suffix('.webp'),'WEBP',quality=92)
    print(f'{target.name}: {SECONDS}s, {W}×{H}, {target.stat().st_size:,} bytes')
