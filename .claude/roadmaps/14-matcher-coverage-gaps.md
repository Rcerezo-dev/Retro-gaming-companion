# Roadmap 14 — `fix/matcher-coverage-gaps`

**Rama:** `fix/matcher-coverage-gaps`
**Base:** `develop`
**Prioridad:** 🟡 P3 — no bloquea nada activo, es cobertura incompleta ya documentada y acotada, no un bug de comportamiento incorrecto
**Esfuerzo estimado:** S-M (~2-4 h, casi todo en `catalog/matcher.py`)
**Riesgo:** Bajo-medio — `MATCH-FIX-3` requiere una decisión de política del usuario antes de tocar código (puede dejar más archivos "sin match" a propósito)

---

## Origen

Dos huecos de cobertura distintos del matcher, ambos en `catalog/matcher.py`,
ambos ya investigados a fondo:

### 1. `MATCH-FIX-3` (2026-09-12) — SHA1 real sin entrada en catálogo

947 archivos (`.zip` 696, `.nes` 141, `.gbc` 57, `.gb` 53) tienen SHA1 ya
calculado correctamente (no es un problema de hash) pero ese SHA1 real no
existe en los catálogos No-Intro/Redump (hacks, traducciones, romsets no
oficiales) — `_match_by_title()` (`catalog/matcher.py:233-262`) cae al
fallback por título y colisiona con un homónimo real de forma tan errónea
como si el archivo siguiera sin descomprimir. El cuello de botella es
cobertura de catálogo, no formato de archivo.

**🔴 Decisión pendiente del usuario, sin la cual no se debe tocar código**:
¿dejar estos 947 archivos sin match (mejor que un match falso) en vez de
asignarles el `canonical_title` de otro juego homónimo? Necesitaría una señal
más fuerte que título+extensión — candidatos: tamaño de archivo como filtro
adicional, o negarse a resolver el fallback por título cuando hay ambigüedad
real y el SHA1 no está en catálogo (en vez de devolver `hits[0]` a ciegas
como hoy).

### 2. `MATCH-HEADER-1` (2026-09-12) — follow-ups no implementados

`MATCH-HEADER-1` (ya ✅ implementado y en producción: identidad por header
interno NDS/GBA vía `detection/rom_header.py::extract_internal_id`, 15 grupos
nuevos de duplicados rescatados en la biblioteca real) dejó dos extensiones
documentadas como no implementadas:

- **Extender a GB/GBC** con una señal más fuerte que el título truncado del
  header (16 caracteres en offset `0x134`, insuficiente por sí solo — puede
  truncar el texto que distingue dos juegos reales, por eso se dejó fuera
  deliberadamente del primer roadmap).
- **Usar el tamaño esperado del DAT como desempate de calidad de dump** en
  `_review_entry_sort_key` (`web/builders/duplicates.py`) — hoy el desempate
  no considera si un archivo tiene el tamaño exacto que el catálogo espera
  para esa entrada.

(El follow-up "investigar por qué 2 filas GBA tenían platform incorrecto" ya
se resolvió como `MDFOLDER-FIX-1`/`MDFOLDER-FIX-2` — no entra en este
roadmap.)

---

## Objetivo

1. **`MATCH-FIX-3`**: implementar la política que decida el usuario (ver
   Paso 1 — este roadmap NO prescribe la respuesta, solo dónde va el código
   una vez decidida).
2. **GB/GBC header matching**: diseñar una señal de identidad más fiable que
   el título truncado antes de replicar el patrón de `MATCH-HEADER-1`.
3. **Desempate por tamaño de DAT**: añadir el tamaño esperado como criterio
   en `_review_entry_sort_key`.

---

## Pasos

### Paso 1 — Decisión de política para `MATCH-FIX-3` (bloqueante, no de código)

