# T++ 3.2.0 Language Specification

This document serves as the canonical grammar, semantic, and syntax reference for **T++ 3.2.0**.

---

## 1. Lexical Conventions & Syntax Structure

- **Indentation**: 4 spaces per indentation level. Indentation denotes statement blocks.
- **Comments**: `#` starts a single-line comment extending to the end of the line.
- **Identifiers**: Match `[A-Za-z_][A-Za-z0-9_]*`.
- **String Literals**: Enclosed in single (`'...'`) or double (`"..."`) quotes.
  - String interpolation: `{expr}` embedded in string literals is dynamically evaluated.
- **Number Literals**: Standard decimal integer and floating-point literals (e.g. `42`, `3.14159`).

---

## 2. Variables & Gradual Types

### Declarations & Assignments
- Untyped: `let <name> be <expr>`
- Typed: `let <name> be <expr> as <type>`
- Mutation: `change <name> to <expr>`
- Fuzzy increment/decrement: `increase <name> by <n>`, `decrease <name> by <n>`

### Supported Types
- `a text` / `text` (`str`)
- `a number` / `number` (`float` or `int`)
- `a whole number` / `whole number` (`int`)
- `a boolean` / `boolean` (`bool`)
- `a list` / `a list of <type>` (`list`)
- `a record` / `a map` (`dict`)
- `a set` (`set`)
- `nothing` (`None`)
- Union types: `<type1> or <type2>` (e.g. `a number or text`)

---

## 3. Control Flow & Expressions

### Conditionals
```tpp
if <condition>:
    <statements>
otherwise if <condition>:
    <statements>
otherwise:
    <statements>
```

### Loops
- Count loop: `count from <start> to <end> as <var>:`
- Iteration: `for each <item> in <iterable>:` / `for each <index>, <item> in <iterable>:`
- While loop: `while <condition>:` / `keep doing while <condition>:`
- Repeat loop: `repeat <count> times:`
- Repeat until: `repeat until <condition>:`
- Loop control: `stop the loop` / `break`, `skip to the next` / `continue`

### Pattern Matching (`match`)
```tpp
match <expr>:
    when <pattern> [if <guard>]:
        <statements>
    otherwise:
        <statements>
```

---

## 4. Functions & Classes

### Functions
```tpp
define <name> with <p1> as <t1>, <p2> as <t2> = <default>, giving back <ret_type> as:
    <statements>
    give back <expr>
```

Calling functions:
- `call <fn> with <arg1> and <arg2>`
- `fn(arg1, arg2)`

### Classes
```tpp
create class <ClassName>:
    when created with <params>:
        set the "attr" of this to <value>

    define <method_name> with <params> as:
        give back <expr>
```

---

## 5. Error Handling

```tpp
try:
    <statements>
handle <ErrorType> as <var>:
    <statements>
handle any error as <var>:
    <statements>
finally:
    <statements>
```

Raising errors: `raise the error "<message>"` or `raise "<message>"`.

---

## 6. Modules & Packages

Exporting symbols:
```tpp
export define calculate with x as:
    give back x * 2

export let PI be 3.14159
```

Importing symbols:
```tpp
use calculate and PI from "./math_utils.tpp"
use the "math" module
use uppercase from "text"
```
