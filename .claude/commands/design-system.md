# Design System Integration Guide

## Context

Design system integrated (DESIGN-1 to 9 ✅ completados en sesión 2026-04-28).

- **Design assets**: `docs/design/ui_kits/retrovault/` (React prototype para referencia)
- **CSS tokens**: `docs/design/colors_and_type.css` (source of truth)
- **Preview components**: `docs/design/preview/` (16 HTML de referencia)
- **Icons**: Lucide CDN (`https://unpkg.com/lucide@latest/dist/umd/lucide.min.js`)
- **Target**: Vanilla JS frontend at `src/rom_manager/web/static/`

**Key insight**: Existing `app.css` already has extensive cyberpunk styling (glitch animations, neon glows, sharp corners). We **added** design tokens + Lucide icons, not replacing the existing aesthetic.

**Fases pendientes**: DESIGN-10 a 14 (Phase 3 — polish, opcional).

---

## Phase 1: CSS Tokens + Fonts

### Step 1.1: Add `--rv-*` variables to app.css

**Location**: `src/rom_manager/web/static/app.css` (after line 36, after existing `:root` block closes)

**Insert new `:root` block** with all `--rv-*` tokens:

```css
:root {
  /* Color aliases — keep backward compat with existing -- vars */
  --rv-bg:         var(--bg);
  --rv-bg-panel:   var(--bg-panel);
  --rv-bg-nav:     var(--bg-nav);
  --rv-bg-alt:     var(--bg-alt);
  --rv-bg-subtle:  var(--bg-subtle);
  --rv-bg-deep:    var(--bg-deep);
  --rv-bg-input:   var(--bg-input);
  --rv-bg-surface: var(--bg-surface);
  --rv-bg-cover:   var(--bg-cover);
  --rv-bg-track:   var(--bg-track);
  --rv-border:     var(--border);
  --rv-border-s:   var(--border-s);
  --rv-border-i:   var(--border-i);
  --rv-border-row: var(--border-row);
  --rv-fg:   var(--fg);
  --rv-fg-2: var(--fg-2);
  --rv-fg-3: var(--fg-3);
  --rv-fg-4: var(--fg-4);
  --rv-fg-5: var(--fg-5);
  --rv-accent:     var(--accent);
  --rv-accent-h:   var(--accent-h);
  --rv-accent-blue: var(--accent-blue);
  --rv-accent-pur: var(--accent-pur);
  --rv-accent-red: var(--accent-red);
  --rv-accent-grn: var(--accent-grn);
  --rv-accent-ora: var(--accent-ora);
  --rv-accent-cyn: var(--accent-cyn);
  --rv-on-accent:  var(--on-accent);
  --rv-modal-bg:   var(--modal-bg);
  --rv-overlay-bg: var(--overlay-bg);
  --rv-shadow-glow: var(--shadow);

  /* Typography */
  --rv-font-mono:    'Space Mono', 'Consolas', 'Courier New', monospace;
  --rv-font-display: 'Exo 2', 'Segoe UI', system-ui, sans-serif;
  --rv-font-body:    'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;

  --rv-text-xs:   10px;
  --rv-text-sm:   11px;
  --rv-text-base: 13px;
  --rv-text-md:   14px;
  --rv-text-lg:   16px;
  --rv-text-xl:   20px;
  --rv-text-2xl:  22px;
  --rv-text-3xl:  28px;

  --rv-weight-normal: 400;
  --rv-weight-medium: 500;
  --rv-weight-semibold: 600;
  --rv-weight-bold: 700;

  --rv-tracking-tight: 0;
  --rv-tracking-normal: 0.5px;
  --rv-tracking-wide: 1px;
  --rv-tracking-wider: 1.5px;
  --rv-tracking-brand: 5px;

  --rv-leading-tight: 1.2;
  --rv-leading-normal: 1.5;
  --rv-leading-relaxed: 1.75;

  /* Spacing (4px grid) */
  --rv-space-1:  4px;
  --rv-space-2:  8px;
  --rv-space-3:  12px;
  --rv-space-4:  16px;
  --rv-space-5:  20px;
  --rv-space-6:  24px;
  --rv-space-8:  32px;
  --rv-space-10: 40px;
  --rv-space-12: 48px;

  /* Border radius */
  --rv-radius-sharp: 2px;
  --rv-radius-sm:    4px;
  --rv-radius-md:    6px;
  --rv-radius-lg:    8px;
  --rv-radius-xl:    10px;
  --rv-radius-pill:  20px;
  --rv-radius-full:  50%;

  /* Shadows & glows */
  --rv-glow-sm:   0 0 8px  rgba(0, 229, 255, .3);
  --rv-glow-md:   0 0 14px rgba(0, 229, 255, .4);
  --rv-glow-lg:   0 0 28px rgba(0, 229, 255, .25);
  --rv-glow-xl:   0 0 60px rgba(0, 229, 255, .2);
  --rv-glow-red:  0 0 12px rgba(255, 32, 96, .45);
  --rv-glow-blue: 0 0 12px rgba(77, 121, 255, .45);
  --rv-glow-pur:  0 0 12px rgba(200, 0, 255, .4);
  --rv-shadow-panel: 0 8px 24px rgba(0, 0, 0, .6);
  --rv-header-glow: 0 1px 0 var(--accent), 0 0 30px rgba(0, 229, 255, .06);

  /* Transitions */
  --rv-trans-fast:   0.15s ease;
  --rv-trans-normal: 0.25s ease;
  --rv-trans-panel:  0.25s cubic-bezier(.4, 0, .2, 1);
  --rv-trans-tab:    0.18s ease;

  /* Z-index scale */
  --rv-z-content:   1;
  --rv-z-sticky:    10;
  --rv-z-sidebar:   8005;
  --rv-z-panel:     8001;
  --rv-z-overlay:   8000;
  --rv-z-modal:     9100;
  --rv-z-toast:     9999;
  --rv-z-scanlines: 9998;

  /* Special */
  --rv-txt-fav: #f9c74f;
  --rv-progress-grad: linear-gradient(90deg, var(--accent) 0%, var(--accent-pur) 100%);
}
```

