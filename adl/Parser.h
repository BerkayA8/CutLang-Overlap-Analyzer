// A Bison parser, made by GNU Bison 3.8.2.

// Skeleton interface for Bison LALR(1) parsers in C++

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


/**
 ** \file Parser.h
 ** Define the  adl ::parser class.
 */

// C++ LALR(1) parser skeleton written by Akim Demaille.

// DO NOT RELY ON FEATURES THAT ARE NOT DOCUMENTED in the manual,
// especially those whose name start with YY_ or yy_.  They are
// private implementation details that can be changed or removed.

#ifndef YY_YY_PARSER_H_INCLUDED
# define YY_YY_PARSER_H_INCLUDED
// "%code requires" blocks.
#line 13 "parser.y"

  #include <iostream>
  #include <string>

  namespace adl {
      class Scanner;
      class Driver;
      class Expr;
  }

#line 60 "Parser.h"

# include <cassert>
# include <cstdlib> // std::abort
# include <iostream>
# include <stdexcept>
# include <string>
# include <vector>

#if defined __cplusplus
# define YY_CPLUSPLUS __cplusplus
#else
# define YY_CPLUSPLUS 199711L
#endif

// Support move semantics when possible.
#if 201103L <= YY_CPLUSPLUS
# define YY_MOVE           std::move
# define YY_MOVE_OR_COPY   move
# define YY_MOVE_REF(Type) Type&&
# define YY_RVREF(Type)    Type&&
# define YY_COPY(Type)     Type
#else
# define YY_MOVE
# define YY_MOVE_OR_COPY   copy
# define YY_MOVE_REF(Type) Type&
# define YY_RVREF(Type)    const Type&
# define YY_COPY(Type)     const Type&
#endif

// Support noexcept when possible.
#if 201103L <= YY_CPLUSPLUS
# define YY_NOEXCEPT noexcept
# define YY_NOTHROW
#else
# define YY_NOEXCEPT
# define YY_NOTHROW throw ()
#endif

// Support constexpr when possible.
#if 201703 <= YY_CPLUSPLUS
# define YY_CONSTEXPR constexpr
#else
# define YY_CONSTEXPR
#endif
# include "location.hh"
#include <typeinfo>
#ifndef YY_ASSERT
# include <cassert>
# define YY_ASSERT assert
#endif


#ifndef YY_ATTRIBUTE_PURE
# if defined __GNUC__ && 2 < __GNUC__ + (96 <= __GNUC_MINOR__)
#  define YY_ATTRIBUTE_PURE __attribute__ ((__pure__))
# else
#  define YY_ATTRIBUTE_PURE
# endif
#endif

#ifndef YY_ATTRIBUTE_UNUSED
# if defined __GNUC__ && 2 < __GNUC__ + (7 <= __GNUC_MINOR__)
#  define YY_ATTRIBUTE_UNUSED __attribute__ ((__unused__))
# else
#  define YY_ATTRIBUTE_UNUSED
# endif
#endif

/* Suppress unused-variable warnings by "using" E.  */
#if ! defined lint || defined __GNUC__
# define YY_USE(E) ((void) (E))
#else
# define YY_USE(E) /* empty */
#endif

/* Suppress an incorrect diagnostic about yylval being uninitialized.  */
#if defined __GNUC__ && ! defined __ICC && 406 <= __GNUC__ * 100 + __GNUC_MINOR__
# if __GNUC__ * 100 + __GNUC_MINOR__ < 407
#  define YY_IGNORE_MAYBE_UNINITIALIZED_BEGIN                           \
    _Pragma ("GCC diagnostic push")                                     \
    _Pragma ("GCC diagnostic ignored \"-Wuninitialized\"")
# else
#  define YY_IGNORE_MAYBE_UNINITIALIZED_BEGIN                           \
    _Pragma ("GCC diagnostic push")                                     \
    _Pragma ("GCC diagnostic ignored \"-Wuninitialized\"")              \
    _Pragma ("GCC diagnostic ignored \"-Wmaybe-uninitialized\"")
# endif
# define YY_IGNORE_MAYBE_UNINITIALIZED_END      \
    _Pragma ("GCC diagnostic pop")
#else
# define YY_INITIAL_VALUE(Value) Value
#endif
#ifndef YY_IGNORE_MAYBE_UNINITIALIZED_BEGIN
# define YY_IGNORE_MAYBE_UNINITIALIZED_BEGIN
# define YY_IGNORE_MAYBE_UNINITIALIZED_END
#endif
#ifndef YY_INITIAL_VALUE
# define YY_INITIAL_VALUE(Value) /* Nothing. */
#endif

#if defined __cplusplus && defined __GNUC__ && ! defined __ICC && 6 <= __GNUC__
# define YY_IGNORE_USELESS_CAST_BEGIN                          \
    _Pragma ("GCC diagnostic push")                            \
    _Pragma ("GCC diagnostic ignored \"-Wuseless-cast\"")
# define YY_IGNORE_USELESS_CAST_END            \
    _Pragma ("GCC diagnostic pop")
#endif
#ifndef YY_IGNORE_USELESS_CAST_BEGIN
# define YY_IGNORE_USELESS_CAST_BEGIN
# define YY_IGNORE_USELESS_CAST_END
#endif

# ifndef YY_CAST
#  ifdef __cplusplus
#   define YY_CAST(Type, Val) static_cast<Type> (Val)
#   define YY_REINTERPRET_CAST(Type, Val) reinterpret_cast<Type> (Val)
#  else
#   define YY_CAST(Type, Val) ((Type) (Val))
#   define YY_REINTERPRET_CAST(Type, Val) ((Type) (Val))
#  endif
# endif
# ifndef YY_NULLPTR
#  if defined __cplusplus
#   if 201103L <= __cplusplus
#    define YY_NULLPTR nullptr
#   else
#    define YY_NULLPTR 0
#   endif
#  else
#   define YY_NULLPTR ((void*)0)
#  endif
# endif

/* Debug traces.  */
#ifndef YYDEBUG
# define YYDEBUG 0
#endif

#line 10 "parser.y"
namespace  adl  {
#line 201 "Parser.h"




  /// A Bison parser.
  class  Parser 
  {
  public:
#ifdef YYSTYPE
# ifdef __GNUC__
#  pragma GCC message "bison: do not #define YYSTYPE in C++, use %define api.value.type"
# endif
    typedef YYSTYPE value_type;
#else
  /// A buffer to store and retrieve objects.
  ///
  /// Sort of a variant, but does not keep track of the nature
  /// of the stored data, since that knowledge is available
  /// via the current parser state.
  class value_type
  {
  public:
    /// Type of *this.
    typedef value_type self_type;

    /// Empty construction.
    value_type () YY_NOEXCEPT
      : yyraw_ ()
      , yytypeid_ (YY_NULLPTR)
    {}

    /// Construct and fill.
    template <typename T>
    value_type (YY_RVREF (T) t)
      : yytypeid_ (&typeid (T))
    {
      YY_ASSERT (sizeof (T) <= size);
      new (yyas_<T> ()) T (YY_MOVE (t));
    }

#if 201103L <= YY_CPLUSPLUS
    /// Non copyable.
    value_type (const self_type&) = delete;
    /// Non copyable.
    self_type& operator= (const self_type&) = delete;
#endif

