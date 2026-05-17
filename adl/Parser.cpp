// A Bison parser, made by GNU Bison 3.8.2.

// Skeleton implementation for Bison LALR(1) parsers in C++

// Copyright (C) 2002-2015, 2018-2021 Free Software Foundation, Inc.

// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.

// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.

// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

// As a special exception, you may create a larger work that contains
// part or all of the Bison parser skeleton and distribute that work
// under terms of your choice, so long as that work isn't itself a
// parser generator using the skeleton or a modified version thereof
// as a parser skeleton.  Alternatively, if you modify or redistribute
// the parser skeleton itself, you may (at your option) remove this
// special exception, which will cause the skeleton and the resulting
// Bison output files to be licensed under the GNU General Public
// License without this special exception.

// This special exception was added by the Free Software Foundation in
// version 2.2 of Bison.

// DO NOT RELY ON FEATURES THAT ARE NOT DOCUMENTED in the manual,
// especially those whose name start with YY_ or yy_.  They are
// private implementation details that can be changed or removed.

// "%code top" blocks.
#line 25 "parser.y"

  #include <iostream>
  #include "scanner.hpp"
  #include "Parser.h"
  #include "driver.h"

namespace adl {
  typedef std::vector<Expr*> ExprVector;
  ExprVector lists;
  ExprVector paramlist;
  ExprVector histoParamList;
  ExprVector histoBinsLists;

  std::vector<int> intLists;
  std::vector<double> doubleLists;

  int cutcount;
  int counter = 0;
  int incrementCounter() { counter += 2; return counter; }
}

  static adl::Parser::symbol_type yylex(adl::Scanner &scanner, adl::Driver &driver) {
         return scanner.adl_yylex();
  }
  // extern FILE* adl::Scanner::yyin;

#line 66 "Parser.cpp"




#include "Parser.h"




#ifndef YY_
# if defined YYENABLE_NLS && YYENABLE_NLS
#  if ENABLE_NLS
#   include <libintl.h> // FIXME: INFRINGES ON USER NAME SPACE.
#   define YY_(msgid) dgettext ("bison-runtime", msgid)
#  endif
# endif
# ifndef YY_
#  define YY_(msgid) msgid
# endif
#endif


// Whether we are compiled with exception support.
#ifndef YY_EXCEPTIONS
# if defined __GNUC__ && !defined __EXCEPTIONS
#  define YY_EXCEPTIONS 0
# else
#  define YY_EXCEPTIONS 1
# endif
#endif

#define YYRHSLOC(Rhs, K) ((Rhs)[K].location)
/* YYLLOC_DEFAULT -- Set CURRENT to span from RHS[1] to RHS[N].
   If N is 0, then set CURRENT to the empty location which ends
   the previous symbol: RHS[0] (always defined).  */

# ifndef YYLLOC_DEFAULT
#  define YYLLOC_DEFAULT(Current, Rhs, N)                               \
    do                                                                  \
      if (N)                                                            \
        {                                                               \
          (Current).begin  = YYRHSLOC (Rhs, 1).begin;                   \
          (Current).end    = YYRHSLOC (Rhs, N).end;                     \
        }                                                               \
      else                                                              \
        {                                                               \
          (Current).begin = (Current).end = YYRHSLOC (Rhs, 0).end;      \
        }                                                               \
    while (false)
# endif


// Enable debugging if requested.
#if YYDEBUG

// A pseudo ostream that takes yydebug_ into account.
# define YYCDEBUG if (yydebug_) (*yycdebug_)

# define YY_SYMBOL_PRINT(Title, Symbol)         \
  do {                                          \
    if (yydebug_)                               \
    {                                           \
      *yycdebug_ << Title << ' ';               \
      yy_print_ (*yycdebug_, Symbol);           \
      *yycdebug_ << '\n';                       \
    }                                           \
  } while (false)

# define YY_REDUCE_PRINT(Rule)          \
  do {                                  \
    if (yydebug_)                       \
      yy_reduce_print_ (Rule);          \
  } while (false)

# define YY_STACK_PRINT()               \
  do {                                  \
    if (yydebug_)                       \
      yy_stack_print_ ();                \
  } while (false)

#else // !YYDEBUG

# define YYCDEBUG if (false) std::cerr
# define YY_SYMBOL_PRINT(Title, Symbol)  YY_USE (Symbol)
# define YY_REDUCE_PRINT(Rule)           static_cast<void> (0)
# define YY_STACK_PRINT()                static_cast<void> (0)

#endif // !YYDEBUG

#define yyerrok         (yyerrstatus_ = 0)
#define yyclearin       (yyla.clear ())

#define YYACCEPT        goto yyacceptlab
#define YYABORT         goto yyabortlab
#define YYERROR         goto yyerrorlab
#define YYRECOVERING()  (!!yyerrstatus_)

#line 10 "parser.y"
namespace  adl  {
#line 166 "Parser.cpp"

  /// Build a parser object.
   Parser :: Parser  (adl::Scanner &scanner_yyarg, adl::Driver &driver_yyarg)
#if YYDEBUG
    : yydebug_ (false),
      yycdebug_ (&std::cerr),
#else
    :
#endif
      scanner (scanner_yyarg),
      driver (driver_yyarg)
  {}

   Parser ::~ Parser  ()
  {}

   Parser ::syntax_error::~syntax_error () YY_NOEXCEPT YY_NOTHROW
  {}

  /*---------.
  | symbol.  |
  `---------*/



  // by_state.
   Parser ::by_state::by_state () YY_NOEXCEPT
    : state (empty_state)
  {}

   Parser ::by_state::by_state (const by_state& that) YY_NOEXCEPT
    : state (that.state)
  {}

  void
   Parser ::by_state::clear () YY_NOEXCEPT
  {
    state = empty_state;
  }

  void
   Parser ::by_state::move (by_state& that)
  {
    state = that.state;
    that.clear ();
  }

   Parser ::by_state::by_state (state_type s) YY_NOEXCEPT
    : state (s)
  {}

   Parser ::symbol_kind_type
   Parser ::by_state::kind () const YY_NOEXCEPT
  {
    if (state == empty_state)
      return symbol_kind::S_YYEMPTY;
    else
      return YY_CAST (symbol_kind_type, yystos_[+state]);
  }

   Parser ::stack_symbol_type::stack_symbol_type ()
  {}

   Parser ::stack_symbol_type::stack_symbol_type (YY_RVREF (stack_symbol_type) that)
    : super_type (YY_MOVE (that.state), YY_MOVE (that.location))
  {
    switch (that.kind ())
    {
      case symbol_kind::S_definition: // definition
      case symbol_kind::S_table: // table
      case symbol_kind::S_function: // function
      case symbol_kind::S_param_list: // param_list
      case symbol_kind::S_object_block: // object_block
      case symbol_kind::S_take: // take
      case symbol_kind::S_take_id: // take_id
      case symbol_kind::S_id_list: // id_list
      case symbol_kind::S_id_list_params: // id_list_params
      case symbol_kind::S_region_block: // region_block
      case symbol_kind::S_criterion: // criterion
      case symbol_kind::S_chained_cond: // chained_cond
      case symbol_kind::S_chain: // chain
      case symbol_kind::S_not: // not
      case symbol_kind::S_condition: // condition
      case symbol_kind::S_expr: // expr
      case symbol_kind::S_factor: // factor
      case symbol_kind::S_term: // term
      case symbol_kind::S_id_qualifiers: // id_qualifiers
      case symbol_kind::S_id_qualifier: // id_qualifier
      case symbol_kind::S_dot_op: // dot_op
      case symbol_kind::S_range: // range
      case symbol_kind::S_num: // num
      case symbol_kind::S_int: // int
      case symbol_kind::S_real: // real
      case symbol_kind::S_id: // id
        value.YY_MOVE_OR_COPY< adl::Expr* > (YY_MOVE (that.value));
        break;

      case symbol_kind::S_boolean: // boolean
        value.YY_MOVE_OR_COPY< bool > (YY_MOVE (that.value));
        break;

      case symbol_kind::S_REAL: // REAL
      case symbol_kind::S_tablelist: // tablelist
      case symbol_kind::S_value: // value
        value.YY_MOVE_OR_COPY< double > (YY_MOVE (that.value));
        break;

      case symbol_kind::S_INT: // INT
      case symbol_kind::S_index: // index
        value.YY_MOVE_OR_COPY< int > (YY_MOVE (that.value));
        break;

      case symbol_kind::S_DEFINE: // DEFINE
      case symbol_kind::S_REGION: // REGION
      case symbol_kind::S_OBJECT: // OBJECT
      case symbol_kind::S_TAKE: // TAKE
      case symbol_kind::S_COMMAND: // COMMAND
      case symbol_kind::S_HISTO: // HISTO
      case symbol_kind::S_HISTOLIST: // HISTOLIST
      case symbol_kind::S_BIN: // BIN
      case symbol_kind::S_QUO: // QUO
      case symbol_kind::S_TABLE: // TABLE
      case symbol_kind::S_TABLETYPE: // TABLETYPE
      case symbol_kind::S_NVARS: // NVARS
      case symbol_kind::S_ERRORS: // ERRORS
      case symbol_kind::S_UNION: // UNION
      case symbol_kind::S_WEIGHT: // WEIGHT
      case symbol_kind::S_TRIGGER: // TRIGGER
      case symbol_kind::S_ID: // ID
      case symbol_kind::S_ERROR: // ERROR
      case symbol_kind::S_FLAG: // FLAG
      case symbol_kind::S_LPAR: // LPAR
      case symbol_kind::S_RPAR: // RPAR
      case symbol_kind::S_VAR: // VAR
      case symbol_kind::S_QUOTE: // QUOTE
      case symbol_kind::S_DESC: // DESC
      case symbol_kind::S_INFO: // INFO
      case symbol_kind::S_PLUS: // PLUS
      case symbol_kind::S_SUBTRACT: // SUBTRACT
      case symbol_kind::S_MULTIPLY: // MULTIPLY
      case symbol_kind::S_DIVIDE: // DIVIDE
      case symbol_kind::S_POW: // POW
      case symbol_kind::S_ASSIGN: // ASSIGN
      case symbol_kind::S_PLUSMINUS: // PLUSMINUS
      case symbol_kind::S_GT: // GT
      case symbol_kind::S_LT: // LT
      case symbol_kind::S_GE: // GE
      case symbol_kind::S_LE: // LE
      case symbol_kind::S_EQ: // EQ
      case symbol_kind::S_NE: // NE
      case symbol_kind::S_TRUE: // TRUE
      case symbol_kind::S_FALSE: // FALSE
      case symbol_kind::S_AND: // AND
      case symbol_kind::S_OR: // OR
      case symbol_kind::S_NOT: // NOT
      case symbol_kind::S_PIPE: // PIPE
      case symbol_kind::S_LBRACKET: // LBRACKET
      case symbol_kind::S_RBRACKET: // RBRACKET
      case symbol_kind::S_LCBRACE: // LCBRACE
      case symbol_kind::S_RCBRACE: // RCBRACE
      case symbol_kind::S_COLON: // COLON
      case symbol_kind::S_QUES: // QUES
      case symbol_kind::S_COMMA: // COMMA
      case symbol_kind::S_DOT: // DOT
      case symbol_kind::S_INCLUSIVE: // INCLUSIVE
      case symbol_kind::S_EXCLUSIVE: // EXCLUSIVE
      case symbol_kind::S_UNDERSCORE: // UNDERSCORE
      case symbol_kind::S_info: // info
      case symbol_kind::S_compare_op: // compare_op
      case symbol_kind::S_logic_op: // logic_op
      case symbol_kind::S_expr_op: // expr_op
      case symbol_kind::S_factor_op: // factor_op
        value.YY_MOVE_OR_COPY< std::string > (YY_MOVE (that.value));
        break;

      case symbol_kind::S_bins: // bins
        value.YY_MOVE_OR_COPY< std::vector<double> > (YY_MOVE (that.value));
        break;

      default:
        break;
    }

#if 201103L <= YY_CPLUSPLUS
    // that is emptied.
    that.state = empty_state;
#endif
  }

