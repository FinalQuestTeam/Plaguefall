from pathlib import Path
script=Path(__file__).resolve().parents[2]/'tools/test_campaign_stages_emulator.py'
source=script.read_text()
anchor="        initial=enter(node);stage_baselines[node]=initial;shot(d['id']+'-entry')"
replacement=anchor+'''
        isolate();pos(*d['start']);settle()
        buf=bytearray(stride);ex,ey=224,200
        struct.pack_into('>hhii',buf,0,ex,ey,ex<<6,ey<<6)
        struct.pack_into('>HHHHHH',buf,16,600,600,600,0,600,600)
        buf[30],buf[31],buf[42],buf[43],buf[44]=2,200,1,1,1
        write(enemy_addr,buf);run(2*fps)
        shot('reference-'+d['id']);print('CAPTURE',d['id'],flush=True)
        continue
'''
assert anchor in source
source=source.replace(anchor,replacement)
exec(compile(source,str(script),'exec'),{'__name__':'__main__','__file__':str(script)})
