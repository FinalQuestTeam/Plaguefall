"""Build a portable, offline HTML atlas from capture_stage_atlas.py output."""
from pathlib import Path
import base64
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib
import json

GAME = Path(__file__).resolve().parents[1]
ROOT = GAME.parent
CAPTURES = GAME / 'art/stage-atlas-01-16/captures'
PREVIOUS = GAME / 'art/stage-atlas-01-14/captures'
DEST = ROOT / 'output/mapa-fases-01-16.html'
LEGACY_DEST = ROOT / 'output/mapa-fases-01-14.html'
# Preserve the URL already opened by the user, with the complete atlas.
OPENED_ATLAS = Path(__file__).with_name('stage_atlas_template.html')

# Descriptive labels, based on the current LevelDefs and campaign dialogue.
INFO = {
    '1': ('Até o último sair', 'Pátio da igreja', 'Sobreviva por 90 segundos enquanto a comunidade evacua.', 'Usar uma bomba leva à igreja destruída (2B); preservá-la leva à 2A.'),
    '2A': ('A igreja de pé', 'Igreja preservada', 'Elimine 15 inimigos.', 'Rota após preservar a igreja na fase 1.'),
    '2B': ('Entre os escombros', 'Igreja destruída', 'Elimine 15 inimigos entre os destroços.', 'Rota após usar uma bomba na fase 1. Os escombros alteram a circulação.'),
    '3': ('Abram caminho', 'Rua até o galpão', 'Chegue ao galpão no final da rua.', 'Nesta inspeção, a igreja está preservada. A mesma fase também herda a igreja destruída da rota 2B.'),
    '4': ('Um teto para a noite', 'Galpão de abrigo', 'Elimine 20 inimigos.', 'O galpão será o abrigo da comunidade durante a noite.'),
    '5': ('O sinal da Santa', 'Pátio do comunicador', 'Proteja a Santa e seu comunicador por 120 segundos.', 'Sucesso leva à 6A; a queda da Santa leva à 6B.'),
    '6A': ('Todos embarcaram', 'Esgotos · resgate completo', 'Escolte Dinorah até a base e abra dois portões com quatro tiros em cada um.', 'Rota de evacuação completa. Não há válvulas de pressão.'),
    '6B': ('O peso das perdas', 'Esgotos · resgate parcial', 'Escolte Dinorah, alivie a pressão em duas válvulas e abra os dois portões.', 'Rota após a interrupção do sinal da Santa.'),
    '7': ('O que ainda resta', 'Feira do Último Chão', 'Recupere cinco cargas e leve uma por vez ao depósito.', 'A saída dos esgotos fica no bueiro da feira.'),
    '8': ('Cortar o chamado', 'Base comprometida', 'Destrua os três emissores que chamam reforços.', 'Mesmo cenário urbano da fase 7; o objetivo agora é eliminar alvos prioritários.'),
    '9': ('Rumo à fábrica', 'Rua industrial', 'Atravesse a rua industrial e alcance a fábrica.', 'Caminhões e oficinas formam passagens de contorno.'),
    '10': ('Romper os ninhos', 'Fábrica infestada', 'Destrua os dez grupos de ovos.', 'Matar insetos não avança este objetivo.'),
    '11': ('Reaquecer a fábrica', 'Fábrica · válvulas', 'Opere seis válvulas; cada uma exige 2,5 segundos de trabalho.', 'A fábrica reaparece com tijolos azuis. Os ovos destruídos não voltam.'),
    '12': ('Até o sindicato', 'Corredor de serviço', 'Escolte Dinorah até a sala do sindicato.', 'Dinorah viva leva à 13A; sua morte com Damião vivo leva à 13B.'),
    '13A': ('Velhos piquetes', 'Sindicato STE · Dinorah viva', 'Elimine 30 inimigos.', 'Dinorah trabalha no compartimento ao norte e prepara o apoio final.'),
    '13B': ('Um lugar vazio', 'Sindicato STE · Dinorah morta', 'Elimine 45 inimigos.', 'Mesma sala e colisões; o memorial substitui a presença de Dinorah.'),
    '14': ('Ligar os geradores', 'Estaleiro · rede de energia', 'Religue cinco geradores: permaneça 10 segundos sem atirar diante de cada painel.', 'Cada estação tem sua barra. Ao se afastar, perde 10% do trabalho a cada segundo; estações concluídas permanecem ligadas. Dinorah viva nesta captura.'),
    '15': ('Manter o sinal', 'Estaleiro · defesa do rádio', 'Proteja o rádio e a antena por 120 segundos.', 'Os cinco geradores já começam ligados. A primeira ignição ocorre após 40 segundos de defesa. O combate e o relógio param durante o breve foco nos motores. Dinorah viva nesta captura.'),
    '16': ('O Escorpião', 'Estaleiro · confronto final', 'Derrote o Escorpião.', 'A sala, as colisões, a antena e os cinco geradores ligados são os mesmos da 15. Os interiores das duas janelas dos motores mudam. O chefe mantém sua IA original.'),
}
MANIFESTS = {
    '3': 'phase03-three-segments-v1/integration-v1/manifest.json',
    '6A': 'phase06-three-segments-v1/integration-v1/6A/manifest.json',
    '6B': 'phase06-three-segments-v1/integration-v1/6B/manifest.json',
    '7': 'phase07-urban-v2/manifest.json', '8': 'phase08-urban-v1/manifest.json',
    '9': 'phase09-three-segments-v1/manifest.json', '10': 'phase10-factory-v2/manifest.json',
    '11': 'phase11-factory-v2/manifest.json', '12': 'phase12-three-segments-v1/manifest.json',
    '13A': 'phase13-union-v2/manifest.json', '13B': 'phase13-union-v2/manifest.json',
    '14': 'phase14-shipyard-v2/manifest.json',
    '15': 'phase15-shipyard-v2/manifest.json',
    '16': 'phase16-shipyard-v2/manifest.json',
}