   Parser ::stack_symbol_type::stack_symbol_type (state_type s, YY_MOVE_REF (symbol_type) that)
    : super_type (s, YY_MOVE (that.location))
  {
    switch (that.kind ())
    {
      case symbol_kind::S_definition: // definition
      case symbol_kind::S_table: // table
      case symbol_kind::S_function: // function
      case symbol_kind::S_param_list: // param_list
      case symbol_kind::S_object_block: // object_block
      case symbol_kind::S_take: // take
      case symbol_kind::S_take_id: // take_id
      case symbol_kind::S_id_list: // id_list
      case symbol_kind::S_id_list_params: // id_list_params
      case symbol_kind::S_region_block: // region_block
      case symbol_kind::S_criterion: // criterion
      case symbol_kind::S_chained_cond: // chained_cond
      case symbol_kind::S_chain: // chain
      case symbol_kind::S_not: // not
      case symbol_kind::S_condition: // condition
      case symbol_kind::S_expr: // expr
      case symbol_kind::S_factor: // factor
      case symbol_kind::S_term: // term
      case symbol_kind::S_id_qualifiers: // id_qualifiers
      case symbol_kind::S_id_qualifier: // id_qualifier
      case symbol_kind::S_dot_op: // dot_op
      case symbol_kind::S_range: // range
      case symbol_kind::S_num: // num
      case symbol_kind::S_int: // int
      case symbol_kind::S_real: // real
      case symbol_kind::S_id: // id
        value.move< adl::Expr* > (YY_MOVE (that.value));
        break;

      case symbol_kind::S_boolean: // boolean
        value.move< bool > (YY_MOVE (that.value));
        break;

      case symbol_kind::S_REAL: // REAL
      case symbol_kind::S_tablelist: // tablelist
      case symbol_kind::S_value: // value
        value.move< double > (YY_MOVE (that.value));
        break;

      case symbol_kind::S_INT: // INT
      case symbol_kind::S_index: // index
        value.move< int > (YY_MOVE (that.value));
        break;

      case symbol_kind::S_DEFINE: // DEFINE
      case symbol_kind::S_REGION: // REGION
      case symbol_kind::S_OBJECT: // OBJECT
      case symbol_kind::S_TAKE: // TAKE
      case symbol_kind::S_COMMAND: // COMMAND
      case symbol_kind::S_HISTO: // HISTO
      case symbol_kind::S_HISTOLIST: // HISTOLIST
      case symbol_kind::S_BIN: // BIN
      case symbol_kind::S_QUO: // QUO
      case symbol_kind::S_TABLE: // TABLE
      case symbol_kind::S_TABLETYPE: // TABLETYPE
      case symbol_kind::S_NVARS: // NVARS
      case symbol_kind::S_ERRORS: // ERRORS
      case symbol_kind::S_UNION: // UNION
      case symbol_kind::S_WEIGHT: // WEIGHT
      case symbol_kind::S_TRIGGER: // TRIGGER
      case symbol_kind::S_ID: // ID
      case symbol_kind::S_ERROR: // ERROR
      case symbol_kind::S_FLAG: // FLAG
      case symbol_kind::S_LPAR: // LPAR
      case symbol_kind::S_RPAR: // RPAR
      case symbol_kind::S_VAR: // VAR
      case symbol_kind::S_QUOTE: // QUOTE
      case symbol_kind::S_DESC: // DESC
      case symbol_kind::S_INFO: // INFO
      case symbol_kind::S_PLUS: // PLUS
      case symbol_kind::S_SUBTRACT: // SUBTRACT
      case symbol_kind::S_MULTIPLY: // MULTIPLY
      case symbol_kind::S_DIVIDE: // DIVIDE
      case symbol_kind::S_POW: // POW
      case symbol_kind::S_ASSIGN: // ASSIGN
      case symbol_kind::S_PLUSMINUS: // PLUSMINUS
      case symbol_kind::S_GT: // GT
      case symbol_kind::S_LT: // LT
      case symbol_kind::S_GE: // GE
      case symbol_kind::S_LE: // LE
      case symbol_kind::S_EQ: // EQ
      case symbol_kind::S_NE: // NE
      case symbol_kind::S_TRUE: // TRUE
      case symbol_kind::S_FALSE: // FALSE
      case symbol_kind::S_AND: // AND
      case symbol_kind::S_OR: // OR
      case symbol_kind::S_NOT: // NOT
      case symbol_kind::S_PIPE: // PIPE
      case symbol_kind::S_LBRACKET: // LBRACKET
      case symbol_kind::S_RBRACKET: // RBRACKET
      case symbol_kind::S_LCBRACE: // LCBRACE
      case symbol_kind::S_RCBRACE: // RCBRACE
      case symbol_kind::S_COLON: // COLON
      case symbol_kind::S_QUES: // QUES
      case symbol_kind::S_COMMA: // COMMA
      case symbol_kind::S_DOT: // DOT
      case symbol_kind::S_INCLUSIVE: // INCLUSIVE
      case symbol_kind::S_EXCLUSIVE: // EXCLUSIVE
      case symbol_kind::S_UNDERSCORE: // UNDERSCORE
      case symbol_kind::S_info: // info
      case symbol_kind::S_compare_op: // compare_op
      case symbol_kind::S_logic_op: // logic_op
      case symbol_kind::S_expr_op: // expr_op
      case symbol_kind::S_factor_op: // factor_op
        value.move< std::string > (YY_MOVE (that.value));
        break;

      case symbol_kind::S_bins: // bins
        value.move< std::vector<double> > (YY_MOVE (that.value));
        break;

      default:
        break;
    }

    // that is emptied.
    that.kind_ = symbol_kind::S_YYEMPTY;
  }

#if YY_CPLUSPLUS < 201103L
   Parser ::stack_symbol_type&
   Parser ::stack_symbol_type::operator= (const stack_symbol_type& that)
  {
    state = that.state;
    switch (that.kind ())
    {
      case symbol_kind::S_definition: // definition
      case symbol_kind::S_table: // table
      case symbol_kind::S_function: // function
      case symbol_kind::S_param_list: // param_list
      case symbol_kind::S_object_block: // object_block
      case symbol_kind::S_take: // take
      case symbol_kind::S_take_id: // take_id
      case symbol_kind::S_id_list: // id_list
      case symbol_kind::S_id_list_params: // id_list_params
      case symbol_kind::S_region_block: // region_block
      case symbol_kind::S_criterion: // criterion
      case symbol_kind::S_chained_cond: // chained_cond
      case symbol_kind::S_chain: // chain
      case symbol_kind::S_not: // not
      case symbol_kind::S_condition: // condition
      case symbol_kind::S_expr: // expr
      case symbol_kind::S_factor: // factor
      case symbol_kind::S_term: // term
      case symbol_kind::S_id_qualifiers: // id_qualifiers
      case symbol_kind::S_id_qualifier: // id_qualifier
      case symbol_kind::S_dot_op: // dot_op
      case symbol_kind::S_range: // range
      case symbol_kind::S_num: // num
      case symbol_kind::S_int: // int
      case symbol_kind::S_real: // real
      case symbol_kind::S_id: // id
        value.copy< adl::Expr* > (that.value);
        break;

      case symbol_kind::S_boolean: // boolean
        value.copy< bool > (that.value);
        break;

      case symbol_kind::S_REAL: // REAL
      case symbol_kind::S_tablelist: // tablelist
      case symbol_kind::S_value: // value
        value.copy< double > (that.value);
        break;

      case symbol_kind::S_INT: // INT
      case symbol_kind::S_index: // index
        value.copy< int > (that.value);
        break;

      case symbol_kind::S_DEFINE: // DEFINE
      case symbol_kind::S_REGION: // REGION
      case symbol_kind::S_OBJECT: // OBJECT
      case symbol_kind::S_TAKE: // TAKE
      case symbol_kind::S_COMMAND: // COMMAND
      case symbol_kind::S_HISTO: // HISTO
      case symbol_kind::S_HISTOLIST: // HISTOLIST
      case symbol_kind::S_BIN: // BIN
      case symbol_kind::S_QUO: // QUO
      case symbol_kind::S_TABLE: // TABLE
      case symbol_kind::S_TABLETYPE: // TABLETYPE
      case symbol_kind::S_NVARS: // NVARS
      case symbol_kind::S_ERRORS: // ERRORS
      case symbol_kind::S_UNION: // UNION
      case symbol_kind::S_WEIGHT: // WEIGHT
      case symbol_kind::S_TRIGGER: // TRIGGER
      case symbol_kind::S_ID: // ID
      case symbol_kind::S_ERROR: // ERROR
      case symbol_kind::S_FLAG: // FLAG
      case symbol_kind::S_LPAR: // LPAR
      case symbol_kind::S_RPAR: // RPAR
      case symbol_kind::S_VAR: // VAR
      case symbol_kind::S_QUOTE: // QUOTE
      case symbol_kind::S_DESC: // DESC
      case symbol_kind::S_INFO: // INFO
      case symbol_kind::S_PLUS: // PLUS
      case symbol_kind::S_SUBTRACT: // SUBTRACT
      case symbol_kind::S_MULTIPLY: // MULTIPLY
      case symbol_kind::S_DIVIDE: // DIVIDE
      case symbol_kind::S_POW: // POW
      case symbol_kind::S_ASSIGN: // ASSIGN
      case symbol_kind::S_PLUSMINUS: // PLUSMINUS
      case symbol_kind::S_GT: // GT
      case symbol_kind::S_LT: // LT
      case symbol_kind::S_GE: // GE
      case symbol_kind::S_LE: // LE
      case symbol_kind::S_EQ: // EQ
      case symbol_kind::S_NE: // NE
      case symbol_kind::S_TRUE: // TRUE
      case symbol_kind::S_FALSE: // FALSE
      case symbol_kind::S_AND: // AND
      case symbol_kind::S_OR: // OR
      case symbol_kind::S_NOT: // NOT
      case symbol_kind::S_PIPE: // PIPE
      case symbol_kind::S_LBRACKET: // LBRACKET
      case symbol_kind::S_RBRACKET: // RBRACKET
      case symbol_kind::S_LCBRACE: // LCBRACE
      case symbol_kind::S_RCBRACE: // RCBRACE
      case symbol_kind::S_COLON: // COLON
      case symbol_kind::S_QUES: // QUES
      case symbol_kind::S_COMMA: // COMMA
      case symbol_kind::S_DOT: // DOT
      case symbol_kind::S_INCLUSIVE: // INCLUSIVE
      case symbol_kind::S_EXCLUSIVE: // EXCLUSIVE
      case symbol_kind::S_UNDERSCORE: // UNDERSCORE
      case symbol_kind::S_info: // info
      case symbol_kind::S_compare_op: // compare_op
      case symbol_kind::S_logic_op: // logic_op
      case symbol_kind::S_expr_op: // expr_op
      case symbol_kind::S_factor_op: // factor_op
        value.copy< std::string > (that.value);
        break;

      case symbol_kind::S_bins: // bins
        value.copy< std::vector<double> > (that.value);
        break;

      default:
        break;
    }

    location = that.location;
    return *this;
  }

   Parser ::stack_symbol_type&
   Parser ::stack_symbol_type::operator= (stack_symbol_type& that)
  {
    state = that.state;
    switch (that.kind ())
    {
      case symbol_kind::S_definition: // definition
      case symbol_kind::S_table: // table
      case symbol_kind::S_function: // function
      case symbol_kind::S_param_list: // param_list
      case symbol_kind::S_object_block: // object_block
      case symbol_kind::S_take: // take
      case symbol_kind::S_take_id: // take_id
      case symbol_kind::S_id_list: // id_list
      case symbol_kind::S_id_list_params: // id_list_params
      case symbol_kind::S_region_block: // region_block
      case symbol_kind::S_criterion: // criterion
      case symbol_kind::S_chained_cond: // chained_cond
      case symbol_kind::S_chain: // chain
      case symbol_kind::S_not: // not
      case symbol_kind::S_condition: // condition
      case symbol_kind::S_expr: // expr
      case symbol_kind::S_factor: // factor
      case symbol_kind::S_term: // term
      case symbol_kind::S_id_qualifiers: // id_qualifiers
      case symbol_kind::S_id_qualifier: // id_qualifier
      case symbol_kind::S_dot_op: // dot_op
      case symbol_kind::S_range: // range
      case symbol_kind::S_num: // num
      case symbol_kind::S_int: // int
      case symbol_kind::S_real: // real
      case symbol_kind::S_id: // id
        value.move< adl::Expr* > (that.value);
        break;

      case symbol_kind::S_boolean: // boolean
        value.move< bool > (that.value);
        break;

      case symbol_kind::S_REAL: // REAL
      case symbol_kind::S_tablelist: // tablelist
      case symbol_kind::S_value: // value
        value.move< double > (that.value);
        break;

      case symbol_kind::S_INT: // INT
      case symbol_kind::S_index: // index
        value.move< int > (that.value);
        break;

      case symbol_kind::S_DEFINE: // DEFINE
      case symbol_kind::S_REGION: // REGION
      case symbol_kind::S_OBJECT: // OBJECT
      case symbol_kind::S_TAKE: // TAKE
      case symbol_kind::S_COMMAND: // COMMAND
      case symbol_kind::S_HISTO: // HISTO
      case symbol_kind::S_HISTOLIST: // HISTOLIST
      case symbol_kind::S_BIN: // BIN
      case symbol_kind::S_QUO: // QUO
      case symbol_kind::S_TABLE: // TABLE
      case symbol_kind::S_TABLETYPE: // TABLETYPE
      case symbol_kind::S_NVARS: // NVARS
      case symbol_kind::S_ERRORS: // ERRORS
      case symbol_kind::S_UNION: // UNION
      case symbol_kind::S_WEIGHT: // WEIGHT
      case symbol_kind::S_TRIGGER: // TRIGGER
      case symbol_kind::S_ID: // ID
      case symbol_kind::S_ERROR: // ERROR
      case symbol_kind::S_FLAG: // FLAG
      case symbol_kind::S_LPAR: // LPAR
      case symbol_kind::S_RPAR: // RPAR
      case symbol_kind::S_VAR: // VAR
      case symbol_kind::S_QUOTE: // QUOTE
      case symbol_kind::S_DESC: // DESC
      case symbol_kind::S_INFO: // INFO
      case symbol_kind::S_PLUS: // PLUS
      case symbol_kind::S_SUBTRACT: // SUBTRACT
      case symbol_kind::S_MULTIPLY: // MULTIPLY
      case symbol_kind::S_DIVIDE: // DIVIDE
      case symbol_kind::S_POW: // POW
      case symbol_kind::S_ASSIGN: // ASSIGN
      case symbol_kind::S_PLUSMINUS: // PLUSMINUS
      case symbol_kind::S_GT: // GT
      case symbol_kind::S_LT: // LT
      case symbol_kind::S_GE: // GE
      case symbol_kind::S_LE: // LE
      case symbol_kind::S_EQ: // EQ
      case symbol_kind::S_NE: // NE
      case symbol_kind::S_TRUE: // TRUE
      case symbol_kind::S_FALSE: // FALSE
      case symbol_kind::S_AND: // AND
      case symbol_kind::S_OR: // OR
      case symbol_kind::S_NOT: // NOT
      case symbol_kind::S_PIPE: // PIPE
      case symbol_kind::S_LBRACKET: // LBRACKET
      case symbol_kind::S_RBRACKET: // RBRACKET
      case symbol_kind::S_LCBRACE: // LCBRACE
      case symbol_kind::S_RCBRACE: // RCBRACE
      case symbol_kind::S_COLON: // COLON
      case symbol_kind::S_QUES: // QUES
      case symbol_kind::S_COMMA: // COMMA
      case symbol_kind::S_DOT: // DOT
      case symbol_kind::S_INCLUSIVE: // INCLUSIVE
      case symbol_kind::S_EXCLUSIVE: // EXCLUSIVE
      case symbol_kind::S_UNDERSCORE: // UNDERSCORE
      case symbol_kind::S_info: // info
      case symbol_kind::S_compare_op: // compare_op
      case symbol_kind::S_logic_op: // logic_op
      case symbol_kind::S_expr_op: // expr_op
      case symbol_kind::S_factor_op: // factor_op
        value.move< std::string > (that.value);
        break;

      case symbol_kind::S_bins: // bins
        value.move< std::vector<double> > (that.value);
        break;

      default:
        break;
    }

    location = that.location;
    // that is emptied.
    that.state = empty_state;
    return *this;
  }
#endif

