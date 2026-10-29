#!/usr/bin/env python3
"""Check or format explicitly named LaTeX sources with latexindent rules.

Checks, per run: duplicate bibliography keys and shorthands across the shared
library, `\\addbibresource` targets that do not resolve to a file in that
library, hand-written `thebibliography` blocks, and formatting drift against the
latexindent config. `--quantities` also flags likely raw quantities.

The quantity scan reports likely omissions, not semantic proof of compliance.
Review identifiers, source pinpoints and algebra separately.
"""
import argparse
import os
from pathlib import Path
import re
import subprocess
import tempfile


def check_library(bib_dir):
    keys = {}
    labels = {}
    failures = 0
    for path in sorted(bib_dir.rglob('*.bib')):
        text = path.read_text()
        for key in re.findall(r'^@\w+\{([^,]+),', text, re.M):
            if key in keys:
                print('DUPLICATE BIBLIOGRAPHY KEY', key, keys[key], path)
                failures += 1
            keys[key] = path
        for label in re.findall(r'^\s*shorthand\s*=\s*\{([^}]+)\}', text, re.M):
            if label in labels:
                print('DUPLICATE SHORTHAND', label, labels[label], path)
                failures += 1
            labels[label] = path
    return failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='apply source formatting')
    parser.add_argument('--quantities', action='store_true', help='also flag likely raw quantities')
    parser.add_argument('--root', type=Path, default=Path.cwd(),
                        help='directory the sources must lie under (default: current directory)')
    parser.add_argument('--bib-dir', type=Path,
                        help='shared bibliography library (default: <root>/bib if it exists); '
                             '\\addbibresource targets must resolve to files inside it. '
                             'Without a library they only need to exist.')
    parser.add_argument('--latexindent-config', type=Path,
                        help='latexindent settings file (default: <root>/latexindent.yaml '
                             'if it exists, else latexindent defaults)')
    parser.add_argument('sources', nargs='+', type=Path)
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    bib_dir = args.bib_dir or (root/'bib' if (root/'bib').is_dir() else None)
    if bib_dir is not None:
        bib_dir = bib_dir.resolve(strict=True)
    config = args.latexindent_config or root/'latexindent.yaml'
    config = config.resolve(strict=True) if config.is_file() else None
    if args.latexindent_config and config is None:
        parser.error(f'latexindent config not found: {args.latexindent_config}')
    failures = check_library(bib_dir) if bib_dir else 0
    for source in args.sources:
        source = source.resolve(strict=True)
        source.relative_to(root)
        if source.suffix != '.tex':
            parser.error(f'expected a .tex source: {source}')
        name = source.relative_to(root)
        before = source.read_text()
        for resource in re.findall(r'\\addbibresource\{([^}]+)\}', before):
            target = (source.parent/resource).resolve()
            if not target.is_file() or (bib_dir and not target.is_relative_to(bib_dir)):
                print('INVALID SHARED RESOURCE', name, resource)
                failures += 1
        if r'\begin{thebibliography}' in before:
            print('HANDWRITTEN BIBLIOGRAPHY', name)
            failures += 1
        with tempfile.TemporaryDirectory(prefix='latexindent-') as scratch:
            command = ['latexindent', '-m', '-c=' + scratch]
            if config:
                command.append('-l=' + str(config))
            result = subprocess.run(
                command + [str(source)], env={**os.environ, 'HOME': scratch},
                text=True, capture_output=True, check=True)
        after = result.stdout
        if not after.startswith(before.splitlines()[0]):
            raise RuntimeError(f'Unexpected formatter output for {source}: {after[:200]}')
        if after != before:
            if args.write:
                source.write_text(after)
                print('formatted', name)
            else:
                print('NEEDS FORMAT', name)
                failures += 1
        if args.quantities:
            body = re.sub(r'\\begin\{(lstlisting|verbatim|minted|tikzpicture)\}.*?\\end\{\1\}', '', after, flags=re.S)
            body = body.split(r'\begin{document}', 1)[-1]
            for number, line in enumerate(body.splitlines(), 1):
                if re.search(r'(?<![\w.])\d+(?:\.\d+)?\\%|\d(?:~|\\,| )+(?:GeV|TeV|MeV|pb|fb)\b|\\mathrm\{(?:GeV|TeV|MeV|pb|fb)\}|-\\(?:SI|num)\{-', line):
                    print(f'REVIEW QUANTITY {name} body:{number}: {line.strip()}')
                    failures += 1
    raise SystemExit(bool(failures))


if __name__ == '__main__':
    main()