NEWS = {
    '13A': [
        'O piso quadriculado agora chega à base dos armários e do balcão; foram removidas faixas e marcas do piso antigo.',
        'Sombras de contato e sombras projetadas acompanham o piso novo, preservando móveis, bancos e a origem dos ladrilhos.',
        'Paleta, dimensões, colisões, câmera e objetivo de 30 inimigos preservados. Dinorah continua no compartimento norte.',
    ],
    '13B': [
        'Mesma correção de piso e sombras da 13A, junto aos armários e ao balcão.',
        'Piso contínuo sob os bancos, sem resíduos do material antigo junto aos móveis.',
        'Paleta, dimensões e colisões preservadas. O memorial permanece e a meta continua em 45 inimigos.',
    ],
    '14': [
        'Piso de placas de ferro com rebites, limites repetíveis e rede de conexões entre cinco geradores, console e bateria.',
        'Geradores nativos de 48 × 48 px, seis estados e cinco barras de progresso independentes.',
        'Ativação exige 10 segundos sem disparar. Cada segundo afastado remove um segundo de trabalho; disparar perto interrompe o avanço sem apagar o que já foi feito.',
        'Pausa congela trabalho e perda de progresso. Geradores concluídos não perdem energia.',
    ],
    '15': [
        'Nova fase no atlas: sala de 512 × 576 px com cinco geradores ligados e rádio compacto de 48 × 64 px, com seis estados.',
        'Só a base de 32 × 16 px bloqueia movimento e recebe dano nas quatro faces externas. O mastro elevado permite passagem e não recebe dano.',
        'Damião passa atrás do mastro e à frente da base. O rádio tem barra de vida junto à base e pisca localmente ao sofrer dano.',
        'Defesa de 120 segundos. A ignição muda os interiores dos motores; o foco breve nos motores congela movimento, inimigos, dano e relógio.',
        'Derrota e reinício restauram o cenário anterior à ignição e o tempo completo.',
    ],
    '16': [
        'Nova fase no atlas: confronto com o Escorpião na mesma sala e com os equipamentos ligados da fase 15.',
        'As duas janelas superiores recebem interiores nativos de 144 × 80 px em 16 cores; o restante do cenário permanece igual ao da 15.',
        'Colisões, piso, rádio compacto, bateria, conexões e cinco geradores são compartilhados com a 15. O mastro continua livre para passagem.',
        'O chefe conserva vida e IA originais. Os ensaios registrados confirmam dano, derrota do chefe e reaparecimento após reiniciar.',
    ],
}