  template <typename Base>
  void
   Parser ::yy_destroy_ (const char* yymsg, basic_symbol<Base>& yysym) const
  {
    if (yymsg)
      YY_SYMBOL_PRINT (yymsg, yysym);
  }

#if YYDEBUG
  template <typename Base>
  void
   Parser ::yy_print_ (std::ostream& yyo, const basic_symbol<Base>& yysym) const
  {
    std::ostream& yyoutput = yyo;
    YY_USE (yyoutput);
    if (yysym.empty ())
      yyo << "empty symbol";
    else
      {
        symbol_kind_type yykind = yysym.kind ();
        yyo << (yykind < YYNTOKENS ? "token" : "nterm")
            << ' ' << yysym.name () << " ("
            << yysym.location << ": ";
        YY_USE (yykind);
        yyo << ')';
      }
  }
#endif

  void
   Parser ::yypush_ (const char* m, YY_MOVE_REF (stack_symbol_type) sym)
  {
    if (m)
      YY_SYMBOL_PRINT (m, sym);
    yystack_.push (YY_MOVE (sym));
  }

  void
   Parser ::yypush_ (const char* m, state_type s, YY_MOVE_REF (symbol_type) sym)
  {
#if 201103L <= YY_CPLUSPLUS
    yypush_ (m, stack_symbol_type (s, std::move (sym)));
#else
    stack_symbol_type ss (s, sym);
    yypush_ (m, ss);
#endif
  }

  void
   Parser ::yypop_ (int n) YY_NOEXCEPT
  {
    yystack_.pop (n);
  }

#if YYDEBUG
  std::ostream&
   Parser ::debug_stream () const
  {
    return *yycdebug_;
  }

  void
   Parser ::set_debug_stream (std::ostream& o)
  {
    yycdebug_ = &o;
  }


   Parser ::debug_level_type
   Parser ::debug_level () const
  {
    return yydebug_;
  }

  void
   Parser ::set_debug_level (debug_level_type l)
  {
    yydebug_ = l;
  }
#endif // YYDEBUG

   Parser ::state_type
   Parser ::yy_lr_goto_state_ (state_type yystate, int yysym)
  {
    int yyr = yypgoto_[yysym - YYNTOKENS] + yystate;
    if (0 <= yyr && yyr <= yylast_ && yycheck_[yyr] == yystate)
      return yytable_[yyr];
    else
      return yydefgoto_[yysym - YYNTOKENS];
  }

  bool
   Parser ::yy_pact_value_is_default_ (int yyvalue) YY_NOEXCEPT
  {
    return yyvalue == yypact_ninf_;
  }

  bool
   Parser ::yy_table_value_is_error_ (int yyvalue) YY_NOEXCEPT
  {
    return yyvalue == yytable_ninf_;
  }

  int
   Parser ::operator() ()
  {
    return parse ();
  }