### Step 1.2: Add Google Fonts to index.html

**Location**: `src/rom_manager/web/static/index.html` (in `<head>` section)

**Before existing `<link rel="stylesheet" href="/static/app.css">`**, add:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Exo+2:wght@400;500;600;700;800&family=Space+Mono:wght@400;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
```

### Step 1.3: Update body font-family in app.css

**Location**: Line 76 in app.css

**Change from**:
```css
body { background: var(--bg); color: var(--fg); font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif; font-size: 14px; }
```

**Change to**:
```css
body { background: var(--bg); color: var(--fg); font-family: var(--rv-font-body); font-size: 14px; }
```

### Step 1.4: Add Lucide CDN to index.html

**Location**: `src/rom_manager/web/static/index.html` (in `<head>` section, after Google Fonts)

```html
<script src="https://unpkg.com/lucide@latest/dist/umd/lucide.min.js"></script>
```

### Step 1.5: Add header h1 glitch class to index.html

**Location**: Line 13 in `index.html`

**Change from**:
```html
<h1>RETRO VAULT</h1>
```

**Change to**:
```html
<h1 class="rv-brand-glitch">RETRO VAULT</h1>
```

### Step 1.6: Add animations to app.css

**Location**: After line 398 (after existing `@keyframes tab-fade-in`), add:

```css
/* ── RetroVault design system animations ─────────────────────────── */
@keyframes rv-glitch {
  0%, 88%, 100% {
    text-shadow: var(--rv-glow-sm), 0 0 20px var(--accent), 0 0 45px rgba(0,229,255,.35);
    transform: none;
  }
  90% {
    text-shadow: -3px 0 var(--accent-red), 3px 0 var(--accent-pur), var(--rv-glow-sm);
    transform: skewX(-1deg);
  }
  92% {
    text-shadow: 3px 0 var(--accent-red), -3px 0 var(--accent-pur), var(--rv-glow-sm);
    transform: skewX(0.8deg);
  }
  94% {
    text-shadow: var(--rv-glow-sm), 0 0 20px var(--accent);
    transform: none;
  }
}

@keyframes rv-shimmer {
  0%   { background-position: -400px 0; }
  100% { background-position:  400px 0; }
}

@keyframes rv-prog-slide {
  0%   { margin-left: -35%; }
  100% { margin-left: 100%; }
}

@keyframes rv-tab-in {
  from { opacity: 0; transform: translateY(5px); }
  to   { opacity: 1; transform: none; }
}

@keyframes rv-toast-in {
  from { opacity: 0; transform: translateX(20px) scale(.95); }
  to   { opacity: 1; transform: translateX(0) scale(1); }
}

