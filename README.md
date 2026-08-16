# Molecular Dynamics Simulation Workshop

Source for the workshop website, published with MkDocs Material to GitHub Pages.

**Live site:** https://cbtml.github.io/md-workshop/

---

## How this repo works

There is one deliberate wrinkle worth understanding before you edit anything.

The Markdown in `docs/` contains **placeholders**, not HTML:

```
{{INTERACTIVE: rmsd-explainer}}
{{VIDEO: sso7d-400k}}
```

`build.py` copies `docs/` to `build/`, expands those placeholders into real
embeds, and MkDocs builds from `build/`. So:

- **`docs/` is what you edit.** It stays readable and the placeholders survive.
- **`build/` is disposable.** It is regenerated every time and is gitignored.
- **`videos.yaml` is the single source of truth for videos** — change a caption
  or swap a file there, never in the Markdown.

---

## Working on it locally

```bash
pip install -r requirements.txt

python build.py        # expand placeholders into build/
mkdocs serve           # live preview at http://127.0.0.1:8000
```

`mkdocs serve` watches `build/`, so after editing a page in `docs/` you need to
re-run `python build.py` to see the change. For prose-only edits it is often
easier to edit `build/` while previewing, then copy the change back into `docs/`.

To check for problems without writing anything:

```bash
python build.py --check
```

It reports missing video files, missing widget files, and manifest entries that
are incomplete. The GitHub Action runs the same check, so fixing these locally
saves a failed deploy.

---

## Adding content

### A new video

1. Put `{{VIDEO: some-id}}` where it belongs in the Markdown.
2. Add a matching entry to `videos.yaml`.
3. If it is your own clip, drop the file in `docs/assets/video/`.

Use descriptive ids, never numbers — inserting one later would renumber
everything after it.

**Which source to use.** Anything you did not make yourself should be
`source: youtube`, embedding the original. That keeps attribution with whoever
produced it and keeps the repo small. Only self-host clips you rendered.

**Write captions as instructions.** "A protein folding" teaches nothing. "Watch
the two helices pack against each other before the loops settle" does.

### A new interactive widget

1. Put the self-contained HTML file in `docs/interactive/`.
2. Reference it with `{{INTERACTIVE: filename-without-extension}}`.
3. Add its height to `WIDGET_HEIGHT` in `build.py` if the default 800px is wrong.

### A new chapter

1. Add `docs/05-whatever.md` starting with a single `#` heading.
2. Add it to the `nav:` list in `mkdocs.yml`.
3. Update the prev/next links at the foot of the neighbouring pages.

---

## Deploying

Pushing to `main` triggers `.github/workflows/deploy.yml`, which installs
dependencies, expands placeholders, builds, and publishes.

**One-time setup:** in the repository under **Settings → Pages**, set the source
to **GitHub Actions**. Without this the workflow runs but nothing is published.

---

## Keeping the repo small

GitHub Pages has a soft limit around 1 GB and 100 GB of bandwidth per month.
Videos are the only realistic way to breach either.

Compress anything you self-host before committing:

```bash
ffmpeg -i input.mp4 -vf "scale=960:-2" -c:v libx264 -crf 28 \
       -preset slow -an -movflags +faststart output.mp4
```

Aim for under 5 MB per clip. Note that some licences — CC BY-NC-ND in
particular — forbid modifying the file, so check before re-encoding anything
that is not yours. If a licence prevents compression, host the file as
downloaded or link to the original instead.

---

## Structure

```
docs/                   the editable source
  index.md              landing page and instructor's note
  01-basics.md          what an MD simulation is
  02-scope-…            what MD can and cannot do
  03-running-…          the GROMACS pipeline
  04-analysis.md        analysing a trajectory
  interactive/          self-contained HTML explainers
  assets/video/         self-hosted video
  images/               figures
  javascripts/          scroll-triggered video autoplay
  stylesheets/          widget and video styling
videos.yaml             the video manifest
build.py                placeholder expansion
mkdocs.yml              site config and navigation
```

---

## Still to do

- Chapter 5: advanced sampling
- Chapter 6: machine learning and AI in MD
- Section 3.2.3 needs prose around the PDB anatomy widget
- `videos.yaml`: the `md-simulations` entry needs a YouTube id, and
  `protein-folding` needs its credit filled in
