"""Render two silent 20s brand films from the existing AI illustrations.
Requires Pillow and imageio-ffmpeg. Does not use customer/shop data.
"""
from pathlib import Path
from functools import lru_cache
import math, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import imageio_ffmpeg

ROOT=Path(__file__).resolve().parent
ASSETS=ROOT/'assets'
FPS=20
DURATION=20
SCENES=[
 ('boutique-hero.jpg','ALIMENTATION GÉNÉRALE','Votre commerce.\nVotre espace.','Alimentation générale & électroménager','Ventes · Stocks · Crédits clients'),
 ('boutique-stock.jpg','LES PRODUITS, EN ORDRE','Vos stocks,\nsans les devinettes.','Produits · Quantités · Réapprovisionnement','Une vente enregistrée, un stock ajusté.'),
 ('boutique-clients.jpg','ÉLECTROMÉNAGER & CLIENTS','Chaque vente notée.\nChaque crédit suivi.','Ventes · Clients · Remboursements','Les informations utiles, au même endroit.'),
 ('boutique-commercant.jpg','VOTRE PROPRE ESPACE','Moins de cahiers.\nPlus de clarté.','BoutiquePilot, votre quotidien en plus simple.','Un compte · Une boutique indépendante'),
]
SOURCES=[Image.open(ASSETS/s[0]).convert('RGB') for s in SCENES]
@lru_cache(None)
def font(size,weight=600):
 f=ImageFont.truetype(str(ASSETS/'manrope.ttf'),size)
 try:f.set_variation_by_axes([weight])
 except Exception:pass
 return f

def cover(im,w,h,zoom,focus=.58,vertical=.5):
 scale=max(w/im.width,h/im.height)*zoom
 nw,nh=round(im.width*scale),round(im.height*scale)
 scaled=im.resize((nw,nh),Image.Resampling.BICUBIC)
 left=int((nw-w)*focus);top=int((nh-h)*vertical)
 return scaled.crop((left,top,left+w,top+h))

def overlay(w,h,i):
 # Cache static typography/gradient at each scene and size.
 layer=Image.new('RGBA',(w,h))
 gradient=Image.new('RGBA',(1,h))
 pix=gradient.load()
 for y in range(h):
  r=y/h
  opacity=int(145*max(0,1-r/.38)+220*max(0,(r-.32)/.68))
  pix[0,y]=(11,35,25,min(235,opacity))
 layer.alpha_composite(gradient.resize((w,h)))
 d=ImageDraw.Draw(layer)
 mobile=w<h
 pad=round(w*.075)
 top=round(h*.065)
 unit=w/900
 # The original shopping bag, with its green fill, not a new logo.
 tile=round(w*.055)
 d.rounded_rectangle((pad,top,pad+tile,top+tile),radius=round(tile*.25),fill='#d4ec98')
 bx=pad+tile*.21;by=top+tile*.22;bs=tile*.58
 d.polygon([(bx+bs*.15,by+bs*.22),(bx+bs*.85,by+bs*.22),(bx+bs,by+bs),(bx,by+bs)],fill='#4da86f',outline='#205f3f',width=max(1,round(unit*2)))
 d.arc((bx+bs*.27,by-bs*.02,bx+bs*.73,by+bs*.52),180,360,fill='#164b32',width=max(2,round(unit*2.4)))
 brand_size=round(w*.033)
 d.text((pad+tile+round(w*.016),top+tile*.15),'BoutiquePilot.',font=font(brand_size,750),fill='#fafbf0')
 chip_font=font(round(w*(.019 if mobile else .016)),650)
 # Main type has generous safe areas for website crops.
 title_size=round(w*(.070 if mobile else .061))
 title_font=font(title_size,700)
 title_y=round(h*(.585 if mobile else .565))
 d.text((pad,title_y-round(h*.048)),SCENES[i][1],font=chip_font,fill='#d4e7a6')
 d.multiline_text((pad,title_y),SCENES[i][2],font=title_font,fill='#fcfdf6',spacing=round(title_size*.10))
 subtitle_size=round(w*(.025 if mobile else .022))
 sub_y=title_y+round(title_size*2.40)
 subtitle=SCENES[i][3]
 subfont=font(subtitle_size,450)
 # The portrait variant wraps a long subtitle rather than shrinking its text.
 if d.textlength(subtitle,font=subfont)>w-pad*2:
  if ' & ' in subtitle:subtitle=subtitle.replace(' & ','\n& ')
  elif ' · ' in subtitle:subtitle=subtitle.replace(' · ','\n',1)
 d.multiline_text((pad,sub_y),subtitle,font=subfont,fill='#e2e9d4',spacing=round(subtitle_size*.25))
 bottom=round(h*.91)
 d.line((pad,bottom-round(h*.018),w-pad,bottom-round(h*.018)),fill='#d4e7a64d',width=1)
 d.text((pad,bottom),SCENES[i][4],font=font(round(w*.018),450),fill='#d5dfc7')
 disclaimer='Illustrations IA · Présentation animée · Sans son'
 d.text((pad,round(h*.962)),disclaimer,font=font(round(w*.012),450),fill='#bccdaf')
 chapter=f'{i+1:02d} / 04'
 chapterfont=font(round(w*.015),600)
 d.text((w-pad-d.textlength(chapter,font=chapterfont),top+tile*.30),chapter,font=chapterfont,fill='#d7e6bb')
 return layer

@lru_cache(None)
def cached_overlay(w,h,i):return overlay(w,h,i)

def scene_frame(w,h,i,local):
 progress=local/5
 zoom=1.02+.045*progress
 focus=.60 if i in (0,3) else .50
 base=cover(SOURCES[i],w,h,zoom,focus,.45+progress*.04).convert('RGBA')
 base.alpha_composite(cached_overlay(w,h,i))
 return base.convert('RGB')

def frame(w,h,t):
 i=min(3,int(t//5));local=t-i*5
 a=scene_frame(w,h,i,local)
 if local>4.55:
  b=scene_frame(w,h,(i+1)%4,local-4.55)
  f=(local-4.55)/.45;f=f*f*(3-2*f)
  a=Image.blend(a,b,f)
 return a

def render(w,h,name):
 target=ASSETS/name
 cmd=[imageio_ffmpeg.get_ffmpeg_exe(),'-y','-loglevel','error','-f','rawvideo','-vcodec','rawvideo','-s',f'{w}x{h}','-pix_fmt','rgb24','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','25','-pix_fmt','yuv420p','-movflags','+faststart','-metadata','title=BoutiquePilot — Votre commerce, en clair','-metadata','comment=Animated presentation made from AI-generated illustrations; no audio or customer data',str(target)]
 process=subprocess.Popen(cmd,stdin=subprocess.PIPE)
 try:
  for n in range(DURATION*FPS):process.stdin.write(frame(w,h,n/FPS).tobytes())
  process.stdin.close()
  status=process.wait()
  if status:raise RuntimeError(f'FFmpeg failed: {status}')
 except BaseException:
  process.kill();process.wait();raise
 frame(w,h,1.2).save(target.with_suffix('.webp'),'WEBP',quality=85)
 print(f'{target.name}: {DURATION}s, {w}x{h}, {target.stat().st_size:,} bytes',flush=True)

if __name__=='__main__':
 render(900,720,'boutiquepilot-accueil.mp4')
 render(640,800,'boutiquepilot-accueil-mobile.mp4')