  int
   Parser ::parse ()
  {
    int yyn;
    /// Length of the RHS of the rule being reduced.
    int yylen = 0;

    // Error handling.
    int yynerrs_ = 0;
    int yyerrstatus_ = 0;

    /// The lookahead symbol.
    symbol_type yyla;

    /// The locations where the error started and ended.
    stack_symbol_type yyerror_range[3];

    /// The return value of parse ().
    int yyresult;

#if YY_EXCEPTIONS
    try
#endif // YY_EXCEPTIONS
      {
    YYCDEBUG << "Starting parse\n";


    /* Initialize the stack.  The initial state will be set in
       yynewstate, since the latter expects the semantical and the
       location values to have been already stored, initialize these
       stacks with a primary value.  */
    yystack_.clear ();
    yypush_ (YY_NULLPTR, 0, YY_MOVE (yyla));

  /*-----------------------------------------------.
  | yynewstate -- push a new symbol on the stack.  |
  `-----------------------------------------------*/
  yynewstate:
    YYCDEBUG << "Entering state " << int (yystack_[0].state) << '\n';
    YY_STACK_PRINT ();

    // Accept?
    if (yystack_[0].state == yyfinal_)
      YYACCEPT;

    goto yybackup;


  /*-----------.
  | yybackup.  |
  `-----------*/
  yybackup:
    // Try to take a decision without lookahead.
    yyn = yypact_[+yystack_[0].state];
    if (yy_pact_value_is_default_ (yyn))
      goto yydefault;

    // Read a lookahead token.
    if (yyla.empty ())
      {
        YYCDEBUG << "Reading a token\n";
#if YY_EXCEPTIONS
        try
#endif // YY_EXCEPTIONS
          {
            symbol_type yylookahead (yylex (scanner, driver));
            yyla.move (yylookahead);
          }
#if YY_EXCEPTIONS
        catch (const syntax_error& yyexc)
          {
            YYCDEBUG << "Caught exception: " << yyexc.what() << '\n';
            error (yyexc);
            goto yyerrlab1;
          }
#endif // YY_EXCEPTIONS
      }
    YY_SYMBOL_PRINT ("Next token is", yyla);

    if (yyla.kind () == symbol_kind::S_YYerror)
    {
      // The scanner already issued an error message, process directly
      // to error recovery.  But do not keep the error token as
      // lookahead, it is too special and may lead us to an endless
      // loop in error recovery. */
      yyla.kind_ = symbol_kind::S_YYUNDEF;
      goto yyerrlab1;
    }

    /* If the proper action on seeing token YYLA.TYPE is to reduce or
       to detect an error, take that action.  */
    yyn += yyla.kind ();
    if (yyn < 0 || yylast_ < yyn || yycheck_[yyn] != yyla.kind ())
      {
        goto yydefault;
      }

    // Reduce or error.
    yyn = yytable_[yyn];
    if (yyn <= 0)
      {
        if (yy_table_value_is_error_ (yyn))
          goto yyerrlab;
        yyn = -yyn;
        goto yyreduce;
      }

    // Count tokens shifted since error; after three, turn off error status.
    if (yyerrstatus_)
      --yyerrstatus_;

    // Shift the lookahead token.
    yypush_ ("Shifting", state_type (yyn), YY_MOVE (yyla));
    goto yynewstate;


  /*-----------------------------------------------------------.
  | yydefault -- do the default action for the current state.  |
  `-----------------------------------------------------------*/
  yydefault:
    yyn = yydefact_[+yystack_[0].state];
    if (yyn == 0)
      goto yyerrlab;
    goto yyreduce;


  /*-----------------------------.
  | yyreduce -- do a reduction.  |
  `-----------------------------*/
  yyreduce:
    yylen = yyr2_[yyn];
    {
      stack_symbol_type yylhs;
      yylhs.state = yy_lr_goto_state_ (yystack_[yylen].state, yyr1_[yyn]);
      /* Variants are always initialized to an empty instance of the
         correct type. The default '$$ = $1' action is NOT applied
         when using variants.  */
      switch (yyr1_[yyn])
    {
      case symbol_kind::S_definition: // definition
      case symbol_kind::S_table: // table
      case symbol_kind::S_function: // function
      case symbol_kind::S_param_list: // param_list
      case symbol_kind::S_object_block: // object_block
      case symbol_kind::S_take: // take
      case symbol_kind::S_take_id: // take_id
      case symbol_kind::S_id_list: // id_list
      case symbol_kind::S_id_list_params: // id_list_params
      case symbol_kind::S_region_block: // region_block
      case symbol_kind::S_criterion: // criterion
      case symbol_kind::S_chained_cond: // chained_cond
      case symbol_kind::S_chain: // chain
      case symbol_kind::S_not: // not
      case symbol_kind::S_condition: // condition
      case symbol_kind::S_expr: // expr
      case symbol_kind::S_factor: // factor
      case symbol_kind::S_term: // term
      case symbol_kind::S_id_qualifiers: // id_qualifiers
      case symbol_kind::S_id_qualifier: // id_qualifier
      case symbol_kind::S_dot_op: // dot_op
      case symbol_kind::S_range: // range
      case symbol_kind::S_num: // num
      case symbol_kind::S_int: // int
      case symbol_kind::S_real: // real
      case symbol_kind::S_id: // id
        yylhs.value.emplace< adl::Expr* > ();
        break;

      case symbol_kind::S_boolean: // boolean
        yylhs.value.emplace< bool > ();
        break;

      case symbol_kind::S_REAL: // REAL
      case symbol_kind::S_tablelist: // tablelist
      case symbol_kind::S_value: // value
        yylhs.value.emplace< double > ();
        break;

      case symbol_kind::S_INT: // INT
      case symbol_kind::S_index: // index
        yylhs.value.emplace< int > ();
        break;

      case symbol_kind::S_DEFINE: // DEFINE
      case symbol_kind::S_REGION: // REGION
      case symbol_kind::S_OBJECT: // OBJECT
      case symbol_kind::S_TAKE: // TAKE
      case symbol_kind::S_COMMAND: // COMMAND
      case symbol_kind::S_HISTO: // HISTO
      case symbol_kind::S_HISTOLIST: // HISTOLIST
      case symbol_kind::S_BIN: // BIN
      case symbol_kind::S_QUO: // QUO
      case symbol_kind::S_TABLE: // TABLE
      case symbol_kind::S_TABLETYPE: // TABLETYPE
      case symbol_kind::S_NVARS: // NVARS
      case symbol_kind::S_ERRORS: // ERRORS
      case symbol_kind::S_UNION: // UNION
      case symbol_kind::S_WEIGHT: // WEIGHT
      case symbol_kind::S_TRIGGER: // TRIGGER
      case symbol_kind::S_ID: // ID
      case symbol_kind::S_ERROR: // ERROR
      case symbol_kind::S_FLAG: // FLAG
      case symbol_kind::S_LPAR: // LPAR
      case symbol_kind::S_RPAR: // RPAR
      case symbol_kind::S_VAR: // VAR
      case symbol_kind::S_QUOTE: // QUOTE
      case symbol_kind::S_DESC: // DESC
      case symbol_kind::S_INFO: // INFO
      case symbol_kind::S_PLUS: // PLUS
      case symbol_kind::S_SUBTRACT: // SUBTRACT
      case symbol_kind::S_MULTIPLY: // MULTIPLY
      case symbol_kind::S_DIVIDE: // DIVIDE
      case symbol_kind::S_POW: // POW
      case symbol_kind::S_ASSIGN: // ASSIGN
      case symbol_kind::S_PLUSMINUS: // PLUSMINUS
      case symbol_kind::S_GT: // GT
      case symbol_kind::S_LT: // LT
      case symbol_kind::S_GE: // GE
      case symbol_kind::S_LE: // LE
      case symbol_kind::S_EQ: // EQ
      case symbol_kind::S_NE: // NE
      case symbol_kind::S_TRUE: // TRUE
      case symbol_kind::S_FALSE: // FALSE
      case symbol_kind::S_AND: // AND
      case symbol_kind::S_OR: // OR
      case symbol_kind::S_NOT: // NOT
      case symbol_kind::S_PIPE: // PIPE
      case symbol_kind::S_LBRACKET: // LBRACKET
      case symbol_kind::S_RBRACKET: // RBRACKET
      case symbol_kind::S_LCBRACE: // LCBRACE
      case symbol_kind::S_RCBRACE: // RCBRACE
      case symbol_kind::S_COLON: // COLON
      case symbol_kind::S_QUES: // QUES
      case symbol_kind::S_COMMA: // COMMA
      case symbol_kind::S_DOT: // DOT
      case symbol_kind::S_INCLUSIVE: // INCLUSIVE
      case symbol_kind::S_EXCLUSIVE: // EXCLUSIVE
      case symbol_kind::S_UNDERSCORE: // UNDERSCORE
      case symbol_kind::S_info: // info
      case symbol_kind::S_compare_op: // compare_op
      case symbol_kind::S_logic_op: // logic_op
      case symbol_kind::S_expr_op: // expr_op
      case symbol_kind::S_factor_op: // factor_op
        yylhs.value.emplace< std::string > ();
        break;

      case symbol_kind::S_bins: // bins
        yylhs.value.emplace< std::vector<double> > ();
        break;

      default:
        break;
    }


      // Default location.
      {
        stack_type::slice range (yystack_, yylen);
        YYLLOC_DEFAULT (yylhs.location, range, yylen);
        yyerror_range[1].location = yylhs.location;
      }

      // Perform the reduction.
      YY_REDUCE_PRINT (yyn);
#if YY_EXCEPTIONS
      try
#endif // YY_EXCEPTIONS
        {
          switch (yyn)
            {
  case 2: // start: info objects
#line 84 "parser.y"
                                                {}
#line 1116 "Parser.cpp"
    break;

  case 3: // start: info table objects
#line 85 "parser.y"
                                                {}
#line 1122 "Parser.cpp"
    break;

  case 4: // start: table objects
#line 86 "parser.y"
                                                {}
#line 1128 "Parser.cpp"
    break;

  case 5: // start: objects
#line 87 "parser.y"
                                                {}
#line 1134 "Parser.cpp"
    break;

  case 6: // start: info
#line 88 "parser.y"
                                                {}
#line 1140 "Parser.cpp"
    break;

  case 7: // info: INFO info_list
#line 91 "parser.y"
                                                {}
#line 1146 "Parser.cpp"
    break;

  case 14: // objects: object_block
#line 97 "parser.y"
                                                {}
#line 1152 "Parser.cpp"
    break;

  case 15: // objects: object_block objects
#line 98 "parser.y"
                                                {}
#line 1158 "Parser.cpp"
    break;

  case 16: // objects: definitions
#line 99 "parser.y"
                                                {}
#line 1164 "Parser.cpp"
    break;

  case 17: // objects: definitions objects
#line 100 "parser.y"
                                                {}
#line 1170 "Parser.cpp"
    break;

  case 18: // definitions: definition
#line 103 "parser.y"
                                                {}
#line 1176 "Parser.cpp"
    break;

  case 19: // definitions: definition definitions
#line 104 "parser.y"
                                                {}
#line 1182 "Parser.cpp"
    break;

  case 20: // definitions: regions
#line 105 "parser.y"
                                                {}
#line 1188 "Parser.cpp"
    break;

  case 21: // regions: region_block
#line 108 "parser.y"
                                                {}
#line 1194 "Parser.cpp"
    break;

  case 22: // regions: region_block regions
#line 109 "parser.y"
                                                {}
#line 1200 "Parser.cpp"
    break;

  case 23: // definition: DEFINE id ASSIGN condition
#line 112 "parser.y"
                                                { yylhs.value.as < adl::Expr* > () = new adl::DefineNode(incrementCounter(), "DEFINE", yystack_[2].value.as < adl::Expr* > (), yystack_[0].value.as < adl::Expr* > ()); driver.ast.push_back(yylhs.value.as < adl::Expr* > ()); std::cout << "define: " << yystack_[2].value.as < adl::Expr* > ()->getId() << "\n"; }
#line 1206 "Parser.cpp"
    break;

  case 24: // definition: DEFINE id COLON condition
#line 113 "parser.y"
                                                { yylhs.value.as < adl::Expr* > () = new adl::DefineNode(incrementCounter(), "DEFINE", yystack_[2].value.as < adl::Expr* > (), yystack_[0].value.as < adl::Expr* > ()); driver.ast.push_back(yylhs.value.as < adl::Expr* > ()); std::cout << "define: " << yystack_[2].value.as < adl::Expr* > ()->getId() << "\n"; }
#line 1212 "Parser.cpp"
    break;

  case 25: // definition: table
#line 114 "parser.y"
                                                { /* make tableNode here. */ }
#line 1218 "Parser.cpp"
    break;

  case 26: // table: TABLE ID TABLETYPE ID NVARS INT ERRORS boolean tablelist
#line 120 "parser.y"
                                                { /* Put this info into a tableNode. */ }
#line 1224 "Parser.cpp"
    break;

  case 27: // tablelist: value tablelist
#line 122 "parser.y"
                                                { doubleLists.push_back(yystack_[1].value.as < double > ()); }
#line 1230 "Parser.cpp"
    break;

  case 28: // tablelist: value
#line 123 "parser.y"
                                                { doubleLists.push_back(yystack_[0].value.as < double > ()); }
#line 1236 "Parser.cpp"
    break;

  case 29: // value: REAL
#line 126 "parser.y"
                                                { yylhs.value.as < double > () = yystack_[0].value.as < double > (); }
#line 1242 "Parser.cpp"
    break;

  case 30: // function: id LPAR param_list RPAR
#line 129 "parser.y"
                                                { yylhs.value.as < adl::Expr* > () = new adl::FunctionNode(incrementCounter(), "FUNCTION", yystack_[3].value.as < adl::Expr* > (), paramlist); paramlist.clear(); }
#line 1248 "Parser.cpp"
    break;

  case 31: // function: LCBRACE param_list RCBRACE id
#line 130 "parser.y"
                                                { yylhs.value.as < adl::Expr* > () = new adl::FunctionNode(incrementCounter(), "FUNCTION", yystack_[0].value.as < adl::Expr* > (), paramlist); paramlist.clear(); }
#line 1254 "Parser.cpp"
    break;

  case 32: // function: PIPE int PIPE
#line 131 "parser.y"
                                                { Expr* e = new adl::VarNode(incrementCounter(),"ID","abs", "", "", {},""); yylhs.value.as < adl::Expr* > () = new adl::FunctionNode(incrementCounter(), "FUNCTION", e, ExprVector(1,yystack_[1].value.as < adl::Expr* > ())); }
#line 1260 "Parser.cpp"
    break;

  case 33: // function: PIPE real PIPE
#line 132 "parser.y"
                                                { Expr* e = new adl::VarNode(incrementCounter(),"ID","abs", "", "", {},""); yylhs.value.as < adl::Expr* > () = new adl::FunctionNode(incrementCounter(), "FUNCTION", e, ExprVector(1,yystack_[1].value.as < adl::Expr* > ())); }
#line 1266 "Parser.cpp"
    break;

  case 34: // function: PIPE id PIPE
#line 133 "parser.y"
                                                { Expr* e = new adl::VarNode(incrementCounter(),"ID","abs", "", "", {},""); yylhs.value.as < adl::Expr* > () = new adl::FunctionNode(incrementCounter(), "FUNCTION", e, ExprVector(1,yystack_[1].value.as < adl::Expr* > ())); }
#line 1272 "Parser.cpp"
    break;

  case 35: // param_list: chain COMMA param_list
#line 136 "parser.y"
                                                { paramlist.push_back(yystack_[2].value.as < adl::Expr* > ()); }
#line 1278 "Parser.cpp"
    break;

  case 36: // param_list: chain
#line 137 "parser.y"
                                                { paramlist.push_back(yystack_[0].value.as < adl::Expr* > ()); }
#line 1284 "Parser.cpp"
    break;

  case 37: // object_block: OBJECT id takes
#line 140 "parser.y"
                                                { yylhs.value.as < adl::Expr* > () = new astObjectNode(incrementCounter(), "OBJECT", yystack_[1].value.as < adl::Expr* > (), lists); driver.ast.push_back(yylhs.value.as < adl::Expr* > ()); lists.clear(); std::cout << "object: " << yystack_[1].value.as < adl::Expr* > ()->getId() << "\n"; }
#line 1290 "Parser.cpp"
    break;

  case 38: // object_block: OBJECT id takes criteria
#line 141 "parser.y"
                                                { yylhs.value.as < adl::Expr* > () = new astObjectNode(incrementCounter(), "OBJECT", yystack_[2].value.as < adl::Expr* > (), lists); driver.ast.push_back(yylhs.value.as < adl::Expr* > ()); lists.clear(); std::cout << "object: " << yystack_[2].value.as < adl::Expr* > ()->getId() << "\n"; }
#line 1296 "Parser.cpp"
    break;

  case 39: // object_block: TRIGGER id criteria
#line 142 "parser.y"
                                                { yylhs.value.as < adl::Expr* > () = new astObjectNode(incrementCounter(), "OBJECT", yystack_[1].value.as < adl::Expr* > (), lists); driver.ast.push_back(yylhs.value.as < adl::Expr* > ()); lists.clear(); std::cout << "object: " << yystack_[1].value.as < adl::Expr* > ()->getId() << "\n"; }
#line 1302 "Parser.cpp"
    break;

  case 40: // takes: take takes
#line 145 "parser.y"
                                                { lists.push_back(yystack_[1].value.as < adl::Expr* > ()); }
#line 1308 "Parser.cpp"
    break;

  case 41: // takes: take
#line 146 "parser.y"
                                                { lists.push_back(yystack_[0].value.as < adl::Expr* > ()); }
#line 1314 "Parser.cpp"
    break;

  case 42: // take: TAKE take_id
#line 149 "parser.y"
                                                { yylhs.value.as < adl::Expr* > () = new CommandNode(incrementCounter(), yystack_[1].value.as < std::string > (),yystack_[0].value.as < adl::Expr* > ()); }
#line 1320 "Parser.cpp"
    break;

  case 43: // take: COLON take_id
#line 150 "parser.y"
                                                { yylhs.value.as < adl::Expr* > () = new CommandNode(incrementCounter(), "TAKE",yystack_[0].value.as < adl::Expr* > ()); }
#line 1326 "Parser.cpp"
    break;

  case 44: // take: TAKE UNION LPAR id COMMA id RPAR
#line 151 "parser.y"
                                                { yylhs.value.as < adl::Expr* > () = new CommandNode(incrementCounter(), "TAKE",yystack_[3].value.as < adl::Expr* > ()); lists.push_back(new CommandNode(incrementCounter(), "TAKE",yystack_[1].value.as < adl::Expr* > ())); }
#line 1332 "Parser.cpp"
    break;

  case 45: // take: COLON UNION LPAR id COMMA id RPAR
#line 152 "parser.y"
                                                { yylhs.value.as < adl::Expr* > () = new CommandNode(incrementCounter(), "TAKE",yystack_[3].value.as < adl::Expr* > ()); lists.push_back(new CommandNode(incrementCounter(), "TAKE",yystack_[1].value.as < adl::Expr* > ())); }
#line 1338 "Parser.cpp"
    break;

  case 46: // take_id: id
#line 155 "parser.y"
                                                { yylhs.value.as < adl::Expr* > () = yystack_[0].value.as < adl::Expr* > (); }
#line 1344 "Parser.cpp"
    break;

  case 47: // take_id: id LPAR id_list RPAR
#line 156 "parser.y"
                                                { yylhs.value.as < adl::Expr* > () = yystack_[3].value.as < adl::Expr* > (); Expr* cn = new CommandNode(incrementCounter(),"TAKE",yystack_[1].value.as < adl::Expr* > ()); lists.push_back(cn); }
#line 1350 "Parser.cpp"
    break;

  case 48: // take_id: id id_list
#line 157 "parser.y"
                                                { yylhs.value.as < adl::Expr* > () = new VarNode(incrementCounter(),"ID",yystack_[1].value.as < adl::Expr* > ()->getId(),yystack_[0].value.as < adl::Expr* > ()->getId(), "", {},""); }
#line 1356 "Parser.cpp"
    break;

  case 49: // id_list: id_list_params
#line 160 "parser.y"
                                                { yylhs.value.as < adl::Expr* > () = yystack_[0].value.as < adl::Expr* > (); }
#line 1362 "Parser.cpp"
    break;

  case 50: // id_list: id_list_params COMMA id_list
#line 161 "parser.y"
                                                { yylhs.value.as < adl::Expr* > () = yystack_[2].value.as < adl::Expr* > (); }
#line 1368 "Parser.cpp"
    break;

  case 51: // id_list_params: id
#line 164 "parser.y"
                                                { yylhs.value.as < adl::Expr* > () = yystack_[0].value.as < adl::Expr* > (); }
#line 1374 "Parser.cpp"
    break;

  case 52: // id_list_params: num
#line 165 "parser.y"
                                                { yylhs.value.as < adl::Expr* > () = yystack_[0].value.as < adl::Expr* > (); }
#line 1380 "Parser.cpp"
    break;

  case 53: // region_block: REGION id criteria
#line 168 "parser.y"
                                                { yylhs.value.as < adl::Expr* > () = new RegionNode(incrementCounter(), "REGION", yystack_[1].value.as < adl::Expr* > (), lists); driver.ast.push_back(yylhs.value.as < adl::Expr* > ()); lists.clear(); std::cout << "region: " << yystack_[1].value.as < adl::Expr* > ()->getId() << "\n"; }
#line 1386 "Parser.cpp"
    break;

  case 54: // region_block: HISTOLIST id criteria
#line 169 "parser.y"
                                                { yylhs.value.as < adl::Expr* > () = new RegionNode(incrementCounter(), "HISTOLIST", yystack_[1].value.as < adl::Expr* > (), lists); driver.ast.push_back(yylhs.value.as < adl::Expr* > ()); lists.clear(); std::cout << "histo: " << yystack_[1].value.as < adl::Expr* > ()->getId() << "\n"; }
#line 1392 "Parser.cpp"
    break;

  case 55: // criteria: criterion criteria
#line 172 "parser.y"
                                                { lists.push_back(yystack_[1].value.as < adl::Expr* > ()); }
#line 1398 "Parser.cpp"
    break;

  case 56: // criteria: criterion
#line 173 "parser.y"
                                                { lists.push_back(yystack_[0].value.as < adl::Expr* > ()); }
#line 1404 "Parser.cpp"
    break;

  case 57: // criterion: COMMAND chained_cond
#line 176 "parser.y"
                                                { yylhs.value.as < adl::Expr* > () = new CommandNode(incrementCounter(), yystack_[1].value.as < std::string > (),yystack_[0].value.as < adl::Expr* > ()); std::cout << "COMMAND: " << yystack_[1].value.as < std::string > () << "\n";}
#line 1410 "Parser.cpp"
    break;

  case 58: // criterion: TRIGGER chained_cond
#line 177 "parser.y"
                                                { yylhs.value.as < adl::Expr* > () = new CommandNode(incrementCounter(), yystack_[1].value.as < std::string > (),yystack_[0].value.as < adl::Expr* > ()); }
#line 1416 "Parser.cpp"
    break;

  case 59: // criterion: HISTO id COMMA DESC comma_sep
#line 178 "parser.y"
                                                { yylhs.value.as < adl::Expr* > () = new HistoNode(incrementCounter(),yystack_[4].value.as < std::string > (),yystack_[3].value.as < adl::Expr* > (),yystack_[1].value.as < std::string > (),histoParamList); histoParamList.clear(); }
#line 1422 "Parser.cpp"
    break;

  case 60: // criterion: BIN DESC chained_cond
#line 179 "parser.y"
                                                { yylhs.value.as < adl::Expr* > () = new CommandNode(incrementCounter(), yystack_[2].value.as < std::string > (), yystack_[0].value.as < adl::Expr* > ()); }
#line 1428 "Parser.cpp"
    break;

  case 61: // criterion: BIN chained_cond
#line 180 "parser.y"
                                                { yylhs.value.as < adl::Expr* > () = new CommandNode(incrementCounter(), yystack_[1].value.as < std::string > (), yystack_[0].value.as < adl::Expr* > ()); }
#line 1434 "Parser.cpp"
    break;

  case 62: // criterion: WEIGHT id id LPAR function RPAR
#line 181 "parser.y"
                                                { yylhs.value.as < adl::Expr* > () = new CommandNode(incrementCounter(), yystack_[5].value.as < std::string > (), yystack_[4].value.as < adl::Expr* > ());}
#line 1440 "Parser.cpp"
    break;

  case 63: // criterion: WEIGHT id num
#line 182 "parser.y"
                                                { yylhs.value.as < adl::Expr* > () = new CommandNode(incrementCounter(), yystack_[2].value.as < std::string > (), yystack_[1].value.as < adl::Expr* > ());}
#line 1446 "Parser.cpp"
    break;

  case 64: // criterion: WEIGHT id id
#line 183 "parser.y"
                                                { yylhs.value.as < adl::Expr* > () = new CommandNode(incrementCounter(), yystack_[2].value.as < std::string > (), yystack_[1].value.as < adl::Expr* > ());}
#line 1452 "Parser.cpp"
    break;

  case 65: // criterion: id
#line 184 "parser.y"
                                                { yylhs.value.as < adl::Expr* > () = new CommandNode(incrementCounter(),"SELECT",yystack_[0].value.as < adl::Expr* > ()); }
#line 1458 "Parser.cpp"
    break;

  case 66: // comma_sep: COMMA comma_sep
#line 187 "parser.y"
                                                {  }
#line 1464 "Parser.cpp"
    break;

  case 67: // comma_sep: num comma_sep
#line 188 "parser.y"
                                                { histoParamList.push_back(yystack_[1].value.as < adl::Expr* > ()); }
#line 1470 "Parser.cpp"
    break;

  case 68: // comma_sep: id comma_sep
#line 189 "parser.y"
                                                { histoParamList.push_back(yystack_[1].value.as < adl::Expr* > ()); }
#line 1476 "Parser.cpp"
    break;

  case 69: // comma_sep: function comma_sep
#line 190 "parser.y"
                                                { histoParamList.push_back(yystack_[1].value.as < adl::Expr* > ()); }
#line 1482 "Parser.cpp"
    break;

  case 70: // comma_sep: LBRACKET bins RBRACKET comma_sep
#line 191 "parser.y"
                                                { /*histoBinsLists.push_back($1);*/ }
#line 1488 "Parser.cpp"
    break;

  case 71: // comma_sep: num
#line 192 "parser.y"
                                                { histoParamList.push_back(yystack_[0].value.as < adl::Expr* > ()); }
#line 1494 "Parser.cpp"
    break;

  case 72: // comma_sep: id
#line 193 "parser.y"
                                                { histoParamList.push_back(yystack_[0].value.as < adl::Expr* > ()); }
#line 1500 "Parser.cpp"
    break;

  case 73: // comma_sep: LBRACKET bins RBRACKET
#line 194 "parser.y"
                                                { /*histoBinsLists.push_back($1);*/ }
#line 1506 "Parser.cpp"
    break;

  case 74: // comma_sep: function
#line 195 "parser.y"
                                                { histoParamList.push_back(yystack_[0].value.as < adl::Expr* > ()); }
#line 1512 "Parser.cpp"
    break;

  case 75: // bins: bins num
#line 198 "parser.y"
                                                { histoBinsLists.push_back(yystack_[0].value.as < adl::Expr* > ()); }
#line 1518 "Parser.cpp"
    break;

  case 76: // bins: num
#line 199 "parser.y"
                                                { histoBinsLists.push_back(yystack_[0].value.as < adl::Expr* > ()); }
#line 1524 "Parser.cpp"
    break;

  case 77: // chained_cond: LPAR chain RPAR
#line 202 "parser.y"
                                                            { yylhs.value.as < adl::Expr* > () = yystack_[1].value.as < adl::Expr* > (); }
#line 1530 "Parser.cpp"
    break;

  case 78: // chained_cond: LPAR chain RPAR logic_op chained_cond
#line 203 "parser.y"
                                                            { yylhs.value.as < adl::Expr* > () = new adl::BinNode(incrementCounter(), "LOGICOP",yystack_[3].value.as < adl::Expr* > (),yystack_[1].value.as < std::string > (),yystack_[0].value.as < adl::Expr* > ()); }
#line 1536 "Parser.cpp"
    break;

  case 79: // chained_cond: chain
#line 204 "parser.y"
                                                            { yylhs.value.as < adl::Expr* > () = yystack_[0].value.as < adl::Expr* > (); }
#line 1542 "Parser.cpp"
    break;

  case 80: // chained_cond: chain QUES chain COLON chain
#line 205 "parser.y"
                                                            { std::cout << "MAKING ITE ASTNODE\n"; yylhs.value.as < adl::Expr* > () = new ITENode(incrementCounter(), "ITE", yystack_[4].value.as < adl::Expr* > (), yystack_[2].value.as < adl::Expr* > (), yystack_[0].value.as < adl::Expr* > ()); }
#line 1548 "Parser.cpp"
    break;

  case 81: // chained_cond: chain QUES chain
#line 206 "parser.y"
                                                            { std::cout << "MAKING ITE ASTNODE\n"; yylhs.value.as < adl::Expr* > () = new ITENode(incrementCounter(), "ITE", yystack_[2].value.as < adl::Expr* > (), yystack_[0].value.as < adl::Expr* > (), nullptr); }
#line 1554 "Parser.cpp"
    break;

  case 82: // chained_cond: id range
#line 207 "parser.y"
                                                            { yylhs.value.as < adl::Expr* > () = new VarNode(incrementCounter(),"ID",yystack_[1].value.as < adl::Expr* > ()->getId(),"","",intLists); intLists.clear(); }
#line 1560 "Parser.cpp"
    break;

  case 83: // chain: condition
#line 210 "parser.y"
                                        { yylhs.value.as < adl::Expr* > () = yystack_[0].value.as < adl::Expr* > (); }
#line 1566 "Parser.cpp"
    break;

  case 84: // chain: condition logic_op chain
#line 211 "parser.y"
                                        { yylhs.value.as < adl::Expr* > () = new adl::BinNode(incrementCounter(), "LOGICOP",yystack_[2].value.as < adl::Expr* > (),yystack_[1].value.as < std::string > (),yystack_[0].value.as < adl::Expr* > ()); }
#line 1572 "Parser.cpp"
    break;

  case 85: // chain: not condition
#line 212 "parser.y"
                                        { paramlist.push_back(yystack_[0].value.as < adl::Expr* > ()); yylhs.value.as < adl::Expr* > () = new adl::FunctionNode(incrementCounter(), "FUNCTION", yystack_[1].value.as < adl::Expr* > (), paramlist); paramlist.clear(); }
#line 1578 "Parser.cpp"
    break;

  case 86: // not: NOT
#line 215 "parser.y"
                                        { yylhs.value.as < adl::Expr* > () = new adl::VarNode(incrementCounter(), "ID", "not", "", "", {},""); }
#line 1584 "Parser.cpp"
    break;

  case 87: // condition: expr
#line 218 "parser.y"
                                        { yylhs.value.as < adl::Expr* > () = yystack_[0].value.as < adl::Expr* > (); }
#line 1590 "Parser.cpp"
    break;

  case 88: // condition: expr compare_op condition
#line 220 "parser.y"
                                        { yylhs.value.as < adl::Expr* > () = new adl::BinNode(incrementCounter(), "COMPAREOP",yystack_[2].value.as < adl::Expr* > (),yystack_[1].value.as < std::string > (),yystack_[0].value.as < adl::Expr* > ()); }
#line 1596 "Parser.cpp"
    break;

  case 89: // condition: expr INCLUSIVE num num
#line 221 "parser.y"
                                        {
                                          Expr* en = yystack_[3].value.as < adl::Expr* > ()->clone(incrementCounter());
                                          Expr* comp1 = new adl::BinNode(incrementCounter(), "COMPAREOP",yystack_[3].value.as < adl::Expr* > (),">=",yystack_[1].value.as < adl::Expr* > ());
                                          Expr* comp2 = new adl::BinNode(incrementCounter(), "COMPAREOP",en,"<=",yystack_[0].value.as < adl::Expr* > ());
                                          yylhs.value.as < adl::Expr* > () = new adl::BinNode(incrementCounter(), "LOGICOP",comp1,"AND",comp2);
                                        }
#line 1607 "Parser.cpp"
    break;

  case 90: // condition: expr EXCLUSIVE num num
#line 227 "parser.y"
                                        {
                                          Expr* en = yystack_[3].value.as < adl::Expr* > ()->clone(incrementCounter());
                                          Expr* comp1 = new adl::BinNode(incrementCounter(), "COMPAREOP",en,"<=",yystack_[1].value.as < adl::Expr* > ());
                                          Expr* comp2 = new adl::BinNode(incrementCounter(), "COMPAREOP",yystack_[3].value.as < adl::Expr* > (),">=",yystack_[0].value.as < adl::Expr* > ());
                                          yylhs.value.as < adl::Expr* > () = new adl::BinNode(incrementCounter(), "LOGICOP",comp1,"OR",comp2);
                                        }
#line 1618 "Parser.cpp"
    break;

  case 91: // compare_op: GT
#line 235 "parser.y"
                                  { yylhs.value.as < std::string > () = yystack_[0].value.as < std::string > (); }
#line 1624 "Parser.cpp"
    break;

  case 92: // compare_op: LT
#line 236 "parser.y"
                                  { yylhs.value.as < std::string > () = yystack_[0].value.as < std::string > (); }
#line 1630 "Parser.cpp"
    break;

  case 93: // compare_op: GE
#line 237 "parser.y"
                                  { yylhs.value.as < std::string > () = yystack_[0].value.as < std::string > (); }
#line 1636 "Parser.cpp"
    break;

  case 94: // compare_op: LE
#line 238 "parser.y"
                                  { yylhs.value.as < std::string > () = yystack_[0].value.as < std::string > (); }
#line 1642 "Parser.cpp"
    break;

  case 95: // compare_op: EQ
#line 239 "parser.y"
                                  { yylhs.value.as < std::string > () = yystack_[0].value.as < std::string > (); }
#line 1648 "Parser.cpp"
    break;

  case 96: // compare_op: NE
#line 240 "parser.y"
                                  { yylhs.value.as < std::string > () = yystack_[0].value.as < std::string > (); }
#line 1654 "Parser.cpp"
    break;

  case 97: // logic_op: AND
#line 243 "parser.y"
                                  { yylhs.value.as < std::string > () = yystack_[0].value.as < std::string > (); }
#line 1660 "Parser.cpp"
    break;

  case 98: // logic_op: OR
#line 244 "parser.y"
                                  { yylhs.value.as < std::string > () = yystack_[0].value.as < std::string > (); }
#line 1666 "Parser.cpp"
    break;

  case 99: // expr: factor
#line 247 "parser.y"
                                  { yylhs.value.as < adl::Expr* > () = yystack_[0].value.as < adl::Expr* > (); }
#line 1672 "Parser.cpp"
    break;

  case 100: // expr: factor expr_op expr
#line 248 "parser.y"
                                  { yylhs.value.as < adl::Expr* > () = new adl::BinNode(incrementCounter(), "EXPROP",yystack_[2].value.as < adl::Expr* > (),yystack_[1].value.as < std::string > (),yystack_[0].value.as < adl::Expr* > ()); }
#line 1678 "Parser.cpp"
    break;

  case 101: // expr_op: PLUS
#line 251 "parser.y"
                                  { yylhs.value.as < std::string > () = yystack_[0].value.as < std::string > (); }
#line 1684 "Parser.cpp"
    break;

  case 102: // expr_op: SUBTRACT
#line 252 "parser.y"
                                  { yylhs.value.as < std::string > () = yystack_[0].value.as < std::string > (); }
#line 1690 "Parser.cpp"
    break;

  case 103: // factor: term
#line 255 "parser.y"
                                  { yylhs.value.as < adl::Expr* > () = yystack_[0].value.as < adl::Expr* > (); }
#line 1696 "Parser.cpp"
    break;

  case 104: // factor: term factor_op factor
#line 256 "parser.y"
                                  { yylhs.value.as < adl::Expr* > () = new adl::BinNode(incrementCounter(), "FACTOROP",yystack_[2].value.as < adl::Expr* > (),yystack_[1].value.as < std::string > (),yystack_[0].value.as < adl::Expr* > ()); }
#line 1702 "Parser.cpp"
    break;

  case 105: // factor_op: MULTIPLY
#line 259 "parser.y"
                                  { yylhs.value.as < std::string > () = yystack_[0].value.as < std::string > (); }
#line 1708 "Parser.cpp"
    break;

  case 106: // factor_op: DIVIDE
#line 260 "parser.y"
                                  { yylhs.value.as < std::string > () = yystack_[0].value.as < std::string > (); }
#line 1714 "Parser.cpp"
    break;

  case 107: // factor_op: POW
#line 261 "parser.y"
                                  { yylhs.value.as < std::string > () = yystack_[0].value.as < std::string > (); }
#line 1720 "Parser.cpp"
    break;

  case 108: // term: id_qualifiers
#line 264 "parser.y"
                                  { yylhs.value.as < adl::Expr* > () = yystack_[0].value.as < adl::Expr* > (); }
#line 1726 "Parser.cpp"
    break;

  case 109: // term: function
#line 265 "parser.y"
                                  { yylhs.value.as < adl::Expr* > () = yystack_[0].value.as < adl::Expr* > (); std::cout << "FUNCTION CALL\n"; }
#line 1732 "Parser.cpp"
    break;

  case 110: // term: function dot_op
#line 266 "parser.y"
                                  { yylhs.value.as < adl::Expr* > () = yystack_[1].value.as < adl::Expr* > (); }
#line 1738 "Parser.cpp"
    break;

  case 111: // term: num
#line 267 "parser.y"
                                  { yylhs.value.as < adl::Expr* > () = yystack_[0].value.as < adl::Expr* > (); }
#line 1744 "Parser.cpp"
    break;

  case 112: // term: LPAR expr RPAR
#line 268 "parser.y"
                                  { yylhs.value.as < adl::Expr* > () = yystack_[1].value.as < adl::Expr* > (); }
#line 1750 "Parser.cpp"
    break;

  case 113: // id_qualifiers: id_qualifier
#line 271 "parser.y"
                                              { yylhs.value.as < adl::Expr* > () = yystack_[0].value.as < adl::Expr* > (); }
#line 1756 "Parser.cpp"
    break;

  case 114: // id_qualifiers: id_qualifier id_qualifiers
#line 272 "parser.y"
                                              { yylhs.value.as < adl::Expr* > () = new VarNode(incrementCounter(),"ID",yystack_[1].value.as < adl::Expr* > ()->getId(),"",yystack_[0].value.as < adl::Expr* > ()->getId(), {},""); std::cout << "ID list\n"; }
#line 1762 "Parser.cpp"
    break;

  case 115: // id_qualifier: dot_op
#line 275 "parser.y"
                                                                 { yylhs.value.as < adl::Expr* > () = yystack_[0].value.as < adl::Expr* > (); }
#line 1768 "Parser.cpp"
    break;

  case 116: // id_qualifier: id
#line 277 "parser.y"
                                                                 { yylhs.value.as < adl::Expr* > () = yystack_[0].value.as < adl::Expr* > (); }
#line 1774 "Parser.cpp"
    break;

  case 117: // id_qualifier: id LBRACKET index RBRACKET
#line 278 "parser.y"
                                                                 { VarNode* vn = static_cast<VarNode*>(yystack_[3].value.as < adl::Expr* > ()); yylhs.value.as < adl::Expr* > () = new VarNode(incrementCounter(),"ID",vn->getId(),vn->getAlias(),vn->getDotOp(),{yystack_[1].value.as < int > ()},vn->getType()); }
#line 1780 "Parser.cpp"
    break;

  case 118: // id_qualifier: id UNDERSCORE index COLON index
#line 279 "parser.y"
                                                                 { VarNode* vn = static_cast<VarNode*>(yystack_[4].value.as < adl::Expr* > ()); yylhs.value.as < adl::Expr* > () = new VarNode(incrementCounter(),"ID",vn->getId(),vn->getAlias(),vn->getDotOp(),{yystack_[2].value.as < int > (), yystack_[0].value.as < int > ()},vn->getType()); }
#line 1786 "Parser.cpp"
    break;

  case 119: // id_qualifier: id UNDERSCORE index
#line 280 "parser.y"
                                                                 { VarNode* vn = static_cast<VarNode*>(yystack_[2].value.as < adl::Expr* > ()); yylhs.value.as < adl::Expr* > () = new VarNode(incrementCounter(),"ID",vn->getId(),vn->getAlias(),vn->getDotOp(),{yystack_[0].value.as < int > ()},vn->getType()); }
#line 1792 "Parser.cpp"
    break;

  case 120: // id_qualifier: id LBRACKET index COLON index RBRACKET
#line 281 "parser.y"
                                                                 { VarNode* vn = static_cast<VarNode*>(yystack_[5].value.as < adl::Expr* > ()); yylhs.value.as < adl::Expr* > () = new VarNode(incrementCounter(),"ID",vn->getId(),vn->getAlias(),vn->getDotOp(),{yystack_[3].value.as < int > (), yystack_[1].value.as < int > ()},vn->getType()); }
#line 1798 "Parser.cpp"
    break;

  case 121: // dot_op: DOT id
#line 287 "parser.y"
                            { yylhs.value.as < adl::Expr* > () = yystack_[0].value.as < adl::Expr* > (); }
#line 1804 "Parser.cpp"
    break;

  case 122: // range: range num
#line 290 "parser.y"
                            { yylhs.value.as < adl::Expr* > () = yystack_[0].value.as < adl::Expr* > (); intLists.push_back(static_cast<int>(yystack_[0].value.as < adl::Expr* > ()->value())); }
#line 1810 "Parser.cpp"
    break;

  case 123: // range: num
#line 291 "parser.y"
                            { yylhs.value.as < adl::Expr* > () = yystack_[0].value.as < adl::Expr* > (); intLists.push_back(static_cast<int>(yystack_[0].value.as < adl::Expr* > ()->value())); }
#line 1816 "Parser.cpp"
    break;

  case 124: // boolean: TRUE
#line 294 "parser.y"
                            { yylhs.value.as < bool > () = 1; }
#line 1822 "Parser.cpp"
    break;

  case 125: // boolean: FALSE
#line 295 "parser.y"
                            { yylhs.value.as < bool > () = 0; }
#line 1828 "Parser.cpp"
    break;

  case 126: // num: int
#line 298 "parser.y"
                            { yylhs.value.as < adl::Expr* > () = yystack_[0].value.as < adl::Expr* > (); }
#line 1834 "Parser.cpp"
    break;

  case 127: // num: real
#line 299 "parser.y"
                            { yylhs.value.as < adl::Expr* > () = yystack_[0].value.as < adl::Expr* > (); }
#line 1840 "Parser.cpp"
    break;

  case 128: // index: SUBTRACT INT
#line 301 "parser.y"
                            { yylhs.value.as < int > () = -yystack_[0].value.as < int > (); }
#line 1846 "Parser.cpp"
    break;

  case 129: // index: INT
#line 302 "parser.y"
                            { yylhs.value.as < int > () = yystack_[0].value.as < int > (); }
#line 1852 "Parser.cpp"
    break;

  case 130: // index: %empty
#line 303 "parser.y"
                            { yylhs.value.as < int > () = 6213;}
#line 1858 "Parser.cpp"
    break;

  case 131: // int: INT
#line 306 "parser.y"
                            { yylhs.value.as < adl::Expr* > () = new adl::NumNode(incrementCounter(), "INT", yystack_[0].value.as < int > ()); }
#line 1864 "Parser.cpp"
    break;

  case 132: // real: REAL
#line 309 "parser.y"
                            { yylhs.value.as < adl::Expr* > () = new adl::NumNode(incrementCounter(), "REAL", yystack_[0].value.as < double > ()); }
#line 1870 "Parser.cpp"
    break;

  case 133: // id: ID
#line 312 "parser.y"
                            { yylhs.value.as < adl::Expr* > () = new adl::VarNode(incrementCounter(), "ID", yystack_[0].value.as < std::string > (), "", "", {},""); std::cout << "ID: " << yystack_[0].value.as < std::string > () << "\n"; }
#line 1876 "Parser.cpp"
    break;


#line 1880 "Parser.cpp"

            default:
              break;
            }
        }
#if YY_EXCEPTIONS
      catch (const syntax_error& yyexc)
        {
          YYCDEBUG << "Caught exception: " << yyexc.what() << '\n';
          error (yyexc);
          YYERROR;
        }
#endif // YY_EXCEPTIONS
      YY_SYMBOL_PRINT ("-> $$ =", yylhs);
      yypop_ (yylen);
      yylen = 0;

      // Shift the result of the reduction.
      yypush_ (YY_NULLPTR, YY_MOVE (yylhs));
    }
    goto yynewstate;


  /*--------------------------------------.
  | yyerrlab -- here on detecting error.  |
  `--------------------------------------*/
  yyerrlab:
    // If not already recovering from an error, report this error.
    if (!yyerrstatus_)
      {
        ++yynerrs_;
        context yyctx (*this, yyla);
        std::string msg = yysyntax_error_ (yyctx);
        error (yyla.location, YY_MOVE (msg));
      }


    yyerror_range[1].location = yyla.location;
    if (yyerrstatus_ == 3)
      {
        /* If just tried and failed to reuse lookahead token after an
           error, discard it.  */

        // Return failure if at end of input.
        if (yyla.kind () == symbol_kind::S_YYEOF)
          YYABORT;
        else if (!yyla.empty ())
          {
            yy_destroy_ ("Error: discarding", yyla);
            yyla.clear ();
          }
      }

    // Else will try to reuse lookahead token after shifting the error token.
    goto yyerrlab1;


  /*---------------------------------------------------.
  | yyerrorlab -- error raised explicitly by YYERROR.  |
  `---------------------------------------------------*/
  yyerrorlab:
    /* Pacify compilers when the user code never invokes YYERROR and
       the label yyerrorlab therefore never appears in user code.  */
    if (false)
      YYERROR;

    /* Do not reclaim the symbols of the rule whose action triggered
       this YYERROR.  */
    yypop_ (yylen);
    yylen = 0;
    YY_STACK_PRINT ();
    goto yyerrlab1;


  /*-------------------------------------------------------------.
  | yyerrlab1 -- common code for both syntax error and YYERROR.  |
  `-------------------------------------------------------------*/
  yyerrlab1:
    yyerrstatus_ = 3;   // Each real token shifted decrements this.
    // Pop stack until we find a state that shifts the error token.
    for (;;)
      {
        yyn = yypact_[+yystack_[0].state];
        if (!yy_pact_value_is_default_ (yyn))
          {
            yyn += symbol_kind::S_YYerror;
            if (0 <= yyn && yyn <= yylast_
                && yycheck_[yyn] == symbol_kind::S_YYerror)
              {
                yyn = yytable_[yyn];
                if (0 < yyn)
                  break;
              }
          }

        // Pop the current state because it cannot handle the error token.
        if (yystack_.size () == 1)
          YYABORT;

        yyerror_range[1].location = yystack_[0].location;
        yy_destroy_ ("Error: popping", yystack_[0]);
        yypop_ ();
        YY_STACK_PRINT ();
      }
    {
      stack_symbol_type error_token;

      yyerror_range[2].location = yyla.location;
      YYLLOC_DEFAULT (error_token.location, yyerror_range, 2);

      // Shift the error token.
      error_token.state = state_type (yyn);
      yypush_ ("Shifting", YY_MOVE (error_token));
    }
    goto yynewstate;


  /*-------------------------------------.
  | yyacceptlab -- YYACCEPT comes here.  |
  `-------------------------------------*/
  yyacceptlab:
    yyresult = 0;
    goto yyreturn;


  /*-----------------------------------.
  | yyabortlab -- YYABORT comes here.  |
  `-----------------------------------*/
  yyabortlab:
    yyresult = 1;
    goto yyreturn;


  /*-----------------------------------------------------.
  | yyreturn -- parsing is finished, return the result.  |
  `-----------------------------------------------------*/
  yyreturn:
    if (!yyla.empty ())
      yy_destroy_ ("Cleanup: discarding lookahead", yyla);

    /* Do not reclaim the symbols of the rule whose action triggered
       this YYABORT or YYACCEPT.  */
    yypop_ (yylen);
    YY_STACK_PRINT ();
    while (1 < yystack_.size ())
      {
        yy_destroy_ ("Cleanup: popping", yystack_[0]);
        yypop_ ();
      }

    return yyresult;
  }
#if YY_EXCEPTIONS
    catch (...)
      {
        YYCDEBUG << "Exception caught: cleaning lookahead and stack\n";
        // Do not try to display the values of the reclaimed symbols,
        // as their printers might throw an exception.
        if (!yyla.empty ())
          yy_destroy_ (YY_NULLPTR, yyla);

        while (1 < yystack_.size ())
          {
            yy_destroy_ (YY_NULLPTR, yystack_[0]);
            yypop_ ();
          }
        throw;
      }
#endif // YY_EXCEPTIONS
  }

