# CutLang ADL Overlap Analyzer

## Building

Make sure `g++` (C++17), `bison` (3.x), `flex`, and `python3` are installed, then run `make` from the project root:

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
python3 Overlap_pipeline/adl_overlap_check.py *.adl --regions --html out.html
```

The binary `Overlap_pipeline/adl_to_json` is found automatically when the script runs from the same directory. If you move the binary, point to it with:

```bash
export ADL_TO_JSON=/path/to/adl_to_json
```
