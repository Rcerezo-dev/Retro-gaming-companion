# Frontend Refactor

> Part of the broader refactor effort. See [refactor-plan.md](./refactor-plan.md) for context.
> Review started: 2026-03-30.

---

## What the frontend is

A single-page app served at `http://127.0.0.1:7777` by a Python HTTP server.
No framework, no build step — vanilla JS and HTML served as plain files.

The UI has a fixed layout: a sidebar with navigation and a main content area
where one tab is visible at a time.

---

## How it is served

- `GET /` → returns `index.html` (read into memory at server startup via `frontend.py`)
- `GET /static/*` → reads files from disk on each request
- `frontend.py` is a 9-line file whose only job is to pre-read `index.html` into a variable.
  It exists for historical reasons and adds no value. It should be removed.

The app can also be compiled into a Windows `.exe` via PyInstaller, which changes the
static file path internally. The server handles this with a `_MEIPASS` check.

---

## Current state

### File structure

```
static/
  index.html        — 2587 lines. Contains ALL 14 views + 3 overlays.
  app.css           — 1061 lines. Global styles.
  app.js            — 4562 lines. Original monolithic JS. Still loaded.
  js/
    main.js         — Module entry point. Imports from all migrated modules
                      and dumps everything onto window.
    api.js          — Centralized fetch wrapper.
    jobs.js         — Background job polling logic.
    components/
      toast.js      — Toast notification component.
      modal.js      — Confirm dialog component.
    tabs/
      config.js     — Settings tab.
      scan.js       — Scan tab.
      collection.js — Collection tab.
      duplicates.js — Duplicates tab.
      organize.js   — Organize/plan tab.
      sync.js       — Cloud sync, cable sync, and Anbernic tabs (all in one file).
```

### Views (tabs)

| Tab | ID | JS module | Status |
|---|---|---|---|
| Overview (dashboard) | `tab-overview` | — | Not migrated |
| Games | `tab-games` | — | Not migrated |
| Organize | `tab-plan` | `tabs/organize.js` | Migrated |
| Duplicates | `tab-duplicates` | `tabs/duplicates.js` | Migrated |
| Assets | `tab-assets` | — | Not migrated |
| Collection | `tab-collection` | `tabs/collection.js` | Migrated |
| Cloud sync | `tab-sync` | `tabs/sync.js` | Migrated |
| Cable sync | `tab-cable` | `tabs/sync.js` | Migrated (same file as cloud) |
| Anbernic | `tab-anbernic` | `tabs/sync.js` | Migrated (same file as cloud) |
| Tools | `tab-tools` | — | Not migrated |
| Formats | `tab-formats` | — | Not migrated |
| Scraper | `tab-scraper` | — | Not migrated |
| Inbox | `tab-inbox` | — | Not migrated |
| Settings | `tab-settings` | `tabs/config.js` | Migrated |
| (ghost) | `tab-tv` | — | No nav button. Abandoned. |

### Overlays in index.html

- Setup wizard modal (shown on first run, 3 internal pages)
- Confirm dialog modal
- Android detection panel (shown when accessed from an Android browser)

---

## Problems identified

### 1. No routing
`showTab()` toggles CSS classes — there are no URL changes, no browser history,
no deep linking, no bookmarkable views. The browser back button does nothing.

### 2. Everything in one HTML file
2587 lines across 14 views, 3 overlays, a header, and a sidebar.
Every view is in the DOM at all times, just hidden.

### 3. Mid-migration JS — two systems loaded in parallel
`index.html` loads both:
```html
<script type="module" src="/static/js/main.js"></script>
<script src="/static/app.js" defer></script>
```
The migrated modules and the old monolith coexist. Risk of duplicate logic and
conflicting state.

### 4. Inline onclick handlers force global scope
Every button in `index.html` uses inline handlers:
```html
<button onclick="doScan()">Scan</button>
```
Inline handlers can only call functions in global scope. This forces `main.js`
to dump every migrated function onto `window`:
```js
Object.assign(window, { doScan, loadSettings, ... }) // ~60 functions
```
This defeats the purpose of ES modules entirely. The encapsulation is fake.

### 5. `frontend.py` is pointless
A 9-line file that reads `index.html` into a string. No logic, no abstraction.
Should be inlined into the server or removed entirely.

### 6. `sync.js` handles three different views
Cloud sync, cable sync, and Anbernic are three separate tabs but share one JS file.
This makes the file large and the concerns mixed.

---

## Decisions made

| Decision | Choice | Ruled out |
|---|---|---|
| Routing model | History API — clean URLs (`/games`, `/sync`) | Hash routing (`/#/games`) |
| Framework | None — vanilla JS ES modules | Preact, Alpine, any CDN framework |
| Build step | None — files served directly | webpack, vite, esbuild |
| HTML structure | One file per view | Keeping everything in `index.html` |
| State management | Hand-rolled observable store + custom browser events | Redux (requires npm), plain mutable singleton |

**State management detail:**

Two complementary mechanisms:

1. **Observable store** (`js/store.js`) — for state that is genuinely global and needs
   to be read by multiple views: active job, connected device, auth status.
   Hand-rolled in ~30 lines, same mental model as Redux but zero dependencies:
   ```js
   // js/store.js
   let _state = { activeJob: null, connectedDevice: null, authStatus: null }
   const _listeners = []
   export const store = {
     get: () => _state,
     dispatch: (action) => {
       _state = reduce(_state, action)
       _listeners.forEach(fn => fn(_state))
     },
     subscribe: (fn) => _listeners.push(fn),
   }
   ```

2. **Custom browser events** — for one-off UI notifications between views that
   don't need persistent state (e.g. a scan completing while you're on a different tab):
   ```js
   // dispatcher
   window.dispatchEvent(new CustomEvent('job:completed', { detail: { job: 'scan' } }))
   // listener in any view
   window.addEventListener('job:completed', (e) => updateDashboard(e.detail))
   ```

Each view owns its own local state. Only truly shared concerns go into the store.

**Required server change for routing:**
The Python server must return `index.html` for any unrecognized path.
In Express terms: `app.get('*', (req, res) => res.sendFile('index.html'))`.
This is a small, targeted change in `server.py`.

---

## What still needs to be decided

- **HTML loading strategy** — fetch each view's HTML on navigation, or bundle into
  `index.html` and show/hide (current approach, but per-file)
- **Inline onclick migration** — how to move from `onclick="fn()"` to `addEventListener`
  without breaking everything at once. Discussed but not yet decided — next topic.
- **Naming conventions** — file names, function names, CSS class names
- **app.js removal** — at what point can the old monolith be deleted safely
- **sync.js split** — cloud sync, cable sync, and Anbernic should be separate modules
- **Ghost tab** — `tab-tv` should be removed if it serves no purpose

---

## Session log

| Date | What was covered |
|---|---|
| 2026-03-30 | Full frontend audit. Identified 14 views, 3 overlays, mid-migration state, routing absence, inline onclick problem. Made decisions on routing, framework, build step, HTML structure, state management. Next: inline onclick migration strategy. |
