"""Build nearest-neighbour galleries and a reviewable native-asset archive."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,zipfile,sys
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/"camera-60-audit"))
from review import write_archive_review
def main():
    catalog=json.loads((ROOT/"catalog.json").read_text())
    previews=ROOT/"previews";previews.mkdir(exist_ok=True)
    font=ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf",16)
    for family in ["sq","tri","pen","boss"]:
        entries=[e for e in catalog if e["family"]==family]
        frames=[]
        for phase in range(6):
            page=Image.new("RGB",(920,40+len(entries)*144),(24,24,36))
            draw=ImageDraw.Draw(page)
            for d,label in enumerate(["N","NE","L","SE","S","SO","O","NO"]):
                draw.text((152+d*96+40,8),label,font=font,fill=(219,219,182))
            for row,e in enumerate(entries):
                y=40+row*144
                draw.text((8,y+52),e["id"],font=font,fill=(219,219,182))
                draw.text((8,y+75),e["name"],font=font,fill=(146,182,182))
                master=Image.open(ROOT/"enemies"/e["id"]/(e["id"]+".png"))
                for d in range(8):
                    f=master.crop((phase*32,d*96+48,phase*32+32,d*96+96)).convert("RGBA")
                    f=f.resize((96,144),Image.Resampling.NEAREST)
                    page.paste(f,(152+d*96,y),f)
            frames.append(page)
        frames[0].save(previews/(family+"-3x.png"))
        frames[0].save(previews/(family+"-movement-3x.gif"),save_all=True,append_images=frames[1:],duration=100,loop=0,disposal=2)
    for p in (ROOT/"validation/emulator").glob("*.ppm"):
        Image.open(p).save(p.with_suffix(".png"))
    for p in (ROOT/"enemies").glob("*/*_opt.png"):
        folder=p.parent/"validation";folder.mkdir(exist_ok=True)
        p.replace(folder/p.name)
    with zipfile.ZipFile(ROOT/"redrex-cangaco-insects-sgdk.zip","w",zipfile.ZIP_DEFLATED) as z:
        write_archive_review(z,ROOT)
        for relative in ["catalog.json","palette.json","palette.gpl","enemies.res",
                "validation/report.json","validation/memory.json"]:
            z.write(ROOT/relative,relative)
        for folder in ["enemies","previews","prompts"]:
            for p in (ROOT/folder).rglob("*"):
                if p.is_file() and "validation" not in p.relative_to(ROOT).parts:z.write(p,p.relative_to(ROOT))
    print("Packaged 13 enemies, 104 directional PNGs and nearest-neighbour previews.")
if __name__=="__main__":main()
