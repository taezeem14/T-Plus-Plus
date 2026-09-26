# T++ LANGUAGE PLATFORM — ENTERPRISE UPGRADE SPECIFICATION

> Target runtime: T++ Enterprise / Modern Edition (v3.2.0 Core Runtime & Tooling Platform)
> Target repository: github.com/taezeem14/T-Plus-Plus
> Target package: `tpp-language` on PyPI, current stable `3.1.3`
> Author of record: Muhammad Taezeem Tariq Matta (taezeem14)
> Brief type: full-platform feature expansion, hardening, and quality upgrade
> Execution mode: multi-agent, orchestrator + specialized sub-agents, staged in phases
> Document purpose: this is the single source of truth the orchestrator hands to every
> sub-agent it spawns. Every sub-agent MUST read Part 0 and its own assigned Part in full
> before writing a single line of code. Do not skim. Do not summarize this document and
> work from the summary — work from the document.

---

## HOW TO USE THIS BRIEF (READ FIRST, EVERY AGENT, EVERY TIME)

1. This brief is organized into **20 parts**. Part 0 is mandatory context for every agent.
   Parts 1–18 are feature/subsystem tracks. Part 19 is the release and validation gate.
2. **Do not work all parts in parallel from a cold start.** Dependency order matters — see
   `PART 0.6 — EXECUTION ORDER AND DEPENDENCY GRAPH` before spawning sub-agents. Working
   the plugin system before the parser's hook points exist will produce code that has to
   be thrown away.
3. Every part below ends with an explicit **"Definition of Done"** checklist. A sub-agent
   is not finished with its part until every box in its own checklist is genuinely true —
   not "mostly true," not "true except for the tests." If a box cannot be checked, the
   agent must say so explicitly in its final report and explain why, rather than silently
   marking it done.
4. Every part also lists **non-goals** — things that sound like they belong in that part
   but are explicitly out of scope for it (usually because they belong in a different part,
   or because they're out of scope for this brief entirely). Read the non-goals. They exist
   because past agent runs on this codebase over-scoped and touched files they shouldn't
   have.
5. **Backward compatibility is a hard constraint, not a suggestion.** T++ is already
   published on PyPI at 3.1.3. Real users may have `.tpp` scripts, `.tppconfig` files, and
   installed plugins written against 3.1.3 semantics. Every change must either (a) be purely
   additive, (b) be gated behind an explicit opt-in flag/config key, or (c) go through the
   deprecation path defined in Part 17. Silent breaking changes to existing syntax,
   semantics, CLI flags, or the JSON API contract are not acceptable under any
   circumstances. If a sub-agent believes a breaking change is genuinely necessary, it must
   stop and produce a written justification in `docs/decisions/` rather than making the
   change unilaterally.
6. **This is a real, shipping, PyPI-published project**, not a toy or a demo. Treat it with
   the care of production software: every change needs tests, every public API needs
   docs, every CLI command needs `--help` text, and nothing merges to `main` with a red CI
   run. "It works on my machine" is not a completion criterion.
7. Work in small, reviewable commits. One logical change per commit. Commit messages follow
   Conventional Commits (`feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`,
   `perf:`, `ci:`, `build:`, `revert:`). This is required for the changelog generation in
   Part 17 to work automatically.
8. When a design decision has more than one reasonable answer, do not silently pick one and
   move on. Write a short ADR (Architecture Decision Record) into `docs/decisions/NNNN-
   title.md` explaining the options considered and why the chosen one won. Future-you
   (or future-agent) will thank present-you.
9. If at any point a sub-agent discovers that implementing a feature as specified would
   require breaking one of the hard constraints in this document (backward compatibility,
   security sandboxing, the plugin API contract, etc.), it must stop, document the conflict,
   and propose alternatives — not silently violate the constraint to make the feature work.

---

# PART 0 — MISSION, CONSTRAINTS, AND CURRENT STATE

## 0.1 What T++ is, in one paragraph

T++ is a programming language and execution platform whose defining bet is that source code
can read like natural, instructive English (`let x be 5`, `increase x by 6`,
`expect x to be 10`, `say "Hello" then name`) while still compiling down to a deterministic,
predictable, debuggable execution model — not a fuzzy LLM-interpreted script, but a real
lexer → parser → semantic analyzer → optimizer → runtime pipeline with a defined grammar.
The pitch is "natural syntax at the top, predictable execution at the core," and every
feature added under this brief must honor that pitch. A feature that makes the language
more powerful but less readable, or more readable but non-deterministic, is a feature that
has failed the core thesis of the project.

## 0.2 What "make it all better" means, operationalized

The user's request was broad: "add more features, update it, upgrade it, make it all
better." Broad requests produce bad results when agents interpret them narrowly (e.g. "I'll
just add one stdlib function and call it done") or when they interpret them as license to
rewrite everything from scratch. This brief exists to convert "make it better" into a
concrete, bounded, staged program of work across every real subsystem of the platform:

- **Language surface** (Part 1, 2): more expressive, more natural syntax; new statement and
  expression forms; better error messages when syntax is almost-right.
- **Type system** (Part 3): currently the language appears dynamically/loosely typed based
  on the examples (`let x be 4`, no type annotation). Add an *optional*, *gradual* type
  layer that never breaks untyped scripts.
- **Runtime & performance** (Part 4): the evaluator, environment model, and profiler need
  real benchmarking, real optimization passes, and a documented performance story.
- **Standard library** (Part 5): math/text/system/time exist; this is a thin stdlib for a
  "production-grade" language claim. Expand it substantially and consistently.
- **Plugin system** (Part 6): "keyword rewrites and transform hooks" exist per the README;
  formalize this into a real, versioned, documented, secure extension API.
- **CLI** (Part 7): run/repl/test/plugin/api/doctor exist; add the commands a serious
  language tooling CLI needs (format, lint, build, bundle, init, upgrade, bench, docs).
- **API & Web IDE** (Part 8): the JSON execution API and web IDE backend need to grow into
  something that could plausibly power a real hosted playground, with the security posture
  that implies.
- **Tooling ecosystem** (Part 9): language server (LSP), editor extensions, syntax
  highlighting definitions, formatter, linter.
- **Package/module system** (Part 10): T++ currently has no visible import/module story
  in the README. This is a first-class gap for anything beyond toy scripts.
- **Interop** (Part 11): "Python module bridging is allow-listed" per the security notes —
  formalize, expand, and document this properly; consider a defined FFI story.
- **Error handling & diagnostics** (Part 12): exceptions, error recovery, and
  the quality of compiler/runtime error messages (a huge DX differentiator for a
  "human-first" language).
- **Testing infrastructure** (Part 13): test blocks exist in `.tpp` source; build out
  fixtures, mocking, coverage reporting, property-based testing hooks.
- **Documentation** (Part 14): `docs/language-guide.md`, `docs/plugin-guide.md`,
  `docs/web-ide.md`, `docs/devops.md` are referenced but need to actually be
  comprehensive, versioned, and example-rich.
- **Security** (Part 15): the sandboxing claims in the README need to be backed by real
  threat modeling, fuzzing, and a documented security policy — especially given T++ will
  run untrusted `.tpp` scripts through a public-facing API and web IDE.
- **Developer experience & onboarding** (Part 16): `tpp doctor`, better error output,
  interactive tutorials, a real "getting started in 5 minutes" path.
- **Versioning, deprecation, and release process** (Part 17): make the existing CI/release
  automation more rigorous and add a formal deprecation policy.
- **Community & governance** (Part 18): CONTRIBUTING.md, CODE_OF_CONDUCT.md, issue/PR
  templates, a public roadmap.
- **Validation & shipping** (Part 19): the actual gate that decides whether any of the
  above is allowed to reach `main` and be tagged for release.

## 0.3 Hard constraints (apply to every part, no exceptions)

- **No breaking changes to 3.1.3 syntax or semantics** without going through the
  deprecation path in Part 17.
- **No breaking changes to the CLI's documented flags/commands** (`tpp --version`,
  `tpp run`, `tpp test`, `tpp repl`, `tpp plugin install/list`, `tpp doctor`, `tpp api
  --serve`) — these are explicitly load-bearing per the CI contract in the current README.
  New flags are additive; existing flags keep their existing meaning.
- **No breaking changes to the JSON execution API's existing request/response shape**
  (`{"source": "...", "mode": "run"}` style payloads) without versioning the API (see
  Part 8.7).
- **Every new stdlib function, CLI command, and public API function needs a docstring, a
  doc page, and at least one test** before it can be considered done.
- **Security-sensitive work (sandboxing, Python interop, plugin execution, API auth) is
  never "good enough" — see Part 15 for the actual bar.**
- **Performance work must be backed by benchmarks, not vibes.** "This should be faster"
  is not an acceptable justification for a runtime change; a before/after benchmark number
  is.
- **Every agent respects the existing project layout** (`tpp/core`, `tpp/parser`,
  `tpp/runtime`, `tpp/stdlib`, `tpp/plugins`, `tpp/cli`, `tpp/api`) and extends it rather
  than inventing a parallel structure. New subsystems get new subpackages under `tpp/`,
  following the existing naming and layering conventions — do not, for example, create a
  top-level `src/` or `lib/` directory that duplicates `tpp/`.
- **License and packaging metadata are not to be touched** without explicit instruction —
  the README badge currently says "see repository" for license; do not assume a license
  and do not add license headers to files claiming a specific license unless the actual
  `LICENSE` file at repo root is read first and matched.

## 0.4 Non-goals for this entire brief

- **Do not rename the language, the package, or the CLI binary.** "T++" and `tpp` stay.
- **Do not switch the implementation language.** T++ is implemented in Python (per
  `pip install -e .[dev]`, `ruff check`, `pytest`); this brief does not ask for a Rust or
  Go rewrite of the core, though a future high-performance backend is *discussed* as an
  optional long-term item in Part 4.9 — discussed, not mandated.
- **Do not remove or destabilize the "human-first syntax" thesis** in the name of adding
  power. If a proposed feature would only be reachable through non-natural, symbol-heavy
  syntax, prefer a natural-syntax alternative or gate the symbol-heavy form behind an
  explicit "advanced mode" rather than making it the primary spelling.
- **Do not build a marketing website, logo, or branding assets** as part of this brief —
  that's out of scope; this brief is about the language platform itself.
- **Do not integrate with any specific commercial hosting provider** (no baked-in
  "deploy to X cloud" button) — keep the platform provider-neutral; deployment guidance
  belongs in docs, not in hardcoded product integrations.

## 0.5 Source-of-truth precedence when instructions conflict

If this brief conflicts with something discovered in the actual repository during
implementation (an existing test that encodes different behavior, an existing doc that
documents a different contract, an existing ADR), the order of precedence is:

1. Existing passing tests in the repo (they encode actual guaranteed behavior).
2. Existing `docs/decisions/*.md` ADRs.
3. This brief.
4. Existing prose docs (`docs/*.md`) that haven't been updated in a while — these are the
   most likely to be stale and should be treated as aspirational rather than authoritative.

When tests and this brief conflict, do not silently change the tests to match the brief.
Stop and flag it.

## 0.6 Execution order and dependency graph

Do not spawn all 18 feature-part sub-agents in parallel from a cold repository. Several
parts depend on infrastructure that other parts create. Recommended staging:

**Stage A — Foundations (sequential, must land first):**
- Part 12 (Error handling & diagnostics) — every other part benefits from and should build
  on the new diagnostic infrastructure.
- Part 3.1–3.3 (Type system: core type representation only, not full inference) —
  needed as a dependency for stdlib type signatures and LSP hover info later.
- Part 10.1–10.3 (Module system: core `import`/`export` grammar and resolution) — needed
  before plugins, stdlib expansion, and package management can be meaningfully designed.

**Stage B — Core subsystems (can parallelize once Stage A lands):**
- Part 1, 2 (Language surface features)
- Part 4 (Runtime & performance)
- Part 5 (Standard library expansion)
- Part 6 (Plugin system formalization)
- Part 11 (Interop & FFI)

**Stage C — Tooling built on Stage B (parallelize once relevant Stage B pieces land):**
- Part 7 (CLI expansion) — depends on whichever Stage B features it exposes.
- Part 8 (API & Web IDE) — depends on Part 15 security work landing alongside it, not
  after.
- Part 9 (LSP & editor tooling) — depends on Part 12 diagnostics and Part 3 types.
- Part 13 (Testing infrastructure)

**Stage D — Platform-wide, can start early but finishes last:**
- Part 14 (Documentation) — should be updated incrementally as each part lands, not
  bolted on at the end, but the *comprehensive* pass happens last.
- Part 15 (Security) — threat modeling starts in Stage A conceptually, but the hardening
  work is validated continuously and gates Stage C's API/Web IDE work specifically.
- Part 16 (DX & onboarding)
- Part 17 (Versioning & release process)
- Part 18 (Community & governance)

**Stage E — Gate:**
- Part 19 (Validation & shipping) — nothing ships without this.

## 0.7 Definition of Done for Part 0

- [ ] Every sub-agent's first commit message references which Part(s) it is working and
      confirms (in the PR description) that it has read Part 0 in full.
- [ ] A `docs/decisions/` directory exists with at least a `0001-brief-adoption.md` ADR
      recording that this brief was adopted as the working plan, with a link back to this
      document (or a copy of it committed at `docs/BRIEF.md` for permanence, since this
      brief will not otherwise persist anywhere in the repo).
- [ ] The execution order in 0.6 is reflected in the actual PR/branch sequencing observed
      in repo history.

---

# PART 1 — CORE LANGUAGE SURFACE: STATEMENTS AND CONTROL FLOW

## 1.1 Context

The README shows `say`, `let ... be`, `increase ... by`, `expect ... to be`. This is a
minimal set — enough for a "hello world" and a basic assertion, not enough for real
programs. Real programs need conditionals, loops, functions, data structures, and error
handling, all spelled in a way that reads as natural English while parsing unambiguously.
This part is the highest-leverage part of the entire brief: if the surface syntax design
is wrong, everything built on top of it (stdlib signatures, LSP hover text, plugin hook
points) inherits the wrongness.

## 1.2 Design principle: the "read-aloud test"