  void
   Parser ::error (const syntax_error& yyexc)
  {
    error (yyexc.location, yyexc.what ());
  }

  /* Return YYSTR after stripping away unnecessary quotes and
     backslashes, so that it's suitable for yyerror.  The heuristic is
     that double-quoting is unnecessary unless the string contains an
     apostrophe, a comma, or backslash (other than backslash-backslash).
     YYSTR is taken from yytname.  */
  std::string
   Parser ::yytnamerr_ (const char *yystr)
  {
    if (*yystr == '"')
      {
        std::string yyr;
        char const *yyp = yystr;

        for (;;)
          switch (*++yyp)
            {
            case '\'':
            case ',':
              goto do_not_strip_quotes;

            case '\\':
              if (*++yyp != '\\')
                goto do_not_strip_quotes;
              else
                goto append;

            append:
            default:
              yyr += *yyp;
              break;

            case '"':
              return yyr;
            }
      do_not_strip_quotes: ;
      }

    return yystr;
  }

  std::string
   Parser ::symbol_name (symbol_kind_type yysymbol)
  {
    return yytnamerr_ (yytname_[yysymbol]);
  }



  //  Parser ::context.
   Parser ::context::context (const  Parser & yyparser, const symbol_type& yyla)
    : yyparser_ (yyparser)
    , yyla_ (yyla)
  {}

