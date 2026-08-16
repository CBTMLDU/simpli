#!/usr/bin/env python3
"""
Expand {{VIDEO: id}} and {{INTERACTIVE: id}} placeholders in docs/*.md
into real HTML, using videos.yaml as the source of truth for videos.

Run before `mkdocs build`. Safe to run repeatedly — it edits copies in
place, so keep your placeholders in the .md files and let this do the rest.

    python build.py            # expand in place
    python build.py --check    # report problems without writing
"""
import os, re, sys, glob

try:
    import yaml
except ImportError:
    sys.exit('pyyaml is required:  pip install pyyaml')

SRC      = 'docs'      # the editable source — placeholders live here
DOCS     = 'build'     # what mkdocs actually reads; regenerated every time
MANIFEST = 'videos.yaml'
CHECK    = '--check' in sys.argv

# widget id -> file in docs/interactive/, and how tall the iframe should be
# The file-listing widgets cap their code area at a fraction of the iframe
# height and scroll it internally, so the annotation card is always visible
# without the reader having to scroll inside the frame first.
WIDGET_HEIGHT = {
    'pdb-anatomy':                680,
    'gro-top-anatomy':            900,
    'mdp-anatomy':                660,
    'minim-mdp-anatomy':          680,
    'nvt-mdp-anatomy':            700,
    'npt-mdp-anatomy':            700,
    'md-mdp-anatomy':             700,
    'rmsd-explainer':             720,
    'rg-explainer':               740,
    'polarizability-explainer':   700,
}
DEFAULT_HEIGHT = 700

# Refresh build/ from docs/ so the source pages keep their placeholders
import shutil
if not CHECK:
    if os.path.isdir(DOCS):
        shutil.rmtree(DOCS)
    shutil.copytree(SRC, DOCS)
elif not os.path.isdir(DOCS):
    shutil.copytree(SRC, DOCS)

videos = {}
if os.path.exists(MANIFEST):
    videos = yaml.safe_load(open(MANIFEST)) or {}

problems = []


def widget_html(wid):
    path = f'interactive/{wid}.html'
    if not os.path.exists(f'{DOCS}/{path}'):
        problems.append(f'missing widget file: docs/{path}')
    h = WIDGET_HEIGHT.get(wid, DEFAULT_HEIGHT)
    return (f'<iframe class="widget-frame" src="../{path}" '
            f'height="{h}" loading="lazy" title="{wid}"></iframe>')


def video_html(vid):
    v = videos.get(vid)
    if not v:
        problems.append(f'no entry in {MANIFEST} for video: {vid}')
        return f'<!-- MISSING VIDEO ENTRY: {vid} -->'

    caption = (v.get('caption') or '').strip()
    credit  = (v.get('credit') or '').strip()
    url     = (v.get('credit_url') or '').strip()

    if credit and url:
        credit_html = f'<span class="credit">Source: <a href="{url}">{credit}</a></span>'
    elif credit:
        credit_html = f'<span class="credit">Source: {credit}</span>'
    else:
        credit_html = ''

    src = (v.get('source') or '').lower()

    if src == 'youtube':
        yid = (v.get('id') or '').strip()
        if not yid:
            problems.append(f'youtube entry "{vid}" has no id')
            return f'<!-- VIDEO {vid}: no youtube id -->'
        start = f'&start={v["start"]}' if v.get('start') else ''
        media = (f'<iframe src="https://www.youtube-nocookie.com/embed/{yid}'
                 f'?rel=0{start}" height="420" loading="lazy" '
                 f'frameborder="0" allowfullscreen title="{vid}"></iframe>')

    elif src == 'local':
        f = (v.get('file') or '').strip()
        if not f:
            problems.append(f'local entry "{vid}" has no file')
            return f'<!-- VIDEO {vid}: no file -->'
        if not os.path.exists(f'{DOCS}/assets/video/{f}'):
            problems.append(f'missing video file: docs/assets/video/{f}')
        poster = v.get('poster')
        # a poster is optional; without one we preload metadata so the first
        # frame is shown rather than a blank rectangle
        pattr = f' poster="../assets/video/{poster}"' if poster else ''
        preload = 'none' if poster else 'metadata'
        media = (f'<video class="scroll-play" muted loop playsinline '
                 f'preload="{preload}"{pattr}>\n'
                 f'      <source src="../assets/video/{f}" type="video/mp4">\n'
                 f'      Your browser does not support the video tag.\n'
                 f'    </video>')
    else:
        problems.append(f'entry "{vid}" has unknown source: {src!r}')
        return f'<!-- VIDEO {vid}: unknown source -->'

    return (f'<figure class="workshop-video" markdown="0">\n'
            f'    {media}\n'
            f'    <figcaption>{caption}{credit_html}</figcaption>\n'
            f'</figure>')


PAT = re.compile(r'\{\{\s*(VIDEO|INTERACTIVE)\s*:\s*([A-Za-z0-9\-\._]+)\s*\}\}')

total = 0
for path in sorted(glob.glob(f'{DOCS}/*.md')):
    text = open(path).read()

    def repl(m):
        global total
        total += 1
        kind, ident = m.group(1).upper(), m.group(2)
        return widget_html(ident) if kind == 'INTERACTIVE' else video_html(ident)

    new = PAT.sub(repl, text)
    if new != text:
        open(path, 'w').write(new)

print(f'{total} placeholder(s) expanded across {len(glob.glob(f"{DOCS}/*.md"))} pages')

if problems:
    print('\nProblems:')
    for p in sorted(set(problems)):
        print('  -', p)
    if CHECK:
        sys.exit(1)
else:
    print('No problems found.')