    /// Destruction, allowed only if empty.
    ~value_type () YY_NOEXCEPT
    {
      YY_ASSERT (!yytypeid_);
    }

# if 201103L <= YY_CPLUSPLUS
    /// Instantiate a \a T in here from \a t.
    template <typename T, typename... U>
    T&
    emplace (U&&... u)
    {
      YY_ASSERT (!yytypeid_);
      YY_ASSERT (sizeof (T) <= size);
      yytypeid_ = & typeid (T);
      return *new (yyas_<T> ()) T (std::forward <U>(u)...);
    }
# else
    /// Instantiate an empty \a T in here.
    template <typename T>
    T&
    emplace ()
    {
      YY_ASSERT (!yytypeid_);
      YY_ASSERT (sizeof (T) <= size);
      yytypeid_ = & typeid (T);
      return *new (yyas_<T> ()) T ();
    }

    /// Instantiate a \a T in here from \a t.
    template <typename T>
    T&
    emplace (const T& t)
    {
      YY_ASSERT (!yytypeid_);
      YY_ASSERT (sizeof (T) <= size);
      yytypeid_ = & typeid (T);
      return *new (yyas_<T> ()) T (t);
    }
# endif

    /// Instantiate an empty \a T in here.
    /// Obsolete, use emplace.
    template <typename T>
    T&
    build ()
    {
      return emplace<T> ();
    }

    /// Instantiate a \a T in here from \a t.
    /// Obsolete, use emplace.
    template <typename T>
    T&
    build (const T& t)
    {
      return emplace<T> (t);
    }

    /// Accessor to a built \a T.
    template <typename T>
    T&
    as () YY_NOEXCEPT
    {
      YY_ASSERT (yytypeid_);
      YY_ASSERT (*yytypeid_ == typeid (T));
      YY_ASSERT (sizeof (T) <= size);
      return *yyas_<T> ();
    }

    /// Const accessor to a built \a T (for %printer).
    template <typename T>
    const T&
    as () const YY_NOEXCEPT
    {
      YY_ASSERT (yytypeid_);
      YY_ASSERT (*yytypeid_ == typeid (T));
      YY_ASSERT (sizeof (T) <= size);
      return *yyas_<T> ();
    }

    /// Swap the content with \a that, of same type.
    ///
    /// Both variants must be built beforehand, because swapping the actual
    /// data requires reading it (with as()), and this is not possible on
    /// unconstructed variants: it would require some dynamic testing, which
    /// should not be the variant's responsibility.
    /// Swapping between built and (possibly) non-built is done with
    /// self_type::move ().
    template <typename T>
    void
    swap (self_type& that) YY_NOEXCEPT
    {
      YY_ASSERT (yytypeid_);
      YY_ASSERT (*yytypeid_ == *that.yytypeid_);
      std::swap (as<T> (), that.as<T> ());
    }

    /// Move the content of \a that to this.
    ///
    /// Destroys \a that.
    template <typename T>
    void
    move (self_type& that)
    {
# if 201103L <= YY_CPLUSPLUS
      emplace<T> (std::move (that.as<T> ()));
# else
      emplace<T> ();
      swap<T> (that);
# endif
      that.destroy<T> ();
    }

# if 201103L <= YY_CPLUSPLUS
    /// Move the content of \a that to this.
    template <typename T>
    void
    move (self_type&& that)
    {
      emplace<T> (std::move (that.as<T> ()));
      that.destroy<T> ();
    }
#endif

    /// Copy the content of \a that to this.
    template <typename T>
    void
    copy (const self_type& that)
    {
      emplace<T> (that.as<T> ());
    }

    /// Destroy the stored \a T.
    template <typename T>
    void
    destroy ()
    {
      as<T> ().~T ();
      yytypeid_ = YY_NULLPTR;
    }

  private:
#if YY_CPLUSPLUS < 201103L
    /// Non copyable.
    value_type (const self_type&);
    /// Non copyable.
    self_type& operator= (const self_type&);
#endif

    /// Accessor to raw memory as \a T.
    template <typename T>
    T*
    yyas_ () YY_NOEXCEPT
    {
      void *yyp = yyraw_;
      return static_cast<T*> (yyp);
     }

    /// Const accessor to raw memory as \a T.
    template <typename T>
    const T*
    yyas_ () const YY_NOEXCEPT
    {
      const void *yyp = yyraw_;
      return static_cast<const T*> (yyp);
     }

    /// An auxiliary type to compute the largest semantic type.
    union union_type
    {
      // definition
      // table
      // function
      // param_list
      // object_block
      // take
      // take_id
      // id_list
      // id_list_params
      // region_block
      // criterion
      // chained_cond
      // chain
      // not
      // condition
      // expr
      // factor
      // term
      // id_qualifiers
      // id_qualifier
      // dot_op
      // range
      // num
      // int
      // real
      // id
      char dummy1[sizeof (adl::Expr*)];

      // boolean
      char dummy2[sizeof (bool)];

      // REAL
      // tablelist
      // value
      char dummy3[sizeof (double)];

      // INT
      // index
      char dummy4[sizeof (int)];

      // DEFINE
      // REGION
      // OBJECT
      // TAKE
      // COMMAND
      // HISTO
      // HISTOLIST
      // BIN
      // QUO
      // TABLE
      // TABLETYPE
      // NVARS
      // ERRORS
      // UNION
      // WEIGHT
      // TRIGGER
      // ID
      // ERROR
      // FLAG
      // LPAR
      // RPAR
      // VAR
      // QUOTE
      // DESC
      // INFO
      // PLUS
      // SUBTRACT
      // MULTIPLY
      // DIVIDE
      // POW
      // ASSIGN
      // PLUSMINUS
      // GT
      // LT
      // GE
      // LE
      // EQ
      // NE
      // TRUE
      // FALSE
      // AND
      // OR
      // NOT
      // PIPE
      // LBRACKET
      // RBRACKET
      // LCBRACE
      // RCBRACE
      // COLON
      // QUES
      // COMMA
      // DOT
      // INCLUSIVE
      // EXCLUSIVE
      // UNDERSCORE
      // info
      // compare_op
      // logic_op
      // expr_op
      // factor_op
      char dummy5[sizeof (std::string)];

      // bins
      char dummy6[sizeof (std::vector<double>)];
    };

    /// The size of the largest semantic type.
    enum { size = sizeof (union_type) };

    /// A buffer to store semantic values.
    union
    {
      /// Strongest alignment constraints.
      long double yyalign_me_;
      /// A buffer large enough to store any of the semantic values.
      char yyraw_[size];
    };

    /// Whether the content is built: if defined, the name of the stored type.
    const std::type_info *yytypeid_;
  };

#endif
    /// Backward compatibility (Bison 3.8).
    typedef value_type semantic_type;

    /// Symbol locations.
    typedef location location_type;

    /// Syntax errors thrown from user actions.
    struct syntax_error : std::runtime_error
    {
      syntax_error (const location_type& l, const std::string& m)
        : std::runtime_error (m)
        , location (l)
      {}

      syntax_error (const syntax_error& s)
        : std::runtime_error (s.what ())
        , location (s.location)
      {}

      ~syntax_error () YY_NOEXCEPT YY_NOTHROW;

      location_type location;
    };

