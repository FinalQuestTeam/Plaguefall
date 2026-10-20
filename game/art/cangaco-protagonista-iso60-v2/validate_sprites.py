"""Validate hero PNGs, all 80 frame references, SGDK output and combined runtime."""
from pathlib import Path
from PIL import Image
import json,re,subprocess,hashlib,sys,os
from export_sprites import pipeline,ROOT,GAME
sys.path.insert(0,str(ROOT.parent/"camera-60-redraw-v2"))
from review import camera_review
def main():
    layout=json.loads((GAME/"res/actor_animation.json").read_text())
    selected=layout["idle_source_poses"]+layout["run_source_poses"]
    master=Image.open(ROOT/"heroi/heroi.png")
    assert master.mode=="P" and master.size==(192,768)
    assert master.info["transparency"]==0
    assert (ROOT/"heroi/heroi.png").read_bytes()[24]==4
    palette=[c for rgb in pipeline.PALETTE for c in rgb]
    assert master.getpalette()[:48]==palette
    assert all(c in pipeline.LEVELS for c in palette)
    assert set(master.convert("RGBA").getchannel("A").tobytes())=={0,255}
    assert set(master.tobytes())<=set(range(16))
    raw=(GAME/"res/heroi/frames.bin").read_bytes()
    assert len(raw)==5*len(selected)*768
    directions=[]
    for d,label in enumerate(pipeline.DIRS):
        f=ROOT/"heroi/directions"/("heroi_"+label+".png")
        sheet=Image.open(f)
        assert sheet.size==(192,96) and sheet.info["transparency"]==0
        assert sheet.getpalette()[:48]==palette
        assert sheet.tobytes()==master.crop((0,d*96,192,d*96+96)).tobytes()
        assert sheet.crop((128,0,192,48)).getbbox() is None
        poses=[]
        for p in range(10):
            row,col=(0,p) if p<4 else (1,p-4)
            cell=sheet.crop((col*32,row*48,col*32+32,row*48+48))
            box=cell.getbbox()
            assert box and 1<=box[0] and box[2]<=31 and 1<=box[1] and box[3]==47,(label,p,box)
            poses.append(cell)
            if d<5:
                if p in selected:
                    offset=(d*len(selected)+selected.index(p))*768
                    assert raw[offset:offset+768]==pipeline.frame_bytes(cell)
            else:
                y=pipeline.CANON[d]*96+row*48
                expected=master.crop((col*32,y,col*32+32,y+48)).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                assert cell.tobytes()==expected.tobytes()
        assert len({p.tobytes() for p in poses[:4]})==4
        assert len({p.tobytes() for p in poses[4:]})==6
        runtime_idle=[poses[i] for i in layout["idle_source_poses"]]
        runtime_run=[poses[i] for i in layout["run_source_poses"]]
        assert len({p.tobytes() for p in runtime_idle})==2
        assert len({p.tobytes() for p in runtime_run})==4
        runtime_delta=[sum(a!=b for a,b in zip(runtime_run[i].tobytes(),runtime_run[(i+1)%4].tobytes())) for i in range(4)]
        assert all(runtime_delta)
        run=poses[4:]
        delta=[sum(a!=b for a,b in zip(run[i].tobytes(),run[(i+1)%6].tobytes())) for i in range(6)]
        directions.append({"direction":label,"idle_frames":4,"movement_frames":6,
            "idle_unique":4,"movement_unique":6,"baseline":46,"cyclic_pixel_differences":delta,"runtime_cyclic_pixel_differences":runtime_delta})
    assert master.crop((0,0,32,48)).tobytes()!=master.crop((0,384,32,432)).tobytes()
    result=subprocess.run(["java","-Djava.awt.headless=true","-jar",str(Path(os.environ.get("GDK",str(GAME.parent/"SGDK")))/"bin/rescomp.jar"),
        str(ROOT/"heroi.res"),str(ROOT/"validation/heroi.s")],capture_output=True,text=True)
    (ROOT/"validation/rescomp.log").write_text(result.stdout+result.stderr)
    assert result.returncode==0
    asm=(ROOT/"validation/heroi.s").read_text()
    for i in range(16):
        m=re.search(r"^heroi_animation"+str(i)+r":\s*\n\s*dc.w\s+(\d+)",asm,re.M)
        assert m and int(m.group(1))>>8==(4 if i%2==0 else 6)
    tests=GAME/"art/cangaco-insects-iso60-v2/tests"
    result=subprocess.run(["clang","-std=c99","-Werror=implicit-function-declaration",
        "-I"+str(tests),"-I"+str(GAME/"src"),str(tests/"runtime_test.c"),
        str(GAME/"src/system/video/herogfx.c"),"-o","/private/tmp/redrex-hero-runtime-test"],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    runtime=subprocess.run(["/private/tmp/redrex-hero-runtime-test"],capture_output=True,text=True)
    assert runtime.returncode==0,runtime.stderr
    report={"passed":True,"pass_scope":"technical_checks_only","camera_art_review_accepted":camera_review("heroi",ROOT/"heroi/heroi.png")["approved"],
        "camera_validation":camera_review("heroi",ROOT/"heroi/heroi.png"),
        "id":"heroi","project_character":"Rex","directions":8,
        "animations":16,"frames_exported":80,"runtime_canonical_frames":5*len(selected),"runtime_source_poses":selected,"runtime_idle_frames":2,"runtime_run_frames":4,"cell":[32,48],
        "sheet":[192,768],"directional_sheet":[192,96],"alpha":[0,255],"transparent_index":0,
        "palette_visible_max":15,"palette_slot":"PAL2","runtime_rom_bytes":len(raw)+32,
        "runtime_vram_frame_bytes":768,"runtime_extra_reserved_vram_bytes":0,
        "runtime_hardware_pieces":2,"extra_palette_slots":0,"runtime_stress":json.loads(runtime.stdout),
        "animation_checks":directions,"source_art_tool":"image_gen built-in",
        "camera":"Redrawn against an analytical 60-degree-above-ground camera guide; visual review recorded separately, no exact 3D measurement.",
        "note":"Five drawn views, three horizontal mirrors; equipment symmetry also mirrors."}
    (ROOT/"validation/report.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k!="animation_checks"},indent=2))
if __name__=="__main__":main()
