# make          build/deck.pdf, then the request asserts
# make watch    rebuild build/deck.pdf on every save (latexmk; Ctrl-C stops)
# make notes    build/deck-notes.pdf, the presenter copy, if you use speaker notes
# make clean    remove build/
LATEX = lualatex -interaction=nonstopmode -halt-on-error -output-directory=build

all: build/deck.pdf
	python3 check_requests.py build/deck.pdf

build/deck.pdf: $(wildcard *.tex figures/* generated/*)
	mkdir -p build
	$(LATEX) deck.tex >/dev/null || { tail -30 build/deck.log; exit 1; }
	-biber --input-directory build --output-directory build deck >/dev/null
	$(LATEX) deck.tex >/dev/null && $(LATEX) deck.tex >/dev/null
	@grep -E "Overfull|LaTeX Warning|undefined" build/deck.log || echo "deck.pdf: log clean"

watch:
	latexmk -lualatex -pvc -interaction=nonstopmode -outdir=build deck.tex

notes:
	mkdir -p build
	for i in 1 2; do $(LATEX) -jobname=deck-notes '\def\withnotes{}\input{deck}' >/dev/null; done

clean:
	rm -rf build

.PHONY: all watch notes clean
