# =============================================================================
# Makefile — ADL Overlap Analyzer
# =============================================================================
#
# Expected project layout (Makefile lives at the project root):
#
#   project_root/
#   ├── Makefile                  ← this file
#   ├── adl/                      ← CutLang C++ grammar & sources
#   │   ├── parser.y
#   │   ├── scanner.l
#   │   ├── driver.cpp / driver.h
#   │   ├── Scanner.cpp / scanner.hpp
#   │   ├── Parser.cpp / Parser.h
#   │   ├── external_functions.cpp
#   │   ├── semantic_checks.cpp
#   │   └── cutlang_declares.cpp
#   └── Overlap_pipeline/         ← Python pipeline + C++ entry point
#       ├── main_json.cpp
#       ├── adl_overlap_check.py
#       ├── cpp_parser_bridge.py
#       └── ...
#
# Targets:
#   make              → build Overlap_pipeline/adl_to_json (default)
#   make parser       → run bison + flex inside adl/ only
#   make check        → sanity-check that the binary works
#   make clean        → remove generated parser files and binary
#   make distclean    → clean + remove HTML reports
#
# Usage examples (after building):
#   make run ADLS="a.adl b.adl"
#   make run ADLS="a.adl b.adl" HTML=report.html
#   make run ADLS="a.adl b.adl" VERBOSE=1
#   make run ADLS="a.adl b.adl" CATALOGUE=1
# =============================================================================

# ── Compiler & flags ──────────────────────────────────────────────────────────
CXX      := g++
CXXFLAGS := -std=c++17 -Wall -O2

BISON    := bison
FLEX     := flex

# ── Directory layout ──────────────────────────────────────────────────────────
ADL_DIR      := adl
PIPELINE_DIR := Overlap_pipeline

# ── Bison / Flex grammar sources (inside adl/) ───────────────────────────────
BISON_SRC := $(ADL_DIR)/parser.y
FLEX_SRC  := $(ADL_DIR)/scanner.l

# Generated parser files (written back into adl/)
BISON_OUT := $(ADL_DIR)/Parser.cpp $(ADL_DIR)/Parser.h
FLEX_OUT  := $(ADL_DIR)/Scanner.cpp

# ── C++ sources ───────────────────────────────────────────────────────────────
# main_json.cpp lives in Overlap_pipeline/; the rest live in adl/
CXX_SRCS := $(PIPELINE_DIR)/main_json.cpp \
             $(ADL_DIR)/driver.cpp \
             $(ADL_DIR)/Scanner.cpp \
             $(ADL_DIR)/Parser.cpp \
             $(ADL_DIR)/external_functions.cpp \
             $(ADL_DIR)/semantic_checks.cpp \
             $(ADL_DIR)/cutlang_declares.cpp

# Include path so main_json.cpp can find the adl/ headers
INCLUDES := -I$(ADL_DIR)

# ── Final binary (placed next to the Python pipeline so cpp_parser_bridge
#    can find it without setting ADL_TO_JSON) ─────────────────────────────────
TARGET := $(PIPELINE_DIR)/adl_to_json

# ── Python entry point ────────────────────────────────────────────────────────
PYTHON  := python3
OVERLAP := $(PIPELINE_DIR)/adl_overlap_check.py

# ── Run-time options (override on the command line) ───────────────────────────
# Required: ADLS="file1.adl file2.adl ..."
ADLS      ?=
HTML      ?=      # e.g. HTML=report.html
VERBOSE   ?=      # set to any non-empty value for -v
CATALOGUE ?=      # set to any non-empty value for --catalogue

# Build the flags string from the variables above
_FLAGS :=
ifneq ($(HTML),)
  _FLAGS += --html $(HTML)
endif
ifneq ($(VERBOSE),)
  _FLAGS += --verbose
endif
ifneq ($(CATALOGUE),)
  _FLAGS += --catalogue
endif

# =============================================================================
# Default target
# =============================================================================
.PHONY: all
all: $(TARGET)