    /// Token kinds.
    struct token
    {
      enum token_kind_type
      {
        TOK_YYEMPTY = -2,
    TOK_YYEOF = 0,                 // "end of file"
    TOK_YYerror = 256,             // error
    TOK_YYUNDEF = 257,             // "invalid token"
    TOK_DEFINE = 258,              // DEFINE
    TOK_REGION = 259,              // REGION
    TOK_OBJECT = 260,              // OBJECT
    TOK_TAKE = 261,                // TAKE
    TOK_COMMAND = 262,             // COMMAND
    TOK_HISTO = 263,               // HISTO
    TOK_HISTOLIST = 264,           // HISTOLIST
    TOK_BIN = 265,                 // BIN
    TOK_QUO = 266,                 // QUO
    TOK_TABLE = 267,               // TABLE
    TOK_TABLETYPE = 268,           // TABLETYPE
    TOK_NVARS = 269,               // NVARS
    TOK_ERRORS = 270,              // ERRORS
    TOK_UNION = 271,               // UNION
    TOK_WEIGHT = 272,              // WEIGHT
    TOK_TRIGGER = 273,             // TRIGGER
    TOK_ID = 274,                  // ID
    TOK_ERROR = 275,               // ERROR
    TOK_FLAG = 276,                // FLAG
    TOK_LPAR = 277,                // LPAR
    TOK_RPAR = 278,                // RPAR
    TOK_VAR = 279,                 // VAR
    TOK_QUOTE = 280,               // QUOTE
    TOK_DESC = 281,                // DESC
    TOK_INFO = 282,                // INFO
    TOK_PLUS = 283,                // PLUS
    TOK_SUBTRACT = 284,            // SUBTRACT
    TOK_MULTIPLY = 285,            // MULTIPLY
    TOK_DIVIDE = 286,              // DIVIDE
    TOK_POW = 287,                 // POW
    TOK_ASSIGN = 288,              // ASSIGN
    TOK_PLUSMINUS = 289,           // PLUSMINUS
    TOK_GT = 290,                  // GT
    TOK_LT = 291,                  // LT
    TOK_GE = 292,                  // GE
    TOK_LE = 293,                  // LE
    TOK_EQ = 294,                  // EQ
    TOK_NE = 295,                  // NE
    TOK_TRUE = 296,                // TRUE
    TOK_FALSE = 297,               // FALSE
    TOK_AND = 298,                 // AND
    TOK_OR = 299,                  // OR
    TOK_NOT = 300,                 // NOT
    TOK_PIPE = 301,                // PIPE
    TOK_LBRACKET = 302,            // LBRACKET
    TOK_RBRACKET = 303,            // RBRACKET
    TOK_LCBRACE = 304,             // LCBRACE
    TOK_RCBRACE = 305,             // RCBRACE
    TOK_COLON = 306,               // COLON
    TOK_QUES = 307,                // QUES
    TOK_COMMA = 308,               // COMMA
    TOK_DOT = 309,                 // DOT
    TOK_INCLUSIVE = 310,           // INCLUSIVE
    TOK_EXCLUSIVE = 311,           // EXCLUSIVE
    TOK_UNDERSCORE = 312,          // UNDERSCORE
    TOK_INT = 313,                 // INT
    TOK_REAL = 314                 // REAL
      };
      /// Backward compatibility alias (Bison 3.6).
      typedef token_kind_type yytokentype;
    };

    /// Token kind, as returned by yylex.
    typedef token::token_kind_type token_kind_type;

    /// Backward compatibility alias (Bison 3.6).
    typedef token_kind_type token_type;

    /// Symbol kinds.
    struct symbol_kind
    {
      enum symbol_kind_type
      {
        YYNTOKENS = 60, ///< Number of tokens.
        S_YYEMPTY = -2,
        S_YYEOF = 0,                             // "end of file"
        S_YYerror = 1,                           // error
        S_YYUNDEF = 2,                           // "invalid token"
        S_DEFINE = 3,                            // DEFINE
        S_REGION = 4,                            // REGION
        S_OBJECT = 5,                            // OBJECT
        S_TAKE = 6,                              // TAKE
        S_COMMAND = 7,                           // COMMAND
        S_HISTO = 8,                             // HISTO
        S_HISTOLIST = 9,                         // HISTOLIST
        S_BIN = 10,                              // BIN
        S_QUO = 11,                              // QUO
        S_TABLE = 12,                            // TABLE
        S_TABLETYPE = 13,                        // TABLETYPE
        S_NVARS = 14,                            // NVARS
        S_ERRORS = 15,                           // ERRORS
        S_UNION = 16,                            // UNION
        S_WEIGHT = 17,                           // WEIGHT
        S_TRIGGER = 18,                          // TRIGGER
        S_ID = 19,                               // ID
        S_ERROR = 20,                            // ERROR
        S_FLAG = 21,                             // FLAG
        S_LPAR = 22,                             // LPAR
        S_RPAR = 23,                             // RPAR
        S_VAR = 24,                              // VAR
        S_QUOTE = 25,                            // QUOTE
        S_DESC = 26,                             // DESC
        S_INFO = 27,                             // INFO
        S_PLUS = 28,                             // PLUS
        S_SUBTRACT = 29,                         // SUBTRACT
        S_MULTIPLY = 30,                         // MULTIPLY
        S_DIVIDE = 31,                           // DIVIDE
        S_POW = 32,                              // POW
        S_ASSIGN = 33,                           // ASSIGN
        S_PLUSMINUS = 34,                        // PLUSMINUS
        S_GT = 35,                               // GT
        S_LT = 36,                               // LT
        S_GE = 37,                               // GE
        S_LE = 38,                               // LE
        S_EQ = 39,                               // EQ
        S_NE = 40,                               // NE
        S_TRUE = 41,                             // TRUE
        S_FALSE = 42,                            // FALSE
        S_AND = 43,                              // AND
        S_OR = 44,                               // OR
        S_NOT = 45,                              // NOT
        S_PIPE = 46,                             // PIPE
        S_LBRACKET = 47,                         // LBRACKET
        S_RBRACKET = 48,                         // RBRACKET
        S_LCBRACE = 49,                          // LCBRACE
        S_RCBRACE = 50,                          // RCBRACE
        S_COLON = 51,                            // COLON
        S_QUES = 52,                             // QUES
        S_COMMA = 53,                            // COMMA
        S_DOT = 54,                              // DOT
        S_INCLUSIVE = 55,                        // INCLUSIVE
        S_EXCLUSIVE = 56,                        // EXCLUSIVE
        S_UNDERSCORE = 57,                       // UNDERSCORE
        S_INT = 58,                              // INT
        S_REAL = 59,                             // REAL
        S_YYACCEPT = 60,                         // $accept
        S_start = 61,                            // start
        S_info = 62,                             // info
        S_info_list = 63,                        // info_list
        S_objects = 64,                          // objects
        S_definitions = 65,                      // definitions
        S_regions = 66,                          // regions
        S_definition = 67,                       // definition
        S_table = 68,                            // table
        S_tablelist = 69,                        // tablelist
        S_value = 70,                            // value
        S_function = 71,                         // function
        S_param_list = 72,                       // param_list
        S_object_block = 73,                     // object_block
        S_takes = 74,                            // takes
        S_take = 75,                             // take
        S_take_id = 76,                          // take_id
        S_id_list = 77,                          // id_list
        S_id_list_params = 78,                   // id_list_params
        S_region_block = 79,                     // region_block
        S_criteria = 80,                         // criteria
        S_criterion = 81,                        // criterion
        S_comma_sep = 82,                        // comma_sep
        S_bins = 83,                             // bins
        S_chained_cond = 84,                     // chained_cond
        S_chain = 85,                            // chain
        S_not = 86,                              // not
        S_condition = 87,                        // condition
        S_compare_op = 88,                       // compare_op
        S_logic_op = 89,                         // logic_op
        S_expr = 90,                             // expr
        S_expr_op = 91,                          // expr_op
        S_factor = 92,                           // factor
        S_factor_op = 93,                        // factor_op
        S_term = 94,                             // term
        S_id_qualifiers = 95,                    // id_qualifiers
        S_id_qualifier = 96,                     // id_qualifier
        S_dot_op = 97,                           // dot_op
        S_range = 98,                            // range
        S_boolean = 99,                          // boolean
        S_num = 100,                             // num
        S_index = 101,                           // index
        S_int = 102,                             // int
        S_real = 103,                            // real
        S_id = 104                               // id
      };
    };

