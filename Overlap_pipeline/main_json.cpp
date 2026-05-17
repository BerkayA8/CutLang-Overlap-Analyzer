/**
 * main_json.cpp
 * =============
 * ADL → JSON AST exporter.
 *
 * Parses an ADL file using the CutLang Bison/Flex grammar and emits
 * the AST as JSON on stdout, for consumption by the Python overlap
 * pipeline (cpp_parser_bridge.py → ir_extractor.py).
 *
 * Usage:
 *   ./adl_to_json  analysis.adl  > ast.json
 *
 * Build:
 * 
 *  g++ -std=c++17 main_json.cpp ../adl/driver.cpp ../adl/Scanner.cpp \
 *      ../adl/Parser.cpp ../adl/external_functions.cpp ../adl/semantic_checks.cpp \
 *      ../adl/cutlang_declares.cpp -o adl_to_json
 */

#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include "../adl/scanner.hpp"
#include "../adl/Parser.h"
#include "../adl/driver.h"

// ── JSON escape helper ────────────────────────────────────────────────────────
static std::string json_str(const std::string& s) {
    std::string out = "\"";
    for (char c : s) {
        switch (c) {
            case '"':  out += "\\\""; break;
            case '\\': out += "\\\\"; break;
            case '\n': out += "\\n";  break;
            case '\r': out += "\\r";  break;
            case '\t': out += "\\t";  break;
            default:   out += c;
        }
    }
    return out + "\"";
}

// ── AST node → JSON ───────────────────────────────────────────────────────────
static std::string expr_to_json(adl::Expr* e, int depth = 0);

static std::string indent(int d) { return std::string(d * 2, ' '); }