EVIDENCE = {
    '13A': [('13A-view-32-160','Piso junto aos armários'),('13A-view-280-160','Balcão e sombras no piso'),('13A-pause','Pausa após travessia'),('13A-objective-complete','Objetivo de 30 inimigos')],
    '13B': [('13B-view-32-160','Piso junto aos armários'),('13B-view-280-160','Balcão e memorial'),('13B-pause','Pausa após travessia'),('13B-objective-complete','Objetivo de 45 inimigos')],
    '14': [('14-progress-working','Operando uma estação'),('14-progress-almost-full','Barra antes de completar'),('14-progress-decay','Perda de progresso ao se afastar'),('14-progress-independent-bars','Barras independentes'),('14-generator-pose-0','Gerador · estado 1'),('14-generator-pose-1','Gerador · estado 2'),('14-generator-pose-2','Gerador · estado 3'),('14-generator-pose-3','Gerador · estado 4'),('14-generator-pose-4','Gerador · estado 5'),('14-generator-pose-5','Gerador · estado 6'),('14-complete','Cinco geradores concluídos')],
    '15': [('15-entry','Rádio e equipamentos ligados'),('15-radio-pose-0','Rádio · estado 1'),('15-radio-pose-1','Rádio · estado 2'),('15-radio-pose-2','Rádio · estado 3'),('15-radio-pose-3','Rádio · estado 4'),('15-radio-pose-4','Rádio · estado 5'),('15-radio-pose-5','Rádio · estado 6'),('15-pass-through-mast','Passagem livre sob o mastro'),('15-core-behind','Damião atrás do mastro'),('15-core-front','Damião à frente da base'),('15-core-damaged','Rádio recebendo dano'),('15-ignition-focus','Ignição · foco nos motores'),('15-ignition-return','Ignição · retorno à defesa'),('15-complete','Defesa de 120 segundos concluída')],
    '16': [('16-boss-entry','Escorpião na entrada'),('16-entry','Sala e equipamentos compartilhados'),('16-controller-traversal','Travessia da sala'),('16-pause','Pausa do confronto'),('16-boss-combat-result','Escorpião derrotado')],
}


def embedded_image(path):
    return 'data:image/png;base64,' + base64.b64encode(path.read_bytes()).decode()


def data_image(name):
    return embedded_image(CAPTURES / name)


def evidence_for(label, rom_hash):
    if label not in EVIDENCE:
        return [], []
    root = CAPTURES.parent / 'validation'
    chapter='13' if label in ('13A','13B') else label
    prefix = 'phase'+chapter+'-'
    checks = []
    for region in ('ntsc', 'pal'):
        folder = root / (prefix + region)
        report = json.loads((folder / 'report.json').read_text())
        assert report['passed'] and report['romSHA256'] == rom_hash, ('Evidence must match captured ROM', label, region)
        details=report['checks']
        if chapter=='13':details={k:v for k,v in details.items() if k.startswith(label+'-')}
        loads = details.get(label+'-moving-five-enemy-six-plus-six-shot-load') or details.get('moving-four-enemy-four-plus-four-shot-load') or details.get('moving-three-enemy-four-plus-four-shot-load') or details.get('controller-boss-combat')
        if not isinstance(loads,list):loads=[loads] if loads else []
        rates=[v['game_fps'] for v in loads]
        checks.append(dict(region=region.upper(),passed=True,rom_sha256=report['romSHA256'],
            check_count=len(details),camera_views=24 if chapter=='13' else 28,
            fps_min=min(rates) if rates else None,fps_max=max(rates) if rates else None,
            origin='Functional emulator test run for this atlas revision on the captured ROM',
            report=str((folder/'report.json').relative_to(ROOT))))
    folder=root/(prefix+'ntsc')
    images=[dict(title=title,image=embedded_image(folder/(name+'.png')),
        source=str((folder/(name+'.png')).relative_to(ROOT))) for name,title in EVIDENCE[label]]
    return checks, images