.rv-brand-glitch { animation: rv-glitch 14s infinite; }
.rv-skeleton {
  background: linear-gradient(90deg, #07071f 25%, #0e0e30 50%, #07071f 75%);
  background-size: 400px 100%;
  animation: rv-shimmer 1.4s ease infinite;
  border-radius: var(--rv-radius-sharp);
}
```

---

## Phase 2: Lucide Icons in Navigation

### Step 2.1: Update .nav-icon CSS in app.css

**Location**: Line 130 in app.css

**Change from**:
```css
.nav-icon { font-size: 15px; min-width: 20px; text-align: center; flex-shrink: 0; line-height: 1; }
```

**Change to**:
```css
.nav-icon { 
  display: flex; 
  align-items: center; 
  justify-content: center; 
  min-width: 20px; 
  flex-shrink: 0; 
}
.nav-icon svg { width: 15px; height: 15px; }
```

### Step 2.2: Replace emoji icons in _nav.html

**Location**: `src/rom_manager/web/static/partials/_nav.html`

**Icon mapping**:

| Tab | Current emoji | Lucide icon |
|-----|-------|----------|
| Inicio | 🏠 | `home` |
| Juegos | 🎮 | `gamepad-2` |
| Organizar | 📋 | `layout-list` |
| Duplicados | 🗂 | `copy` |
| Assets | 🖼 | `image` |
| Colección | 🏆 | `star` |
| Cloud | ☁ | `cloud` |
| Cable Sync | 🔌 | `usb` |
| Anbernic | 📱 | `smartphone` |
| Herramientas | 🔧 | `wrench` |
| Formatos | 📀 | `disc` |
| Scraper | 🎨 | `layers` |
| Inbox | 📥 | `inbox` |
| Modo TV | 📺 | `tv` |
| Ajustes | ⚙ | `settings` |

**Replace all `<span class="nav-icon">EMOJI</span>` with `<i data-lucide="ICON" class="nav-icon"></i>`**

Example:
```html
<!-- BEFORE -->
<span class="nav-icon">🏠</span><span class="nav-label">Inicio</span>

<!-- AFTER -->
<i data-lucide="home" class="nav-icon"></i><span class="nav-label">Inicio</span>
```

### Step 2.3: Initialize Lucide icons

**Location**: `src/rom_manager/web/static/partials/_foot.html` (before line 4 where main.js is loaded)

**Add before `<script type="module" src="/static/js/main.js"></script>`**:

```html
<script>
  document.addEventListener('DOMContentLoaded', () => {
    if (window.lucide) {
      lucide.createIcons();
    }
  });
</script>
```

---

## Phase 3: Verification

### Test checklist

- [ ] **Fonts load**: Open DevTools → Sources → verify `fonts.googleapis.com` requests for Exo 2, Space Mono, Inter
- [ ] **Header glitch**: Logo animates with glitch effect every 14s
- [ ] **Nav icons render**: Sidebar expanded shows 15 icons correctly (all should be ~15x15px SVGs)
- [ ] **Nav icons collapse**: Sidebar collapsed, icons still visible (not hidden by overflow)
- [ ] **Lucide on light theme**: Switch to light theme, icons remain visible
- [ ] **No layout break**: No console errors, page responsive

### Quick tests

```bash
# Verify fonts are imported (no 404s)
curl -I https://fonts.googleapis.com/css2?family=Exo+2:wght@400;500;600;700;800

# Check Lucide CDN
curl -I https://unpkg.com/lucide@latest/dist/umd/lucide.min.js
```

---

## Files Modified

| File | Changes |
|------|---------|
| `app.css` | +1 `:root` block (90 lines), +6 animations (50 lines), +1 `.nav-icon` update (5 lines) |
| `index.html` | +2 preconnect/fonts links, +1 Lucide script, +glitch class on h1 |
| `_nav.html` | Replace 15× emoji → Lucide icons (no structure change) |
| `_foot.html` | +1 script for `lucide.createIcons()` |

---

## Rollback plan

If needed:
1. Remove `--rv-*` tokens from app.css (revert `:root` block addition)
2. Remove Google Fonts links from index.html
3. Remove Lucide `<script>` from index.html
4. Revert emoji icons in _nav.html
5. Remove `lucide.createIcons()` from _foot.html

App will fall back to system fonts + emoji icons (existing behavior).

---

## Performance notes

- **Fonts**: ~50KB (Exo 2 subset) + ~30KB (Space Mono) + ~100KB (Inter) = ~180KB total, but heavily cached by Google CDN
- **Lucide**: ~40KB UMD bundle, cached by unpkg
- **No breaking changes**: Existing CSS still works, new tokens just add to the cascade

---

## Reference

- Design system source: `docs/design/colors_and_type.css`
- Preview components: `docs/design/preview/`
- UI kit (React prototype): `docs/design/ui_kits/retrovault/`
- Icon names: https://lucide.dev/
- CLAUDE.md rules: Keep vanilla JS, no React in production, maintain backend compatibility
