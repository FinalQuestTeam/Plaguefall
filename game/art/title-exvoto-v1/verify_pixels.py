"""Verify emulator captures: pulse is restricted to the core, art stays fixed."""
from pathlib import Path
import json
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parent
INTRO=ROOT.parent/'intro-monologo-v1'

def main():
    native=np.asarray(Image.open(ROOT/'title-native.png')).astype(np.int32)
    hw=np.rint(native*7/255).astype(np.int32)*34
    expected=np.empty_like(hw)
    for channel,bits in enumerate((31,63,31)):
        expected[:,:,channel]=(hw[:,:,channel]>>(2 if channel==1 else 3))*255//bits
    core=np.asarray(Image.open(ROOT/'core-mask.png'))>0
    checks=[]
    for region in ('ntsc','pal'):
        path=INTRO/f'emulator-{region}'
        report=json.loads((path/'report.json').read_text())
        samples=[]
        for capture in report['titlecard']['captures']:
            actual=np.asarray(Image.open(path/(capture['file']+'.png')))
            mask=~core.copy()
            for p in capture['particles']:
                x,y=p['x'],p['y']
                mask[max(0,y-1):min(224,y+9),max(0,x-1):min(320,x+9)]=False
            diff=np.any(actual!=expected,axis=2)
            assert not np.any(diff&mask),(region,capture['file'],'non-core art changed')
            samples.append(actual[core])
        assert any(not np.array_equal(samples[0],sample) for sample in samples[1:]),region
        assert report['titlecard']['core_signatures']>=3
        checks.append(dict(region=region,non_core_art_mismatches=0,pulse_states=report['titlecard']['core_signatures'],captures=len(samples)))
    result=dict(passed=True,checks=checks,core_pixels=int(core.sum()),method='Exact RGB565-expanded native art outside reserved core inks and 12 particle sprites')
    (ROOT/'pixel-validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
if __name__=='__main__': main()
