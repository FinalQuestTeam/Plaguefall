"""Nearest-neighbour hero previews and native SGDK archive."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,shutil,zipfile,sys
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/"camera-60-redraw-v2"))
from review import write_archive_review
def main():
    p=ROOT/"previews";p.mkdir(exist_ok=True)
    font=ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf",18)
    master=Image.open(ROOT/"heroi/heroi.png")
    for state,length,name in [(0,4,"repouso"),(1,6,"movimento")]:
        frames=[]
        for phase in range(length):
            canvas=Image.new("RGB",(1024,224),(24,24,36))
            draw=ImageDraw.Draw(canvas)
            for d,label in enumerate(["N","NE","L","SE","S","SO","O","NO"]):
                draw.text((d*128+52,5),label,font=font,fill=(219,219,182))
                y=d*96+state*48
                f=master.crop((phase*32,y,phase*32+32,y+48)).convert("RGBA")
                f=f.resize((128,192),Image.Resampling.NEAREST)
                canvas.paste(f,(d*128,32),f)
            frames.append(canvas)
        frames[0].save(p/("heroi-"+name+"-4x.png"))
        frames[0].save(p/("heroi-"+name+"-4x.gif"),save_all=True,append_images=frames[1:],duration=200 if state==0 else 100,loop=0,disposal=2)
    shutil.copy2(p/"heroi-repouso-4x.png",p/"heroi-8dir-4x.png")
    source=ROOT.parent/"cangaco-insects-iso60-v2/validation"
    shutil.copy2(source/"memory.json",ROOT/"validation/memory.json")
    dest=ROOT/"validation/emulator";dest.mkdir(exist_ok=True)
    for name in ["report.json","hero-gallery.png","all-enemies-direction-0.png","all-enemies-direction-2.png","all-enemies-direction-4.png"]:
        shutil.copy2(source/"emulator"/name,dest/name)
    opt=ROOT/"heroi/heroi_opt.png"
    if opt.exists():shutil.move(opt,ROOT/"validation/heroi_opt.png")
    catalog={"id":"heroi","name":"Damião","cell":[32,48],"sheet":"heroi/heroi.png",
        "directions":["N","NE","L","SE","S","SO","O","NO"],"animations":{"idle":4,"run":6},
        "palette":"palette.json","resource":"heroi.res","prompt":"prompts/heroi.txt"}
    (ROOT/"catalog.json").write_text(json.dumps(catalog,indent=2)+"\n")
    with zipfile.ZipFile(ROOT/"redrex-heroi-iso60-v2-sgdk.zip","w",zipfile.ZIP_DEFLATED) as z:
        write_archive_review(z,ROOT)
        for name in ["catalog.json","palette.json","palette.gpl","heroi.res",
            "validation/report.json","validation/memory.json","validation/export.json",
            "validation/emulator/report.json","validation/emulator/hero-gallery.png"]:
            z.write(ROOT/name,name)
        for folder in ["heroi","previews","prompts"]:
            for f in (ROOT/folder).rglob("*"):
                if f.is_file():z.write(f,f.relative_to(ROOT))
    print("Packaged Damião:8 directions,16 animations,80 frame references.")
if __name__=="__main__":main()