Every new syntax form proposed under this part must pass the read-aloud test: read the
line of code aloud, exactly as written, to someone who has never programmed. If it sounds
like an instruction a person could plausibly give another person ("if the score is greater
than 90, say 'Excellent'"), it passes. If it sounds like you're reading symbols
("if score greater_than 90 colon say quote Excellent quote"), it fails and needs
rework. This is not a nice-to-have; it is the test that determines whether T++ is
differentiated from every other scripting language, all of which already have adequate
`if`/`for`/`function` keywords.

## 1.3 Conditionals

Design and implement natural conditional syntax with these required forms:

```tpp
if x is greater than 10 then
    say "big"
otherwise if x is 10 then
    say "exact"
otherwise
    say "small"
end
```

Requirements:
- Support comparison phrases as first-class grammar, not just a `>` symbol wearing a
  costume: `is greater than`, `is less than`, `is at least`, `is at most`, `is equal to`
  (or bare `is`), `is not`, `is between X and Y`. Each of these must have a symbolic
  fallback (`>`, `<`, `>=`, `<=`, `==`, `!=`) for users who want it — both must parse to
  the same AST node so tooling (formatter, linter) treats them identically.
- `otherwise if` and `otherwise` (not `else if`/`else` — stay consistent with the
  "otherwise" vocabulary already implied by natural phrasing; but ship `else`/`else if`
  as accepted synonyms since many users will type what they know from other languages —
  see 1.9 on synonym handling).
- A single-line form for simple cases:
  `say "big" if x is greater than 10 otherwise say "small"` — a natural-English postfix
  conditional, analogous to Python's conditional expression but spelled as a sentence.
- Boolean combinators spelled naturally: `and`, `or`, `not`, plus natural phrasing sugar
  `x is greater than 5 and x is less than 20` should also be expressible as
  `x is between 5 and 20` — implement `between` as sugar that desugars to the AND form at
  parse time, so the runtime only ever sees one canonical shape.
- Truthiness rules must be explicitly defined and documented (what counts as falsy: is it
  only `false`, or also `nothing`/`none`, `0`, `""`, empty collections? — pick a rule that
  is predictable and document it prominently, since implicit truthiness is one of the most
  common sources of subtle bugs in dynamically-typed languages; the "predictable execution
  core" thesis in the README argues for a stricter truthiness model — likely: only an
  explicit boolean `false` and the `nothing` value are falsy, everything else (including
  `0` and `""`) is truthy — but this decision should be written up as an ADR with the
  tradeoffs explicit, not silently assumed).

## 1.4 Loops

Required forms, all natural-English spellings:

```tpp
repeat 5 times
    say "hi"
end

for each item in collection
    say item
end

for each index, item in collection
    say index then item
end

while x is less than 10
    increase x by 1
end

repeat until x is 10
    increase x by 1
end
```

Requirements:
- `repeat N times` — fixed-count loop with an implicit loop variable available as
  `the count` or similar natural handle, not a bare unnamed index.
- `for each ... in ...` — iteration over any iterable stdlib type (lists, ranges, maps,
  strings-as-character-sequences, future user-defined iterables via Part 1.7's iterator
  protocol).
- `while` and `repeat until` as two natural framings of the same underlying loop
  construct (pre-condition vs. post-negated-condition framing) — desugar both to one AST
  shape.
- `break` and `continue` — spell these naturally too: `stop the loop` /
  `skip to the next` as primary natural spellings, with `break`/`continue` as accepted
  symbol-style synonyms (see 1.9).
- Loop-else support (a natural-English equivalent of Python's `for...else`) is **explicitly
  out of scope** for this part — it's a known-confusing feature even in mature languages
  and doesn't clearly pass the read-aloud test; do not add it without a separate design
  discussion.
- Infinite-loop protection in the runtime: an optional, configurable max-iteration guard
  (default off in `run`, default on with a sane limit in the web IDE / API context — see
  Part 8 and Part 15) that raises a T++ runtime error rather than hanging the host process
  forever. This is a security requirement, not just a nicety, once untrusted scripts can
  reach the API.

## 1.5 Functions

```tpp
define greet with name as
    say "Hello" then name
end

define add with a and b as
    give back a plus b
end

let result be add with 3 and 4
```

Requirements:
- `define <name> with <params> as ... end` for function declaration. Support zero, one,
  and multiple parameters with natural conjunctions (`with a and b and c`).
- `give back <expr>` as the natural spelling for `return`, with `return` itself accepted
  as a synonym.
- Default parameter values: `define greet with name as "World"` — natural default-value
  spelling using `as` for the default, being careful that this doesn't collide
  grammatically with the `as` used to open the function body; resolve this ambiguity
  explicitly in the grammar (likely: defaults use `defaulting to` instead of `as`, to keep
  the grammar LL(1)-friendly and avoid the collision — `define greet with name defaulting
  to "World" as ... end`).
- Variadic parameters: `define total with numbers (however many) as ...` or similar
  natural spelling for "rest parameters" — design this so it reads sensibly; do not just
  bolt on a `*args`-style symbol.
- Named/keyword arguments at call sites: `add with a as 3 and b as 4` should be valid and
  should resolve identically to positional `add with 3 and 4` when names match parameter
  names — implement this in the semantic analyzer, not just the parser.
- First-class functions: functions must be values that can be assigned to variables,
  passed as arguments, and returned from other functions. Anonymous/lambda functions get
  natural syntax: `a function that takes x and gives back x times 2`. This is required for
  the stdlib's higher-order functions in Part 5 (map/filter/reduce equivalents) to be
  expressible at all.
- Closures: functions must correctly capture their defining environment. This needs
  explicit test coverage of the classic closure-in-a-loop pitfall (each generated closure
  must see its own binding of the loop variable in a `for each`, not a single shared
  mutable slot last-write-wins) — this is a common correctness bug in interpreter
  implementations and must be a named test case, not just implied by "closures work."
- Recursion must work, including mutual recursion between two `define`d functions at the
  same scope. Establish a documented, configurable maximum call-stack depth with a clean
  T++-level "stack overflow" runtime error rather than crashing the Python process with an
  unhandled `RecursionError`.

## 1.6 Data literals and collections

Requirements:
- **Lists**: `let items be a list containing 1 and 2 and 3` as the natural long form, with
  `[1, 2, 3]` as an accepted compact literal synonym (both must parse to the same AST
  node — see 1.9).
- **Maps/records**: `let person be a record with name as "Ana" and age as 30`, with
  `{name: "Ana", age: 30}` as compact synonym. Field access via `person's name` (natural
  possessive) as primary spelling, with `person.name` as accepted synonym.
- **Ranges**: `1 to 10` and `1 to 10 by 2` (step) as first-class range values usable in
  `for each` and slicing.
- **Sets**: natural literal form, e.g. `a unique list containing ...` or a dedicated `a set
  containing ...` — pick one consistent spelling and document why.
- **Nested structures**: literals must nest correctly and the parser must produce sane
  error messages (see Part 12) on common mistakes like unbalanced literal nesting or
  missing `and` separators.
- **Mutability semantics**: define explicitly which literals are mutable in place
  (lists, records) vs. immutable (numbers, strings, booleans, tuples-if-added) and document
  this prominently, since it directly affects the correctness of closures (1.5) and
  function argument passing (value vs. reference semantics — the language needs an
  explicit, documented parameter-passing model, likely "primitives by value, collections by
  reference," matching most mainstream dynamic languages, but this must be a stated
  decision with an ADR, not an emergent accident of the implementation).

## 1.7 Iterators and generators

- Define an internal iterator protocol (analogous to Python's `__iter__`/`__next__`) that
  every built-in collection implements and that user-defined types (once Part 3's type
  system supports user-defined composite types) can implement too.
- Add natural-syntax generator functions: `define count up to N as ... yield i ... end`
  with `yield` spelled naturally, e.g. `give one back and continue with <expr>` as the
  literal spelling, with `yield <expr>` accepted as a compact synonym. This is a
  genuinely hard feature (requires coroutine-style suspension in the evaluator) — do not
  under-scope the runtime work required; budget real design time for the evaluator changes
  in Part 4 before committing to a syntax that can't be implemented cleanly.
- Lazy evaluation: ranges and generator results should be lazily evaluated where sensible
  (don't materialize `1 to 10000000` as a full list) — document which stdlib operations
  force materialization and which stay lazy.

## 1.8 Error handling in the language itself

```tpp
try
    let result be risky_operation with x
handle DivisionError as e
    say "Cannot divide:" then e's message
finally
    say "Cleanup done"
end
```

- `try` / `handle <ErrorType> as <name>` / `finally` / `end` as the natural spelling of
  try/catch/finally, with a documented, extensible built-in exception hierarchy (see Part
  12.4 for the actual hierarchy design — this section just establishes the surface syntax).
- `throw <expr>` (or a more natural `raise the error <expr>` — decide and document one
  primary spelling) for user-raised errors.
- Multiple `handle` clauses for different error types, evaluated in order, first match
  wins — this must be specified precisely (what happens with overlapping/hierarchical
  error types) and tested.
- A natural spelling for "catch anything": `handle any error as e`.

## 1.9 Synonym handling: a first-class grammar concern, not an afterthought

Several sections above call for a "natural primary spelling" plus a "symbol-style accepted
synonym" (e.g. `otherwise`/`else`, `[1,2,3]`/`a list containing 1 and 2 and 3`,
`person.name`/`person's name`). This is not incidental — it's a deliberate strategy to let
T++ be genuinely natural-reading for newcomers while not alienating experienced programmers
who want to type fast. Implementation requirements:

- All synonym pairs must desugar to **identical AST nodes** at parse time. The rest of the
  pipeline (semantic analyzer, optimizer, runtime, formatter, linter) must never need to
  know which spelling the user chose.
- Maintain a single canonical table of synonym mappings in `tpp/parser/` (not scattered
  across multiple files) so it's auditable and extensible by plugins (see Part 6.6).
- The formatter (Part 9.4) needs a configurable "preferred spelling" setting so a team can
  enforce consistent style (`tpp format --style natural` vs `--style compact`) — this is a
  real, useful feature, not scope creep, because it lets T++ serve both "teaching/readable
  codebase" use cases and "fast to write, dense" use cases from the same grammar.
- Document every synonym pair explicitly in the language guide (Part 14) in one canonical
  reference table — do not let synonym pairs be discoverable only by reading the parser
  source.

## 1.10 Non-goals for Part 1

- Do not implement operator overloading for user-defined types in this part — that's
  entangled with the type system and belongs in Part 3 once user-defined composite types
  exist.
- Do not implement pattern matching / destructuring as a full feature in this part; a
  minimal destructuring assignment (`let a and b be the first and second of pair`) is
  in-scope, but a full `match`/`when` expression construct is a Part 2 (advanced
  expressions) concern — see 2.6.
- Do not implement async/await or any concurrency primitives in this part — that is a
  runtime-level concern with its own security and determinism implications, tracked
  separately in Part 4.8, and must not be casually added to the surface grammar without
  that design work happening first.

## 1.11 Definition of Done for Part 1

- [ ] Grammar for every construct above is formally specified (EBNF or equivalent) and
      committed to `docs/language-guide.md` §Grammar, not just implemented ad hoc in the
      parser.
- [ ] Every construct has both natural and (where specified) synonym spellings, verified
      by tests that assert both spellings produce identical ASTs.
- [ ] The synonym table lives in one place and is documented in one canonical table in
      `docs/language-guide.md`.
- [ ] Closures-in-loops, mutual recursion, and stack-depth-limit behaviors each have an
      explicit, named regression test.
- [ ] Truthiness rules and mutability/parameter-passing semantics are each written up as an
      ADR and cross-referenced from the language guide.
- [ ] `tpp doctor` and the CLI's own test suite (`tpp test`) both exercise every new
      construct at least once via example `.tpp` fixture files under `examples/` or
      `tests/`.
- [ ] Every new keyword is checked against the existing grammar for ambiguity — run the
      full existing test suite plus all `examples/*.tpp` scripts from 3.1.3 and confirm
      zero regressions before considering this part done.

---

# PART 2 — ADVANCED EXPRESSIONS AND EXPRESSION-LEVEL FEATURES

## 2.1 Context

Part 1 covers statements and control flow. This part covers everything that happens inside
an expression: arithmetic, string handling, comprehensions, pattern matching, and the
expression-oriented features that separate a merely-usable language from a pleasant one.

## 2.2 Arithmetic and operator vocabulary

The README shows `increase x by 6` and implies `plus` (from `a plus b` in the closures
example above, extrapolated). Formalize the full natural arithmetic vocabulary:

- `plus`, `minus`, `times`, `divided by`, `modulo` (or `remainder of ... divided by ...`
  as a fully natural alternative), `to the power of`, with standard symbols (`+ - * / % **`)
  as accepted synonyms per the 1.9 synonym-handling policy.
- Precedence and associativity must be formally specified in the grammar doc — natural
  language is not naturally left-to-right unambiguous (`a plus b times c` — does this read
  as `(a + b) * c` or `a + (b * c)`?). Decide standard mathematical precedence (multiplication
  binds tighter) since that matches programmer and general expectation, document it loudly,
  and provide a natural way to force grouping: `the sum of a and b, times c` using a comma
  as a natural grouping cue, in addition to standard parentheses.
- Compound assignment: `increase x by 6`, `decrease x by 2`, `multiply x by 3`,
  `divide x by 2` as the natural forms, with `x += 6` etc. as symbol synonyms.
- Increment/decrement shorthand: `increase x` (implicit by 1) and `decrease x`.
- Integer vs. float behavior must be explicitly specified: does `divide 7 by 2` produce
  `3.5` or `3`? Pick float-by-default true division (matching the "predictable, not
  surprising" thesis) and provide an explicit natural spelling for integer/floor division:
  `divide 7 by 2, rounding down`.

## 2.3 String handling

- String interpolation: a natural spelling that avoids symbol-soup. Given the existing
  `say "Welcome" then name` pattern for concatenation-via-multiple-args, also add true
  interpolation: `say "Welcome, {name}!"` with `{expr}` interpolation syntax — this is one
  case where a compact symbol form is justified because natural-language interpolation
  (spelling out "insert the value of name here" inline) is genuinely worse to read, not
  just less familiar; document this as a deliberate exception to the "always provide a
  fully natural primary spelling" rule and explain why in the language guide.
- Multi-line strings with a natural triple-quote or block form.
- String methods exposed as natural method-call-ish syntax matching the `person's name`
  possessive pattern from 1.6: `name's length`, `name's uppercase version`, or as stdlib
  function calls (`the uppercase version of name`) — reconcile this with Part 5's stdlib
  design so there is exactly one, consistently-applied convention for "properties/derived
  values of a value" vs. "functions that operate on a value," not two competing patterns.
- Regular expression support: natural wrapper syntax over standard regex (`text matches
  the pattern "..."`), documented clearly as "this is standard PCRE-style regex under a
  natural-reading wrapper," not a natural-language pattern-matching DSL — don't
  over-promise here, regex is regex, just make invoking it read naturally.

## 2.4 Comprehensions

Natural-language comprehension syntax for building collections from existing ones:

```tpp
let doubled be a list containing item times 2 for each item in numbers
let evens be a list containing item for each item in numbers if item is even
```

- Must desugar cleanly to the `for each`/`if` primitives already defined, so the runtime
  has one execution path, not a special-cased comprehension evaluator.
- Support the filter clause (`if ...`) as optional.
- Support map-comprehension equivalent: `a record with (item's key) as (item's value) for
  each item in pairs`.
- Do not let comprehension syntax nesting get so deep it fails the read-aloud test —
  document a soft style guideline (not a hard parser limit) recommending comprehensions be
  extracted to a named `define`d function once they exceed roughly two clauses.

## 2.5 Optional chaining and null-safety

- Given a `nothing`/`none` value must exist (implied by 1.3's truthiness discussion), add
  natural optional-access syntax: `person's address's city if person's address exists
  otherwise "Unknown"` is verbose — provide a compact but still natural safe-navigation
  form, e.g. `person's address's city, if present, otherwise "Unknown"`.
- A natural "exists"/"is nothing" check as a first-class predicate usable in conditionals.
- This must integrate with Part 3's gradual type system so that, once a variable is typed
  as optional, the analyzer can warn about un-guarded access at analysis time rather than
  only failing at runtime — but the syntax itself should work identically whether or not
  types are in use, since types are optional per Part 3's design goal.

## 2.6 Pattern matching / `match` expressions

```tpp
match shape
    when a Circle with radius as r then
        give back 3.14159 times r times r
    when a Rectangle with width as w and height as h then
        give back w times h
    otherwise
        give back 0
end
```

- This is a substantial feature entangled with Part 3's type system (matching on
  user-defined composite/tagged types). Scope the *first* implementation to matching on:
  literal values, ranges, type-tags of built-in and user-defined record types, and a
  wildcard/otherwise case, with destructuring bindings as shown above.
- Exhaustiveness checking is a stretch goal, not a requirement, for the first version —
  but the design should not preclude adding it later once the type system (Part 3) is far
  enough along to know the full set of variants for a given tagged type.
- `match` is an **expression**, not just a statement — it must produce a value usable in
  `let result be match ... end`, consistent with the language's general expression-oriented
  leanings implied by comprehensions.

## 2.7 Non-goals for Part 2

- Do not implement full monadic/functional-programming-style abstractions (functors,
  applicatives, custom operator definition for arbitrary symbols). This does not fit the
  "human-first, natural syntax" thesis and is explicitly rejected as a direction, not just
  deferred.
- Do not implement macro systems or compile-time metaprogramming in this part — that
  belongs, if ever, under Part 6 (plugins) as a controlled extension point, not as a raw
  language feature, because uncontrolled macros are one of the most common sources of
  unreadable, un-debuggable code in the languages that have them.

## 2.8 Definition of Done for Part 2

- [ ] Full operator precedence table is documented and covered by a dedicated
      precedence-stress-test fixture file exercising every combination of two adjacent
      precedence levels.
- [ ] Integer/float division semantics are documented in one place and consistent across
      every stdlib function that touches numeric division (cross-check against Part 5).
- [ ] String interpolation, comprehensions, optional-chaining, and match expressions each
      have dedicated fixture `.tpp` files under `examples/`, referenced from the language
      guide as canonical examples.
- [ ] `match` correctly produces a value when used in `let ... be match ... end` position,
      verified by test.
- [ ] The "one exception to natural-primary-spelling" carve-out for string interpolation is
      documented explicitly in the language guide's design-rationale section, so it doesn't
      read as an inconsistency to future readers.

---

# PART 3 — GRADUAL, OPTIONAL TYPE SYSTEM

## 3.1 Context and design philosophy

T++ as shown in the README is dynamically typed (`let x be 4` has no type annotation).
A "production-grade" language claim is hard to sustain at scale without *some* type
story — but forcing types onto a language whose whole pitch is approachable, natural
syntax would undermine the thesis for beginners. The answer is a **gradual type system**:
fully optional, fully backward-compatible, useful when adopted, invisible when ignored.
This mirrors the design philosophy of TypeScript-over-JavaScript, Python's type hints, and
Sorbet-over-Ruby — a well-trodden and well-understood path, not a novel risk.

## 3.2 Non-negotiable design constraint

**Untyped T++ 3.1.3 scripts must continue to run byte-for-byte identically, with zero
performance regression attributable to type-checking overhead when no types are present in
the source.** Type checking must be an entirely separate, skippable analysis pass that
never runs at all — not runs-and-no-ops, actually does not execute — when a script contains
zero type annotations. This is the single most important constraint in this entire part
and must be verified by a benchmark comparing an untyped script's execution time before and
after this part's changes land.

## 3.3 Type annotation syntax

Natural-reading, optional, and unobtrusive:

```tpp
let x be 4 as a number
define add with a as a number and b as a number, giving back a number as
    give back a plus b
end
```

- `as a <type>` for variable/parameter annotations — reads naturally, doesn't require
  new punctuation.
- `, giving back a <type>` for function return type annotations.
- Built-in base types: `a number`, `a whole number` (integer specifically, if the language
  distinguishes int/float — reconcile with 2.2's division semantics decision), `text` (for
  strings — consider whether "a string" or "text" reads more naturally and pick one
  consistently), `a boolean`, `nothing` (as a type meaning the optional/null type, reusing
  the value-level vocabulary from 2.5), `a list of <type>`, `a record` (with optional
  shape specification), `a function that takes <types> and gives back <type>`.
- Union types, spelled naturally: `as a number or nothing` for optional types, reusing the
  `or` keyword already established in boolean logic (1.3) rather than inventing a `|`
  pipe-symbol-only spelling (though `|` remains available as a compact synonym per 1.9).
- User-defined composite/record types with a natural declaration form:
  ```tpp
  define a Circle as a shape with
      radius as a number
  end
  ```
  This introduces tagged/nominal types usable in `match` (2.6) and needed for anything
  resembling real domain modeling.

## 3.4 Type inference

- Where a variable is declared without annotation but its initializer is unambiguous
  (`let x be 4` — clearly a number), the analyzer *may* infer a type internally for the
  purposes of optional warnings and LSP hover info (Part 9), but this inference must never
  be *enforced* — an untyped `let x be 4` followed later by `set x to "hello"` must remain
  perfectly legal T++ unless the user explicitly opted into strict mode (3.6). Inference is
  purely advisory unless strict mode says otherwise.
- Document clearly, in the language guide, the difference between "the analyzer inferred a
  likely type for tooling purposes" and "the runtime enforces a type" — these are two
  different concepts and conflating them in documentation will confuse users badly.

## 3.5 Runtime type checking vs. static-only checking

- Decide and document explicitly: are type annotations checked only at analysis time (like
  Python's type hints, erased before execution — "static-only, unenforced at runtime by
  default") or are they also enforced at runtime (like a soft runtime assertion, raising a
  T++ TypeError if violated)? Given the language's "predictable execution" thesis and the
  target audience including learners, the recommended default is: **static-only warnings
  during analysis, PLUS optional lightweight runtime enforcement available via a
  `.tppconfig` setting** (`enforce_types: true`) or a CLI flag (`tpp run --strict-types`),
  defaulting to off. This gives beginners helpful non-blocking hints and gives production
  users an opt-in safety net, satisfying both audiences without picking one.
- If runtime enforcement is enabled, violations must raise a proper T++-level exception
  (integrating with Part 1.8's try/handle system) with a clear, specific message — not a
  raw Python `TypeError` leaking through.

## 3.6 Strict mode

- A per-file or per-project opt-in (`.tppconfig` key `strict_types: true`, or a source-level
  pragma like a leading `use strict types` statement) that makes the analyzer treat type
  mismatches as **errors that block execution** rather than warnings. This is for teams
  who want TypeScript-strict-mode-style guarantees. Must be fully optional and fully
  documented as a project-level choice, not a language-wide default now or ever.

## 3.7 Generics

- Deferred/stretch scope for this part: a minimal generic-function story (`define
  identity with x as a T, giving back a T as ... end` using single-uppercase-letter type
  variables as the natural-enough spelling, avoiding invented angle-bracket syntax) is
  desirable but should not block shipping the rest of Part 3. If time-boxed out, document
  it explicitly as a follow-up in the roadmap (Part 18.4) rather than silently dropping it.

## 3.8 Non-goals for Part 3

- Do not implement a full Hindley-Milner-style type inference engine. Advisory,
  local, per-statement/per-expression inference is sufficient; whole-program unification
  is explicitly out of scope for this brief.
- Do not make types affect runtime dispatch/method resolution in this part (no operator
  overloading based on static types, no multiple dispatch) — that's a much larger,
  separate design problem and is out of scope here.
- Do not require type annotations anywhere in the standard library's own public-facing
  example code in docs — stdlib examples in Part 5/14 should generally stay in the
  natural, unannotated style to keep the "types are optional" message credible throughout
  the documentation, with a dedicated section showing the typed style separately.

## 3.9 Definition of Done for Part 3

- [ ] Benchmark proving zero measurable overhead on scripts with no type annotations
      present, committed to `tests/perf/` and re-run in CI (see Part 19).
- [ ] Every base type and the union/optional spelling is documented with at least one
      example in `docs/language-guide.md`.
- [ ] `enforce_types`/strict-mode behavior is covered by tests for both the "warn only"
      and "block execution" paths.
- [ ] User-defined composite/record types work correctly with `match` (Part 2.6) via
      integration tests spanning both parts.
- [ ] The advisory-vs-enforced distinction is documented prominently and unambiguously,
      including in `tpp doctor`'s output if `tpp doctor` inspects a project's type-related
      config (see Part 16).

---

# PART 4 — RUNTIME, EVALUATOR, AND PERFORMANCE

## 4.1 Context

The existing architecture names `runtime/engine, evaluator, environment, interop,
profiler` — a real tree-walking (most likely) interpreter architecture already exists. This
part is about making that runtime faster, more correct under load, more observable, and
capable of supporting the new language features from Parts 1–3 (generators/coroutines,
gradual types, pattern matching) without architectural rewrites later.

## 4.2 Baseline benchmarking (do this before any optimization work)

- Before touching runtime internals, build a benchmark suite (`tests/perf/benchmarks/`)
  covering: tight numeric loops, recursive function calls (fibonacci-style), string
  concatenation/building at scale, large collection iteration (map/filter/reduce-style
  workloads once Part 5 stdlib exists), and a "realistic mixed workload" script.
- Record baseline numbers for 3.1.3 (or the current pre-this-brief `main`) before any
  changes land, and commit them to `tests/perf/baseline.json` or equivalent. Every
  subsequent performance claim in this part must cite a before/after delta against this
  baseline, run on the same benchmark suite, not a new one invented to make a change look
  good.
- Set up `tpp bench` as a CLI subcommand (coordinate with Part 7) that runs this suite and
  reports results in both human-readable and machine-readable (JSON) form, so CI (Part 19)
  can track performance over time and fail on regressions past a documented threshold
  (e.g. >10% slower than baseline on any benchmark fails CI, configurable).

## 4.3 Evaluator architecture review

- Audit whether the current evaluator is a naive tree-walking interpreter re-dispatching
  on AST node type via something like a big if/elif chain or Python's `visitor` pattern.
  If so, and if benchmarks show dispatch overhead is meaningful, consider (in order of
  increasing invasiveness, and only as far as the benchmarks justify):
  1. Method-dispatch-table optimization (replace linear if/elif with a dict-based dispatch
     keyed on node type) — low risk, easy win if applicable.
  2. AST node caching/memoization for pure sub-expressions where safe.
  3. A bytecode compilation pass (AST → simple stack-based or register-based bytecode →
     bytecode interpreter loop) as a genuinely bigger architectural change — only pursue
     this if the benchmark data from 4.2 shows tree-walking overhead is the actual
     bottleneck (not, say, environment/variable-lookup overhead, which is often the real
     cost in interpreters and should be checked first via profiling, not assumed).
- Whatever is chosen, it must be justified by the profiler output (the existing
  `runtime/profiler` module — use it, don't bypass it) and documented in an ADR.

## 4.4 Environment / variable-lookup model

- Profile variable lookup specifically — in many interpreters this, not raw dispatch, is
  where time goes, especially with the closures and nested-scope requirements from Part
  1.5.
- If lookups are currently a naive linear scope-chain walk with dictionary lookups at each
  level, consider scope-resolution-at-analysis-time (resolving each variable reference to a
  concrete "N scopes up, slot K" address during the semantic-analysis pass, so the runtime
  does an O(1) array access instead of a chain of dict lookups). This is a well-established
  interpreter optimization technique (used by, e.g., CPython's fast locals, Lua's upvalue
  resolution) and pairs naturally with the semantic analyzer that already exists in the
  pipeline.
- This must not change any observable behavior — closures must still capture correctly
  (verify against the Part 1.5 closure-in-loop test), shadowing must still work identically,
  and dynamic features like `eval`-equivalents (if T++ has or gets one) must be handled
  correctly or explicitly documented as incompatible with the optimization.

## 4.5 Optimizer pass

- The existing `parser/optimizer` module (per the architecture tree) should be audited and
  expanded. Concrete optimizer passes worth adding, each independently benchmarked:
  - Constant folding (`2 plus 3` → `5` at compile/analysis time when both operands are
    literals).
  - Dead code elimination for unreachable branches when statically determinable (e.g. after
    an unconditional `give back` in a function body).
  - Common subexpression consideration for comprehensions (Part 2.4) — low priority, only
    if benchmarks justify it.
- Every optimizer pass must be independently toggleable via an internal flag for debugging
  and must have tests asserting that optimized and unoptimized execution produce identical
  *results* (the optimizer must never change program behavior, only how fast it's reached).

## 4.6 Memory model and garbage collection

- Since the runtime is implemented in Python, T++ inherits Python's GC by default via
  however AST nodes/environments/values are represented as Python objects. Document this
  explicitly — do not imply a custom GC exists if it doesn't.
- Audit for reference cycles that could leak memory in long-running contexts (this matters
  especially once the web IDE / API in Part 8 runs long-lived or repeated executions in the
  same process) — closures capturing environments that capture closures are a classic
  cycle source. Use Python's `gc` module diagnostics or `objgraph`-style tooling in a
  dedicated audit, document findings, and fix any genuine leaks found.
- If the API/Web IDE context (Part 8) runs many short-lived scripts in a shared long-running
  process, consider (and document the decision either way) whether each execution should
  get a genuinely isolated environment that's fully dropped and eligible for GC afterward,
  vs. reused environment pooling for performance — this has real security implications
  too (state leaking between "isolated" executions is a vulnerability class) so this
  decision must be cross-referenced with Part 15.

## 4.7 Interop layer hardening and expansion

- The existing security note says "Python module bridging is allow-listed." Formalize
  this: a single, auditable allow-list configuration (not scattered `if module_name ==
  "x"` checks across the codebase) defining exactly which Python stdlib/third-party
  modules T++ scripts can reach through interop, with a documented process for how a new
  module gets added to the allow-list (this belongs partly here, partly in Part 15's
  threat model).
- Expand the *usefully allow-listed* surface thoughtfully: common needs like `json`,
  `datetime` (if not already covered by the `time` stdlib module), `re` (if not wrapping
  it via Part 2.3's regex syntax), `math` (if not already covered), `csv`. Every addition
  to the allow-list must go through: (a) a security review of what that module can do
  (file I/O? network? subprocess spawning?), (b) exposure through a T++-natural wrapper
  API rather than raw Python object leakage into T++ scripts, and (c) a test.
- Modules capable of filesystem access, network access, or process spawning (`os`,
  `subprocess`, `socket`, unrestricted `open`) must NOT be added to the general
  allow-list. If T++ needs controlled file I/O (likely, for a real language), it should get
  its own sandboxed stdlib `system`/`files` API (Part 5.6) that mediates access through
  T++'s own permission model, not raw Python file-object passthrough.

## 4.8 Concurrency (design-only in this part; deferred implementation)

- The surface language explicitly does not get async/await in Part 1 (see 1.10's
  non-goals). This subsection is where the *runtime-level* groundwork gets scoped, since
  it's a legitimate "make it better" request area and users will ask for it.
- Produce an ADR evaluating options: cooperative coroutines built on the generator/yield
  infrastructure already required for Part 1.7, vs. thread-based concurrency with the GIL
  caveats that implies in Python, vs. deferring entirely to a future major version.
  Recommendation to evaluate first: cooperative, generator-based concurrency (an "await
  the result of" natural syntax built on the same suspension mechanism as `yield`) since it
  reuses infrastructure already being built and avoids GIL/thread-safety complexity in the
  interpreter itself. This part's deliverable is the ADR and a prototype behind a feature
  flag, not a fully shipped, documented, stable concurrency feature — that's appropriately
  larger than this brief's scope and should become its own future brief.

## 4.9 Long-term performance ceiling (discussion only, not mandated)

- Document, as a forward-looking section in the ADR, what a compiled/bytecode-VM or
  alternate-backend (e.g. compiling to Python bytecode directly via `ast` module targeting,
  or a longer-term native backend) path could look like, purely so future planning has
  something to reference. **Do not implement this in the current brief** — flag it as an
  explicit, named future direction in Part 18's roadmap instead.

## 4.10 Non-goals for Part 4

- Do not rewrite the runtime in a different language (see Part 0.4).
- Do not add JIT compilation. Far too large a scope for this brief and not justified until
  the benchmark data shows tree-walking/bytecode interpretation is genuinely insufficient
  for real target workloads.
- Do not change the observable execution order or timing semantics of side effects (e.g.
  `say` output ordering) as a side effect of any optimization — output ordering is part of
  the "predictable execution" contract and regressions here are correctness bugs, not
  acceptable performance tradeoffs.

## 4.11 Definition of Done for Part 4

- [ ] `tests/perf/baseline.json` exists, was captured before changes, and is checked into
      version control.
- [ ] `tpp bench` subcommand exists, runs the full benchmark suite, and outputs both
      human-readable and JSON results.
- [ ] Every optimization landed cites a specific before/after benchmark number in its PR
      description.
- [ ] Closure-in-loop and shadowing tests (from Part 1) still pass unmodified after any
      environment-model changes.
- [ ] The Python-interop allow-list is centralized in one auditable location with a
      documented addition process, and no filesystem/network/process-spawning module is
      allow-listed without going through the sandboxed stdlib API of Part 5.6 instead.
- [ ] A GC/reference-cycle audit has been performed and documented, with any found leaks
      fixed or explicitly tracked as known issues.
- [ ] Concurrency ADR exists; no concurrency syntax has leaked into the language surface
      outside the explicit feature-flagged prototype.

---

# PART 5 — STANDARD LIBRARY EXPANSION

## 5.1 Context

Current stdlib: `math, text, system, time`. This is a starter set. A "production-grade"
claim needs breadth and, critically, *consistency* — every module needs to feel like it was
designed by the same team with the same conventions, not bolted on ad hoc by whichever
agent touched it last. This part is as much about establishing and enforcing conventions
as it is about raw feature count.

## 5.2 Cross-cutting stdlib conventions (establish these FIRST, before adding modules)

- **Naming convention**: decide once, document once, apply everywhere. Given the
  "possessive property access" pattern (`name's length`) and "natural function call"
  pattern (`the uppercase version of name`) both appear plausible from Parts 1–2, pick a
  clear rule: *derived properties with no meaningful side effects and O(1)-ish cost* use
  possessive syntax (`name's length`, `list's size`); *operations that transform or that
  read as verbs* use natural function-call syntax (`the sorted version of list`,
  `round x to 2 decimal places`). Write this rule down in `docs/language-guide.md` and
  audit every stdlib function against it — inconsistency here is one of the fastest ways to
  make a "natural language" pitch feel arbitrary and unlearnable.
- **Error behavior convention**: stdlib functions must raise proper T++ exceptions (Part
  1.8/12.4 hierarchy) on invalid input, never let a raw Python exception leak through
  unhandled. This needs a shared decorator/wrapper utility in `tpp/stdlib/` so every module
  gets this for free rather than reimplementing error translation per-module.
- **Purity/mutation convention**: for every collection-touching function, document and
  test explicitly whether it mutates in place or returns a new value (given 1.6 establishes
  lists/records as mutable) — e.g. does `sort` mutate `list` or return a sorted copy?
  Recommend: default to non-mutating (returns new value) for anything ambiguous, since
  that's the more surprising-free default aligned with "predictable execution," with
  explicitly-named mutating variants (`sort list in place`) as a separate, clearly-labeled
  operation.
- **Type-signature documentation**: every stdlib function gets a documented signature using
  Part 3's type vocabulary in its doc entry (Part 14), even though the function itself
  doesn't require type annotations to call — this is documentation, not enforcement.

## 5.3 `math` module expansion

Beyond whatever exists at 3.1.3, ensure coverage of: trigonometric functions (`sine`,
`cosine`, `tangent`, natural-named), logarithms (`log of x` / `log of x, base b`), rounding
family (`round`, `round up`, `round down`, `round to N decimal places` — reconciling with
2.2's floor-division decision so the *vocabulary* for "round down" is shared/consistent
between the two), statistics basics (`the average of`, `the median of`, `the standard
deviation of` over a list of numbers), random number generation with an explicit,
documented note that the default RNG is **not cryptographically secure** and a pointer to
where a secure RNG lives if needed (see Part 15 — never let users reach for `math`'s random
for anything security-sensitive without a clear warning in the docs and, ideally, in the
function's own docstring/help text).

## 5.4 `text` module expansion

Beyond whatever exists: case conversion family, trimming/padding, splitting/joining with
natural phrasing (`text split by ","`, `the pieces of text joined by ", "`), searching
(`text contains "..."`, `the position of "..." in text`), replacement, the interpolation
and regex-wrapper functionality from Part 2.3 should live here as the implementation home
even though the syntax sugar is defined in Part 2, formatting numbers as text
(`x formatted with 2 decimal places`, `x formatted as currency`), and Unicode-awareness —
explicitly test with non-ASCII input (accented characters, emoji, right-to-left scripts)
since silent Unicode bugs are a common, embarrassing class of stdlib defect.

## 5.5 `time` module expansion

Date/time construction, arithmetic (`3 days from now`, `the difference between date_a and
date_b`), formatting/parsing with natural-language format specifiers where feasible,
timezone awareness (explicitly decide and document: is the default naive or
timezone-aware? — recommend timezone-aware by default to avoid the extremely common and
painful bug class naive datetime handling causes, even though it's slightly more complex
to reason about, because "predictable execution" strongly favors avoiding the "silently
wrong in a way that only shows up when your server's TZ differs from your dev machine's TZ"
failure mode), and sleep/delay functions gated appropriately (a `wait for N seconds`
primitive needs to interact sensibly with the infinite-loop/max-execution-time guards from
Part 1.4/8/15 — a script shouldn't be able to `wait for 999999999 seconds` and hang a
shared API worker).

## 5.6 New module: `system`/`files` — sandboxed I/O

Given Part 4.7 explicitly forbids raw Python file/os passthrough via interop, T++ needs its
own mediated I/O story if it's going to be a genuinely usable general-purpose language and
not just an expression evaluator:

- Natural-syntax file operations (`read the contents of "path"`, `write "content" to
  "path"`, `does "path" exist`) that go through a dedicated, sandboxed implementation —
  not raw Python `open()` calls — enforcing a workspace-sandboxed root directory (per the
  existing README security note "system stdlib file operations are workspace-sandboxed" —
  this brief formalizes and expands what's implied to already exist).
- Explicit, loud, documented behavior on path-traversal attempts (`../../etc/passwd`-style
  inputs) — must be rejected with a clear T++ error, not silently resolved or silently
  allowed. This needs dedicated security tests (Part 15) with adversarial path inputs, not
  just happy-path tests.
- Environment variable access, if provided, must go through an explicit allow-list, never
  blanket `os.environ` exposure — scripts should not be able to read arbitrary host
  environment variables (which may contain secrets) unless the host explicitly configures
  which variable names are exposed.
- CLI argument access for scripts run via `tpp run script.tpp -- arg1 arg2` needs a natural
  stdlib surface (`the command line arguments`) — coordinate with Part 7.

## 5.7 New module: `collections` — richer data structure operations

Higher-order operations needed to make the comprehensions from Part 2.4 and first-class
functions from Part 1.5 actually useful in practice: `the result of applying <function> to
each item in <list>` (map), `the items in <list> where <function> is true` (filter, though
comprehension syntax likely covers most of this — this module is for the *functional*
spelling when a named function is being reused rather than an inline comprehension),
`combine <list> into one value starting from <initial> using <function>` (reduce/fold),
`sort <list>` / `sort <list> by <function>`, grouping (`group the items in <list> by
<function>`), set operations (union/intersection/difference) for the set type from 1.6,
flattening nested lists, zipping multiple lists together.

## 5.8 New module: `json`/`data` — structured data interchange

Given a real API (Part 8) exists and real programs need to talk to the outside world:
parsing JSON text into T++ records/lists and serializing T++ values back to JSON text,
with clear, tested behavior for edge cases (what happens serializing a function value? a
`nothing`? a value with a reference cycle in a mutable record — must be detected and raise
a clear error, not infinite-loop or crash).

## 5.9 New module: `validate` — input validation helpers

Given T++ scripts will often process external/untrusted input (files, API payloads):
common validation predicates (`is a valid email`, `is a valid number`, `is within the
range`) as natural, composable checks — this directly supports the "human-first" pitch for
the very common real-world task of validating user input, and pairs naturally with Part
1.8's error handling.

## 5.10 Non-goals for Part 5

- Do not implement networking primitives (HTTP client, sockets) in the stdlib in this
  brief — that's a significant additional security surface (SSRF risk in a
  script-execution context, especially once the public API/Web IDE in Part 8 exists) that
  deserves its own dedicated security-first design pass, not a rushed addition alongside
  everything else here. Explicitly flag this as a deferred, security-gated future item in
  Part 18's roadmap.
- Do not implement a full ORM/database-connectivity stdlib module — out of scope for a
  language-platform brief; if users need this, it belongs in the plugin/package ecosystem
  (Part 6/10), not core stdlib.
- Do not add stdlib functions that shell out to system commands (no `run the command
  "..."`-style primitive) — this is a direct code-execution security hole and is
  explicitly rejected, not just deferred.

## 5.11 Definition of Done for Part 5

- [ ] The naming/error/mutation conventions from 5.2 are written up as a stdlib style
      guide in `docs/` and every new function is checked against it.
- [ ] Every new stdlib function has: a docstring, a doc-page entry with a worked example, a
      positive test, and at least one negative/error-path test.
- [ ] `system`/`files` module's sandboxing is covered by adversarial path-traversal tests,
      cross-referenced from Part 15.
- [ ] Timezone-awareness decision for `time` is documented and consistently applied; no
      naive-vs-aware mismatch bugs exist between different `time` functions.
- [ ] Unicode edge cases are explicitly tested in `text` module functions.
- [ ] The random-number-is-not-cryptographically-secure warning is present in both the
      docs and the function's own help text (verify via `tpp doctor` or equivalent
      introspection, if such a mechanism surfaces stdlib docs at runtime).

---

# PART 6 — PLUGIN SYSTEM FORMALIZATION

## 6.1 Context

The README mentions "extensible plugin system with keyword rewrites and transform hooks"
and shows `tpp plugin install examples/sample_plugin.json` / `tpp plugin list` /
`tpp run ... --plugin examples/sample_plugin.json`. This exists but is under-specified from
the README alone. This part formalizes it into a real, versioned, secure, documented
extension mechanism — this is what will let a community grow around T++ without every new
idea needing to land in core.

## 6.2 Plugin manifest schema (versioned, from day one)

- Define a formal, versioned JSON Schema for the plugin manifest format (building on
  whatever `examples/sample_plugin.json` currently contains) including: plugin name,
  version (semver), T++ platform compatibility range (so a plugin can declare "works with
  tpp-language >=3.2,<4.0" and the CLI can warn/refuse on incompatible installs), author,
  description, license, declared hook points used (see 6.4), and a permissions declaration
  (see 6.5).
- Include a `manifest_version` field from the start (even if it's `1` today) so future
  manifest format changes don't require guessing at an implicit version — this is a small
  addition now that prevents real pain later, matching the deprecation-path discipline
  required elsewhere in this brief.
- Validate manifests against the schema at `tpp plugin install` time and reject
  malformed/incompatible manifests with a clear error, not a silent partial install.

## 6.3 Plugin distribution and installation

- `tpp plugin install <path-or-url-or-registry-name>` — expand beyond local file paths (the
  README example) to support: a local file path (existing), a URL to a manifest+bundle, and
  (if a plugin registry is established — see 6.7) a bare name lookup.
- `tpp plugin list` — expand to show version, compatibility status against the currently
  installed T++ version, and enabled/disabled state.
- Add `tpp plugin uninstall <name>`, `tpp plugin update <name>` (or `--all`), `tpp plugin
  info <name>` (show full manifest + declared permissions), `tpp plugin enable/disable
  <name>` (toggle without uninstalling).
- Installed plugin state lives in a well-defined location (coordinate with `.tppconfig`
  design) and is per-project by default, with an explicit opt-in for global/user-level
  plugin installs — per-project-by-default reduces the risk of a plugin silently affecting
  unrelated projects on the same machine.

## 6.4 Hook point taxonomy (formalize what "keyword rewrites and transform hooks" means)

Define a closed, documented set of extension points a plugin can register against, rather
than arbitrary code-injection anywhere in the pipeline:

- **Lexer/keyword hooks**: register new keywords or keyword synonyms (integrating with the
  centralized synonym table from Part 1.9 — plugin-registered synonyms must go through the
  same table, tagged with their owning plugin, so `tpp doctor`/conflict detection can spot
  two plugins fighting over the same keyword).
- **Parser/grammar-extension hooks**: register new statement or expression forms — this is
  the highest-risk, highest-power hook point and needs the strongest sandboxing (6.5) since
  it can affect how *any* script using the plugin's keywords is parsed.
- **AST transform hooks**: a documented pass that runs post-parse, pre-semantic-analysis,
  allowing a plugin to rewrite the AST (this is likely what "transform hooks" already
  refers to in the existing README) — must run in a defined, deterministic order when
  multiple plugins register transforms, with conflicts (two plugins transforming the same
  node) detected and reported rather than silently producing order-dependent behavior.
- **Stdlib-extension hooks**: register new stdlib-style functions/modules that scripts can
  call, without needing parser changes — this is the lowest-risk, most-encouraged hook
  point for most plugin authors, and the docs (6.8) should steer plugin authors here first
  unless they genuinely need syntax-level extension.
- **CLI-extension hooks**: register new `tpp <subcommand>` entries (coordinate with Part 7).
- Explicitly reject "arbitrary pipeline injection" as a hook category — every hook must be
  one of the above, named, ordered, and conflict-checked. This closed taxonomy is a
  deliberate security and stability choice, not a temporary simplification.

## 6.5 Plugin security model

This is not optional or "nice to have" — a plugin system is, definitionally, a way to run
third-party code, and it must be treated with the same seriousness as Part 15's overall
security work, cross-referenced heavily:

- Plugins declare required permissions in their manifest (e.g. "registers new stdlib
  functions," "extends grammar," "requires filesystem access via the sandboxed `system`
  module from Part 5.6"). `tpp plugin install` must show these permissions to the user and
  require confirmation before installing a plugin that requests anything beyond
  pure-syntax/stdlib extension — mirroring how mobile app stores handle permission
  disclosure, adapted to a CLI confirmation prompt (`--yes`/`-y` flag to skip for CI/
  scripted installs, but interactive-by-default).
- Plugin code itself, if it contains arbitrary Python (per the existing "plugin Python
  hooks are namespace-restricted" security note), must run under the same
  allow-listed-interop constraints as Part 4.7's general interop hardening — a plugin must
  not be able to reach further into the host system than a T++ script itself can, unless
  explicitly and loudly granted that permission.
- No plugin should be able to silently override or disable another plugin's or core's
  security-relevant behavior (e.g. a plugin claiming to add a stdlib function should not be
  able to also patch over the `system` module's sandboxing).
- Document a clear, public plugin security policy (who to report a malicious/vulnerable
  plugin to, what happens when one is found) as part of Part 15/18's overall
  security/governance documentation.

## 6.6 Plugin API stability and versioning

- The plugin API surface (whatever internal interfaces a plugin's code actually touches to
  register hooks) is itself a public API and must follow the same backward-compatibility
  discipline as the language surface (Part 0.5) — a plugin written against the "3.2" plugin
  API should not silently break on "3.3" without going through Part 17's deprecation path.
- Version the plugin API explicitly (distinct from the T++ language version, since these
  can evolve at different rates) and expose it via `tpp --version` or a dedicated `tpp
  plugin api-version` command so plugin authors and their manifests' compatibility ranges
  (6.2) have something concrete to declare against.

## 6.7 Plugin registry (design, minimal-viable implementation)

- A lightweight, documented format for a plugin registry (could be as simple as a curated
  JSON index hosted in a well-known location, similar in spirit to how many young language
  ecosystems bootstrap package discovery before a full package-manager registry exists —
  see Part 10 for how this relates to the module/package system) so `tpp plugin install
  some-plugin-name` (bare name, no path/URL) can resolve to a real download. Full
  self-service publish-your-own-plugin infrastructure (accounts, web UI, abuse handling) is
  explicitly out of scope for this brief — ship the resolution mechanism and a
  process/documentation for how a plugin gets added to the initial curated index, not a
  full public registry service.

## 6.8 Plugin author documentation

- `docs/plugin-guide.md` (referenced in the existing README but needs to actually be
  comprehensive under this brief) must include: the manifest schema reference, a
  walkthrough of each hook-point category from 6.4 with a complete working example plugin
  per category, the permissions/security model from 6.5 explained from a "what will my
  users see when they install this" perspective, and a compatibility/versioning guide.
- Ship at least three real, working example plugins in `examples/plugins/` (not just the
  one `sample_plugin.json` implied by the current README) — one stdlib-extension example,
  one keyword-synonym example, and one AST-transform example — each fully documented and
  fully tested, serving as both documentation and regression-test fixtures simultaneously.

## 6.9 Non-goals for Part 6

- Do not build a full plugin marketplace web UI in this brief (see 6.7) — that's tracked
  as a roadmap item in Part 18, not delivered here.
- Do not allow plugins to modify the core language's backward-compatibility guarantees —
  a plugin cannot be used as a backdoor to make a breaking change that core itself isn't
  allowed to make per Part 0.3.

## 6.10 Definition of Done for Part 6

- [ ] Plugin manifest JSON Schema is versioned, published, and validated at install time.
- [ ] All five hook-point categories from 6.4 are implemented, documented, and each has a
      working example plugin.
- [ ] Permission declaration and install-time confirmation flow is implemented and tested,
      including the `-y`/`--yes` non-interactive path.
- [ ] Plugin API version is exposed via CLI and referenced in manifest compatibility
      checks.
- [ ] `docs/plugin-guide.md` is comprehensive per 6.8's requirements.
- [ ] Two plugins registering conflicting hooks (same keyword, overlapping AST transform
      target) produce a clear, actionable error rather than silent last-write-wins
      behavior or a crash.

---

# PART 7 — CLI EXPANSION

## 7.1 Context

Existing commands: `run, repl, test, plugin install/list, api --serve, doctor`. This is a
reasonable minimal set for a young language. A "production-grade" CLI needs the commands
professional tooling users expect from ecosystems they already know (npm, cargo, go,
poetry) — not because T++ should copy those tools' design uncritically, but because
familiar command shapes reduce the learning curve for adopting a *new* language, which
matters enormously for adoption.

## 7.2 New command: `tpp init`

- Scaffolds a new T++ project: creates a sensible directory structure, a starter
  `.tppconfig`, a starter `main.tpp` or equivalent entry point, a `.gitignore` appropriate
  to the ecosystem, and optionally a starter test file demonstrating the `tpp test`
  workflow.
- Interactive by default (prompts for project name, whether to include example plugins,
  whether to set up strict type mode per Part 3.6) with a `--yes`/non-interactive mode for
  scripting and CI usage, and named templates (`tpp init --template minimal`, `--template
  web-api` using Part 8's API server, `--template cli-tool`) covering common starting
  points.

## 7.3 New command: `tpp format`

- Implements the formatter referenced in Part 1.9 (synonym-spelling-preference-aware
  formatting). Must be idempotent (running it twice produces no further changes) and must
  support both a `--check` mode (exit non-zero if formatting would change anything, for CI
  use — coordinate with Part 19) and an in-place-write mode (default).
- Must never change program *behavior* — this needs a dedicated test category: for every
  fixture script, assert that `tpp run` on the pre-format and post-format versions produces
  identical output.

## 7.4 New command: `tpp lint`

- A real static analysis linter, distinct from `tpp format` (formatting is about
  whitespace/style; linting is about catching likely bugs and code smells): unused
  variables, unreachable code (building on Part 4.5's dead-code-detection analysis, reused
  here for a diagnostic rather than an optimization purpose), shadowed variable warnings,
  and — once Part 3's type system exists — type-mismatch warnings surfaced through this
  command specifically (not just IDE-only, per Part 9).
- Configurable via `.tppconfig` (which lint rules are enabled/disabled/error-vs-warning) and
  supports inline suppression comments for individual lines (`# tpp-lint-ignore:
  unused-variable` or a natural-language equivalent consistent with the language's
  aesthetic — worth a small design discussion in an ADR on whether even lint-suppression
  comments should read naturally, e.g. `# ignore this line for the unused variable check`,
  to stay consistent with the project's overall philosophy).

## 7.5 New command: `tpp build`/`tpp bundle`

- For deploying a T++ project as a single distributable artifact: resolve all local module
  imports (Part 10) into a single bundled `.tpp` file or a packaged directory with a
  manifest, suitable for distribution without requiring the target machine to have the full
  source module graph laid out identically. Consider (and document the decision) whether
  bundled output should remain human-readable `.tpp` source (favoring the "predictable,
  inspectable" thesis, easier to security-audit before running) or a more opaque serialized
  form (potentially faster to load, but harder to inspect) — recommend defaulting to
  readable bundled source, given the project's transparency-first ethos, with a `--minify`
  opt-in for size-sensitive deployment if genuinely needed.

## 7.6 New command: `tpp upgrade`

- Self-upgrade helper: checks PyPI for a newer `tpp-language` version, shows changelog
  highlights (coordinate with Part 17's changelog automation) relevant to the jump from the
  currently-installed version, and performs the upgrade via pip on confirmation. Must
  clearly warn about any pending deprecations (Part 17.4) that will become breaking in the
  target version before proceeding.

## 7.7 New command: `tpp docs`

- Local documentation browser/server: `tpp docs` opens the language guide and stdlib
  reference (built from Part 14's docs) in a local browser view, and `tpp docs <search
  term>` does an offline search across the docs and stdlib reference — genuinely useful
  for users working without reliable internet access or who want the exact docs matching
  their exact installed version rather than whatever's live on a website (which may be
  ahead of or behind their installed version).

## 7.8 Existing command expansion

- `tpp doctor`: expand beyond whatever currently exists (README doesn't detail its checks)
  to comprehensively check: T++ installation health, `.tppconfig` validity, installed
  plugin compatibility (per Part 6.6's versioning), Python interop environment sanity, and
  — importantly — surface this brief's new features' health where relevant (e.g. "strict
  type mode is enabled but N type errors exist," "M plugins are installed but incompatible
  with the current version"). `tpp doctor` should be the single command a confused user
  runs first, and it should almost always point them at the specific next fix rather than
  just reporting "problems found."
- `tpp repl`: add multi-line input support (for `define`/`if`/`repeat`/`try` blocks —
  verify this actually works well given the `end`-delimited block syntax, since naive REPLs
  often struggle with knowing when a multi-line block is "done" — needs an explicit
  incomplete-input-detection design, likely based on tracking unclosed block-openers),
  tab-completion for keywords/stdlib functions/locally-defined names, and a `.tpprepl`
  history file. Consider syntax highlighting in the REPL if a reasonable terminal-rendering
  library is already a natural fit for the existing dependency footprint.
- `tpp test`: expand to support test discovery (running all `*.test.tpp` or similarly-
  named files in a project, not just an explicitly-named file per the current README
  example), coverage reporting (coordinate with Part 13), and structured/machine-readable
  output (`--format json`) for CI integration.
- `tpp run`: add `--watch` mode (re-run on file change, useful for rapid iteration),
  `--profile` (routes through the runtime profiler from Part 4 and prints a summary),
  and pass-through script arguments via `--` per Part 5.6's CLI-args stdlib access.

## 7.9 CLI consistency requirements

- Every command and subcommand must have complete, accurate `--help` text — this is not
  optional documentation, it's the primary discoverability mechanism for a CLI tool.
- Consistent flag naming across commands (`--format json` should mean the same thing and
  use the same flag name everywhere it appears, not `--output-format` in one command and
  `--fmt` in another).
- Consistent exit codes: `0` success, non-zero on failure, with a documented convention for
  what different non-zero codes mean if the CLI distinguishes them (e.g. syntax error vs.
  runtime error vs. type error vs. internal tool error) — useful for scripting/CI
  consumers.
- Shell completion scripts (bash, zsh, fish at minimum) generated and distributable,
  likely via a `tpp completion <shell>` command that prints the appropriate completion
  script for the user to source.

## 7.10 Non-goals for Part 7

- Do not build a GUI application as part of the CLI work — CLI means terminal-based; the
  Web IDE (Part 8) is the GUI story and is a separate surface.
- Do not add telemetry/usage-analytics collection to any CLI command without an extremely
  explicit, separate, opt-in-only design discussion and its own ADR — silent or
  opt-out telemetry in a developer tool is a trust-destroying move and is not something to
  bundle quietly into a broader CLI-expansion effort.

## 7.11 Definition of Done for Part 7

- [ ] Every new command listed above is implemented, documented in `--help`, documented in
      `docs/`, and covered by CLI-integration tests (extending the existing
      `tests/test_cli_integration.py` referenced in the README's developer workflow).
- [ ] `tpp format --check` and idempotency are verified by test.
- [ ] `tpp lint` rules are individually toggleable and documented.
- [ ] `tpp doctor` surfaces at least one check for each major new subsystem added under
      this brief (types, plugins, modules).
- [ ] Shell completion scripts exist for bash, zsh, and fish and are verified to actually
      load without error in each shell (not just generated and never tested).
- [ ] No telemetry of any kind has been added without a separate, explicit, opt-in-only
      design discussion and ADR.

---

# PART 8 — API AND WEB IDE

## 8.1 Context

The existing JSON execution API (`{"source": "...", "mode": "run"}` → `tpp api --serve`)
and the web IDE backend represent T++'s path to browser-based, zero-install trial and
collaborative use — genuinely valuable for adoption. This is also, unavoidably, the highest
security-risk surface in the whole platform: it means running arbitrary user-submitted code
on a server. This part must be built hand-in-hand with Part 15, not after it.

## 8.2 API versioning

- Introduce explicit API versioning from this point forward (`/v1/execute` style paths, or
  a version field in the request/response envelope) so future changes to the JSON contract
  never need to silently break existing integrations — the *existing* unversioned contract
  (`{"source": ..., "mode": "run"}`) must continue to work exactly as before (per Part
  0.3's hard constraint), either by treating it as the implicit `v1` contract going forward,
  or by adding a compatibility shim that translates unversioned requests to the new
  versioned internal handling. Document this translation explicitly.

## 8.3 New API capabilities

- **Execution modes beyond `run`**: `format`, `lint`, `test` (running embedded test blocks
  via the API, mirroring the CLI's `tpp test`), `parse` (return the AST as JSON, useful for
  tooling built on top of the API — e.g. a future browser-based visualizer), and `check`
  (analysis-only, no execution — runs the type checker and linter without running the
  script, useful for editor-integration use cases that want fast feedback without full
  execution risk).
- **Streaming output**: for long-running or `say`-heavy scripts, support a streaming
  response mode (Server-Sent Events or chunked response) so output appears incrementally
  rather than only after the entire script finishes — significantly better UX for the web
  IDE specifically, and directly enables real-time REPL-like experiences in the browser.
- **Resource limits as explicit, documented, per-request-configurable parameters** (within
  server-enforced hard ceilings — a request can ask for less than the ceiling, never more):
  max execution time, max memory (as far as Python allows meaningfully enforcing this — 
  document the real, honest limits of what's enforceable in-process versus what requires
  process/container-level isolation, and be upfront in the docs about which guarantees are
  "soft" vs. "hard"), max output size.
- **Session/multi-execution support** for the web IDE's REPL-like use case: an execution
  session that preserves variable state across multiple API calls (so a web-based REPL can
  work), with explicit session expiry/cleanup and the environment-isolation-between-
  sessions guarantee this implies (cross-reference Part 4.6's memory-model discussion of
  isolated-vs-pooled environments — for the API specifically, per-session isolation is a
  security requirement, not just a nice architectural property, since sessions may belong
  to different untrusted users sharing the same server process).

## 8.4 Web IDE feature expansion

- Real-time diagnostics as the user types, powered by the `check` API mode from 8.3 and
  the LSP-equivalent analysis from Part 9 — the browser IDE should feel like it has the
  same intelligence as a local editor with the LSP installed, not a dumb textarea that only
  reports errors after clicking "run."
- Shareable script links (a script gets a unique URL that reproduces it — needs careful
  design around storage, abuse-prevention/rate-limiting on link creation, and a documented
  data-retention policy since this is now a small user-generated-content surface, however
  minor).
- An embeddable mode (an `<iframe>`-friendly stripped-down view, useful for documentation
  pages wanting live, runnable T++ examples — directly supports Part 14's documentation
  work, since "runnable example" beats "static code block" for a language whose whole pitch
  is approachability).
- File/multi-file project support in the web IDE (not just single-script execution),
  building on Part 10's module system once it exists, so the web IDE can demo real,
  multi-file T++ projects, not just isolated snippets.

## 8.5 Authentication and rate limiting

- The current API, per the README, appears to be unauthenticated/open (`tpp api --serve
  --host 127.0.0.1 --port 8787`, a local dev server). As this grows toward a genuinely
  public-facing service (implied by "web IDE"), add: an optional API-key auth mode (opt-in
  via server config, so local/trusted-network deployments can stay simple and
  authless — do not force auth complexity onto every deployment context), and rate limiting
  (per-IP and/or per-API-key, configurable) to prevent both abuse and accidental
  resource-exhaustion self-inflicted-DoS from a buggy client retry loop.
- Document clearly, prominently, in `docs/web-ide.md` and `docs/devops.md`, that running
  `tpp api --serve` with a public bind address (`0.0.0.0` or similar) without additional
  hardening (see Part 15) is dangerous, and provide an explicit, safe, recommended
  production deployment pattern (reverse proxy, container isolation, resource limits at
  the OS/container level, not just the application level) — do not let users discover this
  the hard way.

## 8.6 Observability

- Structured logging for every API request (method, execution mode, duration, resource
  usage, success/failure — never logging full script *content* by default, since scripts
  may contain sensitive data the submitter didn't intend to have logged/retained; make
  content-logging an explicit, separately-configured opt-in for debugging deployments only).
- Basic metrics endpoint (request counts, error rates, execution-time percentiles) in a
  standard, scrapable format (Prometheus-style plaintext exposition is a reasonable,
  widely-compatible default) so operators running this in production have the observability
  a real service needs.

## 8.7 Non-goals for Part 8

- Do not build user accounts, billing, or a hosted-SaaS-product business layer as part of
  this brief — that's a product/business decision entirely outside a language-platform
  engineering brief. Build the API/IDE to be *capable* of being hosted as a service by
  whoever wants to, not to *be* a specific hosted service with accounts and payments.
- Do not weaken any resource-limit or sandboxing default "to make demos look snappier" —
  security defaults in a public-code-execution surface are not something to trade away for
  polish; if a demo needs more time/memory, that should be an explicit, visible
  configuration choice made by whoever's running that specific deployment, not a silently
  loosened platform default.

## 8.8 Definition of Done for Part 8

- [ ] API versioning scheme is implemented; the exact 3.1.3 unversioned request/response
      shape continues to work unmodified, verified by a regression test using literal
      request/response examples from the current README.
- [ ] Every new execution mode (`format`, `lint`, `test`, `parse`, `check`) is implemented,
      documented, and tested.
- [ ] Streaming output mode works and is demonstrated in the web IDE.
- [ ] Session-based execution correctly isolates state between distinct sessions —
      verified by an adversarial test attempting to read one session's variables from
      another.
- [ ] Rate limiting and optional auth are implemented, documented, and off-by-default in a
      way that doesn't complicate simple local/dev usage, but are clearly documented as
      required for any public deployment.
- [ ] `docs/web-ide.md` and `docs/devops.md` explicitly document the public-deployment
      danger and the recommended hardened deployment pattern.
- [ ] Structured logging never includes full script content unless explicitly, separately
      opted into.
- [ ] Every item in this part has been reviewed jointly against Part 15's threat model
      before being considered done — not just functionally tested, but security-reviewed.

---

# PART 9 — LANGUAGE SERVER AND EDITOR TOOLING

## 9.1 Context

None of the existing README-described surfaces mention a Language Server Protocol (LSP)
implementation or editor extensions. This is a significant gap for any language wanting
real adoption — modern developers expect syntax highlighting, inline diagnostics,
autocomplete, and go-to-definition as table stakes, not optional extras. This part builds
that story.

## 9.2 Language Server (LSP) implementation

- Implement a standard LSP server (`tpp-language-server` or exposed via `tpp lsp` as a
  CLI subcommand that speaks LSP over stdio, coordinating with Part 7's CLI conventions)
  reusing the existing parser/semantic-analyzer/type-checker pipeline directly — the LSP
  server must not be a separate reimplementation of parsing/analysis logic; it wraps the
  same `tpp/parser`, `tpp/core`, and (once it exists) type-checking code the CLI and
  runtime use, so LSP diagnostics and `tpp lint`/`tpp run` error output never drift out of
  sync with each other.
- Required LSP capabilities for a genuinely usable first version: diagnostics (syntax
  errors, semantic errors, and — once Part 3 lands — type warnings/errors, all using the
  improved error messages from Part 12), hover (showing type info per Part 3.4's inference,
  stdlib function signatures/docs per Part 5's documented signatures), go-to-definition
  (for user-defined functions and, once Part 10 lands, imported names), autocomplete
  (keywords, stdlib functions, locally-defined names, with the synonym-awareness from Part
  1.9 so autocomplete suggests whichever spelling the file/project has been using
  consistently), and document formatting (delegating to `tpp format` from Part 7.3).
- Incremental/fast re-analysis on keystroke is important for LSP usability — profile this
  explicitly (an LSP server that takes 500ms to respond to every keystroke is unusable) and
  consider incremental re-parsing strategies if the naive "re-parse the whole file on every
  change" approach proves too slow on realistically-sized files.

## 9.3 Editor extensions

- **VS Code extension**: syntax highlighting (via a TextMate grammar or semantic
  highlighting driven by the LSP server), LSP client wiring, snippet library for the
  constructs from Parts 1–2, and packaging/publishing readiness (a `package.json`,
  extension manifest, and a documented local-install/testing path — full VS Code
  Marketplace publishing is a reasonable stretch goal but the extension must at minimum be
  locally installable and fully functional from source).
- **Other editors**: at minimum, ship a standard TextMate-grammar-compatible syntax
  definition (reusable across many editors beyond just VS Code) and clear documentation for
  wiring the LSP server into Neovim (via `nvim-lspconfig`-style configuration) and any other
  editor with generic LSP client support — full first-party extensions for every editor is
  out of scope, but "any LSP-capable editor can be configured to work with T++ following
  documented steps" is the bar.

## 9.4 Formatter (implementation home; syntax rules defined in Part 1.9/7.3)

- The actual formatting-engine implementation lives here architecturally (parser output →
  formatted-source-text renderer), reusable by both `tpp format` (Part 7.3) and the LSP
  server's format-on-save capability (9.2) — one formatting engine, two entry points, never
  two separate implementations that could drift.
- Must handle comments correctly (a very common formatter failure mode is losing or
  misplacing comments during the parse-and-re-render round trip) — dedicated test coverage
  for comment preservation across every construct from Parts 1–2.

## 9.5 Linter (implementation home; command surface defined in Part 7.4)

- Similarly, the actual lint-rule-engine lives here, shared between `tpp lint` and the
  LSP server's diagnostic capability.

## 9.6 Syntax highlighting definition maintenance

- Whatever grammar-definition format is chosen for highlighting (TextMate grammar,
  Tree-sitter grammar, or both) must be treated as a build artifact derived from — or at
  minimum kept in continuous lockstep with, via a CI check — the actual parser grammar
  (Part 1.11's formal EBNF spec), not hand-maintained independently and left to drift as
  new syntax is added in later brief work. A CI check (Part 19) verifying every keyword the
  parser accepts has a corresponding highlighting rule is a cheap, high-value addition here.

## 9.7 Non-goals for Part 9

- Do not attempt to support every possible editor with a first-party extension — VS Code
  first-party plus documented generic-LSP instructions for everything else is the
  appropriate scope for this brief.
- Do not build a debugger/DAP (Debug Adapter Protocol) implementation in this part — that's
  a substantial, separate effort (needs runtime-level breakpoint/step support that doesn't
  currently exist per the architecture description) and should be explicitly flagged as a
  roadmap item in Part 18 rather than attempted here.

## 9.8 Definition of Done for Part 9

- [ ] LSP server implements diagnostics, hover, go-to-definition, autocomplete, and
      format-on-save, reusing (not duplicating) the core parser/analyzer/formatter/linter.
- [ ] LSP response latency is benchmarked on a realistically-sized file and documented.
- [ ] VS Code extension is locally installable from source and demonstrably functional for
      every LSP capability above.
- [ ] Neovim (or equivalent generic-LSP-client) setup is documented and verified to work
      by someone actually following the documented steps, not just written from theory.
- [ ] A CI check exists confirming syntax-highlighting keyword coverage matches the parser's
      actual accepted keyword set.
- [ ] Comment-preservation through format round-trips is covered by dedicated tests for
      every Part 1–2 construct.

---

# PART 10 — MODULE AND PACKAGE SYSTEM

## 10.1 Context

The current README shows no visible `import`/module story — every example is a single
self-contained script. This is a first-class gap: no real, multi-file program can be
written cleanly without it, and it blocks Part 6.3's plugin distribution, Part 7.5's
bundling, and Part 8.4's multi-file web IDE support, all of which reference this part as a
dependency. Per Part 0.6, core module grammar and resolution should land early (Stage A).

## 10.2 Import/export syntax

Natural-reading spelling consistent with the rest of the language:

```tpp
use the "shapes" module
use Circle from the "shapes" module

from "shapes" use Circle and Rectangle

export define Circle as a shape with
    radius as a number
end
```

- `use ... from the "..." module` / `use the "..." module` as natural import forms, with
  `import ... from "..."` accepted as a symbol-adjacent synonym per the 1.9 policy for
  users coming from other languages.
- `export` prefix on any top-level `define` (function or type) to mark it as part of a
  module's public surface — unexported names are not visible to importers, giving modules a
  real, enforced public/private boundary rather than everything being implicitly global.
- Relative (`"./helpers"`) and module-graph-root-relative (`"shapes"`, resolved via the
  project's module-resolution configuration) path forms, both explicitly specified — do not
  leave path-resolution ambiguity for the implementation to improvise.
- Circular import detection: must be caught at analysis time with a clear, specific error
  identifying the cycle (`shapes → geometry → shapes`), not a runtime stack overflow or a
  silent partial-module bug.

## 10.3 Module resolution and project structure

- Define a canonical project layout convention (coordinate with `tpp init` from 7.2 and
  `.tppconfig`) — where do a project's own modules live relative to its root, how are
  third-party/plugin-distributed modules (once packages beyond plugins exist — see 10.5)
  resolved, and what does `.tppconfig` need to specify explicitly versus infer by
  convention.
- Module-level caching: a module imported by multiple other modules within one execution
  must be parsed/analyzed once and its resulting namespace reused, not re-parsed per
  import site — this is both a correctness concern (module-level state like a top-level
  `let` should exist exactly once, not once per importer) and a performance concern
  (cross-reference Part 4.2's benchmark suite — add a multi-module-import benchmark).

## 10.4 Interaction with existing subsystems

- **Type system (Part 3)**: exported function/type signatures must be visible to importers
  for type-checking/LSP-hover purposes without needing the importer to re-analyze the
  imported module's full implementation — design an efficient "signature-only" resolution
  path.
- **Plugins (Part 6)**: plugin-registered stdlib extensions should be import-able using the
  same `use ... from ...` syntax as user modules where sensible, giving one consistent
  mental model for "where did this name come from" rather than a special-cased,
  differently-spelled plugin-access mechanism.
- **CLI (Part 7)**: `tpp run entry.tpp` must correctly resolve the full module graph
  starting from the entry file; `tpp test` must support running tests that live alongside
  the modules they test, with correct resolution of what those test files import.

## 10.5 Package management (scoped narrowly for this brief)

- This brief does **not** mandate building a full package registry/publish-and-install
  ecosystem for arbitrary reusable T++ code (distinct from the plugin registry in Part
  6.7, which is narrower in scope — plugin manifests specifically). A full package-manager
  story (`tpp add some-package`, a public package index, dependency-version resolution) is
  explicitly large enough to warrant its own future brief.
- What this part *does* require: the local multi-file module system (10.2–10.4) must be
  designed in a way that does not preclude a future package manager from being layered on
  top cleanly — e.g. module-resolution configuration should already have a clean extension
  point for "also look in this externally-managed directory of installed packages," even if
  nothing populates that directory yet in this brief. Document this forward-compatibility
  intent explicitly in an ADR so a future package-manager effort inherits a sound
  foundation rather than needing to retrofit one.

## 10.6 Non-goals for Part 10

- Do not build a public package registry or `tpp add`-style installer in this brief (see
  10.5) — flag as a roadmap item in Part 18.
- Do not support dynamic/runtime-computed import paths (`use the module named
  (some_variable)`) in this first version — static, source-visible import paths only, since
  dynamic imports significantly complicate both static analysis (Part 3/9) and security
  auditability (Part 15), and the use cases for dynamic imports in typical T++ programs are
  likely thin enough not to justify that complexity yet.

## 10.7 Definition of Done for Part 10

- [ ] Import/export grammar is formally specified and added to `docs/language-guide.md`'s
      grammar section alongside Part 1's.
- [ ] Circular import detection produces a clear, specific, tested error message.
- [ ] Module-level caching/single-evaluation is verified by a test asserting a module's
      top-level side effect (e.g. a `say` at module scope, if permitted, or a counter
      increment) happens exactly once regardless of import-site count.
- [ ] `tpp run`, `tpp test`, `tpp bundle` (Part 7.5), and the type-checker/LSP (Part 3, 9)
      all correctly handle multi-file projects, verified by a realistic multi-module
      example project committed under `examples/multi-module-project/`.
- [ ] The forward-compatibility ADR for future package-manager layering is written.

---

# PART 11 — INTEROP AND FOREIGN FUNCTION INTERFACE

## 11.1 Context

Part 4.7 already covers hardening and expanding the existing "allow-listed Python module
bridging." This part is broader: formalizing interop as a real, documented, first-class
capability of the platform — not just "some Python modules are reachable" but a coherent
story for how T++ talks to the outside software world, since a language that can't
interoperate with anything has a much harder adoption path.

## 11.2 Python interop: calling Python from T++ (formalize existing capability)

- Building on Part 4.7's allow-list hardening, define the actual *calling* syntax/story
  clearly: natural-reading syntax for invoking an allow-listed Python function
  (`use the "json" python module` then `json's dumps of my_record`, reusing the possessive
  convention from 1.6/5.2 for consistency) and for passing T++ values across the boundary
  (documented, precise conversion rules: how does a T++ record become a Python dict and
  back, how does a T++ list become a Python list and back, what happens to a T++ function
  value passed into a Python callback parameter — this last one is genuinely tricky and
  needs explicit design, likely requiring the Python-interop layer to wrap T++ closures in
  a Python-callable shim that re-enters the T++ evaluator).
- Error translation must be bidirectional and clean: a Python exception raised inside an
  interop call must surface as a well-formed T++ exception (Part 1.8/12.4) with the
  underlying Python error type/message preserved as accessible detail, not swallowed or
  turned into an opaque "something went wrong."

## 11.3 Calling T++ from Python (embedding story)

- A documented, stable public Python API (`import tpp; tpp.run_source(source_code)` or
  similar) for embedding T++ execution inside a larger Python application — this is
  distinct from the CLI and from the HTTP API (Part 8); it's a library-level embedding
  story for Python developers who want T++ as a scripting/config layer inside their own
  Python programs (a very common and valuable use case for an approachable scripting
  language — many successful embedded languages, like Lua-in-games, succeed primarily
  through this exact use case).
- This embedding API must expose the same resource-limiting/sandboxing controls as the
  HTTP API (Part 8.3) as first-class Python-API parameters, not require embedding users to
  reimplement their own sandboxing around a raw, unguarded execution call.
- Document this API thoroughly with a dedicated `docs/embedding-guide.md`, including a
  complete worked example (e.g. "using T++ as a safe, sandboxed configuration/rules
  language inside a Python application").

## 11.4 JSON/data interchange as a baseline interop layer

- Ensure the `json`/`data` stdlib module from Part 5.8 is positioned, in documentation, as
  the *lowest-friction, recommended-first* interop path for talking to non-Python systems
  (any language/service that can produce or consume JSON) — before reaching for
  language-specific FFI, which should be understood as the higher-power, higher-complexity
  option for when JSON-based interop genuinely isn't sufficient.

## 11.5 Non-goals for Part 11

- Do not build FFI bindings for languages other than Python in this brief (no native C
  extension FFI, no JVM interop, no Node.js interop) — Python interop, hardened and
  formalized, plus JSON-based interchange as the universal fallback, is the appropriately-
  scoped target for this brief. Flag broader FFI as a roadmap item in Part 18 if there's
  clear demand signal for it later.
- Do not allow the interop/embedding APIs to become a backdoor around the security
  sandboxing established in Parts 4.7, 5.6, and 15 — every resource limit and allow-list
  constraint that applies to a T++ script run via the CLI or HTTP API must apply identically
  when that same script is run via the embedding API, with no separate, weaker code path
  that embedding users could stumble into and unknowingly expose themselves through.

## 11.6 Definition of Done for Part 11

- [ ] Python-calling-T++ syntax is documented, implemented, and covered by tests including
      the closure-passed-as-Python-callback case explicitly.
- [ ] Bidirectional error translation is verified by tests asserting a Python-side
      exception surfaces as a proper, catchable T++ exception with underlying detail intact.
- [ ] The embedding Python API (`tpp.run_source` or equivalent) is documented in
      `docs/embedding-guide.md` with a complete, runnable worked example.
- [ ] The embedding API exposes the same resource-limit controls as the HTTP API, verified
      by a test asserting identical enforcement behavior across both entry points for the
      same resource-limit violation (e.g. an infinite loop is stopped identically whether
      triggered via the CLI, the HTTP API, or the embedding API).

---

# PART 12 — ERROR HANDLING, DIAGNOSTICS, AND MESSAGE QUALITY

## 12.1 Context and why this part matters more than its position in the numbering implies

Per Part 0.6, this part lands in Stage A — before most other work — because every other
part's quality is bottlenecked by it. A "human-first" language's single biggest
differentiator from every other scripting language is not its keywords; it's whether the
error a beginner sees when they get something almost-right actually helps them fix it. This
is the single highest-leverage investment in the entire brief for the stated goal of making
T++ genuinely better, not just featureful.

## 12.2 Diagnostic message design principles

Every diagnostic emitted anywhere in the pipeline (lexer, parser, semantic analyzer, type
checker, runtime) must satisfy:

- **State what's wrong in plain language first**, not a category label first. Bad:
  `SyntaxError: unexpected token 'be' at line 4`. Good: `I expected the word "as" here, but
  found "be" instead — did you mean "let x as a number" or "let x be 5"?` The second form
  identifies the likely two things the user might have been reaching for and asks, rather
  than just reporting the mechanical parse failure.
- **Show the exact source location** with a caret/underline pointing at the precise
  problematic span, using the surrounding source line(s) for context, not just a line
  number in isolation.
- **Suggest a fix when a fix is confidently inferable** — this includes: likely-typo
  keyword detection (edit-distance matching against the known keyword/synonym table from
  Part 1.9 — `"repaet" 5 times` should suggest `"repeat" 5 times`), common near-miss
  patterns (missing `end`, missing `then`/`as`, mismatched `if`/`otherwise` nesting), and
  — once Part 3's type system exists — type-mismatch messages that name both the expected
  and actual type in plain terms (`I expected a number here, but "hello" is text`, not
  `TypeError: str is not compatible with number`).
- **Never show a raw Python traceback to a T++ script author under normal operation.** Any
  unhandled internal exception during T++ parsing/analysis/execution must be caught at the
  pipeline boundary and converted into either a proper diagnostic (if it maps to a known
  error category) or, worst case, a clearly-labeled "T++ internal error, please report this
  as a bug" message with a way to get a bug-report-ready detail dump (e.g. a `--debug` flag
  that *does* show the full traceback, for T++ platform developers debugging the compiler
  itself, kept separate from the default user-facing path).
- **Multiple errors in one pass where safely possible**, not fail-fast-on-first-error —
  a parser that stops at the very first syntax error and refuses to report anything else in
  the file is a frustrating, slow feedback loop, especially once Part 9's LSP wants to show
  every problem in a file at once, not one-at-a-time-per-save-cycle. Implement error
  recovery in the parser (synchronizing at statement/block boundaries after an error, so
  parsing can continue and find further real errors) as a genuine, tested capability, not
  an afterthought.

## 12.3 Warnings vs. errors

- Establish a clear, documented three-tier severity model used consistently across every
  diagnostic-producing subsystem: **Error** (execution cannot proceed — a genuine syntax
  or semantic problem, or a strict-mode type violation per Part 3.6), **Warning** (code will
  run but is likely wrong or worth reconsidering — unused variable, advisory type mismatch
  in non-strict mode, a lint rule from Part 7.4), **Hint/Info** (style suggestions,
  performance notes — e.g. "this comprehension could be simplified"). This tiering must be
  the same model used by the CLI's exit-code conventions (Part 7.9), the LSP's diagnostic
  severity (Part 9.2), and `tpp doctor`'s output.

## 12.4 Built-in exception hierarchy

- Design and document a real, extensible built-in exception type hierarchy for use with
  Part 1.8's `try`/`handle` — at minimum: a root `Error` type, with documented built-in
  subtypes covering the error categories the language itself can raise (a type error once
  Part 3 exists, a division-by-zero-style `MathError`, an out-of-range `IndexError`-
  equivalent for collection access, a `ModuleNotFoundError`-equivalent for Part 10's import
  system, a `PluginError` for Part 6 plugin-related failures). User-defined error types
  (via the record/type syntax from Part 3.3, extending the root `Error` type) must be fully
  supported so scripts can define and raise their own domain-specific error types, not be
  limited to the built-in set.
- Every stdlib module (Part 5) and every core language construct that can fail must raise
  from this hierarchy consistently — audit this explicitly as part of Part 5's
  Definition-of-Done cross-reference.

## 12.5 Runtime stack traces

- When a runtime error propagates unhandled out of a T++ program, the printed trace must
  show the T++-level call stack (which `define`d functions were active, at which source
  locations) in natural, readable form — not a Python interpreter stack trace showing the
  evaluator's own internal call frames. This requires the runtime to maintain its own
  T++-level call-stack bookkeeping (likely already partially needed for Part 1.5's
  stack-depth-limit and Part 4's profiler) and render it distinctly from the Python
  process's actual stack.

## 12.6 Non-goals for Part 12

- Do not attempt fully automatic error *correction* (silently "fixing" and continuing past
  an error the user didn't explicitly resolve) — suggest fixes, never silently apply them
  without the user's action, since silent auto-correction of source code is a correctness
  and trust hazard, not a convenience, in a language whose core promise is predictable
  execution.
- Do not build a telemetry pipeline that reports which errors users hit most often back to
  a central service — if this is ever wanted for prioritizing future work, it needs the
  same explicit, separate, opt-in-only design treatment flagged in Part 7.10, not a quiet
  addition here.

## 12.7 Definition of Done for Part 12

- [ ] Every diagnostic message across lexer/parser/analyzer/type-checker/runtime is audited
      against the 12.2 principles — plain-language-first, precise location, suggestion
      where confidently inferable, no raw Python traceback leakage in the default path.
- [ ] Parser error recovery is implemented and tested: a fixture file with three
      independent, unrelated syntax errors produces three separate, correctly-located
      diagnostics in one pass, not just the first one.
- [ ] The three-tier severity model is documented once, centrally, and referenced (not
      redefined) by the CLI, LSP, and `tpp doctor` docs.
- [ ] The exception hierarchy is documented in `docs/language-guide.md` with the full type
      tree shown, and every stdlib module's error-raising behavior is audited against it.
- [ ] A `--debug` flag path exists that shows full internal tracebacks for platform-
      developer debugging, kept clearly separate from default user-facing error output.
- [ ] T++-level runtime stack traces are demonstrated via a test fixture with at least
      three levels of nested `define`d function calls, verifying the printed trace shows
      T++ function names and source locations, not Python evaluator internals.

---

# PART 13 — TESTING INFRASTRUCTURE

## 13.1 Context

Test blocks already exist directly in `.tpp` source per the README. This part expands that
into a genuinely capable testing story — fixtures, mocking, coverage, and integration with
the broader Python-ecosystem testing tools the project itself uses for its own test suite
(`pytest`, per the developer workflow section of the README).

## 13.2 Test block syntax expansion

```tpp
test "addition works correctly"
    let result be add with 2 and 3
    expect result to be 5
end

test "throws on invalid input" expecting an error
    add with "not a number" and 3
end
```

- Expand `expect ... to be ...` (existing) with a fuller natural assertion vocabulary:
  `expect ... to be greater than ...`, `expect ... to contain ...`, `expect ... to be
  close to ... within ...` (for float comparison, avoiding the classic float-equality
  footgun by making an explicit-tolerance comparison the natural, easy-to-reach spelling
  rather than requiring users to know to avoid bare `to be` for floats), `expect ... to be
  nothing` / `expect ... to exist`.
- `test "..." expecting an error` / `test "..." expecting a <SpecificErrorType>` as the
  natural spelling for "this test should raise" — integrating with Part 12.4's exception
  hierarchy so a test can assert not just "an error happened" but "specifically this kind
  of error happened."
- Test grouping/organization: a natural `describe`/`suite`-equivalent grouping construct
  (`about "the add function" ... test "..." ... test "..." ... end`) so related tests can
  share setup and be organized hierarchically, reported hierarchically.

## 13.3 Fixtures and setup/teardown

- Natural syntax for shared setup run before each test in a group and cleanup run after:
  `before each test in this group ... end` / `after each test in this group ... end` within
  an `about "..."` block from 13.2.
- Parameterized/data-driven tests: a natural spelling for running the same test body across
  multiple input/expected-output pairs (`test "doubling" for each (input, expected) in
  [(1,2), (2,4), (3,6)] ... end` or similar natural framing) — avoids the copy-paste-many-
  near-identical-tests anti-pattern.

## 13.4 Mocking and test doubles

- Given interop (Part 11) and stdlib I/O (Part 5.6) exist, tests need a way to substitute
  fake implementations without hitting real files/network/etc. Design a natural mocking
  API (`replace the "system" module's "read_file" function with a function that gives back
  "fake content", for the duration of this test`) — this is a genuinely tricky feature to
  get right (scoping the replacement correctly so it doesn't leak beyond the intended test,
  restoring the original afterward even if the test fails/throws) and deserves careful,
  explicit design rather than a quick bolt-on.

## 13.5 Coverage reporting

- `tpp test --coverage` (coordinate flag naming with Part 7.8's `tpp test` expansion)
  reports which lines/branches of the tested `.tpp` source were actually exercised,
  outputting both a human-readable summary and a standard machine-readable format (e.g.
  Cobertura-XML or LCOV-compatible output) so it can plug into existing CI
  coverage-tracking tooling and badges (relevant to the CI badges already shown at the top
  of the current README).

## 13.6 The project's own test suite (meta: testing the testing infrastructure, and
everything else)

- Every part of this brief that touches `tpp/` Python source must have corresponding
  `pytest`-based tests in the existing `tests/` Python test tree (distinct from
  `.tpp`-source test blocks, which test T++ *programs*; this is about testing the T++
  *implementation* itself) — this is the standard the existing `pytest -q
  tests/test_cli_integration.py` developer-workflow line implies is already the norm, and
  it must be upheld rigorously for every new Python module added under this brief.
- Property-based testing (via `hypothesis` or a similar Python property-testing library) is
  strongly encouraged for the parser and evaluator specifically — generating random-but-
  valid-shaped T++ source and asserting invariants (e.g. "format then parse then format
  again produces identical output," "every valid program that runs without error produces
  the same output when run twice," "the optimizer never changes a program's output") is a
  disproportionately effective way to catch the kind of subtle correctness bugs that
  hand-written example-based tests tend to miss, and directly supports the "predictable
  execution" thesis by giving it teeth beyond documentation.
- Golden-file/snapshot testing for CLI output, formatter output, and diagnostic message
  text, so accidental output-format regressions are caught automatically rather than
  requiring a human to notice a subtly-wrong error message slipped through.

## 13.7 Non-goals for Part 13

- Do not build a custom test runner/framework from scratch for the Python-level test suite
  — keep using `pytest`, per the existing project convention; this part is about T++-level
  (`.tpp` source) testing capability and about ensuring Python-level test coverage
  discipline, not about replacing the existing, working Python testing toolchain.
- Do not make coverage reporting a hard CI-blocking gate at some arbitrary percentage
  threshold as part of *this* brief's own required deliverables — recommend establishing
  and trending coverage numbers (Part 19 tracks this) but leave the decision of an
  enforced minimum threshold as a project-governance decision for Part 18, since an
  aggressively-enforced coverage percentage decided unilaterally by an implementing agent,
  rather than by the project's actual maintainer, risks being either meaninglessly low or
  counterproductively rigid.

## 13.8 Definition of Done for Part 13

- [ ] Expanded assertion vocabulary from 13.2 is implemented and each form has a
      demonstration test.
- [ ] `about`/grouping, `before each`/`after each`, and parameterized test forms are
      implemented, documented, and demonstrated.
- [ ] The mocking API correctly scopes and restores replacements even when the test under
      mock throws — verified by an explicit test-of-the-mocking-mechanism-itself.
- [ ] `tpp test --coverage` produces both human-readable and machine-readable
      (Cobertura/LCOV-compatible) output.
- [ ] Every new Python module added anywhere in this brief has corresponding `pytest`
      coverage — verified as part of Part 19's overall gate, not just self-reported by
      each part's implementing agent.
- [ ] At least one property-based test exists for the parser (format/parse round-trip
      invariant) and at least one for the optimizer (output-preservation invariant).

---

# PART 14 — DOCUMENTATION

## 14.1 Context

The README references `docs/language-guide.md`, `docs/plugin-guide.md`,
`docs/web-ide.md`, `docs/devops.md`. Every part above has generated documentation
obligations pointing back into these files (and new ones this part formalizes:
`docs/embedding-guide.md` from Part 11, `docs/decisions/` ADRs referenced throughout, a
stdlib reference). This part is where all of that gets assembled into a coherent,
navigable whole — per Part 0.6, documentation should be updated incrementally as each part
lands, with the comprehensive consistency pass happening last, in Stage D.

## 14.2 Documentation architecture

- Establish a clear, consistent structure across all doc files: every guide follows the
  same top-level pattern (overview → quickstart/first example → detailed reference →
  common pitfalls/FAQ → links to related guides) so a reader who's learned to navigate one
  guide already knows how to navigate all of them.
- `docs/language-guide.md` becomes the canonical, comprehensive reference for the entire
  language surface (Parts 1–3, 10, 12) — grammar reference, full synonym table (Part 1.9),
  type system reference (Part 3), module system reference (Part 10), exception hierarchy
  (Part 12.4) — and must stay internally consistent (no contradictions between, say, the
  grammar section and a worked example elsewhere in the same document).
- A dedicated, auto-generated (where feasible, from docstrings per Part 5.11's requirement
  that every stdlib function has one) **stdlib reference** covering every module from Part
  5, formatted consistently (signature, description, parameters, return value, example,
  error conditions) — auto-generation from source docstrings, rather than hand-maintained
  prose duplicating what's in the code, is strongly preferred since hand-maintained
  reference docs reliably drift out of sync with the actual implementation over time.
- `docs/plugin-guide.md`, `docs/web-ide.md`, `docs/devops.md`, `docs/embedding-guide.md`
  each get the comprehensiveness treatment specified in their respective parts' sections
  above (6.8, 8.5, 11.3).

## 14.3 Tutorial / learning path

- Beyond reference documentation, build a genuine beginner-friendly tutorial: "Your first
  T++ program in 5 minutes" through progressively more advanced worked examples (a small
  real program — something like a simple todo-list manager or a basic text-adventure game
  — built up incrementally across the tutorial, introducing conditionals, loops, functions,
  and finally a taste of the module system, in that order, each building on the last).
  This is distinct from and complements the reference material — reference docs answer "how
  does X work," a tutorial answers "how do I build something."
- Every tutorial code example must be a real, executable `.tpp` file under `examples/`
  (not just an inline code block in prose that's never actually verified to run) and must
  be exercised by CI (Part 19) so tutorial examples can never silently rot and stop
  working as the language evolves.

## 14.4 Runnable examples throughout

- Wherever feasible, prefer embedding genuinely runnable examples (leveraging Part 8.4's
  embeddable web IDE mode) over static code blocks in any web-published version of the
  docs — "try it yourself, right here" is a significantly stronger teaching tool for a
  language whose core value proposition is approachability, and directly reinforces
  the "predictable execution" trust story by letting a skeptical reader verify claims
  themselves rather than take the docs' word for it.

## 14.5 Changelog and migration guides

- Coordinate with Part 17's automated changelog generation — every user-facing change
  from every part of this brief must have a corresponding, clear changelog entry, written
  for the actual end user reading it to decide whether to upgrade, not written as an
  internal engineering summary of what code changed.
- For any deprecation introduced under Part 17.4, a dedicated migration-guide section
  showing the old spelling/pattern next to the new recommended one, with a worked
  before/after example — not just "X is deprecated, use Y instead" as a bare, unexplained
  statement.

## 14.6 Non-goals for Part 14

- Do not stand up a separate documentation website/hosting infrastructure as part of this
  brief (no Docusaurus/MkDocs site build-out mandated) — focus on the actual Markdown
  content under `docs/` being comprehensive, accurate, and well-organized; a
  website-generation layer on top of that content is a reasonable follow-up but not
  required here, and should be flagged as a roadmap item in Part 18 if genuinely wanted.

## 14.7 Definition of Done for Part 14

- [ ] Every doc file listed in 14.2 exists, follows the consistent structural pattern, and
      has no internal contradictions with the actual current implementation (verified by
      having every code example in every doc file actually execute successfully as part of
      CI — see Part 19).
- [ ] The stdlib reference is generated (or verifiably kept in sync) from actual source
      docstrings, covering 100% of public stdlib functions across every module from Part 5.
- [ ] The beginner tutorial exists as a complete, working, incrementally-building sequence
      with every example runnable and CI-verified.
- [ ] Every deprecation from Part 17 has a corresponding migration-guide entry with a
      before/after example.
- [ ] A single top-level `docs/README.md` or equivalent index exists, linking to every
      other doc file with a one-line description of what each covers, so a new reader has
      an obvious starting point.

---

# PART 15 — SECURITY

## 15.1 Context and why this part is not optional polish

T++ scripts will, once this brief's work lands, potentially: read/write files (Part 5.6,
sandboxed), call out to allow-listed Python code (Part 4.7, 11.2), run inside a
publicly-reachable execution API and web IDE (Part 8), and be extended by third-party
plugins that may themselves contain arbitrary Python (Part 6.5). This is a real attack
surface, not a hypothetical one, and it must be treated with commensurate seriousness. Per
Part 0.6, security work gates the Stage C API/Web IDE delivery specifically — Part 8 is
not done until it has passed the review described here.

## 15.2 Threat model (produce this first, as a concrete artifact)

Write and commit a formal threat model document (`docs/security/threat-model.md`)
explicitly enumerating:
- **Actors**: a script author running their own code locally (lowest risk — they're
  attacking themselves at worst); a script author submitting code to the public HTTP API
  or web IDE (the primary adversarial actor to design against — assume hostile intent);
  a plugin author (a semi-trusted actor whose code other users' scripts will depend on);
  an operator running `tpp api --serve` in a production deployment (needs guidance on how
  to deploy safely, per Part 8.5).
- **Assets to protect**: the host machine/container running the API server (against RCE,
  filesystem escape, resource exhaustion/DoS); other users' data/sessions on a shared API
  deployment (against cross-session data leakage, per Part 8.3's session-isolation
  requirement); the T++ ecosystem's reputation and user trust (against a widely-installed
  malicious plugin, per Part 6.5).
- **Explicit attack scenarios to defend against**, each with a named mitigation
  cross-referenced to the relevant part of this brief: path traversal via `system`/`files`
  module (5.6) → sandboxed root enforcement; resource exhaustion via infinite
  loops/unbounded recursion/huge allocations (1.4, 1.5, 8.3) → execution time/memory/output
  limits; privilege escalation via Python interop reaching disallowed modules (4.7, 11.2) →
  centralized, audited allow-list; session/state leakage between untrusted API users (8.3)
  → per-session isolated environments; malicious plugin code (6.5) → permission
  declaration/confirmation and namespace-restricted execution; injection-style attacks
  where crafted T++ source triggers unintended behavior in the *host* Python process (e.g.
  an eval-style vulnerability, or a crafted deeply-nested/recursive grammar construct
  causing catastrophic parser recursion/stack overflow in the Python process itself, distinct
  from the T++-level stack-limit which only protects *T++ program* recursion, not the
  parser's own recursive-descent recursion on adversarially deep input) → explicit parser
  depth limits, fuzzing (15.4).

## 15.3 Sandboxing implementation review

- Formally review, and where necessary strengthen, every sandboxing boundary named in the
  threat model: confirm the `system`/`files` sandboxed root (5.6) cannot be escaped via
  symlinks, `..`-sequences in various encodings, or absolute-path injection; confirm
  resource limits (execution time, memory where enforceable, output size) are actually
  enforced server-side and cannot be bypassed by a request simply omitting or lying about
  them (per 8.3's "server-enforced hard ceilings" requirement — a client-supplied limit
  must only ever be able to *tighten*, never loosen, the server's actual ceiling); confirm
  the Python-interop allow-list (4.7) is checked at every call site, not just at some but
  not all entry points into the interop layer.
- Consider, and document the decision on, whether OS-level sandboxing (seccomp, containers,
  or a subprocess-per-execution isolation model) is warranted in addition to
  application-level sandboxing for the API server specifically, given that
  application-level sandboxing bugs are an inherent risk in any sufficiently complex
  interpreter and defense-in-depth is a sound principle for a public code-execution
  service — this doesn't have to be fully implemented in this brief if it's a substantial
  infrastructure lift, but the decision and its rationale must be documented, and if
  deferred, it must be flagged clearly in `docs/devops.md` as a **known limitation**
  operators should understand before deploying the API publicly, not silently omitted.

## 15.4 Fuzzing

- Set up automated fuzz testing (e.g. via `atheris` or a comparable Python-compatible
  fuzzing harness) targeting: the lexer/parser (feeding malformed/adversarial byte
  sequences and confirming no unhandled crash, no excessive resource consumption, no
  Python-process-level stack overflow from pathological grammar nesting), the JSON API's
  request parsing (malformed JSON, wrong types, oversized payloads), and the
  Python-interop/allow-list boundary (attempting to reach disallowed modules through
  crafted input).
- Run fuzzing in CI on a scheduled/periodic basis (not necessarily on every single commit,
  given time cost, but genuinely regularly — coordinate the cadence with Part 19) and treat
  any crash/hang found as a real bug requiring a regression test, not just a fuzzer curiosity
  to be dismissed.

## 15.5 Dependency and supply-chain security

- Audit the project's own Python dependencies (whatever `pyproject.toml` currently
  declares) for known vulnerabilities using a standard tool (`pip-audit` or equivalent) as
  part of CI (Part 19).
- Ensure the release process (Part 17) produces genuinely reproducible, verifiable
  artifacts — confirm `twine check` (already in the existing release workflow per the
  README) is complemented by artifact checksums/signing where the PyPI publish pipeline
  supports it, so a downstream user has a real basis for trusting an installed release
  matches its source.

## 15.6 Security disclosure policy

- Publish a `SECURITY.md` at repo root (coordinate with Part 18's community/governance
  documentation work) with a clear, explicit process for responsibly reporting a
  vulnerability (a contact channel, expected response time, whether/how credit is given) —
  this is both a genuine safety practice and a trust signal to anyone evaluating T++ for
  serious use.

## 15.7 Non-goals for Part 15

- Do not claim or imply a formal, third-party-audited security certification — this brief
  produces genuinely strong internal security engineering practice, not a marketing claim
  of "audited and certified secure," which would require actual external audit engagement
  entirely outside this brief's scope.
- Do not build a fully custom OS-level sandboxing/container-orchestration system from
  scratch as a mandatory deliverable — evaluate and document (15.3) whether existing,
  well-established tools (standard container runtimes, `seccomp` profiles) suffice, rather
  than inventing new isolation technology.

## 15.8 Definition of Done for Part 15

- [ ] `docs/security/threat-model.md` exists, covering every actor/asset/scenario in 15.2,
      each scenario cross-referenced to its mitigating part/section of this brief.
- [ ] Path-traversal, resource-limit-bypass, allow-list-bypass, and cross-session-leakage
      scenarios each have a dedicated, explicit, adversarial test — not just happy-path
      coverage of the feature the security property is attached to.
- [ ] Fuzzing harnesses exist for lexer/parser, JSON API parsing, and the interop boundary,
      run on a documented CI cadence, with any discovered issue converted to a permanent
      regression test.
- [ ] `pip-audit` (or equivalent) runs in CI and the project has zero known-vulnerable
      dependencies at time of Part 19's final gate (or documented, justified exceptions if
      a fix genuinely isn't yet available upstream).
- [ ] `SECURITY.md` exists with a clear disclosure process.
- [ ] Every item in Part 8's Definition of Done that references "security-reviewed" has
      genuinely been reviewed against this part's threat model, not just functionally
      tested — this is the actual mechanism by which Part 15 gates Part 8, per Part 0.6.
- [ ] The OS-level-sandboxing decision (implemented, or deferred-and-documented-as-a-known-
      limitation) is explicit, not silently absent from the documentation either way.

---

# PART 16 — DEVELOPER EXPERIENCE AND ONBOARDING

## 16.1 Context

Several other parts already touch DX heavily (`tpp doctor` in Part 7.8, error message
quality in Part 12, the tutorial in Part 14.3). This part is specifically about the
first-15-minutes experience and the ongoing quality-of-life details that compound into
"this tool feels good to use" or "this tool is annoying" over time — genuinely important
for adoption, genuinely easy to under-invest in relative to flashier features.

## 16.2 The absolute first-run experience

- `pip install tpp-language` followed immediately by `tpp doctor` should, on a totally
  fresh environment, produce a clean, encouraging, accurate health report — audit this
  path explicitly end-to-end on a genuinely clean environment (not a developer machine with
  pre-existing state), since this is most new users' literal first interaction with the
  tool after install and first impressions here disproportionately affect adoption.
- `tpp init` (Part 7.2) followed by whatever the default template produces followed by
  `tpp run` on that default output should work with zero manual intervention and should
  print something genuinely welcoming and orienting, not just raw script output with no
  context — a "you just ran your first T++ program, here's what to try next" style message
  on the default template specifically is worth the small effort.

## 16.3 Interactive tutorial/learning mode

- Consider (design and, time permitting, implement) a `tpp learn` command: an interactive,
  terminal-based, step-by-step tutorial mode that walks a brand-new user through core
  concepts hands-on, inside the REPL, checking their work as they go (analogous in spirit
  to tools like `rustlings` for Rust or interactive Python tutorials) — this is a
  meaningfully larger effort than most items in this part and should be treated as a
  stretch goal explicitly flagged in Part 18's roadmap if it doesn't fit the brief's
  overall timeline, rather than rushed to a half-working state.

## 16.4 Quality-of-life details worth explicit attention

- Colorized, well-formatted terminal output throughout the CLI (errors, test results,
  `tpp doctor` output) with a documented, respected `NO_COLOR`/`--no-color` convention for
  environments that need plain output (CI logs, accessibility needs, piping to files).
- Progress indication for anything that takes more than roughly a second (plugin
  installation, `tpp bench`'s full run, fuzzing/coverage runs) — silent multi-second waits
  with no feedback read as "is this stuck?" and erode trust in the tool.
- Consistent, well-considered use of the "did you mean...?" pattern (already required for
  parser diagnostics in Part 12.2) extended to CLI subcommand typos too (`tpp rnu
  script.tpp` → `did you mean "tpp run"?`) — a small, cheap, high-goodwill detail.
- A genuinely useful `tpp --help` at the top level that doesn't just dump every subcommand
  flatly, but groups them sensibly (core: run/repl/test; project: init/build/bundle;
  quality: format/lint/doctor; ecosystem: plugin/docs; advanced: api/bench) so a new user
  scanning it isn't overwhelmed by the full surface area this brief adds.

## 16.5 Non-goals for Part 16

- Do not build gamification (badges, streaks, points) into any learning-mode feature — this
  reads as gimmicky for a serious language-tooling project and doesn't match the
  "production-grade" positioning the project claims for itself.
- Do not collect any usage analytics as part of onboarding-flow "improvement," per the
  same explicit-opt-in-only constraint established in Part 7.10/12.6.

## 16.6 Definition of Done for Part 16

- [ ] The fresh-install → `tpp doctor` → `tpp init` → `tpp run` path is manually walked
      through on a genuinely clean environment (a fresh container/VM, not a developer's
      existing machine) and confirmed to work with zero manual intervention and helpful,
      encouraging output at each step.
- [ ] `NO_COLOR`/`--no-color` is respected consistently across every CLI command that
      produces colorized output.
- [ ] CLI subcommand typo suggestion ("did you mean") is implemented and tested against a
      representative set of common typos of real subcommand names.
- [ ] Top-level `tpp --help` output is grouped sensibly per 16.4 and reviewed for whether a
      genuinely new user could scan it and find the right starting command within a few
      seconds.
- [ ] The `tpp learn` interactive-tutorial decision (implemented, or explicitly deferred to
      Part 18's roadmap) is documented either way, not silently dropped.

---

# PART 17 — VERSIONING, DEPRECATION, AND RELEASE PROCESS

## 17.1 Context

The README already shows real release automation (`ci.yml`, `release.yml`, tag-based
releases, `twine check`, smoke tests, generated release notes, optional PyPI publish). This
part makes that rigor more comprehensive and, critically, adds the formal deprecation
process that Part 0.3/0.5's backward-compatibility requirements depend on throughout this
entire brief.

## 17.2 Semantic versioning discipline

- Formally commit the project to strict SemVer for `tpp-language` releases going forward:
  patch (bugfixes, no surface changes), minor (new, backward-compatible features — this
  brief's additive work generally lands as minor bumps), major (breaking changes, only via
  the deprecation path in 17.4). Document this explicitly in `docs/versioning-policy.md`
  and cross-reference it from `CONTRIBUTING.md` (Part 18).
- The plugin API version (Part 6.6) and the HTTP API version (Part 8.2) may each evolve on
  their own independent versioning tracks from the core language version — document the
  relationship between all three version numbers clearly so users aren't confused about
  which version number governs which compatibility guarantee.

## 17.3 Automated changelog generation

- Given Conventional Commits are already mandated (Part 0's instructions), wire up
  automated changelog generation from commit history (e.g. via `git-cliff` or a comparable
  tool) as part of the release workflow, producing genuinely readable, user-facing
  changelog entries grouped by type (Features / Fixes / Performance / Breaking Changes) —
  not just a raw commit-message dump, and not purely mechanical either (a human/agent
  editorial pass on the generated draft before it's finalized in a release is worthwhile,
  especially for anything in the Breaking Changes section, to ensure the migration-guide
  cross-reference from Part 14.5 is actually present and correct).

## 17.4 Formal deprecation process

This is the mechanism that makes every "no breaking changes" constraint throughout this
brief actually livable long-term rather than a permanent freeze:

1. A feature/syntax form/API shape being deprecated gets marked as such in code (a
   deprecation marker mechanism — for language syntax, this likely means the parser/linter
   emits a Warning-tier diagnostic per Part 12.3 when the deprecated form is used, not that
   the form stops working) and in docs (a clearly labeled "deprecated since 3.X, will be
   removed in 4.0, use Y instead" note, with the migration guide entry from Part 14.5).
2. Deprecated features must continue functioning, unchanged, for **at minimum one full
   major version cycle** after being marked deprecated — never remove something in the same
   major version it was deprecated in.
3. Removal only happens in a major version bump, and the release notes for that major
   version must include a complete, consolidated list of every removed deprecation with
   its migration path, not just a link back to scattered historical changelog entries.
4. `tpp doctor` and `tpp lint` (Parts 7.8, 7.4) should both be able to scan a project and
   report which deprecated forms it currently uses, to help users migrate proactively
   before a major version lands, and `tpp upgrade` (Part 7.6) must surface this
   information at upgrade time per its own Part 7.6 requirement.

## 17.5 Release cadence and branching

- Document a clear, sustainable release cadence (does not need to be rigid/calendar-based
  for a project this size, but should be documented as a stated intention — e.g. "minor
  releases as meaningful feature sets land, patch releases promptly for bugfixes, major
  releases infrequently and only with a published deprecation runway per 17.4") and a
  branching strategy (trunk-based with release tags, per what the existing tag-triggered
  `release.yml` implies, versus a dedicated release-branch model) — pick one, document why,
  and ensure the CI/release workflows genuinely match the documented policy rather than the
  policy being aspirational prose disconnected from the actual automation.

## 17.6 Non-goals for Part 17

- Do not introduce a rigid, calendar-locked release schedule that would force shipping
  half-finished work to hit a date — cadence guidance, not a hard deadline commitment, is
  the appropriate scope here for a project at this stage.
- Do not build custom release-automation tooling from scratch where mature, widely-used
  tools already solve the problem well (changelog generation, dependency auditing) — reuse
  established tooling per 17.3/15.5 rather than reinventing it.

## 17.7 Definition of Done for Part 17

- [ ] `docs/versioning-policy.md` exists and clearly documents SemVer commitment and the
      relationship between core/plugin-API/HTTP-API version numbers.
- [ ] Automated changelog generation is wired into the release workflow and produces a
      genuinely readable, correctly-grouped changelog on a test release.
- [ ] The formal deprecation process (17.4) is documented, and at least one real
      deprecation marker mechanism is implemented and demonstrated end-to-end (mark
      something deprecated → confirm it still works → confirm `tpp doctor`/`tpp lint`
      correctly flag its use → confirm the migration guide entry exists) even if nothing
      genuinely needs deprecating yet at brief-completion time — build and prove the
      mechanism regardless.
- [ ] Release cadence and branching strategy are documented and match the actual CI/release
      workflow behavior.

---

# PART 18 — COMMUNITY AND GOVERNANCE

## 18.1 Context

A solo-maintained project that wants real community adoption and contribution needs the
standard scaffolding that signals "this project is genuinely open to contribution and has
a clear process," even at a small scale — this is as much about setting expectations
clearly for a project of one maintainer as it is about actually onboarding a large
contributor base immediately.

## 18.2 Required governance documents

- `CONTRIBUTING.md`: how to set up a dev environment (already partially covered by the
  README's developer workflow section — consolidate and expand it here), how to run the
  full test/lint/format/bench suite locally before opening a PR, the Conventional Commits
  requirement (Part 0), the ADR process (Part 0.8) for non-trivial design decisions, and
  what reviewers will look for.
- `CODE_OF_CONDUCT.md`: a standard, widely-recognized code of conduct (e.g. adopting the
  Contributor Covenant rather than drafting a bespoke one from scratch, since a
  well-known standard is both faster to adopt correctly and more immediately legible to
  potential contributors who've seen it elsewhere).
- Issue templates (bug report, feature request) and a pull request template, each
  structured to elicit the information actually needed to act on a submission quickly (for
  bug reports: T++ version, minimal reproduction script, expected vs. actual behavior; for
  PRs: what changed and why, link to any relevant ADR, confirmation the full local test
  suite passes).
- `SECURITY.md` — already specified in Part 15.6; cross-referenced here as part of the
  overall governance-document set.

## 18.3 Project roadmap

- A living `ROADMAP.md` (or a pinned GitHub issue/discussion serving the same purpose)
  giving a genuine, honest sense of direction — near-term (what's actively being worked,
  drawn from this brief's Stage-based execution plan per Part 0.6), and longer-term
  (explicitly consolidating every item this brief has flagged as "deferred," "out of
  scope for this brief," or "stretch goal" across every part — the JIT discussion from Part
  4.9, full concurrency support from 4.8, a full package registry from 10.5/6.7, broader
  FFI from 11.5, a debugger/DAP from 9.7, `tpp learn` from 16.3, generics from 3.7, loop-
  else from 1.4, and any other explicitly-flagged deferred item — so none of this brief's
  deliberate scoping decisions get silently lost once the brief itself is no longer the
  active reference document).

## 18.4 Governance model for a growing project

- Even for a currently-solo-maintained project, briefly document the intended decision-
  making model as the project grows (e.g. "currently BDFL-style with the original author
  as sole maintainer; will formalize a more distributed model, such as a core-team RFC
  process, once contributor volume genuinely warrants it") — this doesn't need to be
  elaborate, but stating it explicitly avoids ambiguity for early contributors wondering
  "who decides."

## 18.5 Non-goals for Part 18

- Do not attempt to bootstrap an actual contributor community as a deliverable of this
  brief (no outreach, no marketing, no community-calls-scheduling) — this part produces the
  *documentation and process scaffolding* that makes community growth possible later, not
  community growth itself, which is a separate, ongoing, human effort outside an
  engineering brief's scope.
- Do not adopt an unusual or bespoke license/governance structure — if the project's
  existing `LICENSE` file (per Part 0.3's explicit instruction not to assume a license)
  already establishes a clear license, governance documentation must be consistent with it,
  not introduce contradictory terms.

## 18.6 Definition of Done for Part 18

- [ ] `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, issue templates, and a PR
      template all exist and are internally consistent with each other and with the actual
      current state of the project's CI/test/release tooling.
- [ ] `ROADMAP.md` exists and explicitly consolidates every deferred/out-of-scope/stretch-
      goal item flagged anywhere in this brief, cross-referenced back to the originating
      part, so the full set of "known future work" is discoverable from one place.
- [ ] A governance-model statement, however brief, exists and is consistent with the
      project's actual current license.

---

# PART 19 — VALIDATION AND SHIPPING GATE

## 19.1 Context and role

Nothing from Parts 1–18 reaches `main` and gets tagged for release without passing through
this gate. This part is deliberately the strictest, least negotiable part of the entire
brief, because it's the only thing standing between "a lot of ambitious work happened" and
"a lot of ambitious, *actually correct and shippable* work happened." Per Part 0.6, this is
Stage E and runs continuously as other stages' work lands, not just once at the very end.

## 19.2 Continuous integration requirements (expand the existing `ci.yml`)

Every one of the following must be a required, blocking CI check on every PR, not an
optional/advisory one, building on and expanding the existing checks already named in the
README (package install, compile checks, `ruff check`, CLI contract check, `tpp doctor`):

- Full `pytest` suite (all Python-level tests across every subsystem touched by this
  brief) — zero failures, zero skips without an explicit, reviewed justification comment
  on the skip.
- Full `.tpp`-source test-block suite (via `tpp test`, exercising the language-level
  testing infrastructure from Part 13 against itself) across every `examples/` and
  `tests/` fixture — zero failures.
- `tpp format --check` across the entire `.tpp` fixture corpus — zero formatting
  violations.
- `tpp lint` — zero Error-tier findings; Warning-tier findings tracked but not
  necessarily blocking (coordinate with the severity-model documentation from Part 12.3).
- Benchmark suite (`tpp bench` per Part 4.2) run and compared against the committed
  baseline — fail on regression past the documented threshold.
- `pip-audit` (or equivalent, per Part 15.5) — zero unaddressed known vulnerabilities.
- The scheduled fuzzing cadence from Part 15.4 reports clean (or any finding has already
  been converted to a fixed regression test before merge).
- Every code example embedded in every `docs/*.md` file (per Part 14.7's requirement) is
  extracted and actually executed, confirming documentation never silently drifts from
  reality.
- The syntax-highlighting-keyword-coverage check from Part 9.6.
- Cross-platform matrix validation (the existing CI presumably already runs a matrix per
  the README's "matrix validation" mention — confirm this continues to cover, at minimum,
  Linux/macOS/Windows and the Python version range declared in `pyproject.toml`, and
  expand the matrix if any new Part's work introduces platform-sensitive behavior, e.g.
  the sandboxed file I/O from Part 5.6 needing explicit path-separator/case-sensitivity
  testing across platforms).

## 19.3 Manual/human-judgment review gates (things CI cannot verify by itself)

- **Read-aloud test compliance** (Part 1.2) for every new syntax form — this is
  fundamentally a human-judgment call and must be explicitly confirmed, not assumed, before
  a language-surface PR is considered mergeable.
- **Diagnostic message quality** (Part 12.2) — spot-check a representative sample of new
  error messages against the plain-language-first, helpful-suggestion principles; CI can
  verify a diagnostic *fires*, but not that its wording is genuinely good.
- **Documentation clarity** (Part 14) — a fresh-eyes read-through by whoever/whatever is
  performing final review, checking that a genuinely new reader (not someone who already
  knows what the doc is trying to say) could follow it.
- **Security review sign-off** (Part 15.8's final bullet) — the explicit statement that
  Part 8's API/Web IDE work has been reviewed against the threat model, not just
  functionally tested, must be a real, documented review event (recorded in the PR
  description or a linked review document), not an implicit assumption.

## 19.4 Pre-release checklist (run once, immediately before any tagged release under this
brief's work)

- [ ] Every part's Definition of Done checklist (Parts 1–18) has been genuinely reviewed
      and is either fully checked or has explicit, documented justification for any
      unchecked item (deferred to roadmap per Part 18.3, not silently dropped).
- [ ] `docs/BRIEF.md` (the committed copy of this document, per Part 0.7) is retained in
      the repository for historical reference, cross-linked from `ROADMAP.md`.
- [ ] The full pre-this-brief 3.1.3 test suite and example corpus still passes unmodified
      against the new `main` — the single most important backward-compatibility check in
      the entire gate.
- [ ] Every hard constraint from Part 0.3 has been verified, explicitly, one by one, not
      just generally assumed to have been respected throughout.
- [ ] A release candidate has been built via the actual release workflow (`git tag`, the
      existing `release.yml` automation) and smoke-tested exactly as a real user would
      (`pip install` the built wheel in a clean environment, run through the Part 16.2
      fresh-install onboarding path end to end) before the tag is considered final and
      pushed for real.

## 19.5 What happens when the gate finds a problem

- A failing gate item blocks merge/release of the specific work that caused it — it does
  not block unrelated, already-passing work elsewhere in the brief from proceeding
  independently, given the staged, multi-part nature of this brief. Each Stage's items
  (per Part 0.6) should be gated and released to `main` (even if not immediately tagged
  for a PyPI release) independently as they clear this gate, rather than the entire,
  enormous scope of this brief being held as one single all-or-nothing merge — that would
  be an unmanageable, high-risk release pattern for a change of this magnitude.

## 19.6 Definition of Done for Part 19

- [ ] Every CI check in 19.2 is implemented, wired into `ci.yml`, and required (blocking),
      not advisory.
- [ ] Every manual review gate in 19.3 has a documented process for how/when it's actually
      performed and by whom (or which agent role, per the orchestration appendix below).
- [ ] The pre-release checklist in 19.4 has been run at least once, for real, against a
      genuine release candidate, before any tag from this brief's work is pushed as a real
      PyPI release.

---

# APPENDIX A — SUB-AGENT ROLE ASSIGNMENTS FOR T++ ORCHESTRATION

This appendix translates Parts 0–19 into concrete orchestration roles, since
the T++ platform execution model is orchestrator-plus-specialized-sub-agents rather than a
single agent working sequentially through a flat task list. Adjust agent count to whatever
your available parallelism/budget supports — this is a recommended decomposition, not a
rigid requirement.

## A.1 Orchestrator responsibilities

- Owns Part 0 in full and is the only role that reads and internalizes the entire brief
  end to end before dispatching work.
- Enforces the staging order from Part 0.6 — does not dispatch Stage B sub-agents until
  Stage A's PRs have actually merged, not just been opened.
- Owns Part 19's gate — reviews every sub-agent's Definition-of-Done self-report, spot-
  checks rather than blindly trusts it, and is the final authority on whether a Stage's
  work is genuinely ready to move to the next Stage.
- Maintains `docs/BRIEF.md` (Part 0.7) and `ROADMAP.md` (Part 18.3) as living documents
  updated as Stages complete, not written once at the start and forgotten.
- Resolves cross-part conflicts explicitly flagged by sub-agents (per Part 0's instruction
  that agents stop and document conflicts rather than silently resolving them alone) —
  this is one of the orchestrator's most important jobs and should not be delegated.

## A.2 Recommended sub-agent roster

- **Diagnostics Agent** — Part 12 (Stage A, first to start). Also provides the shared
  error-formatting utility every later agent's part depends on.
- **Types Agent** — Part 3.1–3.3 core (Stage A), then full Part 3 (Stage B/C as
  dependencies allow).
- **Modules Agent** — Part 10.1–10.3 core (Stage A), then full Part 10.
- **Language-Surface Agent(s)** — Parts 1, 2 (Stage B) — may be split into two agents
  (Statements/Control-Flow, Expressions) if working in parallel, but both must coordinate
  tightly on the shared synonym table (Part 1.9) to avoid conflicting registrations.
- **Runtime-Performance Agent** — Part 4 (Stage B).
- **Stdlib Agent** — Part 5 (Stage B) — benefits from close coordination with the
  Language-Surface agents on the possessive-vs-function-call convention (Part 5.2).
- **Plugins Agent** — Part 6 (Stage B), depends on Language-Surface's synonym table and
  Diagnostics' error infrastructure being stable first.
- **Interop Agent** — Part 11 (Stage B), depends on Runtime-Performance's Part 4.7 interop
  hardening landing first.
- **CLI Agent** — Part 7 (Stage C), depends on whichever Stage B features it's exposing
  commands for.
- **API/Web-IDE Agent** — Part 8 (Stage C) — **must work in lockstep with the Security
  Agent, not sequentially before or after it**, per Part 0.6 and Part 15.1's explicit
  instruction that Part 15 gates Part 8.
- **Tooling Agent** — Part 9, LSP and editor extensions (Stage C).
- **Testing-Infra Agent** — Part 13 (Stage C).
- **Docs Agent** — Part 14 (Stage D, but ideally contributing incrementally throughout
  every earlier Stage rather than starting cold at Stage D — see Part 14.1's note on
  incremental documentation).
- **Security Agent** — Part 15 (starts conceptually in Stage A doing threat-model drafting,
  works continuously as a reviewer/gater throughout, does concentrated hardening work
  alongside the API/Web-IDE Agent in Stage C).
- **DX Agent** — Part 16 (Stage D).
- **Release-Process Agent** — Part 17 (Stage D).
- **Governance Agent** — Part 18 (Stage D) — lightest-weight role, mostly documentation.
- **QA/Gate Agent** — Part 19 (Stage E, but its CI-infrastructure work should actually
  start early in Stage A/B so the gate exists and is enforcing checks throughout, not only
  built at the very end when it's too late to have caught early mistakes).

## A.3 Coordination artifacts every sub-agent must check before starting work

- The current state of `docs/decisions/` (ADRs) — a sub-agent must not re-litigate a
  decision another agent already made and documented; if it disagrees, it flags the
  disagreement to the orchestrator rather than unilaterally overriding a committed ADR.
- The shared synonym table's current state (Part 1.9) before registering any new keyword.
- The centralized Python-interop allow-list's current state (Part 4.7) before adding any
  interop capability.
- The exception hierarchy's current state (Part 12.4) before adding any new error type.

---

# APPENDIX B — QUICK-REFERENCE: EVERY EXPLICITLY DEFERRED / OUT-OF-SCOPE ITEM

Consolidated here so nothing flagged as deliberately out-of-scope across this entire brief
gets lost — the Governance Agent should use this exact list as the seed for `ROADMAP.md`'s
longer-term section (Part 18.3):

- JIT compilation / native-backend performance ceiling work (Part 4.9)
- Full cooperative-concurrency / async-await language feature (Part 4.8 — prototype/ADR
  only is in-scope; full shipped feature is not)
- Full public package registry and `tpp add`-style installer (Parts 6.7, 10.5)
- Networking primitives in the stdlib — HTTP client, sockets (Part 5.10)
- Database/ORM stdlib module (Part 5.10)
- Full macro system / compile-time metaprogramming as a raw language feature (Part 2.7)
- Full generics with dedicated syntax beyond single-letter type variables (Part 3.7)
- Exhaustiveness checking for `match` expressions (Part 2.6, stretch goal)
- Loop-`else` construct (Part 1.4)
- FFI for languages beyond Python (Part 11.5)
- Debugger / DAP (Debug Adapter Protocol) implementation (Part 9.7)
- `tpp learn` full interactive tutorial mode (Part 16.3, stretch goal — design encouraged,
  full implementation may be deferred)
- Any form of usage telemetry/analytics, anywhere, under any framing, without a separate,
  explicit, opt-in-only design discussion (Parts 7.10, 12.6, 16.5 — repeated deliberately,
  this is the single most consistently-repeated non-goal in the entire brief)
- A hosted-SaaS business layer (accounts, billing) around the API/Web IDE (Part 8.7)
- A documentation website/hosting build-out beyond the Markdown content itself (Part 14.6)
- Gamification of any onboarding/learning feature (Part 16.5)
- Third-party-audited formal security certification claims (Part 15.7)

---

*End of brief. Total scope: 19 parts plus 2 appendices, covering language surface, type
system, runtime, standard library, plugins, CLI, API/Web IDE, tooling, modules, interop,
diagnostics, testing, documentation, security, developer experience, release process,
governance, and the validation gate that ties all of it together. Every part is
independently gate-checked; nothing ships without passing Part 19. Good luck — this is a
big, ambitious, genuinely worthwhile scope of work for T++, and it's meant to be worked in
the staged order Part 0.6 lays out, not all at once.*

---

# APPENDIX C — WORKED EXAMPLE PROGRAMS (CANONICAL FIXTURES)

Every program below must exist, verbatim or near-verbatim, as a real, executable `.tpp`
file under `examples/` once its dependent Part lands, and must be referenced from the
relevant doc page per Part 14.3/14.4's "every example is runnable and CI-verified"
requirement. These are not illustrative-only snippets — treat each as a required
deliverable, not optional flavor text.

## C.1 `examples/basics/temperature-converter.tpp` (Parts 1, 2)

Demonstrates: functions with typed-optional params, conditionals, natural arithmetic,
string interpolation.

```tpp
define celsius_to_fahrenheit with celsius as a number, giving back a number as
    give back (celsius times 9 divided by 5) plus 32
end

define describe_weather with fahrenheit as a number as
    if fahrenheit is greater than 90 then
        say "It's scorching out there! {fahrenheit} degrees."
    otherwise if fahrenheit is between 60 and 90 then
        say "Pleasant day, {fahrenheit} degrees."
    otherwise
        say "Bundle up, it's {fahrenheit} degrees."
    end
end

for each c in [0, 20, 37, 100]
    let f be celsius_to_fahrenheit with c
    describe_weather with f
end
```

## C.2 `examples/basics/todo-list.tpp` (Parts 1, 2, 3, 5)

Demonstrates: user-defined record types, collections module, comprehensions, match.

```tpp
define a Task as
    title as text
    is done as a boolean defaulting to false
end

let tasks be a list containing
    a Task with title as "Write the T++ brief" and is done as true and
    a Task with title as "Ship Part 1" and is done as false and
    a Task with title as "Ship Part 19" and is done as false

let remaining be the items in tasks where (item's is done) is false

say "{remaining's size} tasks left:"
for each task in remaining
    say "- {task's title}"
end

define status_line with task as a Task, giving back text as
    match task's is done
        when true then
            give back "[x] {task's title}"
        otherwise
            give back "[ ] {task's title}"
    end
end
```

## C.3 `examples/intermediate/word-frequency.tpp` (Parts 2, 5, 12)

Demonstrates: text module, records-as-maps, error handling, iterators.

```tpp
define count_words with text_block as text, giving back a record as
    let counts be a record with
    let words be the pieces of (text_block's lowercase version) split by " "
    for each word in words
        try
            increase counts's (word) by 1
        handle KeyNotFoundError as e
            set counts's (word) to 1
        end
    end
    give back counts
end
```

## C.4 `examples/intermediate/plugin-stdlib-extension.tpp` + manifest (Part 6)

A complete, minimal, working plugin per Part 6.8's requirement for one worked
stdlib-extension example — manifest, implementation, and a `.tpp` script consuming it —
must all exist together as one coherent fixture set under `examples/plugins/stdlib-
extension/`.

## C.5 `examples/multi-module-project/` (Part 10)

A small, realistic 3-4 file project (an entry point plus at least two imported modules,
one of which imports the other, demonstrating non-circular but non-trivial module
resolution) — the canonical fixture required by Part 10.7's Definition of Done.

## C.6 `examples/testing/full-test-suite-demo.tpp` (Part 13)

Demonstrates every assertion form, `about`/grouping, `before each`/`after each`, and one
parameterized test, all in one coherent, readable file suitable for copy-paste-and-adapt
by a new user's first real test file.

---

# APPENDIX D — STDLIB FUNCTION CATALOG STARTING POINT

This is a non-exhaustive starting checklist for the Stdlib Agent (Part 5) — a concrete
seed list so "expand the stdlib" doesn't start from a blank page. Each function must still
independently satisfy Part 5.11's Definition of Done (docstring, doc entry, positive test,
negative test) regardless of appearing on this seed list.

**math**: `absolute value of`, `square root of`, `sine of` / `cosine of` / `tangent of`,
`log of ... base ...`, `round`, `round up`, `round down`, `round ... to N decimal places`,
`the greater of ... and ...`, `the lesser of ... and ...`, `a random number between ... and
...`, `the average of`, `the median of`, `the sum of`, `the minimum of`, `the maximum of`,
`is even`, `is odd`, `is prime`.

**text**: `uppercase version of`, `lowercase version of`, `trimmed version of`, `padded to
length ... with ...`, `pieces of ... split by ...`, `... joined by ...`, `does ... contain
...`, `the position of ... in ...`, `... with ... replaced by ...`, `... matches the
pattern ...`, `... formatted with N decimal places`, `... formatted as currency`, `the
length of`, `reversed version of`.

**time**: `the current moment`, `... days/hours/minutes from now`, `the difference between
... and ...`, `... formatted as ...`, a moment parsed from text given a format, `... in the
timezone ...`.

**collections**: `the result of applying ... to each item in ...`, `the items in ... where
... is true`, `combine ... into one value starting from ... using ...`, `sort`, `sort ...
by ...`, `group the items in ... by ...`, `the union of ... and ...`, `the intersection of
... and ...`, `flattened version of`, `... zipped with ...`, `the first N items of`, `the
last N items of`, `a unique version of`.

**system/files** (sandboxed, per Part 5.6): `read the contents of`, `write ... to`, `does
... exist`, `append ... to`, `the command line arguments`, `an allow-listed environment
variable named ...`.

**json/data**: `parse ... as json`, `... converted to json text`.

**validate**: `is a valid email`, `is a valid number`, `is within the range ... to ...`,
`is not nothing`.

---

# APPENDIX E — FULL GRAMMAR SKETCH (SEED FOR PART 1.11'S FORMAL EBNF)

This is a working sketch, not the final formal grammar — the Language-Surface Agents must
still produce the fully rigorous EBNF required by Part 1.11, but this sketch establishes
the intended shape so independent agents converge on compatible structure rather than
inventing incompatible grammars in parallel.

```ebnf
program        ::= statement*

statement      ::= let_stmt | set_stmt | say_stmt | if_stmt | while_stmt
                  | repeat_stmt | for_each_stmt | define_stmt | give_back_stmt
                  | try_stmt | test_stmt | use_stmt | export_stmt | expr_stmt

let_stmt       ::= "let" IDENT "be" expr (type_annotation)?
type_annotation::= "as" "a" TYPE_NAME | "as" TYPE_NAME

if_stmt        ::= "if" condition "then" statement*
                    ("otherwise" "if" condition "then" statement*)*
                    ("otherwise" statement*)?
                    "end"

condition      ::= expr comparator expr | condition "and" condition
                  | condition "or" condition | "not" condition
                  | expr "is" "between" expr "and" expr

comparator     ::= "is" "greater" "than" | "is" "less" "than"
                  | "is" "at" "least" | "is" "at" "most"
                  | "is" ("equal" "to")? | "is" "not"

for_each_stmt  ::= "for" "each" IDENT ("," IDENT)? "in" expr statement* "end"

define_stmt    ::= "define" IDENT "with" param_list ("," "giving" "back" type)? "as"
                    statement* "end"

param_list     ::= param ("and" param)*
param          ::= IDENT (type_annotation)? ("defaulting" "to" expr)?

try_stmt       ::= "try" statement*
                    ("handle" (error_type | "any" "error") "as" IDENT statement*)+
                    ("finally" statement*)?
                    "end"

match_expr     ::= "match" expr ("when" pattern "then" statement*)+
                    ("otherwise" statement*)? "end"
```

Full expression precedence (highest to lowest binding — required by Part 2.2, sketched
here for continuity): unary (`not`, unary minus) > `to the power of` > `times` /
`divided by` / `modulo` > `plus` / `minus` > comparators > `and` > `or`.

---

*This document is complete. Hand it to the orchestration manager as the working task
brief for the T-Plus-Plus repository, following the staging order in Part 0.6 and the
sub-agent decomposition in Appendix A. Update `docs/BRIEF.md` as work progresses — this
document is a starting plan, not immutable scripture; where reality and this brief diverge,
Part 0.5's precedence rules apply.*

---

# APPENDIX F — IMPLEMENTATION-LEVEL DEEP DIVES

Parts 1–19 specify *what* to build and *why*. This appendix goes one level deeper into
*how* for the pieces most likely to be under-specified in a way that causes real
implementation disagreement between independently-working sub-agents. Treat every
subsection here as binding detail for its referenced Part, not as optional elaboration.

## F.1 Lexer token table (deepens Part 1)

The lexer must recognize the following token categories, each with precise, tested
boundary behavior:

- **Keywords**: reserved words matched case-sensitively (`let`, `be`, `if`, `otherwise`,
  `then`, `end`, `repeat`, `times`, `while`, `for`, `each`, `in`, `define`, `with`, `as`,
  `give`, `back`, `try`, `handle`, `finally`, `throw`, `use`, `export`, `match`, `when`,
  `test`, `expect`, `about`, `before`, `after`, `and`, `or`, `not`, `is`, `plus`, `minus`,
  `times` (overloaded with the loop keyword — the parser, not the lexer, must
  disambiguate via context, since `times` means "multiplication" in `a times b` but
  "repeat count unit" in `repeat 5 times`; this ambiguity must be resolved by grammar
  position, not by the lexer guessing, and needs an explicit test case exercising both
  uses in one file to prove the disambiguation is genuinely context-sensitive and correct).
- **Identifiers**: must support multi-word natural identifiers where the grammar allows
  possessive/prepositional phrasing (`the count`, `a Task`) without those becoming
  ambiguous with keyword sequences — the lexer should NOT try to tokenize `the count` as a
  single identifier token; instead, the *parser* recognizes certain keyword-plus-identifier
  sequences as idiomatic phrases at the grammar level. This keeps the lexer simple
  (standard single-word identifier tokenization) and pushes the natural-phrase recognition
  entirely into the parser grammar (F.2), which is the more maintainable split and avoids
  lexer/parser layering violations.
- **Literals**: integer (`42`), float (`3.14`), string (double-quoted, with `{expr}`
  interpolation per Part 2.3 requiring the lexer to track interpolation-brace nesting
  depth so a literal `{` inside a string that isn't meant as interpolation can still be
  escaped — define the escape sequence explicitly, e.g. `\{` for a literal brace), boolean
  (`true`, `false`), `nothing`.
- **Comments**: a single-line comment marker (recommend `#`, matching the Python-adjacent
  ecosystem this ships alongside, for muscle-memory familiarity) and, separately, whether a
  block-comment form is needed — decide and document; do not leave comment syntax
  undefined this late in a language's life.
- **Whitespace/newline significance**: explicitly decide whether T++ is
  whitespace-significant (Python-style indentation-as-structure) or whether the `end`
  keyword makes indentation purely cosmetic (Ruby/Ada-style, matching every example shown
  throughout this brief, which consistently uses explicit `end` markers) — the examples
  throughout this document assume the latter (indentation is for human readability only,
  `end` is what actually closes a block), and this must be the confirmed, documented,
  tested behavior: a `.tpp` file with "wrong" indentation but correct `end` placement must
  parse and run identically to a "correctly" indented version, verified by an explicit test
  pair.

## F.2 Parser: precedence climbing vs. Pratt parsing (deepens Part 2.2)

For the expression grammar's precedence handling (Appendix E's precedence table),
recommend a Pratt parser (operator-precedence parser using per-operator binding powers)
over a naive precedence-climbing recursive-descent cascade with one function per
precedence level. Justification: Pratt parsing scales much better as the natural-language
operator vocabulary grows (each new natural comparator phrase like `is at least` is a new
token with a binding power, not a new grammar production requiring a new recursive-descent
function), and it's the more maintainable choice given Part 1.9's requirement that the
operator/synonym table keeps growing over the platform's life as plugins (Part 6.4's
lexer/keyword hooks) register new synonym forms — a Pratt parser's table-driven nature
means a plugin-registered operator synonym can be added by inserting a table entry with a
binding power, not by modifying parser control flow. Document this choice as an ADR.

## F.3 Semantic analyzer pass ordering (deepens Parts 3, 4.4, 10)

The semantic analysis phase must run as a sequence of clearly separated sub-passes, not one
monolithic tree walk doing everything at once — this matters because Part 4.4's
scope-resolution optimization, Part 3's type inference, and Part 10's import resolution
all need well-defined inputs/outputs from each other:

1. **Import resolution** (Part 10): resolve every `use`/`export` statement, build the
   module dependency graph, detect cycles, and produce a fully-resolved symbol table of
   what names are available at each scope *before* anything else runs — every later pass
   depends on knowing what's in scope.
2. **Scope resolution** (Part 4.4): walk the AST, resolving every identifier reference to
   a concrete "N scopes up, slot K" address, using the symbol table from step 1 as the
   starting environment for module-level names.
3. **Type inference/checking** (Part 3): using the scope-resolved AST from step 2, perform
   local type inference and, if strict mode (Part 3.6) is active, type-checking that can
   produce blocking errors.
4. **Diagnostic-producing lint analysis** (Part 7.4/12): unused-variable detection,
   unreachable-code detection, deprecation-usage detection (Part 17.4) — these run last
   since they benefit from having fully-resolved scope and type information available,
   producing higher-quality, less-false-positive-prone diagnostics than if they ran on raw,
   unresolved AST.

Each pass must be independently unit-testable in isolation (feed it a pre-resolved AST
fixture, assert its specific output) rather than only testable end-to-end through the full
pipeline — this is essential for the property-based testing strategy in Part 13.6 to be
tractable, since testing one pass's invariants in isolation is far more tractable than
testing the whole pipeline's combined behavior.

## F.4 Value representation (deepens Part 4.6)

Define, explicitly, the internal Python representation for every T++ runtime value, since
this decision ripples through the evaluator, the JSON interop layer (Part 5.8/8.3), and the
Python-embedding API (Part 11.3):

- T++ number → Python `int` for whole numbers, Python `float` for anything with a
  fractional part or produced by true division (per Part 2.2's division-semantics
  decision) — do not use a custom numeric wrapper class unless a specific documented need
  (e.g. arbitrary-precision decimal support) emerges; prefer native Python numerics for
  performance and natural interop.
- T++ text → Python `str`, always Unicode-correct (per Part 5.4's explicit Unicode testing
  requirement) — never bytes.
- T++ list → a custom `TppList` wrapper around a Python `list`, not a bare Python `list`
  directly — the wrapper exists specifically to intercept mutation for the purposes of
  Part 4.6's environment-sharing/isolation guarantees and to attach T++-level metadata
  (e.g. an element-type hint, if inferred, per Part 3.4) without polluting a raw Python
  list's identity.
- T++ record → a custom `TppRecord` wrapper (ordered-field-preserving, since field
  declaration order likely matters for both `match` destructuring per Part 2.6 and for
  natural, predictable JSON serialization per Part 5.8) — not a bare Python `dict`, for
  the same interception/metadata reasons as `TppList`.
- T++ function/closure → a custom `TppFunction` wrapping the AST node plus captured
  environment reference, callable from Python interop (Part 11.2's callback-shim
  requirement) via a defined `__call__`-equivalent protocol.
- `nothing` → a true Python singleton (`TppNothing`, a single shared instance, checked via
  identity, analogous to Python's own `None` singleton pattern) — never represented as
  Python `None` directly, so that the interop boundary (Part 11) has an unambiguous,
  explicit translation rule for `nothing` rather than accidentally colliding with however
  Python's own `None` might separately need to be represented when crossing the boundary.

## F.5 Error-recovery synchronization points (deepens Part 12.2's parser error recovery
requirement)

For the parser to recover after a syntax error and keep finding further real errors in one
pass (required by Part 12.2), it needs defined synchronization points to resume parsing
from after discarding the malformed region. Recommend synchronizing at: the next `end`
keyword at the same or a shallower nesting depth than where the error occurred, or the
next statement-starting keyword (`let`, `if`, `for`, `define`, `try`, etc.) at the current
block's nesting depth, whichever comes first in the remaining token stream. This must be
implemented as a genuinely tested capability (per Part 12.7's explicit three-independent-
errors-in-one-file test requirement), not left as a vague "the parser tries to recover"
aspiration.

## F.6 Type-compatibility matrix (deepens Part 3.5)

For runtime-enforced type checking (when `enforce_types: true`, Part 3.5) to produce
correct, non-surprising behavior, define an explicit compatibility matrix rather than
leaving "is this value compatible with that annotation" as an implicit, ad hoc check:

- A Python-native `int` value is compatible with both `a whole number` and `a number`
  annotations; a `float` value is compatible with `a number` but NOT with `a whole number`
  (no silent narrowing) — a `float` that happens to have no fractional part (e.g. `4.0`) is
  still NOT compatible with `a whole number` under strict enforcement, since silently
  treating `4.0` as satisfying a whole-number annotation reintroduces exactly the kind of
  surprising, non-predictable behavior the "predictable execution" thesis exists to avoid;
  document this explicitly as a deliberate strictness choice, with a clear diagnostic
  message (per Part 12.2) explaining *why* `4.0` doesn't satisfy `a whole number` when a
  user hits this.
- `nothing` is compatible with any annotation explicitly unioned with `nothing`
  (`a number or nothing`) and with NO annotation that doesn't include that union — a bare
  `a number` annotation does NOT implicitly accept `nothing`, again favoring explicitness
  over convenience per the same predictability principle.
- A `TppRecord` value is compatible with a user-defined composite type annotation (Part
  3.3) only if it was constructed via that type's `define a <TypeName> as ... with ...`
  constructor form — a structurally-identical-but-differently-named record is NOT
  compatible (nominal typing, not structural typing, for user-defined types) — document
  this choice explicitly as an ADR, since structural vs. nominal typing is a genuine,
  consequential design fork and the recommendation here (nominal) should be treated as a
  strong default suggestion for the implementing agent to confirm or override with
  documented reasoning, not as an unquestionable final decision already fully settled by
  this brief.

## F.7 Plugin transform-hook conflict resolution (deepens Part 6.4)

When multiple installed plugins register AST-transform hooks (Part 6.4) that could apply
to overlapping AST regions, the deterministic conflict-detection/ordering algorithm must
be:

1. Transform hooks declare, in their manifest (Part 6.2), which AST node *types* they
   transform (not arbitrary "anything"), and this declaration is checked at plugin-install
   time.
2. If two enabled plugins both declare transforms targeting the same node type, `tpp
   plugin install` (for the second-installed plugin) must surface an explicit warning
   naming both plugins and the conflicting node type, requiring explicit user confirmation
   before proceeding (extending the same permission-confirmation UX pattern already
   required by Part 6.5).
3. If the user confirms and proceeds with both installed, transforms execute in
   plugin-installation order (first-installed transforms first) — this ordering must be
   documented, queryable (`tpp plugin list` per Part 6.3 should show transform-application
   order for any node type with multiple registered transforms), and stable/reproducible
   across runs, never nondeterministic.

## F.8 Resource-limit enforcement mechanism specifics (deepens Parts 1.4, 8.3, 15.3)

"Execution time limit" and "max iteration guard" need one concrete, shared enforcement
mechanism, not per-feature reimplementation:

- Implement a single, central `ExecutionBudget` object threaded through the evaluator's
  main dispatch loop, checked at a bounded, cheap interval (e.g. every N evaluated AST
  nodes, N tuned via the Part 4.2 benchmark suite to balance overhead against
  responsiveness — checking every single node dispatch may be too much overhead; checking
  only every hundred loop iterations may let a tight, node-cheap infinite loop run far
  longer than intended before being caught) rather than via OS-level wall-clock
  signal-based interruption (which is notoriously fragile to get right safely inside a
  Python interpreter loop, particularly around interaction with any Python-interop calls
  in flight per Part 4.7/11.2 — an OS signal arriving mid-way through a Python-interop call
  can leave host-side state in an inconsistent condition). Wall-clock time IS still checked
  as part of what trips the budget (not just a raw node-count ceiling, since node cost
  varies enormously by construct), but the *checking* happens cooperatively inside the
  evaluator's own loop, not via asynchronous interruption.
- When a budget is exceeded, the evaluator raises a specific, catchable-in-principle (but
  not intended to be silently swallowed by user `try`/`handle` in the CLI/API default
  configuration — document this nuance explicitly: should a script be able to `handle` its
  own resource-exhaustion error and keep running indefinitely by re-entering another
  expensive operation? Recommend: no — a budget-exceeded error is a special, non-`handle`-
  able termination signal distinct from the normal user-facing exception hierarchy from
  Part 12.4, analogous to how some languages treat true OOM/stack-overflow conditions as
  unrecoverable rather than catchable, precisely to prevent a malicious or buggy script
  from using its own error handling to defeat the resource limit meant to protect the
  host) `ExecutionBudgetExceeded` termination.

## F.9 CLI argument-parsing conventions (deepens Part 7.9)

To keep the growing CLI surface (Part 7) consistent, establish these conventions
explicitly rather than letting each new subcommand's flags be designed independently and
inconsistently by whichever agent implements it:

- Boolean flags always have both a long form (`--watch`) and, for genuinely
  frequently-used ones only (not every flag), a short form (`-w`) — do not assign short
  forms casually to every flag, since short-form letters are a scarce, easily-exhausted
  namespace and collisions across subcommands create real confusion.
- Every subcommand accepting a target path defaults sensibly (current directory /
  conventional entry-point file per Part 10.3's project-layout convention) when the path
  argument is omitted, rather than requiring it explicitly in the common case.
- Output-format flags are always spelled `--format <name>` (never `--output-format`,
  `--fmt`, or any other variant) wherever a command supports multiple output
  representations (human/JSON/etc.), per Part 7.9's explicit consistency requirement — this
  subsection exists specifically to give that requirement a single, named, canonical flag
  spelling so every implementing agent converges on it rather than each guessing
  independently.

---

*End of Appendix F. This is the deepest level of implementation guidance this brief
provides; anything genuinely still ambiguous after F.1–F.9 should become a documented ADR
(Part 0.8) rather than an unstated implementation guess.*
