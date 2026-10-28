#!/usr/bin/env python3
"""Check explicitly supplied BibTeX libraries with Biber; never rewrite inputs.

This is a syntax/identity preflight, not metadata or claim verification. Each
library must define the string macros it uses (apart from Biber's standard
macros). Citation resolution and the actual report build are separate checks.
"""

import argparse
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET


NAMESPACE = "{http://biblatex-biber.sourceforge.net/biblatexml}"


def check_bibliography(paths, timeout=30):
    """Return findings. Any Biber warning fails conservatively, including
    duplicate keys within a file, which Biber collapses in its XML output.
    Comparisons use exact parsed keys and stripped, nonempty shorthands.
    """
    if not paths:
        return ["Supply at least one explicit .bib path."]
    if not math.isfinite(timeout) or timeout <= 0:
        return ["Biber timeout must be finite and positive."]
    sources = [Path(path).resolve() for path in paths]
    findings = []
    for source in sources:
        if source.suffix.lower() != ".bib" or not source.is_file():
            findings.append(f"{source}: expected an existing .bib file")
    if findings:
        return findings
    biber = shutil.which("biber")
    if biber is None:
        return ["Biber executable not found on PATH; bibliography was not checked."]

    keys = {}
    shorthands = {}
    preferred_tmp = Path("/tmp/opencode")
    temp_root = preferred_tmp if preferred_tmp.is_dir() else None
    try:
        with tempfile.TemporaryDirectory(prefix="bibliography-", dir=temp_root) as directory:
            work = Path(directory)
            for index, source in enumerate(sources):
                # Safe filenames also prevent Biber from expanding input globs.
                staged = work / f"source-{index}.bib"
                output = work / f"parsed-{index}.xml"
                shutil.copyfile(source, staged)
                command = [
                    biber, "--tool", "--noconf", "--input-format=bibtex",
                    "--output-format=biblatexml", "--no-bltxml-schema",
                    "--decodecharsset=null",
                    f"--logfile={work / f'parse-{index}.blg'}",
                    f"--output-file={output}", str(staged),
                ]
                try:
                    result = subprocess.run(
                        command, cwd=work, capture_output=True, text=True,
                        encoding="utf-8", errors="replace", timeout=timeout,
                    )
                except subprocess.TimeoutExpired:
                    findings.append(f"{source}: Biber timed out after {timeout:g} seconds")
                    continue
                except OSError as error:
                    findings.append(f"{source}: could not run Biber: {error}")
                    continue
                diagnostics = (result.stdout + "\n" + result.stderr).replace(str(staged), str(source))
                warnings = [line for line in diagnostics.splitlines()
                            if re.match(r"^(?:WARN|ERROR|FATAL)\s+-", line)]
                if result.returncode or warnings:
                    detail = "\n".join(warnings) or diagnostics.strip() or "no diagnostic output"
                    findings.append(f"{source}: Biber failed preflight (exit {result.returncode}):\n{detail}")
                    continue
                try:
                    root = ET.parse(output).getroot()
                    if root.tag != NAMESPACE + "entries":
                        raise ValueError("unexpected XML root")
                    for entry in root.findall(NAMESPACE + "entry"):
                        key = entry.get("id")
                        if not key:
                            raise ValueError("entry without an id")
                        location = f"{source} (key {key!r})"
                        if key in keys:
                            findings.append(f"Duplicate key {key!r}: {keys[key]}; {location}")
                        else:
                            keys[key] = location
                        field = entry.find(NAMESPACE + "shorthand")
                        shorthand = "" if field is None else "".join(field.itertext()).strip()
                        if shorthand:
                            if shorthand in shorthands:
                                findings.append(
                                    f"Duplicate shorthand {shorthand!r}: "
                                    f"{shorthands[shorthand]}; {location}"
                                )
                            else:
                                shorthands[shorthand] = location
                except (OSError, ET.ParseError, ValueError) as error:
                    findings.append(f"{source}: invalid or missing Biber XML output: {error}")
    except OSError as error:
        findings.append(f"Bibliography temporary-file/input failure: {error}")
    return findings


def positive_seconds(value):
    seconds = float(value)
    if not math.isfinite(seconds) or seconds <= 0:
        raise argparse.ArgumentTypeError("must be finite and positive")
    return seconds


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", metavar="LIBRARY.bib", nargs="+", type=Path,
                        help="explicit local libraries; no directory scans")
    parser.add_argument("--timeout", type=positive_seconds, default=30,
                        help="Biber timeout in seconds per library (default: 30)")
    args = parser.parse_args(argv)
    findings = check_bibliography(args.paths, args.timeout)
    if findings:
        print("\n".join(findings), file=sys.stderr)
        return 1
    print(f"Bibliography preflight passed for {len(args.paths)} libraries. "
          "Metadata truth, claim support and report citations/build were not checked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