    /// (Internal) symbol kind.
    typedef symbol_kind::symbol_kind_type symbol_kind_type;

    /// The number of tokens.
    static const symbol_kind_type YYNTOKENS = symbol_kind::YYNTOKENS;

    /// A complete symbol.
    ///
    /// Expects its Base type to provide access to the symbol kind
    /// via kind ().
    ///
    /// Provide access to semantic value and location.
    template <typename Base>
    struct basic_symbol : Base
    {
      /// Alias to Base.
      typedef Base super_type;

      /// Default constructor.
      basic_symbol () YY_NOEXCEPT
        : value ()
        , location ()
      {}

#if 201103L <= YY_CPLUSPLUS
      /// Move constructor.
      basic_symbol (basic_symbol&& that)
        : Base (std::move (that))
        , value ()
        , location (std::move (that.location))
      {
        switch (this->kind ())
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
        value.move< adl::Expr* > (std::move (that.value));
        break;

      case symbol_kind::S_boolean: // boolean
        value.move< bool > (std::move (that.value));
        break;

      case symbol_kind::S_REAL: // REAL
      case symbol_kind::S_tablelist: // tablelist
      case symbol_kind::S_value: // value
        value.move< double > (std::move (that.value));
        break;

      case symbol_kind::S_INT: // INT
      case symbol_kind::S_index: // index
        value.move< int > (std::move (that.value));
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
        value.move< std::string > (std::move (that.value));
        break;

      case symbol_kind::S_bins: // bins
        value.move< std::vector<double> > (std::move (that.value));
        break;

      default:
        break;
    }

      }
#endif

      /// Copy constructor.
      basic_symbol (const basic_symbol& that);

      /// Constructors for typed symbols.
#if 201103L <= YY_CPLUSPLUS
      basic_symbol (typename Base::kind_type t, location_type&& l)
        : Base (t)
        , location (std::move (l))
      {}
#else
      basic_symbol (typename Base::kind_type t, const location_type& l)
        : Base (t)
        , location (l)
      {}
#endif

#if 201103L <= YY_CPLUSPLUS
      basic_symbol (typename Base::kind_type t, adl::Expr*&& v, location_type&& l)
        : Base (t)
        , value (std::move (v))
        , location (std::move (l))
      {}
#else
      basic_symbol (typename Base::kind_type t, const adl::Expr*& v, const location_type& l)
        : Base (t)
        , value (v)
        , location (l)
      {}
#endif

#if 201103L <= YY_CPLUSPLUS
      basic_symbol (typename Base::kind_type t, bool&& v, location_type&& l)
        : Base (t)
        , value (std::move (v))
        , location (std::move (l))
      {}
#else
      basic_symbol (typename Base::kind_type t, const bool& v, const location_type& l)
        : Base (t)
        , value (v)
        , location (l)
      {}
#endif

#if 201103L <= YY_CPLUSPLUS
      basic_symbol (typename Base::kind_type t, double&& v, location_type&& l)
        : Base (t)
        , value (std::move (v))
        , location (std::move (l))
      {}
#else
      basic_symbol (typename Base::kind_type t, const double& v, const location_type& l)
        : Base (t)
        , value (v)
        , location (l)
      {}
#endif

#if 201103L <= YY_CPLUSPLUS
      basic_symbol (typename Base::kind_type t, int&& v, location_type&& l)
        : Base (t)
        , value (std::move (v))
        , location (std::move (l))
      {}
#else
      basic_symbol (typename Base::kind_type t, const int& v, const location_type& l)
        : Base (t)
        , value (v)
        , location (l)
      {}
#endif

#if 201103L <= YY_CPLUSPLUS
      basic_symbol (typename Base::kind_type t, std::string&& v, location_type&& l)
        : Base (t)
        , value (std::move (v))
        , location (std::move (l))
      {}
#else
      basic_symbol (typename Base::kind_type t, const std::string& v, const location_type& l)
        : Base (t)
        , value (v)
        , location (l)
      {}
#endif

#if 201103L <= YY_CPLUSPLUS
      basic_symbol (typename Base::kind_type t, std::vector<double>&& v, location_type&& l)
        : Base (t)
        , value (std::move (v))
        , location (std::move (l))
      {}
#else
      basic_symbol (typename Base::kind_type t, const std::vector<double>& v, const location_type& l)
        : Base (t)
        , value (v)
        , location (l)
      {}
#endif

      /// Destroy the symbol.
      ~basic_symbol ()
      {
        clear ();
      }



      /// Destroy contents, and record that is empty.
      void clear () YY_NOEXCEPT
      {
        // User destructor.
        symbol_kind_type yykind = this->kind ();
        basic_symbol<Base>& yysym = *this;
        (void) yysym;
        switch (yykind)
        {
       default:
          break;
        }

        // Value type destructor.
switch (yykind)
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
        value.template destroy< adl::Expr* > ();
        break;

      case symbol_kind::S_boolean: // boolean
        value.template destroy< bool > ();
        break;

      case symbol_kind::S_REAL: // REAL
      case symbol_kind::S_tablelist: // tablelist
      case symbol_kind::S_value: // value
        value.template destroy< double > ();
        break;

      case symbol_kind::S_INT: // INT
      case symbol_kind::S_index: // index
        value.template destroy< int > ();
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
        value.template destroy< std::string > ();
        break;

      case symbol_kind::S_bins: // bins
        value.template destroy< std::vector<double> > ();
        break;

      default:
        break;
    }

        Base::clear ();
      }

      /// The user-facing name of this symbol.
      std::string name () const YY_NOEXCEPT
      {
        return  Parser ::symbol_name (this->kind ());
      }

      /// Backward compatibility (Bison 3.6).
      symbol_kind_type type_get () const YY_NOEXCEPT;

      /// Whether empty.
      bool empty () const YY_NOEXCEPT;

      /// Destructive move, \a s is emptied into this.
      void move (basic_symbol& s);

      /// The semantic value.
      value_type value;

      /// The location.
      location_type location;

