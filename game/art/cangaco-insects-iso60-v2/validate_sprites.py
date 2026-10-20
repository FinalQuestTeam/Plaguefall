"""Validate native images, byte packing, SGDK declarations and compiled memory."""
from pathlib import Path
from PIL import Image
import json, re, subprocess, sys, struct, os
from export_sprites import DIRS,CANON,PALETTE,LEVELS,frame_bytes

ROOT=Path(__file__).resolve().parent
GAME=ROOT.parents[1]
REPO=GAME.parent
sys.path.insert(0,str(ROOT.parent/"camera-60-redraw-v2"))
from review import camera_review

def main():
    layout=json.loads((GAME/"res/actor_animation.json").read_text())
    if layout.get("enemy_art_directory"):
        subprocess.run([sys.executable,str(GAME/layout["enemy_art_directory"]/"validate_sprites.py")],check=True)
        return
    selected=layout["idle_source_poses"]+layout["run_source_poses"]
    catalog=json.loads((ROOT/"catalog.json").read_text())
    assert len(catalog)==13
    for color in PALETTE:
        assert all(c in LEVELS for c in color)
    rows=[]
    raw=(GAME/"res/insects/frames.bin").read_bytes()
    icons=(GAME/"res/insects/icons.bin").read_bytes()
    assert len(raw)==13*5*len(selected)*768 and len(icons)==15*512
    for index,e in enumerate(catalog):
        folder=ROOT/"enemies"/e["id"]
        master=Image.open(folder/(e["id"]+".png"))
        assert master.mode=="P" and master.size==(192,768)
        assert master.info.get("transparency")==0
        assert (folder/(e["id"]+".png")).read_bytes()[24]==4
        assert master.getpalette()[:48]==[c for rgb in PALETTE for c in rgb]
        assert set(master.tobytes())<=set(range(16))
        assert set(master.convert("RGBA").getchannel("A").tobytes())=={0,255}
        directions=[]
        for d,label in enumerate(DIRS):
            sheet=Image.open(folder/"directions"/(e["id"]+"_"+label+".png"))
            assert sheet.size==(192,96) and sheet.mode=="P" and sheet.info.get("transparency")==0
            assert sheet.tobytes()==master.crop((0,d*96,192,d*96+96)).tobytes()
            poses=[]
            for p in range(10):
                state,col=(0,p) if p<4 else (1,p-4)
                f=sheet.crop((col*32,state*48,col*32+32,state*48+48))
                box=f.getbbox()
                assert box and 1<=box[0] and box[2]<=31 and 1<=box[1] and box[3]==47,(e["id"],label,p,box)
                poses.append(f)
                if d<5 and p in selected:
                    offset=((index*5+d)*len(selected)+selected.index(p))*768
                    assert raw[offset:offset+768]==frame_bytes(f)
            assert sheet.crop((128,0,192,48)).getbbox() is None
            if d>=5:
                original=master.crop((0,CANON[d]*96,192,CANON[d]*96+96))
                # Mirror each cell, not the order of animation columns.
                for p,f in enumerate(poses):
                    state,col=(0,p) if p<4 else (1,p-4)
                    ref=original.crop((col*32,state*48,col*32+32,state*48+48))
                    assert f.tobytes()==ref.transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes()
            runtime_idle=[poses[i] for i in layout["idle_source_poses"]]
            runtime_run=[poses[i] for i in layout["run_source_poses"]]
            assert len({p.tobytes() for p in runtime_idle})==2
            assert len({p.tobytes() for p in runtime_run})==4
            runtime_delta=[sum(a!=b for a,b in zip(runtime_run[i].tobytes(),runtime_run[(i+1)%4].tobytes())) for i in range(4)]
            assert all(runtime_delta)
            idle,run=poses[:4],poses[4:]
            assert len(set(f.tobytes() for f in idle))==4
            assert len(set(f.tobytes() for f in run))==6
            delta=[sum(a!=b for a,b in zip(run[p].tobytes(),run[(p+1)%6].tobytes())) for p in range(6)]
            directions.append({"direction":label,"idle_unique":4,"movement_unique":6,
                "baseline":46,"cyclic_pixel_differences":delta,"runtime_cyclic_pixel_differences":runtime_delta,
                "seam_to_mean_ratio":round(delta[-1]/(sum(delta)/6),3)})
        assert master.crop((0,0,32,48)).tobytes()!=master.crop((0,384,32,432)).tobytes()
        rows.append({"id":e["id"],"directions":directions,
            "camera_validation":camera_review(e["id"],folder/(e["id"]+".png"))})
    jar=Path(os.environ.get("GDK",str(REPO/"SGDK")))/"bin/rescomp.jar"
    process=subprocess.run(["java","-Djava.awt.headless=true","-jar",str(jar),
        str(ROOT/"enemies.res"),str(ROOT/"validation/enemies.s")],capture_output=True,text=True)
    log=process.stdout+process.stderr
    (ROOT/"validation/rescomp.log").write_text(log)
    assert process.returncode==0,"ResComp compilation failed"
    asm=(ROOT/"validation/enemies.s").read_text()
    for e in catalog:
        for d in range(8):
            for state,count in [(0,4),(1,6)]:
                symbol=f'insect_{e["id"]}_animation{d*2+state}'
                m=re.search(r"^"+symbol+r":\s*\n\s*dc.w\s+(\d+)",asm,re.M)
                assert m and (int(m.group(1))>>8)==count,(symbol,m.group(1) if m else None)
    host=subprocess.run(["clang","-std=c99","-Werror=implicit-function-declaration",
        "-I"+str(ROOT/"tests"),"-I"+str(GAME/"src"),str(ROOT/"tests/runtime_test.c"),str(GAME/"src/system/video/herogfx.c"),
        "-o","/private/tmp/redrex-insect-runtime-test"],capture_output=True,text=True)
    assert host.returncode==0,host.stderr
    result=subprocess.run(["/private/tmp/redrex-insect-runtime-test"],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    report={"technical_checks_passed":True,"camera_art_review_accepted":all(r["camera_validation"]["approved"] for r in rows),
        "camera_review":"../camera-60-redraw-v2/README.md",
        "enemies":13,"directions":104,"animation_rows":208,"frames_exported":1040,
        "runtime_canonical_frames":13*5*len(selected),"runtime_source_poses":selected,"runtime_idle_frames":2,"runtime_run_frames":4,"png_cell":[32,48],"png_sheet":[192,768],
        "per_direction_sheet":[192,96],"frame_tile_count":24,"palette_visible_max":15,
        "alpha":[0,255],"renderer_stress":json.loads(result.stdout),
        "raw_frame_rom_bytes":len(raw),"menu_icon_rom_bytes":len(icons),
        "manual_renderer_vdp_pieces":2,"source_art_tool":"image_gen built-in",
        "perspective_note":"Redrawn against an analytical 60-degree-above-ground camera guide. Visual comparison per asset; actual elevation is not numerically measurable from these rasters alone.",
        "cycle_note":"Pixel differences include the loop seam; visual gait still needs art review.",
        "assets":rows}
    (ROOT/"validation/report.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k!="assets"},indent=2))

if __name__=="__main__":main()
