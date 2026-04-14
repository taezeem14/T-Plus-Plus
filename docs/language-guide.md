# T++ Language Guide

## Install and Run

Install locally:

```powershell
pip install .
```

Run with CLI:

```powershell
tpp run examples/hello.tpp
tpp repl
tpp test tests/regression.tpp
tpp doctor
```

## Parser Modes

- strict: accepts only formal T++ syntax
- fuzzy: supports natural variants (increase x by 2)
- intent: accepts assignment sugar (x = 2)

## Core Syntax

Variables:

```text
let x be 5
change x to x plus 10
x is like 12
```

Output and input:

```text
say "hello"
say "value" then x
ask "name?" into name
```

Conditions:

```text
if x is greater than 10:
    say "big"
but if x is at least 5:
    say "mid"
otherwise:
    say "small"
```

Loops:

```text
keep doing while x is less than 10:
    change x to x plus 1

repeat 5 times:
    say "hello"

for each item in items:
    say item

count from 1 to 3 as i:
    say i
```

Functions:

```text
define function add with a and b:
    give back a plus b

say call add with 2 and 3
```

Classes:

```text
create class Dog:
    when created with name:
        remember name
    define speak with no inputs:
        say "woof" then name
```

## GUI

```text
create window titled "My App" as app
set window size to 400 by 300 for app
create button "Click Me" as btn in window app
on button click for btn:
    say "Hello"
show window app
```

## Testing

```text
test "addition":
    expect 2 plus 3 to be 5
    expect type of 2 plus 3 to be int
    expect 8 to be between 1 and 10
```

Suites:

```text
suite "math suite":
    test "simple add":
        expect 2 plus 2 to be 4
```

## Imports

Native modules:

```text
bring in math
bring in text
bring in system
bring in time
```

Python bridge modules (restricted allow-list):

```text
bring in random as rng
bring in sqrt from math
```