static std::string expr_to_json(adl::Expr* e, int depth) {
    if (!e) return "null";
    std::string tok = e->getToken();
    std::string i   = indent(depth);
    std::string i1  = indent(depth + 1);

    // ── NumNode ───────────────────────────────────────────────────────────────
    if (tok == "INT" || tok == "REAL") {
        return "{\n" + i1 + "\"tok\": " + json_str(tok) + ",\n" +
               i1 + "\"value\": " + e->getId() + "\n" + i + "}";
    }

    // ── VarNode ───────────────────────────────────────────────────────────────
    if (tok == "ID") {
        auto* vn = static_cast<adl::VarNode*>(e);
        std::string acc = "[";
        for (int j = 0; j < (int)vn->getAccessor().size(); j++) {
            if (j) acc += ",";
            acc += std::to_string(vn->getAccessor()[j]);
        }
        acc += "]";
        return "{\n" + i1 + "\"tok\": \"ID\",\n" +
               i1 + "\"id\": " + json_str(vn->getId()) + ",\n" +
               i1 + "\"alias\": " + json_str(vn->getAlias()) + ",\n" +
               i1 + "\"dotop\": " + json_str(vn->getDotOp()) + ",\n" +
               i1 + "\"accessor\": " + acc + ",\n" +
               i1 + "\"type\": " + json_str(vn->getType()) + "\n" + i + "}";
    }

    // ── BinNode ───────────────────────────────────────────────────────────────
    if (tok == "COMPAREOP" || tok == "LOGICOP" ||
        tok == "EXPROP"    || tok == "FACTOROP") {
        auto* bn = static_cast<adl::BinNode*>(e);
        return "{\n" + i1 + "\"tok\": " + json_str(tok) + ",\n" +
               i1 + "\"op\": " + json_str(bn->getOp()) + ",\n" +
               i1 + "\"lhs\": " + expr_to_json(bn->getLHS(), depth + 1) + ",\n" +
               i1 + "\"rhs\": " + expr_to_json(bn->getRHS(), depth + 1) + "\n" + i + "}";
    }

    // ── FunctionNode ──────────────────────────────────────────────────────────
    if (tok == "FUNCTION") {
        auto* fn = static_cast<adl::FunctionNode*>(e);
        std::string params = "[\n";
        auto pv = fn->getParams();
        for (size_t j = 0; j < pv.size(); j++) {
            params += i1 + "  " + expr_to_json(pv[j], depth + 2);
            if (j + 1 < pv.size()) params += ",";
            params += "\n";
        }
        params += i1 + "]";
        return "{\n" + i1 + "\"tok\": \"FUNCTION\",\n" +
               i1 + "\"id\": " + json_str(fn->getId()) + ",\n" +
               i1 + "\"params\": " + params + "\n" + i + "}";
    }

    // ── DefineNode ────────────────────────────────────────────────────────────
    if (tok == "DEFINE") {
        auto* dn = static_cast<adl::DefineNode*>(e);
        return "{\n" + i1 + "\"tok\": \"DEFINE\",\n" +
               i1 + "\"id\": " + json_str(dn->getId()) + ",\n" +
               i1 + "\"body\": " + expr_to_json(dn->getBody(), depth + 1) + "\n" + i + "}";
    }

    // ── astObjectNode ─────────────────────────────────────────────────────────
    if (tok == "OBJECT" || tok == "TRIGGER") {
        auto* on = static_cast<adl::astObjectNode*>(e);
        std::string stmts = "[\n";
        auto sv = on->getStatements();
        for (size_t j = 0; j < sv.size(); j++) {
            stmts += i1 + "  " + expr_to_json(sv[j], depth + 2);
            if (j + 1 < sv.size()) stmts += ",";
            stmts += "\n";
        }
        stmts += i1 + "]";
        return "{\n" + i1 + "\"tok\": " + json_str(tok) + ",\n" +
               i1 + "\"id\": " + json_str(on->getId()) + ",\n" +
               i1 + "\"statements\": " + stmts + "\n" + i + "}";
    }

    // ── RegionNode ────────────────────────────────────────────────────────────
    if (tok == "REGION" || tok == "HISTOLIST") {
        auto* rn = static_cast<adl::RegionNode*>(e);
        std::string stmts = "[\n";
        auto sv = rn->getStatements();
        for (size_t j = 0; j < sv.size(); j++) {
            stmts += i1 + "  " + expr_to_json(sv[j], depth + 2);
            if (j + 1 < sv.size()) stmts += ",";
            stmts += "\n";
        }
        stmts += i1 + "]";
        return "{\n" + i1 + "\"tok\": " + json_str(tok) + ",\n" +
               i1 + "\"id\": " + json_str(rn->getId()) + ",\n" +
               i1 + "\"statements\": " + stmts + "\n" + i + "}";
    }

    // ── CommandNode ───────────────────────────────────────────────────────────
    if (tok == "SELECT" || tok == "REJECT" || tok == "TAKE" ||
        tok == "BIN"    || tok == "WEIGHT" || tok == "TRIGGER" ||
        tok == "CMD"    || tok == "COMMAND") {
        auto* cn = static_cast<adl::CommandNode*>(e);
        return "{\n" + i1 + "\"tok\": " + json_str(tok) + ",\n" +
               i1 + "\"condition\": " + expr_to_json(cn->getCondition(), depth + 1) + "\n" + i + "}";
    }

    // ── ITENode ───────────────────────────────────────────────────────────────
    if (tok == "ITE") {
        auto* ite = static_cast<adl::ITENode*>(e);
        return "{\n" + i1 + "\"tok\": \"ITE\",\n" +
               i1 + "\"condition\": " + expr_to_json(ite->getCondition(), depth + 1) + ",\n" +
               i1 + "\"then\": " + expr_to_json(ite->getThenBranch(), depth + 1) + ",\n" +
               i1 + "\"else\": " + expr_to_json(ite->getElseBranch(), depth + 1) + "\n" + i + "}";
    }

    // ── HistoNode ─────────────────────────────────────────────────────────────
    if (tok == "HISTO") {
        auto* hn = static_cast<adl::HistoNode*>(e);
        return "{\n" + i1 + "\"tok\": \"HISTO\",\n" +
               i1 + "\"id\": " + json_str(hn->getId()) + ",\n" +
               i1 + "\"desc\": " + json_str(hn->getDescription()) + "\n" + i + "}";
    }

    // ── fallback ──────────────────────────────────────────────────────────────
    return "{\n" + i1 + "\"tok\": " + json_str(tok) + ",\n" +
           i1 + "\"id\": " + json_str(e->getId()) + "\n" + i + "}";
}

// ── main ──────────────────────────────────────────────────────────────────────
int main(int argc, char** argv) {
    if (argc < 2) {
        std::cerr << "Usage: adl_to_json <adl_file>\n";
        return 1;
    }

    std::ifstream fin(argv[1]);
    if (!fin.good()) {
        std::cerr << "Cannot open: " << argv[1] << "\n";
        return 1;
    }

    // Suppress diagnostic output from the driver to stderr
    // (parse() and setTables() print to std::cout — redirect that to stderr)
    std::streambuf* saved_cout = std::cout.rdbuf(std::cerr.rdbuf());

    adl::Driver drv(&fin);
    int res = drv.parse();
    if (res == 0) res = drv.setTables();

    // Restore stdout for JSON output
    std::cout.rdbuf(saved_cout);

    if (res != 0) {
        std::cerr << "Parse/setTables failed for: " << argv[1] << "\n";
        return 1;
    }

    // Emit JSON array of AST nodes
    std::cout << "[\n";
    auto& ast = drv.ast;
    for (size_t i = 0; i < ast.size(); i++) {
        std::cout << "  " << expr_to_json(ast[i], 1);
        if (i + 1 < ast.size()) std::cout << ",";
        std::cout << "\n";
    }
    std::cout << "]\n";

    return 0;
}
