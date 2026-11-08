# CutLang ADL Overlap Analyzer

## Building

Make sure `g++` (C++17), `bison` (3.x), `flex`, and `python3` (3.12+) are installed, then run `make` from the project root:

```bash
make
```

`make` runs three steps automatically:

1. `bison adl/parser.y` → `adl/Parser.cpp`, `adl/Parser.h`
2. `flex adl/scanner.l` → `adl/Scanner.cpp`
3. `g++ -std=c++17 -Iadl ...` → `Overlap_pipeline/adl_to_json`

Verify the build:

```bash
make check
```

To regenerate only the parser files without recompiling:

```bash
make parser
```

---

## Running

All options are passed through `make run`. At least two `.adl` files are required.

```bash
# Basic comparison
make run ADLS="analysis_A.adl analysis_B.adl"

# Three or more files (every pair is compared)
make run ADLS="a.adl b.adl c.adl"

# Save an HTML report
make run ADLS="a.adl b.adl" HTML=report.html

# Verbose terminal output (per-variable cut details)
make run ADLS="a.adl b.adl" VERBOSE=1

# Print the OverlapObject catalogue for each analysis
make run ADLS="a.adl b.adl" CATALOGUE=1

# Combine flags
make run ADLS="a.adl b.adl" VERBOSE=1 HTML=report.html CATALOGUE=1

# Wildcard expansion
make run ADLS="analyses/*.adl" HTML=full_report.html
```

### Running the Python script directly

If you prefer to bypass `make run`:

```bash
python3 Overlap_pipeline/adl_overlap_check.py a.adl b.adl
python3 Overlap_pipeline/adl_overlap_check.py a.adl b.adl --html report.html
python3 Overlap_pipeline/adl_overlap_check.py a.adl b.adl --verbose --catalogue
python3 Overlap_pipeline/adl_overlap_check.py *.adl --html out.html
```

The binary `Overlap_pipeline/adl_to_json` is found automatically when the script runs from the same directory. If you move the binary, point to it with:

```bash
export ADL_TO_JSON=/path/to/adl_to_json
```

---

## Example: self-comparison of published ATLAS analyses

These examples use ADL files from the [ADL4Reinterpretation](https://github.com/ADL4HEP/ADL4Reinterpretation) repository. Each analysis is compared **with itself**: the same file is passed twice, so every signal region in the analysis is checked against every other signal region of that same analysis. This shows which regions are disjoint, which overlap, and which are nested (SUBSET / SUPERSET). Every region compared with itself should come out EQUAL, which is a useful sanity check.

| Analysis | Title | arXiv | Lumi (fb⁻¹) |
|---|---|---|---|
| ATLAS-SUSY-2015-06 | Squarks and gluinos, jets + missing transverse momentum | [1605.03814](https://arxiv.org/abs/1605.03814) | 3.2 |
| ATLAS-SUSY-2016-07 | Squarks and gluinos, jets + missing transverse momentum | [1712.02332](https://arxiv.org/abs/1712.02332) | 36.1 |
| ATLAS-SUSY-2018-09 | Squarks and gluinos, same-sign leptons + jets | [1909.08457](https://arxiv.org/abs/1909.08457) | 139 |
| ATLAS-SUSY-2018-22 | Squarks and gluinos, jets + missing transverse momentum (BDT regions not included) | [2010.14293](https://arxiv.org/abs/2010.14293) | 139 |

### 1. Get the ADL files

Clone the repository into the project root (next to the `Makefile`):

```bash
git clone https://github.com/ADL4HEP/ADL4Reinterpretation.git
```

The files used below are:

```
ADL4Reinterpretation/ATLAS-SUSY-2015-06/ATLAS-SUSY-2015-06_Delphes.adl
ADL4Reinterpretation/ATLAS-SUSY-2016-07/ATLAS-SUSY-2016-07_Delphes.adl
ADL4Reinterpretation/ATLAS-SUSY-2018-09/ATLAS-SUSY-2018-09_Delphes.adl
ADL4Reinterpretation/ATLAS-SUSY-2018-22/ATLAS-SUSY-2018-22_Delphes.adl
```

### 2. Build the parser

```bash
make
```

### 3. Run each self-comparison

Each command compares one analysis with itself and writes its own HTML report.

**ATLAS-SUSY-2015-06**

```bash
make run ADLS="ADL4Reinterpretation/ATLAS-SUSY-2015-06/ATLAS-SUSY-2015-06_Delphes.adl \
               ADL4Reinterpretation/ATLAS-SUSY-2015-06/ATLAS-SUSY-2015-06_Delphes.adl" \
         HTML=ATLAS-SUSY-2015-06_self.html
```

**ATLAS-SUSY-2016-07**

```bash
make run ADLS="ADL4Reinterpretation/ATLAS-SUSY-2016-07/ATLAS-SUSY-2016-07_Delphes.adl \
               ADL4Reinterpretation/ATLAS-SUSY-2016-07/ATLAS-SUSY-2016-07_Delphes.adl" \
         HTML=ATLAS-SUSY-2016-07_self.html
```

**ATLAS-SUSY-2018-09**

```bash
make run ADLS="ADL4Reinterpretation/ATLAS-SUSY-2018-09/ATLAS-SUSY-2018-09_Delphes.adl \
               ADL4Reinterpretation/ATLAS-SUSY-2018-09/ATLAS-SUSY-2018-09_Delphes.adl" \
         HTML=ATLAS-SUSY-2018-09_self.html
```

**ATLAS-SUSY-2018-22**

```bash
make run ADLS="ADL4Reinterpretation/ATLAS-SUSY-2018-22/ATLAS-SUSY-2018-22_Delphes.adl \
               ADL4Reinterpretation/ATLAS-SUSY-2018-22/ATLAS-SUSY-2018-22_Delphes.adl" \
         HTML=ATLAS-SUSY-2018-22_self.html
```

Add `VERBOSE=1` to see the per-variable cut details in the terminal, or `CATALOGUE=1` to print the object catalogue of the analysis.

### Running all four at once

```bash
for ID in ATLAS-SUSY-2015-06 ATLAS-SUSY-2016-07 ATLAS-SUSY-2018-09 ATLAS-SUSY-2018-22; do
    F="ADL4Reinterpretation/${ID}/${ID}_Delphes.adl"
    make run ADLS="$F $F" HTML="${ID}_self.html"
done
```

Or with the Python script directly:

```bash
for ID in ATLAS-SUSY-2015-06 ATLAS-SUSY-2016-07 ATLAS-SUSY-2018-09 ATLAS-SUSY-2018-22; do
    F="ADL4Reinterpretation/${ID}/${ID}_Delphes.adl"
    python3 Overlap_pipeline/adl_overlap_check.py "$F" "$F" --html "${ID}_self.html"
done
```

Each run produces one `<ID>_self.html` report in the project root.