def main():
    report = json.loads((CAPTURES / 'report.json').read_text())
    assert report['passed'] and [s['id'] for s in report['stages']] == list(INFO)
    rom = Path(report['buildDirectory']) / 'rom.bin'
    assert report['romSHA256'] == hashlib.sha256(rom.read_bytes()).hexdigest(), 'Recapture the current ROM first'
    stages = []
    previous_report = json.loads((PREVIOUS/'report.json').read_text())
    previous_stages = {s['id']:s for s in previous_report['stages']}
    for source in report['stages']:
        s = json.loads(json.dumps(source));label = s['id']
        s['title'], s['place'], s['objective'], s['note'] = INFO[label]
        s['map'] = data_image(s['map']);s['entry'] = data_image(s['entry'])
        for view in s['views']:view['image'] = data_image(view['file'])
        old=previous_stages.get(label)
        if old:
            visual_changed=(PREVIOUS/old['map']).read_bytes() != (CAPTURES/source['map']).read_bytes()
            geometry_changed=old['geometry'] != s['geometry']
            s['revision']=dict(status='updated' if visual_changed or geometry_changed or label in NEWS else 'recaptured',
                visual_changed=visual_changed,geometry_changed=geometry_changed,
                previous_dimensions=[old['geometry']['width'],old['geometry']['height']],
                previous_bounds=old['geometry']['bounds'],previous_obstacles=len(old['geometry']['solids']))
            if visual_changed and not geometry_changed:s['previous_map']=embedded_image(PREVIOUS/old['map'])
        else:s['revision']=dict(status='new',visual_changed=True,geometry_changed=True)
        s['news']=list(NEWS.get(label,[]))
        if not s['news']:
            s['news'].append('Novas capturas feitas nesta revisão. '+('Cenário ou colisões mudaram em relação ao atlas anterior.' if s['revision']['visual_changed'] or s['revision']['geometry_changed'] else 'Cenário base, paleta e geometria estática coincidem com o atlas anterior.'))
        s['validation'],s['evidence']=evidence_for(label,report['romSHA256'])
        s['points'] = [{'x':s['geometry']['start'][0]+8, 'y':s['geometry']['start'][1]+8, 'label':'Entrada de Damião', 'kind':'start'}]
        s['route'] = []
        if label in MANIFESTS:
            manifest = json.loads((GAME / 'art' / MANIFESTS[label]).read_text())
            # Overlay metadata is accepted only for this exact current geometry.
            assert manifest['bounds'] == s['geometry']['bounds'], label
            assert [r[:4] for r in manifest['solids']] == [r[:4] for r in s['geometry']['solids']], label
            native_files={
                '13A':('phase13-union-v2/native/tiles.bin','phase13-union-v2/native/alive.bin'),
                '13B':('phase13-union-v2/native/tiles.bin','phase13-union-v2/native/dead.bin'),
                '14':('phase14-shipyard-v2/native/tiles.bin','phase14-shipyard-v2/native/map.bin'),
                '15':('phase15-shipyard-v2/native/normal-tiles.bin','phase15-shipyard-v2/native/normal-map.bin'),
                '16':('phase16-shipyard-v2/native/tiles.bin','phase16-shipyard-v2/native/map.bin'),
            }.get(label)
            if native_files:
                for file,fingerprint in zip(native_files,['tiles_sha256','map_sha256']):
                    assert hashlib.sha256((GAME/'art'/file).read_bytes()).hexdigest()==s['source'][fingerprint], ('Art differs from captured ROM',label,file)
            s['route'] = manifest.get('points', [])
            memory=manifest.get('memory',{})
            s['total_tiles']=memory.get('total_resident_tiles')
            s['memory']=memory
            for key, name, kind in [('cargo','Carga','cargo'),('targets','Emissor','target'),('eggs','Grupo de ovos','eggs'),('valves','Válvula','valve'),('machines','Gerador','power')]:
                values = manifest.get(key, [])
                if not isinstance(values, list):continue
                for i, (x,y) in enumerate(values):s['points'].append(dict(x=x,y=y,label=f'{name} {i+1}',kind=kind))
            for i, rect in enumerate(manifest.get('gates', [])):
                x,y,w,h=rect;s['points'].append(dict(x=x+w/2,y=y+h/2,label=f'Portão {i+1}',kind='gate',rect=rect))
            for key,name in [('depot','Depósito'),('exit','Saída / destino')]:
                if key in manifest:
                    v=manifest[key];x,y=v[:2]
                    if len(v)==4:x+=v[2]/2;y+=v[3]/2
                    s['points'].append(dict(x=x,y=y,label=name,kind='exit'))
            if 'radio' in manifest:
                x,y=manifest['radio'];s['points'].append(dict(x=x,y=y,label='Rádio / antena protegida',kind='target'))
            if label in ('14','15','16'):
                s['points'].extend([dict(x=256,y=288,label='Console / antena',kind='power'),dict(x=256,y=464,label='Bateria central',kind='power')])
            if label=='16':
                for i,(x1,y1,x2,y2) in enumerate(manifest['window']['positions']):
                    s['points'].append(dict(x=(x1+x2)/2,y=(y1+y2)/2,label=f'Janela de motor {i+1}',kind='power'))
        if label == '5':s['points'].append(dict(x=196,y=280,label='Santa / comunicador',kind='target'))
        stages.append(s)
    payload = dict(stages=stages, rom=report['romSHA256'], region=report['region'],
        generated=datetime.now(ZoneInfo('America/Sao_Paulo')).strftime('%d/%m/%Y às %H:%M'),
        method=report['method'], view_count=sum(len(s['views'])+1 for s in stages))
    payload['comparison']=dict(previous_rom=previous_report['romSHA256'],
        added=[s['id'] for s in stages if s['revision']['status']=='new'],
        updated=[s['id'] for s in stages if s['revision']['status']=='updated'],
        base_unchanged=[s['id'] for s in stages if s['revision']['status']=='recaptured'])
    payload['evidence_count']=sum(len(s['evidence']) for s in stages)
    template = Path(__file__).with_name('stage_atlas_template.html.in').read_text()
    DEST.parent.mkdir(parents=True,exist_ok=True)
    rendered = template.replace('__ATLAS_DATA__', json.dumps(payload,ensure_ascii=False).replace('</','<\\/'))
    DEST.write_text(rendered)
    LEGACY_DEST.write_text(rendered)
    OPENED_ATLAS.write_text(rendered)
    summary = dict(html=str(DEST.relative_to(ROOT)), rom_sha256=payload['rom'], phases=16, variants=len(stages),
        emulator_stills=payload['view_count'], self_contained=True, bytes=DEST.stat().st_size,
        evidence_stills=payload['evidence_count'],comparison=payload['comparison'],
        functional_reports_checked=len({v['report'] for s in stages for v in s['validation']}),
        captures='captures/report.json', generated=payload['generated'])
    (CAPTURES.parent / 'manifest.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(summary,ensure_ascii=False))


if __name__ == '__main__':
    main()
