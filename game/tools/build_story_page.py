#!/usr/bin/env python3
"""Build an offline, self-contained reader from Plaguefall's narrative sources."""
import base64
import hashlib
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GAME = ROOT / "game"
OUTPUT = ROOT / "output/historia-completa.html"
COMPAT_OUTPUT = Path(__file__).with_name("story_page_template.html")
SOURCES = [
    "src/levels/story.c",
    "src/system/video/screens/intro_shots.h",
    "src/system/video/screens/ending_shots.h",
    "src/system/video/screens/ending.h",
    "src/system/video/screens/result.c",
    "art/intro-monologo-v2/export.json",
    "art/ending-slides-v1/storyboard.json",
    "doc/historia/tratamento-proposto.md",
]
SPEAKERS = {"P_DAMIAO": "Damião", "P_COMANDO": "Comando / Padre",
            "P_DINORAH": "Dinorah", "P_ESCORPIAO": "Escorpião"}


def read(path):
    return (GAME / path).read_text(encoding="utf-8")


def c_strings(text):
    return [json.loads(s) for s in re.findall(r'"(?:[^"\\]|\\.)*"', text)]


def caption_texts(source):
    block = source.split("CAPTIONS[", 1)[1].split("};", 1)[0]
    return [" ".join(s for s in c_strings(m) if s)
            for m in re.findall(r'\{\s*\d+,\s*\d+,\s*\d+,(?:\s*\d+,)?\s*\{(.*?)\}', block)]


def image_uri(path):
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()


def inline(text):
    text = html.escape(text)
    def link(match):
        label, target = match.groups()
        if not re.match(r'^(?:https?://|#)', target):
            target = "../game/doc/historia/" + target
        return f'<a href="{target}">{label}</a>'
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', link, text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    return re.sub(r'`([^`]+)`', r'<code>\1</code>', text)


def markdown(source):
    """Render the source's headings, prose, quotes, tables, lists and code."""
    lines, out, i = source.splitlines(), [], 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.startswith("```"):
            chunk = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                chunk.append(lines[i])
                i += 1
            out.append('<pre>' + html.escape("\n".join(chunk)) + '</pre>')
        elif line.startswith("#"):
            level = min(len(line) - len(line.lstrip("#")) + 1, 6)
            out.append(f'<h{level}>' + inline(line.lstrip("# ")) + f'</h{level}>')
        elif line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [s.strip() for s in lines[i].strip("|").split("|")]
                if not all(re.fullmatch(r'[:\- ]+', s) for s in cells):
                    tag = "th" if not rows else "td"
                    rows.append('<tr>' + ''.join(f'<{tag}>{inline(s)}</{tag}>' for s in cells) + '</tr>')
                i += 1
            out.append('<div class="table-wrap"><table>' + ''.join(rows) + '</table></div>')
            continue
        elif line.startswith(">"):
            chunk = []
            while i < len(lines) and lines[i].startswith(">"):
                chunk.append(inline(lines[i].lstrip("> ")) or '<br>')
                i += 1
            out.append('<blockquote>' + '<br>'.join(chunk) + '</blockquote>')
            continue
        elif re.match(r'^(?:- |\d+\. )', line):
            ordered = bool(re.match(r'^\d+\.', line))
            pattern = r'^\d+\. ' if ordered else r'^- '
            tag, items = ("ol" if ordered else "ul"), []
            while i < len(lines) and re.match(pattern, lines[i]):
                items.append('<li>' + inline(re.sub(pattern, '', lines[i])) + '</li>')
                i += 1
            out.append(f'<{tag}>' + ''.join(items) + f'</{tag}>')
            continue
        else:
            chunk = [line]
            while i + 1 < len(lines) and lines[i + 1].strip() and not re.match(r'^(?:#|\||>|```|- |\d+\. )', lines[i + 1]):
                i += 1
                chunk.append(lines[i])
            out.append('<p>' + inline(' '.join(chunk)) + '</p>')
        i += 1
    return '\n'.join(out)