    private:
#if YY_CPLUSPLUS < 201103L
      /// Assignment operator.
      basic_symbol& operator= (const basic_symbol& that);
#endif
    };

    /// Type access provider for token (enum) based symbols.
    struct by_kind
    {
      /// The symbol kind as needed by the constructor.
      typedef token_kind_type kind_type;

      /// Default constructor.
      by_kind () YY_NOEXCEPT;

#if 201103L <= YY_CPLUSPLUS
      /// Move constructor.
      by_kind (by_kind&& that) YY_NOEXCEPT;
#endif

      /// Copy constructor.
      by_kind (const by_kind& that) YY_NOEXCEPT;

      /// Constructor from (external) token numbers.
      by_kind (kind_type t) YY_NOEXCEPT;



      /// Record that this symbol is empty.
      void clear () YY_NOEXCEPT;

      /// Steal the symbol kind from \a that.
      void move (by_kind& that);

      /// The (internal) type number (corresponding to \a type).
      /// \a empty when empty.
      symbol_kind_type kind () const YY_NOEXCEPT;

      /// Backward compatibility (Bison 3.6).
      symbol_kind_type type_get () const YY_NOEXCEPT;

      /// The symbol kind.
      /// \a S_YYEMPTY when empty.
      symbol_kind_type kind_;
    };

    /// Backward compatibility for a private implementation detail (Bison 3.6).
    typedef by_kind by_type;

    /// "External" symbols: returned by the scanner.
    struct symbol_type : basic_symbol<by_kind>
    {
      /// Superclass.
      typedef basic_symbol<by_kind> super_type;

      /// Empty symbol.
      symbol_type () YY_NOEXCEPT {}

      /// Constructor for valueless symbols, and symbols from each type.
#if 201103L <= YY_CPLUSPLUS
      symbol_type (int tok, location_type l)
        : super_type (token_kind_type (tok), std::move (l))
#else
      symbol_type (int tok, const location_type& l)
        : super_type (token_kind_type (tok), l)
#endif
      {
#if !defined _MSC_VER || defined __clang__
        YY_ASSERT (tok == token::TOK_YYEOF
                   || (token::TOK_YYerror <= tok && tok <= token::TOK_YYUNDEF));
#endif
      }
#if 201103L <= YY_CPLUSPLUS
      symbol_type (int tok, double v, location_type l)
        : super_type (token_kind_type (tok), std::move (v), std::move (l))
#else
      symbol_type (int tok, const double& v, const location_type& l)
        : super_type (token_kind_type (tok), v, l)
#endif
      {
#if !defined _MSC_VER || defined __clang__
        YY_ASSERT (tok == token::TOK_REAL);
#endif
      }
#if 201103L <= YY_CPLUSPLUS
      symbol_type (int tok, int v, location_type l)
        : super_type (token_kind_type (tok), std::move (v), std::move (l))
#else
      symbol_type (int tok, const int& v, const location_type& l)
        : super_type (token_kind_type (tok), v, l)
#endif
      {
#if !defined _MSC_VER || defined __clang__
        YY_ASSERT (tok == token::TOK_INT);
#endif
      }
#if 201103L <= YY_CPLUSPLUS
      symbol_type (int tok, std::string v, location_type l)
        : super_type (token_kind_type (tok), std::move (v), std::move (l))
#else
      symbol_type (int tok, const std::string& v, const location_type& l)
        : super_type (token_kind_type (tok), v, l)
#endif
      {
#if !defined _MSC_VER || defined __clang__
        YY_ASSERT ((token::TOK_DEFINE <= tok && tok <= token::TOK_UNDERSCORE));
#endif
      }
    };

    /// Build a parser object.
     Parser  (adl::Scanner &scanner_yyarg, adl::Driver &driver_yyarg);
    virtual ~ Parser  ();

#if 201103L <= YY_CPLUSPLUS
    /// Non copyable.
     Parser  (const  Parser &) = delete;
    /// Non copyable.
     Parser & operator= (const  Parser &) = delete;
#endif

    /// Parse.  An alias for parse ().
    /// \returns  0 iff parsing succeeded.
    int operator() ();

    /// Parse.
    /// \returns  0 iff parsing succeeded.
    virtual int parse ();

#if YYDEBUG
    /// The current debugging stream.
    std::ostream& debug_stream () const YY_ATTRIBUTE_PURE;
    /// Set the current debugging stream.
    void set_debug_stream (std::ostream &);

    /// Type for debugging levels.
    typedef int debug_level_type;
    /// The current debugging level.
    debug_level_type debug_level () const YY_ATTRIBUTE_PURE;
    /// Set the current debugging level.
    void set_debug_level (debug_level_type l);
#endif

    /// Report a syntax error.
    /// \param loc    where the syntax error is found.
    /// \param msg    a description of the syntax error.
    virtual void error (const location_type& loc, const std::string& msg);

    /// Report a syntax error.
    void error (const syntax_error& err);

    /// The user-facing name of the symbol whose (internal) number is
    /// YYSYMBOL.  No bounds checking.
    static std::string symbol_name (symbol_kind_type yysymbol);

    // Implementation of make_symbol for each token kind.
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_YYEOF (location_type l)
      {
        return symbol_type (token::TOK_YYEOF, std::move (l));
      }