  int
   Parser ::context::expected_tokens (symbol_kind_type yyarg[], int yyargn) const
  {
    // Actual number of expected tokens
    int yycount = 0;

    const int yyn = yypact_[+yyparser_.yystack_[0].state];
    if (!yy_pact_value_is_default_ (yyn))
      {
        /* Start YYX at -YYN if negative to avoid negative indexes in
           YYCHECK.  In other words, skip the first -YYN actions for
           this state because they are default actions.  */
        const int yyxbegin = yyn < 0 ? -yyn : 0;
        // Stay within bounds of both yycheck and yytname.
        const int yychecklim = yylast_ - yyn + 1;
        const int yyxend = yychecklim < YYNTOKENS ? yychecklim : YYNTOKENS;
        for (int yyx = yyxbegin; yyx < yyxend; ++yyx)
          if (yycheck_[yyx + yyn] == yyx && yyx != symbol_kind::S_YYerror
              && !yy_table_value_is_error_ (yytable_[yyx + yyn]))
            {
              if (!yyarg)
                ++yycount;
              else if (yycount == yyargn)
                return 0;
              else
                yyarg[yycount++] = YY_CAST (symbol_kind_type, yyx);
            }
      }

    if (yyarg && yycount == 0 && 0 < yyargn)
      yyarg[0] = symbol_kind::S_YYEMPTY;
    return yycount;
  }