Antes de escribir nada: confirmar con el usuario qué política aplicar a los
947 archivos. Opciones ya identificadas en el hallazgo original:
(a) dejar sin match si hay ambigüedad real de título y el SHA1 no calza con
ningún candidato — más conservador, más archivos quedan "pendientes" en vez
de con un `canonical_title` potencialmente incorrecto;
(b) usar el tamaño de archivo como señal adicional de desambiguación cuando
hay varios candidatos de título igual;
(c) alguna combinación de ambas.
Sin esta decisión explícita, no tocar `_match_by_title()` para este caso —
mismo criterio que ya se siguió el 2026-09-12 (`Tareas/diario/Día61.md`).

### Paso 2 — Implementar la política decidida

`catalog/matcher.py:233-262` (`_match_by_title`). El cambio exacto depende
del Paso 1 — como guía, si se opta por (a): cuando `candidates` tiene más de
1 hit tras el filtro por plataforma/extensión Y el SHA1 del archivo no
coincide con ninguno, devolver `None`/confianza `low` explícita en vez de
`candidates[0]`. Re-lanzar `match` con `include_low_confidence: true` sobre
las plataformas afectadas tras el cambio (mismo patrón ya usado en
`MATCH-FIX-5`) para medir el impacto real antes de darlo por cerrado.

### Paso 3 — Señal de identidad GB/GBC

Investigar alternativas al título truncado de 16 caracteres del header
(`0x134`): ¿el checksum interno de la cabecera GB/GBC (offset `0x14D`,
verificación de integridad estándar del cartucho) combinado con el título
truncado reduce lo suficiente el riesgo de falso positivo? Documentar la
señal elegida y su tasa de colisión esperada antes de implementar — mismo
cuidado que ya se tuvo con GBA (`0xB2 == 0x96` como validación adicional del
byte fijo antes de confiar en el código de 4 caracteres).

### Paso 4 — Desempate por tamaño de DAT

`_review_entry_sort_key` (`web/builders/duplicates.py:153-187`): añadir un
nuevo nivel de comparación (tamaño real del archivo vs. tamaño esperado por
la entrada de catálogo, si el DAT lo expone) en la cadena de desempate
existente (`integrity_tier > ra_tier > folder_tier > lang_tier > filename`) —
decidir en qué punto de la cadena entra (probablemente tras `integrity_tier`,
antes de `ra_tier`, ya que un dump del tamaño correcto es una señal de
integridad más).

### Paso 5 — Tests

- `MATCH-FIX-3`: caso con SHA1 real sin catálogo + 2 candidatos homónimos →
  comportamiento según la política decidida (sin match, o desambiguado por
  tamaño).
- GB/GBC: caso con título truncado idéntico entre 2 juegos reales distintos
  → no se fusionan si el checksum de header difiere.
- Desempate por tamaño: 2 candidatos, uno con el tamaño exacto del DAT y otro
  no → gana el de tamaño correcto en el orden de recomendación.

### Paso 6 — Verificación

```bash
python -m pytest tests/ -q
ruff check src/rom_manager/catalog/matcher.py src/rom_manager/web/builders/duplicates.py src/rom_manager/detection/rom_header.py
```

---

## Fuera de alcance

- Extender el header matching a otras plataformas más allá de GB/GBC (NDS/GBA
  ya cubiertos por `MATCH-HEADER-1`).
- Cualquier cambio al mecanismo de `resolve-duplicates`/`apply_ra_conflicts`
  en sí — este roadmap solo toca la señal de desambiguación de `matcher.py` y
  el desempate de `_review_entry_sort_key`.

---

## Checklist

- [ ] Paso 1 — decisión de política confirmada por el usuario (`MATCH-FIX-3`)
- [ ] Paso 2 — política implementada y medida contra la biblioteca real
- [ ] Paso 3 — señal de identidad GB/GBC diseñada e implementada
- [ ] Paso 4 — desempate por tamaño de DAT
- [ ] Paso 5 — tests nuevos
- [ ] Paso 6 — suite completa + ruff limpios
- [ ] Commit en rama, PR a `develop` — pendiente, requiere confirmación explícita del usuario
