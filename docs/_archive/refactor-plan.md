# Retro Vault — Refactor Plan

> This document is the index for the ongoing refactor effort and the primary context
> file for anyone (human or AI) picking this up mid-way.
> Written during a review session on 2026-03-30.

---

## Who is doing this

The original developer built this as one of his first projects, with heavy AI assistance.
The code works, but it lacks architectural consistency and clarity.

The refactor is being led by his partner, a full-stack JavaScript developer with experience
in Domain-Driven Design and event-driven systems. She is not familiar with Python.
The goal is to make the codebase readable, maintainable, and portfolio-worthy —
not to rewrite it from scratch.

**Working style:** conversational and incremental. One area at a time. No big upfront plans.
Decisions are made together before anything is written or changed.

---

## Non-negotiable constraints

These come from the original project philosophy and must be respected:

- No build step — no npm, no webpack, no vite, no bundler
- No external runtime dependencies — Python stdlib only on the backend
- No CDN dependencies — the app must run fully offline on a local machine
- No framework — vanilla JS with ES modules only
- The app can be compiled to a Windows `.exe` via PyInstaller — nothing should break that

---

## Decisions made

### Frontend routing
- **Decision:** History API routing (Option B) — clean URLs like `/games`, `/sync`
- **Ruled out:** Hash routing (`/#/games`) — works but less clean
- **Ruled out:** Any client-side framework (Preact, Alpine, etc.) — CDN dependency, offline risk, unnecessary complexity
- **Required server change:** Python server must return `index.html` for any unrecognized path, so the JS router can take over (same pattern as Express `app.get('*')`)

### Frontend module system
- **Decision:** Native ES modules (`type="module"`) served directly by the Python server
- This is already partially in place — `js/` folder exists, migration was started

---

## Existing refactor work

Before this review, the original developer had already produced a migration plan:
`Tareas/Archivo/Roadmap-Arquitectura-Frontend.md`

That document contains a solid diagnosis of the problems and a phase-by-phase migration plan.
It was partially executed:

- **Phase 0** (infrastructure setup) — complete
- **Phase 1** (backend handler split) — complete
- **Phase 2** (JS module migration, tab by tab) — started, stopped mid-way

**We are not replacing that document.** This refactor folder picks up from where it left off,
adds the architectural decisions that were missing from that plan, and tracks progress going forward.

### Known issue from that plan
The migrated JS modules access leftover global variables from `app.js` via `window._devName` etc.
This is duct tape, not a clean boundary. It needs to be addressed as part of completing the migration.

---

## Areas

| Area | File | Status |
|---|---|---|
| Frontend | [frontend.md](./frontend.md) | In progress — decisions made, migration pending |
| Backend | — | Not started |
| Database layer | — | Not started |
| Sync modules | — | Not started |