  int
   Parser ::yy_syntax_error_arguments_ (const context& yyctx,
                                                 symbol_kind_type yyarg[], int yyargn) const
  {
    /* There are many possibilities here to consider:
       - If this state is a consistent state with a default action, then
         the only way this function was invoked is if the default action
         is an error action.  In that case, don't check for expected
         tokens because there are none.
       - The only way there can be no lookahead present (in yyla) is
         if this state is a consistent state with a default action.
         Thus, detecting the absence of a lookahead is sufficient to
         determine that there is no unexpected or expected token to
         report.  In that case, just report a simple "syntax error".
       - Don't assume there isn't a lookahead just because this state is
         a consistent state with a default action.  There might have
         been a previous inconsistent state, consistent state with a
         non-default action, or user semantic action that manipulated
         yyla.  (However, yyla is currently not documented for users.)
       - Of course, the expected token list depends on states to have
         correct lookahead information, and it depends on the parser not
         to perform extra reductions after fetching a lookahead from the
         scanner and before detecting a syntax error.  Thus, state merging
         (from LALR or IELR) and default reductions corrupt the expected
         token list.  However, the list is correct for canonical LR with
         one exception: it will still contain any token that will not be
         accepted due to an error action in a later state.
    */

    if (!yyctx.lookahead ().empty ())
      {
        if (yyarg)
          yyarg[0] = yyctx.token ();
        int yyn = yyctx.expected_tokens (yyarg ? yyarg + 1 : yyarg, yyargn - 1);
        return yyn + 1;
      }
    return 0;
  }

  // Generate an error message.
  std::string
   Parser ::yysyntax_error_ (const context& yyctx) const
  {
    // Its maximum.
    enum { YYARGS_MAX = 5 };
    // Arguments of yyformat.
    symbol_kind_type yyarg[YYARGS_MAX];
    int yycount = yy_syntax_error_arguments_ (yyctx, yyarg, YYARGS_MAX);

    char const* yyformat = YY_NULLPTR;
    switch (yycount)
      {
#define YYCASE_(N, S)                         \
        case N:                               \
          yyformat = S;                       \
        break
      default: // Avoid compiler warnings.
        YYCASE_ (0, YY_("syntax error"));
        YYCASE_ (1, YY_("syntax error, unexpected %s"));
        YYCASE_ (2, YY_("syntax error, unexpected %s, expecting %s"));
        YYCASE_ (3, YY_("syntax error, unexpected %s, expecting %s or %s"));
        YYCASE_ (4, YY_("syntax error, unexpected %s, expecting %s or %s or %s"));
        YYCASE_ (5, YY_("syntax error, unexpected %s, expecting %s or %s or %s or %s"));
#undef YYCASE_
      }

    std::string yyres;
    // Argument number.
    std::ptrdiff_t yyi = 0;
    for (char const* yyp = yyformat; *yyp; ++yyp)
      if (yyp[0] == '%' && yyp[1] == 's' && yyi < yycount)
        {
          yyres += symbol_name (yyarg[yyi++]);
          ++yyp;
        }
      else
        yyres += *yyp;
    return yyres;
  }


  const signed char  Parser ::yypact_ninf_ = -113;

  const signed char  Parser ::yytable_ninf_ = -1;

  const short
   Parser ::yypact_[] =
  {
     258,   -10,   -10,   -10,   -10,    -6,   -10,     5,    17,   205,
    -113,   205,  -113,   129,   205,   205,   144,  -113,   -18,   276,
       6,   276,    16,   276,     5,     5,     5,  -113,  -113,  -113,
     205,  -113,  -113,  -113,  -113,  -113,  -113,   178,   178,   115,
     -10,    56,   -10,   115,  -113,   276,  -113,    74,   136,   276,
       6,  -113,    26,  -113,  -113,  -113,  -113,  -113,   178,    30,
     153,   -10,  -113,  -113,    13,  -113,   242,   107,   203,  -113,
       9,  -113,  -113,  -113,  -113,    15,  -113,   153,  -113,  -113,
      27,   178,   119,   100,    39,   115,  -113,    30,  -113,  -113,
      37,  -113,    -3,    78,  -113,  -113,  -113,    82,    81,    63,
      79,    96,    94,    97,  -113,  -113,  -113,  -113,  -113,  -113,
    -113,  -113,   123,   123,   178,  -113,  -113,   178,  -113,  -113,
    -113,   178,  -113,   -22,   153,     7,     7,   131,   219,   153,
    -113,  -113,  -113,   153,   123,  -113,   152,  -113,  -113,   148,
     -10,    30,  -113,   132,  -113,  -113,   -10,   126,  -113,  -113,
    -113,  -113,   -10,   153,   123,   123,  -113,  -113,  -113,   165,
     134,  -113,    68,   150,   119,   155,  -113,  -113,   194,    57,
     142,   180,    30,   151,   201,  -113,  -113,  -113,  -113,  -113,
    -113,  -113,     7,     7,   115,   153,   123,   194,   194,  -113,
     194,   172,   197,   200,   -10,  -113,  -113,   -10,   124,   181,
    -113,  -113,  -113,    65,  -113,  -113,  -113,  -113,  -113,  -113,
     215,   216,  -113,  -113,   167,  -113,   194,  -113,  -113,  -113,
    -113,  -113,   167,  -113,  -113
  };

  const unsigned char
   Parser ::yydefact_[] =
  {
       0,     0,     0,     0,     0,     0,     0,     0,     0,     6,
       5,    16,    20,    18,    25,    14,    21,   133,     0,     0,
       0,     0,     0,     0,    11,    12,    13,     7,     1,     2,
      25,    17,    25,    19,     4,    15,    22,     0,     0,     0,
       0,     0,     0,     0,    53,    56,    65,     0,     0,    37,
      41,    54,     0,    39,     8,     9,    10,     3,     0,     0,
       0,     0,   131,   132,   109,    23,    87,    99,   103,   108,
     113,   115,   111,   126,   127,   116,    24,     0,    86,    57,
      79,     0,    83,   116,     0,     0,    61,     0,    58,    55,
       0,    42,    46,     0,    43,    38,    40,     0,     0,     0,
       0,     0,     0,    36,   121,   110,    91,    92,    93,    94,
      95,    96,     0,     0,     0,   101,   102,     0,   105,   106,
     107,     0,   114,   116,     0,   130,   130,     0,    87,     0,
      85,    97,    98,     0,    82,   123,     0,    60,    63,    64,
       0,     0,    48,    49,    52,    51,     0,     0,   112,    32,
      33,    34,     0,     0,     0,     0,    88,   100,   104,     0,
       0,   129,     0,   119,    77,    81,    84,   122,     0,     0,
       0,     0,     0,     0,     0,    31,    35,    89,    90,    30,
     128,   117,   130,   130,     0,     0,     0,     0,    74,    59,
      71,    72,     0,     0,     0,    47,    50,     0,     0,     0,
     118,    78,    80,     0,    76,    66,    69,    67,    68,    62,
       0,     0,   124,   125,     0,   120,    73,    75,    44,    45,
      29,    26,    28,    70,    27
  };

  const short
   Parser ::yypgoto_[] =
  {
    -113,  -113,  -113,   247,   235,   232,   212,  -113,    34,    29,
    -113,   -70,   -73,  -113,   198,  -113,   218,  -111,  -113,  -113,
      62,  -113,   -11,  -113,   -35,   -56,  -113,   -27,  -113,   104,
     -51,  -113,   139,  -113,  -113,   199,  -113,   223,  -113,  -113,
     -60,  -112,   229,   230,    -1
  };

  const unsigned char
   Parser ::yydefgoto_[] =
  {
       0,     8,     9,    27,    10,    11,    12,    13,    32,   221,
     222,    64,   102,    15,    49,    50,    91,   142,   143,    16,
      44,    45,   189,   203,    79,    80,    81,    82,   114,   133,
      66,   117,    67,   121,    68,    69,    70,    71,   134,   214,
      72,   162,    73,    74,    75
  };

