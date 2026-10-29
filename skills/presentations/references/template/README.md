# Deck and poster templates

`deck.tex` is a 16:9 Beamer talk on the metropolis theme with the Catppuccin
Latte palette in `colors.tex`. It shows the structure
[../deck-production.md](../deck-production.md) describes: title, question
frame, sections, a claim frame with a reveal, a source line and a link to its
backup frame, the take-away, references, a questions frame and the backup
appendix. `poster.tex` is an A0 portrait poster in blocks with the same
palette (beamerposter).

Put logos, institute and author in your copy; they are personal settings.
Point `\addbibresource` at your shared bibliography library.

Build with pdfLaTeX and Biber:

```bash
pdflatex deck && biber deck && pdflatex deck && pdflatex deck
N='\def\withnotes{}\input{deck}'
pdflatex -jobname=deck-notes "$N" && biber deck-notes && pdflatex -jobname=deck-notes "$N" && pdflatex -jobname=deck-notes "$N"
```

`deck-notes.pdf` is the presenter copy: every page twice as wide, the slide on
the left and its `\note{}` on the right, for a second screen or a PDF
presenter tool. `../../scripts/export_pptx.py` reads its right halves as the
speaker notes of the PowerPoint copy.

metropolis warns that it prefers XeLaTeX or LuaLaTeX for the Fira fonts; under
pdfLaTeX it falls back to Computer Modern Sans, which is what the template is
tested with. The template wraps metropolis's title page in a box of the text
height, because the theme's full-paper-height box is otherwise reported as an
overfull `\vbox` on every build.
