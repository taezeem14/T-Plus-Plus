# ADR 0001: Adoption of Antigravity 2.0 Master Upgrade Brief

## Status
Accepted

## Context
T++ (`tpp-language` on PyPI, version 3.1.3) requires a comprehensive platform expansion, hardening, and quality upgrade across language surface, type system, runtime performance, standard library, plugins, tooling, modules, error diagnostics, testing, security, and developer experience.

The single source of truth for this platform upgrade is defined in `tpp_antigravity_upgrade_brief.md`, persisted as `docs/BRIEF.md`.

## Decision
1. We adopt `tpp_antigravity_upgrade_brief.md` as the working specification and execution roadmap for all future platform upgrades.
2. Execution follows the 5-stage dependency graph defined in Part 0.6:
   - **Stage A (Foundations)**: Part 12 (Diagnostics), Part 3.1–3.3 (Core Types), Part 10.1–10.3 (Core Modules).
   - **Stage B (Core Subsystems)**: Parts 1 & 2 (Language Surface), Part 4 (Runtime & Performance), Part 5 (Standard Library), Part 6 (Plugins), Part 11 (Interop).
   - **Stage C (Tooling)**: Part 7 (CLI), Part 8 (API & Web IDE), Part 9 (LSP), Part 13 (Testing Infra).
   - **Stage D (Platform-Wide)**: Part 14 (Docs), Part 15 (Security), Part 16 (DX), Part 17 (Versioning & Deprecation), Part 18 (Governance).
   - **Stage E (Shipping Gate)**: Part 19 (Validation Gate).
3. Zero breaking changes to existing 3.1.3 syntax, CLI flags, and API contracts.

## Consequences
- All subsequent additions are purely additive or opt-in.
- Diagnostics, type representations, and module import resolutions are established as the foundational tier for the rest of the language.