#else
      static
      symbol_type
      make_YYEOF (const location_type& l)
      {
        return symbol_type (token::TOK_YYEOF, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_YYerror (location_type l)
      {
        return symbol_type (token::TOK_YYerror, std::move (l));
      }
#else
      static
      symbol_type
      make_YYerror (const location_type& l)
      {
        return symbol_type (token::TOK_YYerror, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_YYUNDEF (location_type l)
      {
        return symbol_type (token::TOK_YYUNDEF, std::move (l));
      }
#else
      static
      symbol_type
      make_YYUNDEF (const location_type& l)
      {
        return symbol_type (token::TOK_YYUNDEF, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_DEFINE (std::string v, location_type l)
      {
        return symbol_type (token::TOK_DEFINE, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_DEFINE (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_DEFINE, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_REGION (std::string v, location_type l)
      {
        return symbol_type (token::TOK_REGION, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_REGION (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_REGION, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_OBJECT (std::string v, location_type l)
      {
        return symbol_type (token::TOK_OBJECT, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_OBJECT (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_OBJECT, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_TAKE (std::string v, location_type l)
      {
        return symbol_type (token::TOK_TAKE, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_TAKE (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_TAKE, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_COMMAND (std::string v, location_type l)
      {
        return symbol_type (token::TOK_COMMAND, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_COMMAND (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_COMMAND, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_HISTO (std::string v, location_type l)
      {
        return symbol_type (token::TOK_HISTO, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_HISTO (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_HISTO, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_HISTOLIST (std::string v, location_type l)
      {
        return symbol_type (token::TOK_HISTOLIST, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_HISTOLIST (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_HISTOLIST, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_BIN (std::string v, location_type l)
      {
        return symbol_type (token::TOK_BIN, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_BIN (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_BIN, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_QUO (std::string v, location_type l)
      {
        return symbol_type (token::TOK_QUO, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_QUO (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_QUO, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_TABLE (std::string v, location_type l)
      {
        return symbol_type (token::TOK_TABLE, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_TABLE (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_TABLE, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_TABLETYPE (std::string v, location_type l)
      {
        return symbol_type (token::TOK_TABLETYPE, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_TABLETYPE (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_TABLETYPE, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_NVARS (std::string v, location_type l)
      {
        return symbol_type (token::TOK_NVARS, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_NVARS (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_NVARS, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_ERRORS (std::string v, location_type l)
      {
        return symbol_type (token::TOK_ERRORS, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_ERRORS (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_ERRORS, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_UNION (std::string v, location_type l)
      {
        return symbol_type (token::TOK_UNION, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_UNION (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_UNION, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_WEIGHT (std::string v, location_type l)
      {
        return symbol_type (token::TOK_WEIGHT, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_WEIGHT (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_WEIGHT, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_TRIGGER (std::string v, location_type l)
      {
        return symbol_type (token::TOK_TRIGGER, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_TRIGGER (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_TRIGGER, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_ID (std::string v, location_type l)
      {
        return symbol_type (token::TOK_ID, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_ID (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_ID, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_ERROR (std::string v, location_type l)
      {
        return symbol_type (token::TOK_ERROR, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_ERROR (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_ERROR, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_FLAG (std::string v, location_type l)
      {
        return symbol_type (token::TOK_FLAG, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_FLAG (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_FLAG, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_LPAR (std::string v, location_type l)
      {
        return symbol_type (token::TOK_LPAR, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_LPAR (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_LPAR, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_RPAR (std::string v, location_type l)
      {
        return symbol_type (token::TOK_RPAR, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_RPAR (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_RPAR, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_VAR (std::string v, location_type l)
      {
        return symbol_type (token::TOK_VAR, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_VAR (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_VAR, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_QUOTE (std::string v, location_type l)
      {
        return symbol_type (token::TOK_QUOTE, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_QUOTE (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_QUOTE, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_DESC (std::string v, location_type l)
      {
        return symbol_type (token::TOK_DESC, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_DESC (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_DESC, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_INFO (std::string v, location_type l)
      {
        return symbol_type (token::TOK_INFO, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_INFO (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_INFO, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_PLUS (std::string v, location_type l)
      {
        return symbol_type (token::TOK_PLUS, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_PLUS (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_PLUS, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_SUBTRACT (std::string v, location_type l)
      {
        return symbol_type (token::TOK_SUBTRACT, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_SUBTRACT (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_SUBTRACT, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_MULTIPLY (std::string v, location_type l)
      {
        return symbol_type (token::TOK_MULTIPLY, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_MULTIPLY (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_MULTIPLY, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_DIVIDE (std::string v, location_type l)
      {
        return symbol_type (token::TOK_DIVIDE, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_DIVIDE (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_DIVIDE, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_POW (std::string v, location_type l)
      {
        return symbol_type (token::TOK_POW, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_POW (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_POW, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_ASSIGN (std::string v, location_type l)
      {
        return symbol_type (token::TOK_ASSIGN, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_ASSIGN (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_ASSIGN, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_PLUSMINUS (std::string v, location_type l)
      {
        return symbol_type (token::TOK_PLUSMINUS, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_PLUSMINUS (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_PLUSMINUS, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_GT (std::string v, location_type l)
      {
        return symbol_type (token::TOK_GT, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_GT (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_GT, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_LT (std::string v, location_type l)
      {
        return symbol_type (token::TOK_LT, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_LT (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_LT, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_GE (std::string v, location_type l)
      {
        return symbol_type (token::TOK_GE, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_GE (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_GE, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_LE (std::string v, location_type l)
      {
        return symbol_type (token::TOK_LE, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_LE (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_LE, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_EQ (std::string v, location_type l)
      {
        return symbol_type (token::TOK_EQ, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_EQ (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_EQ, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_NE (std::string v, location_type l)
      {
        return symbol_type (token::TOK_NE, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_NE (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_NE, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_TRUE (std::string v, location_type l)
      {
        return symbol_type (token::TOK_TRUE, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_TRUE (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_TRUE, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_FALSE (std::string v, location_type l)
      {
        return symbol_type (token::TOK_FALSE, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_FALSE (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_FALSE, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_AND (std::string v, location_type l)
      {
        return symbol_type (token::TOK_AND, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_AND (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_AND, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_OR (std::string v, location_type l)
      {
        return symbol_type (token::TOK_OR, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_OR (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_OR, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_NOT (std::string v, location_type l)
      {
        return symbol_type (token::TOK_NOT, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_NOT (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_NOT, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_PIPE (std::string v, location_type l)
      {
        return symbol_type (token::TOK_PIPE, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_PIPE (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_PIPE, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_LBRACKET (std::string v, location_type l)
      {
        return symbol_type (token::TOK_LBRACKET, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_LBRACKET (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_LBRACKET, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_RBRACKET (std::string v, location_type l)
      {
        return symbol_type (token::TOK_RBRACKET, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_RBRACKET (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_RBRACKET, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_LCBRACE (std::string v, location_type l)
      {
        return symbol_type (token::TOK_LCBRACE, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_LCBRACE (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_LCBRACE, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_RCBRACE (std::string v, location_type l)
      {
        return symbol_type (token::TOK_RCBRACE, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_RCBRACE (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_RCBRACE, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_COLON (std::string v, location_type l)
      {
        return symbol_type (token::TOK_COLON, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_COLON (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_COLON, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_QUES (std::string v, location_type l)
      {
        return symbol_type (token::TOK_QUES, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_QUES (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_QUES, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_COMMA (std::string v, location_type l)
      {
        return symbol_type (token::TOK_COMMA, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_COMMA (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_COMMA, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_DOT (std::string v, location_type l)
      {
        return symbol_type (token::TOK_DOT, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_DOT (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_DOT, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_INCLUSIVE (std::string v, location_type l)
      {
        return symbol_type (token::TOK_INCLUSIVE, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_INCLUSIVE (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_INCLUSIVE, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_EXCLUSIVE (std::string v, location_type l)
      {
        return symbol_type (token::TOK_EXCLUSIVE, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_EXCLUSIVE (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_EXCLUSIVE, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_UNDERSCORE (std::string v, location_type l)
      {
        return symbol_type (token::TOK_UNDERSCORE, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_UNDERSCORE (const std::string& v, const location_type& l)
      {
        return symbol_type (token::TOK_UNDERSCORE, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_INT (int v, location_type l)
      {
        return symbol_type (token::TOK_INT, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_INT (const int& v, const location_type& l)
      {
        return symbol_type (token::TOK_INT, v, l);
      }
#endif
#if 201103L <= YY_CPLUSPLUS
      static
      symbol_type
      make_REAL (double v, location_type l)
      {
        return symbol_type (token::TOK_REAL, std::move (v), std::move (l));
      }
#else
      static
      symbol_type
      make_REAL (const double& v, const location_type& l)
      {
        return symbol_type (token::TOK_REAL, v, l);
      }
#endif


    class context
    {
    public:
      context (const  Parser & yyparser, const symbol_type& yyla);
      const symbol_type& lookahead () const YY_NOEXCEPT { return yyla_; }
      symbol_kind_type token () const YY_NOEXCEPT { return yyla_.kind (); }
      const location_type& location () const YY_NOEXCEPT { return yyla_.location; }

      /// Put in YYARG at most YYARGN of the expected tokens, and return the
      /// number of tokens stored in YYARG.  If YYARG is null, return the
      /// number of expected tokens (guaranteed to be less than YYNTOKENS).
      int expected_tokens (symbol_kind_type yyarg[], int yyargn) const;

    private:
      const  Parser & yyparser_;
      const symbol_type& yyla_;
    };

  private:
#if YY_CPLUSPLUS < 201103L
    /// Non copyable.
     Parser  (const  Parser &);
    /// Non copyable.
     Parser & operator= (const  Parser &);
#endif


    /// Stored state numbers (used for stacks).
    typedef unsigned char state_type;

    /// The arguments of the error message.
    int yy_syntax_error_arguments_ (const context& yyctx,
                                    symbol_kind_type yyarg[], int yyargn) const;

    /// Generate an error message.
    /// \param yyctx     the context in which the error occurred.
    virtual std::string yysyntax_error_ (const context& yyctx) const;
    /// Compute post-reduction state.
    /// \param yystate   the current state
    /// \param yysym     the nonterminal to push on the stack
    static state_type yy_lr_goto_state_ (state_type yystate, int yysym);

    /// Whether the given \c yypact_ value indicates a defaulted state.
    /// \param yyvalue   the value to check
    static bool yy_pact_value_is_default_ (int yyvalue) YY_NOEXCEPT;

    /// Whether the given \c yytable_ value indicates a syntax error.
    /// \param yyvalue   the value to check
    static bool yy_table_value_is_error_ (int yyvalue) YY_NOEXCEPT;

    static const signed char yypact_ninf_;
    static const signed char yytable_ninf_;

    /// Convert a scanner token kind \a t to a symbol kind.
    /// In theory \a t should be a token_kind_type, but character literals
    /// are valid, yet not members of the token_kind_type enum.
    static symbol_kind_type yytranslate_ (int t) YY_NOEXCEPT;

    /// Convert the symbol name \a n to a form suitable for a diagnostic.
    static std::string yytnamerr_ (const char *yystr);

    /// For a symbol, its name in clear.
    static const char* const yytname_[];


    // Tables.
    // YYPACT[STATE-NUM] -- Index in YYTABLE of the portion describing
    // STATE-NUM.
    static const short yypact_[];

    // YYDEFACT[STATE-NUM] -- Default reduction number in state STATE-NUM.
    // Performed when YYTABLE does not specify something else to do.  Zero
    // means the default is an error.
    static const unsigned char yydefact_[];

    // YYPGOTO[NTERM-NUM].
    static const short yypgoto_[];

    // YYDEFGOTO[NTERM-NUM].
    static const unsigned char yydefgoto_[];

    // YYTABLE[YYPACT[STATE-NUM]] -- What to do in state STATE-NUM.  If
    // positive, shift that token.  If negative, reduce the rule whose
    // number is the opposite.  If YYTABLE_NINF, syntax error.
    static const unsigned char yytable_[];

    static const short yycheck_[];

    // YYSTOS[STATE-NUM] -- The symbol kind of the accessing symbol of
    // state STATE-NUM.
    static const signed char yystos_[];

    // YYR1[RULE-NUM] -- Symbol kind of the left-hand side of rule RULE-NUM.
    static const signed char yyr1_[];

    // YYR2[RULE-NUM] -- Number of symbols on the right-hand side of rule RULE-NUM.
    static const signed char yyr2_[];


#if YYDEBUG
    // YYRLINE[YYN] -- Source line where rule number YYN was defined.
    static const short yyrline_[];
    /// Report on the debug stream that the rule \a r is going to be reduced.
    virtual void yy_reduce_print_ (int r) const;
    /// Print the state stack on the debug stream.
    virtual void yy_stack_print_ () const;

    /// Debugging level.
    int yydebug_;
    /// Debug stream.
    std::ostream* yycdebug_;

    /// \brief Display a symbol kind, value and location.
    /// \param yyo    The output stream.
    /// \param yysym  The symbol.
    template <typename Base>
    void yy_print_ (std::ostream& yyo, const basic_symbol<Base>& yysym) const;
#endif

    /// \brief Reclaim the memory associated to a symbol.
    /// \param yymsg     Why this token is reclaimed.
    ///                  If null, print nothing.
    /// \param yysym     The symbol.
    template <typename Base>
    void yy_destroy_ (const char* yymsg, basic_symbol<Base>& yysym) const;

  private:
    /// Type access provider for state based symbols.
    struct by_state
    {
      /// Default constructor.
      by_state () YY_NOEXCEPT;

      /// The symbol kind as needed by the constructor.
      typedef state_type kind_type;

      /// Constructor.
      by_state (kind_type s) YY_NOEXCEPT;

      /// Copy constructor.
      by_state (const by_state& that) YY_NOEXCEPT;

      /// Record that this symbol is empty.
      void clear () YY_NOEXCEPT;

      /// Steal the symbol kind from \a that.
      void move (by_state& that);

      /// The symbol kind (corresponding to \a state).
      /// \a symbol_kind::S_YYEMPTY when empty.
      symbol_kind_type kind () const YY_NOEXCEPT;

      /// The state number used to denote an empty symbol.
      /// We use the initial state, as it does not have a value.
      enum { empty_state = 0 };

      /// The state.
      /// \a empty when empty.
      state_type state;
    };

    /// "Internal" symbol: element of the stack.
    struct stack_symbol_type : basic_symbol<by_state>
    {
      /// Superclass.
      typedef basic_symbol<by_state> super_type;
      /// Construct an empty symbol.
      stack_symbol_type ();
      /// Move or copy construction.
      stack_symbol_type (YY_RVREF (stack_symbol_type) that);
      /// Steal the contents from \a sym to build this.
      stack_symbol_type (state_type s, YY_MOVE_REF (symbol_type) sym);
#if YY_CPLUSPLUS < 201103L
      /// Assignment, needed by push_back by some old implementations.
      /// Moves the contents of that.
      stack_symbol_type& operator= (stack_symbol_type& that);

      /// Assignment, needed by push_back by other implementations.
      /// Needed by some other old implementations.
      stack_symbol_type& operator= (const stack_symbol_type& that);
#endif
    };

    /// A stack with random access from its top.
    template <typename T, typename S = std::vector<T> >
    class stack
    {
    public:
      // Hide our reversed order.
      typedef typename S::iterator iterator;
      typedef typename S::const_iterator const_iterator;
      typedef typename S::size_type size_type;
      typedef typename std::ptrdiff_t index_type;

      stack (size_type n = 200) YY_NOEXCEPT
        : seq_ (n)
      {}

#if 201103L <= YY_CPLUSPLUS
      /// Non copyable.
      stack (const stack&) = delete;
      /// Non copyable.
      stack& operator= (const stack&) = delete;
#endif

      /// Random access.
      ///
      /// Index 0 returns the topmost element.
      const T&
      operator[] (index_type i) const
      {
        return seq_[size_type (size () - 1 - i)];
      }

      /// Random access.
      ///
      /// Index 0 returns the topmost element.
      T&
      operator[] (index_type i)
      {
        return seq_[size_type (size () - 1 - i)];
      }

      /// Steal the contents of \a t.
      ///
      /// Close to move-semantics.
      void
      push (YY_MOVE_REF (T) t)
      {
        seq_.push_back (T ());
        operator[] (0).move (t);
      }

      /// Pop elements from the stack.
      void
      pop (std::ptrdiff_t n = 1) YY_NOEXCEPT
      {
        for (; 0 < n; --n)
          seq_.pop_back ();
      }

      /// Pop all elements from the stack.
      void
      clear () YY_NOEXCEPT
      {
        seq_.clear ();
      }

      /// Number of elements on the stack.
      index_type
      size () const YY_NOEXCEPT
      {
        return index_type (seq_.size ());
      }

      /// Iterator on top of the stack (going downwards).
      const_iterator
      begin () const YY_NOEXCEPT
      {
        return seq_.begin ();
      }

      /// Bottom of the stack.
      const_iterator
      end () const YY_NOEXCEPT
      {
        return seq_.end ();
      }

      /// Present a slice of the top of a stack.
      class slice
      {
      public:
        slice (const stack& stack, index_type range) YY_NOEXCEPT
          : stack_ (stack)
          , range_ (range)
        {}

        const T&
        operator[] (index_type i) const
        {
          return stack_[range_ - i];
        }

      private:
        const stack& stack_;
        index_type range_;
      };

    private:
#if YY_CPLUSPLUS < 201103L
      /// Non copyable.
      stack (const stack&);
      /// Non copyable.
      stack& operator= (const stack&);
#endif
      /// The wrapped container.
      S seq_;
    };


    /// Stack type.
    typedef stack<stack_symbol_type> stack_type;

    /// The stack.
    stack_type yystack_;

    /// Push a new state on the stack.
    /// \param m    a debug message to display
    ///             if null, no trace is output.
    /// \param sym  the symbol
    /// \warning the contents of \a s.value is stolen.
    void yypush_ (const char* m, YY_MOVE_REF (stack_symbol_type) sym);

    /// Push a new look ahead token on the state on the stack.
    /// \param m    a debug message to display
    ///             if null, no trace is output.
    /// \param s    the state
    /// \param sym  the symbol (for its value and location).
    /// \warning the contents of \a sym.value is stolen.
    void yypush_ (const char* m, state_type s, YY_MOVE_REF (symbol_type) sym);

    /// Pop \a n symbols from the stack.
    void yypop_ (int n = 1) YY_NOEXCEPT;

    /// Constants.
    enum
    {
      yylast_ = 298,     ///< Last index in yytable_.
      yynnts_ = 45,  ///< Number of nonterminal symbols.
      yyfinal_ = 28 ///< Termination state number.
    };


    // User arguments.
    adl::Scanner &scanner;
    adl::Driver &driver;

  };

  inline
   Parser ::symbol_kind_type
   Parser ::yytranslate_ (int t) YY_NOEXCEPT
  {
    // YYTRANSLATE[TOKEN-NUM] -- Symbol number corresponding to
    // TOKEN-NUM as returned by yylex.
    static
    const signed char
    translate_table[] =
    {
       0,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     1,     2,     3,     4,
       5,     6,     7,     8,     9,    10,    11,    12,    13,    14,
      15,    16,    17,    18,    19,    20,    21,    22,    23,    24,
      25,    26,    27,    28,    29,    30,    31,    32,    33,    34,
      35,    36,    37,    38,    39,    40,    41,    42,    43,    44,
      45,    46,    47,    48,    49,    50,    51,    52,    53,    54,
      55,    56,    57,    58,    59
    };
    // Last valid token kind.
    const int code_max = 314;

    if (t <= 0)
      return symbol_kind::S_YYEOF;
    else if (t <= code_max)
      return static_cast <symbol_kind_type> (translate_table[t]);
    else
      return symbol_kind::S_YYUNDEF;
  }

  // basic_symbol.
  template <typename Base>
   Parser ::basic_symbol<Base>::basic_symbol (const basic_symbol& that)
    : Base (that)
    , value ()
    , location (that.location)
  {
    switch (this->kind ())
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
        value.copy< adl::Expr* > (YY_MOVE (that.value));
        break;

      case symbol_kind::S_boolean: // boolean
        value.copy< bool > (YY_MOVE (that.value));
        break;

      case symbol_kind::S_REAL: // REAL
      case symbol_kind::S_tablelist: // tablelist
      case symbol_kind::S_value: // value
        value.copy< double > (YY_MOVE (that.value));
        break;

      case symbol_kind::S_INT: // INT
      case symbol_kind::S_index: // index
        value.copy< int > (YY_MOVE (that.value));
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
        value.copy< std::string > (YY_MOVE (that.value));
        break;

      case symbol_kind::S_bins: // bins
        value.copy< std::vector<double> > (YY_MOVE (that.value));
        break;

      default:
        break;
    }

  }




  template <typename Base>
   Parser ::symbol_kind_type
   Parser ::basic_symbol<Base>::type_get () const YY_NOEXCEPT
  {
    return this->kind ();
  }


  template <typename Base>
  bool
   Parser ::basic_symbol<Base>::empty () const YY_NOEXCEPT
  {
    return this->kind () == symbol_kind::S_YYEMPTY;
  }

  template <typename Base>
  void
   Parser ::basic_symbol<Base>::move (basic_symbol& s)
  {
    super_type::move (s);
    switch (this->kind ())
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
        value.move< adl::Expr* > (YY_MOVE (s.value));
        break;

      case symbol_kind::S_boolean: // boolean
        value.move< bool > (YY_MOVE (s.value));
        break;

      case symbol_kind::S_REAL: // REAL
      case symbol_kind::S_tablelist: // tablelist
      case symbol_kind::S_value: // value
        value.move< double > (YY_MOVE (s.value));
        break;

      case symbol_kind::S_INT: // INT
      case symbol_kind::S_index: // index
        value.move< int > (YY_MOVE (s.value));
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
        value.move< std::string > (YY_MOVE (s.value));
        break;

      case symbol_kind::S_bins: // bins
        value.move< std::vector<double> > (YY_MOVE (s.value));
        break;

      default:
        break;
    }

    location = YY_MOVE (s.location);
  }

  // by_kind.
  inline
   Parser ::by_kind::by_kind () YY_NOEXCEPT
    : kind_ (symbol_kind::S_YYEMPTY)
  {}

#if 201103L <= YY_CPLUSPLUS
  inline
   Parser ::by_kind::by_kind (by_kind&& that) YY_NOEXCEPT
    : kind_ (that.kind_)
  {
    that.clear ();
  }
#endif

  inline
   Parser ::by_kind::by_kind (const by_kind& that) YY_NOEXCEPT
    : kind_ (that.kind_)
  {}

  inline
   Parser ::by_kind::by_kind (token_kind_type t) YY_NOEXCEPT
    : kind_ (yytranslate_ (t))
  {}



  inline
  void
   Parser ::by_kind::clear () YY_NOEXCEPT
  {
    kind_ = symbol_kind::S_YYEMPTY;
  }

  inline
  void
   Parser ::by_kind::move (by_kind& that)
  {
    kind_ = that.kind_;
    that.clear ();
  }

  inline
   Parser ::symbol_kind_type
   Parser ::by_kind::kind () const YY_NOEXCEPT
  {
    return kind_;
  }


  inline
   Parser ::symbol_kind_type
   Parser ::by_kind::type_get () const YY_NOEXCEPT
  {
    return this->kind ();
  }


#line 10 "parser.y"
} //  adl 
#line 2955 "Parser.h"




#endif // !YY_YY_PARSER_H_INCLUDED