def build_data():
    story = read(SOURCES[0])
    arrays = {}
    for name, body in re.findall(r'static const StoryLine (\w+)\[\]=\{(.*?)\};', story, re.S):
        arrays[name] = [{"speaker": SPEAKERS[speaker], "text": json.loads(text)}
                        for speaker, text in re.findall(r'LINE\((P_\w+),("(?:[^"\\]|\\.)*")\)', body)]
    assert sum(map(len, arrays.values())) == len(re.findall(r'LINE\(P_', story)) == 67
    treatment = read(SOURCES[-1])
    phases = re.findall(r'### Fase (\d+[AB]?) (.*?)\n(.*?)(?=\n### Fase |\n## |\Z)', treatment, re.S)
    meta = {n: (title, body) for n, title, body in phases}
    assert len(meta) == 19
    entries = re.findall(r'ENTRY\(N_(\w+),(ANTES|DEPOIS),(\w+)\)', story)
    groups = []
    for phase, moment, name in entries:
        title, body = meta[phase]
        rule = {}
        if phase in ("2A", "2B"):
            rule = {"church": "intact" if phase.endswith("A") else "ruined"}
        elif phase in ("6A", "6B"):
            rule = {"rescue": "all" if phase.endswith("A") else "partial"}
        elif phase in ("13A", "13B"):
            rule = {"dinorah": "alive" if phase.endswith("A") else "dead"}
        elif int(phase) >= 14:
            rule = {"dinorah": "dead" if name.endswith("morta") else "alive"}
        # Local/objective are editorial context from the literary treatment.
        context = re.search(r'\*\*Local:\*\* (.*?)(?:\n\n|$)', body, re.S).group(0).strip()
        groups.append({"id": name, "section": "fase-" + re.match(r'\d+', phase)[0],
                       "phase": phase, "title": title, "when": moment,
                       "rule": rule, "context": markdown(context), "lines": arrays[name]})
    assert len(groups) == 24 and {g['id'] for g in groups} == set(arrays)
    opening = json.loads(read(SOURCES[5]))["scenes"]
    intro_text = caption_texts(read(SOURCES[1]))
    assert [c['text'] for shot in opening for c in shot['captions']] == intro_text
    elapsed = 0
    for shot in opening:
        shot['image'] = image_uri(GAME / f"art/intro-monologo-v2/frames/{shot['shot']:02}.png")
        # Export metadata stores offsets relative to each shot, not the film.
        for caption in shot['captions']:
            caption['start_seconds'] += elapsed
        elapsed += shot['seconds']
    assert elapsed == 101
    ending = json.loads(read(SOURCES[6]))['shots']
    end_text = caption_texts(read(SOURCES[2]))
    assert [c['text'].upper() for shot in ending for c in shot['captions']] == end_text
    end_rules = [('church', 'intact'), ('church', 'ruined'), ('rescue', 'all'),
                 ('rescue', 'partial'), ('dinorah', 'alive'), ('dinorah', 'dead')]
    for i, shot in enumerate(ending):
        shot['rule'] = dict([end_rules[i]])
        shot['image'] = image_uri(GAME / f'art/ending-slides-v1/frames/{i:02}.png')
        for caption in shot['captions']:
            caption['text'] = caption['text'].upper()
    victory_block = read(SOURCES[4]).split('else if(resultKind==3)\n    {', 1)[1].split('menu(', 1)[0]
    victory = re.findall(r'line\(("(?:[^"\\]|\\.)*"),\d+,\d+\)', victory_block)
    assert len(victory) == 5
    docs = []
    for index, block in enumerate(re.split(r'(?=^## )', treatment, flags=re.M)):
        if not block.strip():
            continue
        title = block.splitlines()[0].lstrip('# ')
        docs.append({"id": f"documento-{index}", "title": title, "html": markdown(block), "raw": block})
    return {"opening": opening, "groups": groups, "ending": ending,
            "victory": [json.loads(s) for s in victory], "documents": docs,
            "premise": markdown(treatment.split('## Premissa e personagens\n', 1)[1].split('\n## ', 1)[0]),
            "sources": [{"path": s, "sha256": hashlib.sha256((GAME / s).read_bytes()).hexdigest()}
                        for s in SOURCES],
            "counts": {"opening": len(intro_text), "dialogue": sum(map(len, arrays.values())),
                       "ending": len(end_text), "stages": 19, "versions": 8}}


def main():
    data = build_data()
    template = (Path(__file__).with_name('story_page_template.html.in')).read_text(encoding='utf-8')
    assert template.count('<!-- STORY_DATA -->') == 1, 'Missing or duplicate story data slot'
    payload = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    page = template.replace('<!-- STORY_DATA -->', payload)
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(page, encoding='utf-8')
    # Keep the previously opened HTML path usable too. The actual source is
    # now .html.in, so opening either HTML entry renders the complete reader.
    # Adjust source links only; a <base> would also redirect chapter anchors.
    COMPAT_OUTPUT.write_text(page.replace('../game/', '../'), encoding='utf-8')
    print(json.dumps({"file": str(OUTPUT), "compatible_entry": str(COMPAT_OUTPUT),
                      "bytes": OUTPUT.stat().st_size, **data['counts']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
