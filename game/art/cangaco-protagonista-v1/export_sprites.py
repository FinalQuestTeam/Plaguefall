"""Export the protagonist using the same validated technical pixel pipeline."""
from pathlib import Path
import importlib.util,json,struct,sys,shutil
ROOT=Path(__file__).resolve().parent
GAME=ROOT.parents[1]
module=GAME/"art/cangaco-insects-v1/export_sprites.py"
spec=importlib.util.spec_from_file_location("insect_export",module)
pipeline=importlib.util.module_from_spec(spec);spec.loader.exec_module(pipeline)
pipeline.ROOT=ROOT
pipeline.PALETTE=[
    (0,0,0),(0,0,0),(36,36,36),(36,73,73),
    (73,109,109),(109,146,146),(182,182,182),(219,219,182),
    (73,36,0),(146,73,36),(182,109,73),(219,146,73),
    (109,36,36),(182,36,36),(36,182,219),(73,73,73),
]
def main():
    frames,icon,report=pipeline.export({"id":"heroi","family":"hero"})
    # Normalize the deliverable path to the project resource ID.
    folder=ROOT/"enemies/heroi"
    final=ROOT/"heroi"
    if final.exists():shutil.rmtree(final)
    folder.rename(final)
    folder.parent.rmdir()
    res=GAME/"res/heroi";res.mkdir(exist_ok=True)
    (res/"frames.bin").write_bytes(frames)
    palette=b"".join(struct.pack(">H",(round(r/255*7)<<1)|(round(g/255*7)<<5)|(round(b/255*7)<<9)) for r,g,b in pipeline.PALETTE)
    (res/"palette.bin").write_bytes(palette)
    (GAME/"res/heroi.res").write_text('BIN heroi_frames "heroi/frames.bin" 4\nBIN heroi_palette "heroi/palette.bin" 2\n')
    (ROOT/"heroi.res").write_text('SPRITE heroi "heroi/heroi.png" 4 6 FAST 6 NONE BALANCED FAST\n')
    (ROOT/"palette.json").write_text(json.dumps(pipeline.PALETTE,indent=2)+"\n")
    (ROOT/"palette.gpl").write_text("GIMP Palette\nName: RedRex Hero PAL2\nColumns:4\n#\n"+
        "\n".join(f"{r} {g} {b} index{i}" for i,(r,g,b) in enumerate(pipeline.PALETTE))+"\n")
    (ROOT/"validation/export.json").write_text(json.dumps(report,indent=2)+"\n")
    print("Hero exported:8 directions,80 frames; ROM:",len(frames)+len(palette),"bytes")
if __name__=="__main__":main()
