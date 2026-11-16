# Deck and poster templates

`deck.tex` is a 16:9 Beamer talk on the metropolis theme with the Catppuccin
Latte palette in `colors.tex`. It shows the structure
[../deck-production.md](../deck-production.md) describes: title, question
frame, sections, a claim frame with a reveal, a commented equation in a box,
a source line and a link to its backup frame, the take-away, numbered
references, a questions frame, the backup appendix and a blank last frame to
draw on. `poster.tex` is an A0 portrait poster in blocks with the same
palette (beamerposter).

Put logos, institute and author in your copy; they are personal settings.
Use a white version of the logo on the coloured title page. `colors.tex`
defines institution presets, each a main and an accent colour from the
palette, the nearest palette colours to the institution's: `tum` (blue and
sky, the default) and `mpp` (teal and green). Choose one with
`\usepreset{mpp}` after `\input{colors.tex}`, or define your own with
`\definepreset{name}{main}{accent}`. Point `\addbibresource` at your shared
bibliography library.

Build with `make` (LuaLaTeX and Biber, output in `build/`): it builds
`build/deck.pdf` and runs `check_requests.py`, which holds one check per
request the presenter made, so a request once met stays met. `make watch`
rebuilds on every save for a presenter who edits the source by hand. The
poster builds by hand:

```bash
lualatex poster && biber poster && lualatex poster && lualatex poster
```

Speaker notes are optional. For a presenter who uses them, keep a `\note{}`
on each content frame and run `make notes`: `build/deck-notes.pdf` is the
presenter copy, every page twice as wide, the slide on the left and its note
on the right, for a second screen or a PDF presenter tool.
`../../scripts/export_pptx.py --notes` reads its right halves as the speaker
notes of the PowerPoint copy. Otherwise delete the `\note{}` lines; the
rehearsal pack ([../deck-production.md](../deck-production.md#the-rehearsal-pack))
carries what the presenter says.

LuaLaTeX gives metropolis its Fira Sans (TeX Live's `fira` package); pdfLaTeX
falls back to Computer Modern Sans. Mathematics stays in Computer Modern
(`professionalfonts`); siunitx sets numbers in the text font. The template
wraps metropolis's title page in a box of the text height, because the theme's
full-paper-height box is otherwise reported as an overfull `\vbox` on every
build.
