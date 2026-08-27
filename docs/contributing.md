# How to contribute

This site is open to corrections and additions from anyone in the lab.
The source lives at [CBTMLDU/simpli](https://github.com/CBTMLDU/simpli) —
*simulating bits and pieces of life*.

## Small fixes

Every page has a pencil icon at the top right. It opens that page's source
on GitHub, where you can edit and save directly in the browser. Good for
typos, broken links and clarifications.

## Larger changes

Clone the repository, then work locally:

```bash
python build.py && mkdocs build --strict
```

Fix anything it reports before you push. The same command runs on every
push, and a warning there stops the site from updating.

## House rules

- **Edit `docs/`, never `build/`.** `build/` is regenerated from `docs/`
  every time and your changes there will be erased.
- **Write plainly.** The audience is biochemistry students with little
  computational background. Prefer a longer plain sentence to a short
  technical one.
- **New chapter?** Add the file to `docs/`, then add a matching line to
  `nav:` in `mkdocs.yml`. A page missing from `nav:` fails the build.
- **Videos and widgets** go in as placeholders, not as raw HTML —
  `build.py` expands them. Videos are declared in `videos.yaml`; widgets
  are standalone HTML files in `docs/interactive/`.
- **New widget?** Follow the existing visual system — the shared palette,
  Archivo and JetBrains Mono, and a dark annotation card at the foot that
  responds to hover, tap and keyboard focus. Then add its height to
  `WIDGET_HEIGHT` in `build.py`.
- **Test on a phone.** Much of the audience will read this on one.

## Questions

Open an issue on the repository, or contact the lab directly.