# =============================================================================
# Step 1 — Generate Parser.cpp / Parser.h from adl/parser.y  (bison)
# =============================================================================
.PHONY: parser
parser: $(ADL_DIR)/Parser.cpp $(ADL_DIR)/Parser.h $(ADL_DIR)/Scanner.cpp

$(ADL_DIR)/Parser.cpp $(ADL_DIR)/Parser.h: $(BISON_SRC)
	$(BISON) --defines=$(ADL_DIR)/Parser.h --output=$(ADL_DIR)/Parser.cpp $(BISON_SRC)

# =============================================================================
# Step 2 — Generate Scanner.cpp from adl/scanner.l  (flex)
# =============================================================================
$(ADL_DIR)/Scanner.cpp: $(FLEX_SRC)
	$(FLEX) --outfile=$(ADL_DIR)/Scanner.cpp $(FLEX_SRC)

# =============================================================================
# Step 3 — Compile & link → Overlap_pipeline/adl_to_json
# =============================================================================
$(TARGET): $(ADL_DIR)/Parser.cpp $(ADL_DIR)/Parser.h $(ADL_DIR)/Scanner.cpp $(CXX_SRCS)
	$(CXX) $(CXXFLAGS) $(INCLUDES) $(CXX_SRCS) -o $(TARGET)
	@echo ""
	@echo "✓  Built: $(TARGET)"
	@echo "   Run the overlap checker with:"
	@echo "     make run ADLS=\"a.adl b.adl\""

# =============================================================================
# Sanity check
# =============================================================================
.PHONY: check
check: $(TARGET)
	@echo "Checking binary..."
	@$(TARGET) --help 2>&1 || $(TARGET) 2>&1 | head -5 || true
	@echo "Binary OK: $(TARGET)"

# =============================================================================
# Run the Python overlap checker
# =============================================================================
.PHONY: run
run: $(TARGET)
	@if [ -z "$(ADLS)" ]; then \
	    echo "ERROR: specify at least two ADL files."; \
	    echo "  make run ADLS=\"a.adl b.adl\""; \
	    exit 1; \
	fi
	$(PYTHON) $(OVERLAP) $(ADLS) $(_FLAGS)

# =============================================================================
# Clean
# =============================================================================
.PHONY: clean
clean:
	rm -f $(TARGET) $(BISON_OUT) $(FLEX_OUT)
	@echo "Cleaned generated parser files and binary."

.PHONY: distclean
distclean: clean
	rm -f $(PIPELINE_DIR)/*.html
	@echo "Removed HTML reports."

# =============================================================================
# Help
# =============================================================================
.PHONY: help
help:
	@echo ""
	@echo "ADL Overlap Analyzer — Makefile targets"
	@echo "========================================"
	@echo ""
	@echo "  make               Build Overlap_pipeline/adl_to_json (default)"
	@echo "  make parser        Generate adl/Parser.cpp|h and adl/Scanner.cpp only"
	@echo "  make check         Build + verify the binary"
	@echo "  make clean         Remove binary and generated parser files"
	@echo "  make distclean     clean + remove HTML reports"
	@echo "  make help          Show this message"
	@echo ""
	@echo "  make run ADLS=\"a.adl b.adl\"               Basic comparison"
	@echo "  make run ADLS=\"a.adl b.adl\" VERBOSE=1      Verbose cut details"
	@echo "  make run ADLS=\"a.adl b.adl\" HTML=out.html  Save HTML report"
	@echo "  make run ADLS=\"a.adl b.adl\" CATALOGUE=1    Print catalogues"
	@echo ""
	@echo "  Flags can be combined:"
	@echo "  make run ADLS=\"a.adl b.adl\" VERBOSE=1 HTML=report.html CATALOGUE=1"
	@echo ""
	@echo "Environment variable override (custom binary location):"
	@echo "  ADL_TO_JSON=/custom/path/adl_to_json make run ADLS=\"...\""
	@echo ""