  const unsigned char
   Parser ::yytable_[] =
  {
      18,    19,    20,    21,   103,    23,    86,    98,    88,    17,
      65,    76,    47,    22,   163,    37,    17,    28,    46,   141,
      46,   127,    46,   135,    24,   125,   128,   138,    17,    52,
     171,    25,   144,    38,    14,   126,   160,   124,    83,    84,
      83,    87,    83,    30,    46,    97,    92,    92,    46,    17,
     137,   159,   154,   155,   130,    62,    63,    48,   101,   140,
     104,   196,   125,    61,    26,   161,   157,    61,   103,   123,
     199,   200,   126,   165,   167,    17,    17,   166,    77,   129,
     176,   144,    85,    51,    83,    53,   139,   156,    62,    63,
      90,   145,   136,    17,   177,   178,   147,   103,   188,   192,
     146,    78,    59,    59,   148,    60,    60,    89,   190,   149,
      61,    95,   144,   216,    62,    63,   181,   188,   188,   182,
     188,   188,   124,    62,    63,   150,   204,   190,   190,   202,
     190,   190,     1,     2,    17,   115,   116,    77,     4,   170,
     145,     5,   151,   217,   152,   173,   188,   125,     2,   201,
     153,   175,    93,     4,   164,    17,   190,   126,    62,    63,
      78,    59,   131,   132,    60,   212,   213,   191,   193,    61,
     169,   145,    17,    62,    63,    58,   205,   206,   168,   207,
     208,    62,    63,    83,   174,   172,   191,   191,   179,   191,
     191,    17,   180,   210,   124,   194,   211,    17,    78,    59,
      58,   183,    60,   195,   197,   223,   185,    61,     1,     2,
       3,    62,    63,    17,     4,   191,   198,     5,    59,   186,
     209,    60,   124,     6,    59,   187,   220,    60,    36,   215,
      62,    63,    61,   118,   119,   120,    62,    63,   218,   219,
      59,   186,   148,    60,    29,    33,    31,   187,    96,    34,
      35,   224,    62,    63,   106,   107,   108,   109,   110,   111,
     158,     1,     2,     3,     0,    57,    94,     4,   184,   122,
       5,    54,    55,    56,   112,   113,     6,   106,   107,   108,
     109,   110,   111,    39,    40,     7,    41,   105,    99,   100,
       0,     0,     0,    42,    43,    17,     0,   112,   113
  };

  const short
   Parser ::yycheck_[] =
  {
       1,     2,     3,     4,    60,     6,    41,    58,    43,    19,
      37,    38,     6,    19,   126,    33,    19,     0,    19,    22,
      21,    77,    23,    83,    19,    47,    77,    87,    19,    13,
     141,    26,    92,    51,     0,    57,    29,    22,    39,    40,
      41,    42,    43,     9,    45,    19,    47,    48,    49,    19,
      85,   124,   112,   113,    81,    58,    59,    51,    59,    22,
      61,   172,    47,    54,    59,    58,   117,    54,   124,    70,
     182,   183,    57,   129,   134,    19,    19,   133,    22,    52,
     153,   141,    26,    21,    85,    23,    87,   114,    58,    59,
      16,    92,    53,    19,   154,   155,    14,   153,   168,   169,
      22,    45,    46,    46,    23,    49,    49,    45,   168,    46,
      54,    49,   172,    48,    58,    59,    48,   187,   188,    51,
     190,   191,    22,    58,    59,    46,   186,   187,   188,   185,
     190,   191,     3,     4,    19,    28,    29,    22,     9,   140,
     141,    12,    46,   203,    50,   146,   216,    47,     4,   184,
      53,   152,    16,     9,    23,    19,   216,    57,    58,    59,
      45,    46,    43,    44,    49,    41,    42,   168,   169,    54,
      22,   172,    19,    58,    59,    22,   187,   188,    26,   190,
     191,    58,    59,   184,    58,    53,   187,   188,    23,   190,
     191,    19,    58,   194,    22,    53,   197,    19,    45,    46,
      22,    51,    49,    23,    53,   216,    51,    54,     3,     4,
       5,    58,    59,    19,     9,   216,    15,    12,    46,    47,
      23,    49,    22,    18,    46,    53,    59,    49,    16,    48,
      58,    59,    54,    30,    31,    32,    58,    59,    23,    23,
      46,    47,    23,    49,     9,    13,    11,    53,    50,    14,
      15,   222,    58,    59,    35,    36,    37,    38,    39,    40,
     121,     3,     4,     5,    -1,    30,    48,     9,   164,    70,
      12,    24,    25,    26,    55,    56,    18,    35,    36,    37,
      38,    39,    40,     7,     8,    27,    10,    64,    59,    59,
      -1,    -1,    -1,    17,    18,    19,    -1,    55,    56
  };

  const signed char
   Parser ::yystos_[] =
  {
       0,     3,     4,     5,     9,    12,    18,    27,    61,    62,
      64,    65,    66,    67,    68,    73,    79,    19,   104,   104,
     104,   104,    19,   104,    19,    26,    59,    63,     0,    64,
      68,    64,    68,    65,    64,    64,    66,    33,    51,     7,
       8,    10,    17,    18,    80,    81,   104,     6,    51,    74,
      75,    80,    13,    80,    63,    63,    63,    64,    22,    46,
      49,    54,    58,    59,    71,    87,    90,    92,    94,    95,
      96,    97,   100,   102,   103,   104,    87,    22,    45,    84,
      85,    86,    87,   104,   104,    26,    84,   104,    84,    80,
      16,    76,   104,    16,    76,    80,    74,    19,    90,   102,
     103,   104,    72,    85,   104,    97,    35,    36,    37,    38,
      39,    40,    55,    56,    88,    28,    29,    91,    30,    31,
      32,    93,    95,   104,    22,    47,    57,    85,    90,    52,
      87,    43,    44,    89,    98,   100,    53,    84,   100,   104,
      22,    22,    77,    78,   100,   104,    22,    14,    23,    46,
      46,    46,    50,    53,   100,   100,    87,    90,    92,    72,
      29,    58,   101,   101,    23,    85,    85,   100,    26,    22,
     104,    77,    53,   104,    58,   104,    72,   100,   100,    23,
      58,    48,    51,    51,    89,    51,    47,    53,    71,    82,
     100,   104,    71,   104,    53,    23,    77,    53,    15,   101,
     101,    84,    85,    83,   100,    82,    82,    82,    82,    23,
     104,   104,    41,    42,    99,    48,    48,   100,    23,    23,
      59,    69,    70,    82,    69
  };

  const signed char
   Parser ::yyr1_[] =
  {
       0,    60,    61,    61,    61,    61,    61,    62,    63,    63,
      63,    63,    63,    63,    64,    64,    64,    64,    65,    65,
      65,    66,    66,    67,    67,    67,    68,    69,    69,    70,
      71,    71,    71,    71,    71,    72,    72,    73,    73,    73,
      74,    74,    75,    75,    75,    75,    76,    76,    76,    77,
      77,    78,    78,    79,    79,    80,    80,    81,    81,    81,
      81,    81,    81,    81,    81,    81,    82,    82,    82,    82,
      82,    82,    82,    82,    82,    83,    83,    84,    84,    84,
      84,    84,    84,    85,    85,    85,    86,    87,    87,    87,
      87,    88,    88,    88,    88,    88,    88,    89,    89,    90,
      90,    91,    91,    92,    92,    93,    93,    93,    94,    94,
      94,    94,    94,    95,    95,    96,    96,    96,    96,    96,
      96,    97,    98,    98,    99,    99,   100,   100,   101,   101,
     101,   102,   103,   104
  };

  const signed char
   Parser ::yyr2_[] =
  {
       0,     2,     2,     3,     2,     1,     1,     2,     2,     2,
       2,     1,     1,     1,     1,     2,     1,     2,     1,     2,
       1,     1,     2,     4,     4,     1,     9,     2,     1,     1,
       4,     4,     3,     3,     3,     3,     1,     3,     4,     3,
       2,     1,     2,     2,     7,     7,     1,     4,     2,     1,
       3,     1,     1,     3,     3,     2,     1,     2,     2,     5,
       3,     2,     6,     3,     3,     1,     2,     2,     2,     2,
       4,     1,     1,     3,     1,     2,     1,     3,     5,     1,
       5,     3,     2,     1,     3,     2,     1,     1,     3,     4,
       4,     1,     1,     1,     1,     1,     1,     1,     1,     1,
       3,     1,     1,     1,     3,     1,     1,     1,     1,     1,
       2,     1,     3,     1,     2,     1,     1,     4,     5,     3,
       6,     2,     2,     1,     1,     1,     1,     1,     2,     1,
       0,     1,     1,     1
  };


#if YYDEBUG || 1
  // YYTNAME[SYMBOL-NUM] -- String name of the symbol SYMBOL-NUM.
  // First, the terminals, then, starting at \a YYNTOKENS, nonterminals.
  const char*
  const  Parser ::yytname_[] =
  {
  "\"end of file\"", "error", "\"invalid token\"", "DEFINE", "REGION",
  "OBJECT", "TAKE", "COMMAND", "HISTO", "HISTOLIST", "BIN", "QUO", "TABLE",
  "TABLETYPE", "NVARS", "ERRORS", "UNION", "WEIGHT", "TRIGGER", "ID",
  "ERROR", "FLAG", "LPAR", "RPAR", "VAR", "QUOTE", "DESC", "INFO", "PLUS",
  "SUBTRACT", "MULTIPLY", "DIVIDE", "POW", "ASSIGN", "PLUSMINUS", "GT",
  "LT", "GE", "LE", "EQ", "NE", "TRUE", "FALSE", "AND", "OR", "NOT",
  "PIPE", "LBRACKET", "RBRACKET", "LCBRACE", "RCBRACE", "COLON", "QUES",
  "COMMA", "DOT", "INCLUSIVE", "EXCLUSIVE", "UNDERSCORE", "INT", "REAL",
  "$accept", "start", "info", "info_list", "objects", "definitions",
  "regions", "definition", "table", "tablelist", "value", "function",
  "param_list", "object_block", "takes", "take", "take_id", "id_list",
  "id_list_params", "region_block", "criteria", "criterion", "comma_sep",
  "bins", "chained_cond", "chain", "not", "condition", "compare_op",
  "logic_op", "expr", "expr_op", "factor", "factor_op", "term",
  "id_qualifiers", "id_qualifier", "dot_op", "range", "boolean", "num",
  "index", "int", "real", "id", YY_NULLPTR
  };
#endif


#if YYDEBUG
  const short
   Parser ::yyrline_[] =
  {
       0,    84,    84,    85,    86,    87,    88,    91,    94,    94,
      94,    94,    94,    94,    97,    98,    99,   100,   103,   104,
     105,   108,   109,   112,   113,   114,   119,   122,   123,   126,
     129,   130,   131,   132,   133,   136,   137,   140,   141,   142,
     145,   146,   149,   150,   151,   152,   155,   156,   157,   160,
     161,   164,   165,   168,   169,   172,   173,   176,   177,   178,
     179,   180,   181,   182,   183,   184,   187,   188,   189,   190,
     191,   192,   193,   194,   195,   198,   199,   202,   203,   204,
     205,   206,   207,   210,   211,   212,   215,   218,   220,   221,
     227,   235,   236,   237,   238,   239,   240,   243,   244,   247,
     248,   251,   252,   255,   256,   259,   260,   261,   264,   265,
     266,   267,   268,   271,   272,   275,   277,   278,   279,   280,
     281,   287,   290,   291,   294,   295,   298,   299,   301,   302,
     303,   306,   309,   312
  };

  void
   Parser ::yy_stack_print_ () const
  {
    *yycdebug_ << "Stack now";
    for (stack_type::const_iterator
           i = yystack_.begin (),
           i_end = yystack_.end ();
         i != i_end; ++i)
      *yycdebug_ << ' ' << int (i->state);
    *yycdebug_ << '\n';
  }

  void
   Parser ::yy_reduce_print_ (int yyrule) const
  {
    int yylno = yyrline_[yyrule];
    int yynrhs = yyr2_[yyrule];
    // Print the symbols being reduced, and their result.
    *yycdebug_ << "Reducing stack by rule " << yyrule - 1
               << " (line " << yylno << "):\n";
    // The symbols being reduced.
    for (int yyi = 0; yyi < yynrhs; yyi++)
      YY_SYMBOL_PRINT ("   $" << yyi + 1 << " =",
                       yystack_[(yynrhs) - (yyi + 1)]);
  }
#endif // YYDEBUG


#line 10 "parser.y"
} //  adl 
#line 2525 "Parser.cpp"

#line 314 "parser.y"


void adl::Parser::error(const location_type& l, const std::string& msg) {
    std::cerr << "ERROR: line " << incrementCounter() << " : " << msg << "\n";
    std::cerr << " : Last token was " << scanner.YYText() << "\n";
}
