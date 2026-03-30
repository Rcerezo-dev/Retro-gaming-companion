# Propuestas — Recomendador de juegos con NLP

> Análisis de viabilidad para añadir recomendaciones inteligentes a Retro Vault.
> Fecha: 2026-03-30

---

## Fuentes de datos disponibles (sin tocar nada)

| Campo | Tabla | Disponibilidad |
|-------|-------|----------------|
| `description` | `game_metadata` | Solo juegos con scraping hecho |
| `genre` | `game_metadata` | Solo juegos con scraping hecho |
| `year`, `developer`, `publisher`, `rating` | `game_metadata` | Solo juegos con scraping hecho |
| `platform`, `region` | `games` | Todos los juegos |
| `canonical_title` | `games` | Juegos matcheados con DAT |
| `play_status`, `last_played_at` | `games` | Manual/automático según uso |
| `is_favorite` | `games` | Manual |
| `game_tags` | `game_tags` | Manual |

**Cobertura real:** el recomendador solo es útil para juegos con metadata scrapeada.
Recomendado lanzar un scraping masivo antes de activar esta feature.

> **Dato extra disponible pero no persistido:** `genres_list` (lista completa de géneros de ScreenScraper, ej. "RPG, Action RPG, Fantasy") y `players` ("1-2") se calculan durante el scraping pero no se guardan en la BD. Habría que hacer una migración mínima para almacenarlos.

---

## Propuesta A — Smart Filter con scoring (sin ML)

**Complejidad:** ⭐ Baja | **Dependencias:** ninguna | **Coste:** 0€

### Qué hace
Un panel de filtros interactivos donde el usuario marca preferencias:
- Género (RPG, Plataformas, Acción, Puzzle...)
- Era (80s / 90s / 00s / 10s)
- Plataforma
- Nº jugadores (1 / 2+ / multijugador)
- Rating mínimo (filtro ScreenScraper)

Cada juego recibe un score = suma ponderada de coincidencias. Se muestran los 5 mejores.

### Por qué vale la pena
Cubre el 90% del caso de uso ("quiero un RPG de SNES de los 90s") sin ningún modelo.
Funciona aunque la descripción esté vacía — solo necesita `genre`, `year`, `platform`.

### UI sugerida
Panel deslizante lateral o modal "¿Qué quiero jugar hoy?" con checkboxes y un slider de rating. Botón → muestra 5 tarjetas con carátula.

### Lo que hay que hacer
1. Endpoint `GET /api/recommend?genres=RPG&era=90s&platform=snes`
2. Query SQL con `WHERE` dinámico + ORDER BY score
3. Panel de filtros en el frontend (JS vanilla, ~80 líneas)

---

## Propuesta B — Similitud por contenido con TF-IDF

**Complejidad:** ⭐⭐ Media | **Dependencias:** `scikit-learn` (o numpy puro) | **Coste:** 0€

### Qué hace
"Juegos similares a este" — dado un juego, encuentra los 5 más parecidos por contenido textual.

Técnica:
1. Concatenar `description + genre + developer + canonical_title` para cada juego
2. Construir matriz TF-IDF (o CountVectorizer)
3. Cosine similarity entre el juego seleccionado y el resto
4. Top 5 por similitud

### Por qué vale la pena
Funciona completamente offline, no necesita red. La matriz TF-IDF se puede precalcular y cachear en disco (`.pkl`) — reconstruir solo cuando hay nuevos juegos scrapeados. Es la técnica más clásica y predecible: fácil de depurar.

### Limitaciones
- Solo tan bueno como las descripciones de ScreenScraper (en inglés o español según config)
- Requiere sklearn (`pip install scikit-learn`) o implementación manual con numpy

### UI sugerida
Botón "Juegos similares ↗" en el detalle de cada juego. Al pulsar, muestra 5 tarjetas debajo con carátula y porcentaje de similitud.

### Lo que hay que hacer
1. `src/rom_manager/recommender/tfidf_recommender.py` — clase `TFIDFRecommender`
2. Endpoint `GET /api/recommend/similar/{game_id}`
3. Caché de la matriz en `.rommgr/recommender_cache.pkl`
4. Botón en la ficha de juego (frontend)

---

## Propuesta C — Perfil de usuario desde señales manuales

**Complejidad:** ⭐⭐ Media | **Dependencias:** ninguna (o numpy) | **Coste:** 0€

### ⚠️ Limitación real — no hay tracking automático
No existe integración con RetroArch, detección de proceso, ni medición de tiempo de juego.
`last_played_at` se rellena indirectamente del `mtime` del archivo `.sav` al escanear — es un proxy poco fiable.

**Las únicas señales disponibles son las que el usuario marca a mano:**

| Señal | Fiabilidad | Condición |
|-------|-----------|-----------|
| `is_favorite` | Alta | Solo si el usuario la usa |
| `play_status` (playing/completed/dropped) | Alta | Solo si el usuario la usa |
| `game_tags` (etiquetas libres) | Alta | Solo si el usuario las usa |
| `last_played_at` (mtime del .sav) | Baja | Proxy, no siempre actualiza |

### Qué hace (cuando hay datos)
"Recomendado para ti" basado en favoritos y juegos completados.

Lógica:
1. Tomar todos los juegos con `is_favorite=1` o `play_status IN ('completed','playing')`
2. Construir perfil: géneros más frecuentes, era preferida, plataformas más usadas
3. Puntuar el resto de la biblioteca contra ese perfil
4. Top 5 juegos no jugados con mayor afinidad

Se puede combinar con la Propuesta B: perfil = centroide de los vectores TF-IDF de los favoritos. Los juegos más cercanos = recomendaciones.

### Por qué vale la pena (con matices)
Funciona bien si el usuario tiene el hábito de marcar favoritos/completados. **Si la colección está vacía de esos datos, no hay perfil que construir** — la sección directamente no aparece.

### UI sugerida
Sección "Recomendado para ti" en el dashboard. Se muestra **solo si hay ≥3 favoritos o juegos con play_status definido**. Si no, se muestra un CTA: "Marca tus favoritos para obtener recomendaciones personalizadas".

---

## Propuesta D — Embeddings locales con Sentence Transformers

**Complejidad:** ⭐⭐⭐ Alta | **Dependencias:** `sentence-transformers`, `numpy` | **Coste:** 0€

### Qué hace
Embeddings semánticos de alta calidad para las descripciones de juego. Permite consultas en lenguaje natural como:
- "un juego de exploración con historia oscura"
- "algo rápido para jugar 10 minutos"
- "como Zelda pero más difícil"

Técnica:
1. Modelo recomendado: `all-MiniLM-L6-v2` (22 MB, muy rápido en CPU, 384 dimensiones)
2. Embeds de `description + genre + title` → vector por juego
3. Query del usuario → embed → cosine similarity → top 5
4. Embeddings precalculados y guardados en `.npy` o en una tabla SQLite (`BLOB`)

### Por qué vale la pena
Es el salto cualitativo real. TF-IDF no entiende que "RPG de mazmorra" y "dungeon crawler" son lo mismo. Los embeddings sí. Permite el chatbot semántico del que hablas.

### Limitaciones
- Descarga única del modelo (~22 MB desde HuggingFace)
- Requiere romper la regla de "sin dependencias externas" — solo para esta feature opcional
- Precalcular embeddings para 1000 juegos tarda ~5s en CPU moderno

### UI sugerida
Barra de búsqueda semántica global: "¿Qué quieres jugar?" → input libre → 5 resultados con carátula y descripción. Separado del filtro normal.

### Lo que hay que hacer (tú manejas el modelo)
1. `src/rom_manager/recommender/embedding_recommender.py`
2. Job en background para calcular/actualizar embeddings tras scraping
3. Endpoint `POST /api/recommend/semantic` con `{"query": "..."}`
4. Barra de búsqueda en frontend

---

## Propuesta E — Chatbot con Claude API

**Complejidad:** ⭐⭐ Media | **Dependencias:** `anthropic` SDK | **Coste:** ~$0.001/consulta (Haiku)

### Qué hace
El usuario escribe en lenguaje natural lo que quiere. La app serializa los metadatos de la colección (JSON compacto) y pregunta a Claude API qué recomienda.

Ejemplo de prompt al modelo:
```
Tengo esta colección de juegos retro: [JSON con título, género, año, plataforma, descripción corta].
El usuario quiere: "algo relajante para jugar antes de dormir, sin demasiada acción".
Recomiéndame 5 juegos con una frase de explicación para cada uno.
```

### Por qué vale la pena
La UX más natural posible. Claude entiende contexto, matices, humor ("quiero algo que no me haga llorar como Final Fantasy VII"). No necesita embeddings ni precálculo.

### Limitaciones
- Requiere API key de Anthropic (el usuario ya tiene conocimiento de esto)
- Coste mínimo pero no cero (~$0.001/consulta con claude-haiku-4-5)
- Con colecciones grandes (>500 juegos), el JSON de metadatos ocupa tokens → conviene pasar solo los campos clave (title, genre, year, platform)
- Depende de red

### UI sugerida
Modal "Pregunta al Vault" con un textarea libre. El resultado muestra 5 tarjetas con carátula, título, plataforma y la frase de explicación que generó Claude.

### Lo que hay que hacer
1. `src/rom_manager/recommender/claude_recommender.py` — usa `anthropic` SDK
2. Serializar colección: `SELECT title, genre, year, platform FROM games JOIN game_metadata`
3. Endpoint `POST /api/recommend/chat` con `{"query": "..."}`
4. Modal en frontend

---

## Resumen comparativo

| Propuesta | Coste | Offline | Calidad | Dificultad total | Quién hace el modelo |
|-----------|-------|---------|---------|-----------------|----------------------|
| A — Smart Filter | 0€ | ✅ | ⭐⭐ | Baja | N/A |
| B — TF-IDF | 0€ | ✅ | ⭐⭐⭐ | Media | Tú |
| C — Perfil historial | 0€ | ✅ | ⭐⭐⭐ | Media | N/A |
| D — Embeddings locales | 0€ | ✅ | ⭐⭐⭐⭐⭐ | Alta | Tú |
| E — Claude API chatbot | ~$0/mes | ❌ | ⭐⭐⭐⭐⭐ | Media | N/A |

---

## Recomendación de implementación

**Mínimo valioso (1 sesión):** Propuesta A + C
— Smart Filter + perfil de historial. 0 dependencias nuevas, UI inmediata, útil desde el primer día.

**Feature completa (2-3 sesiones):** A + B + C
— Añade "Juegos similares" en la ficha. Requiere sklearn pero es el flujo más natural para un usuario.

**El salto cualitativo (sesión dedicada, tú llevas el modelo):** D
— Búsqueda semántica libre. Requiere sentence-transformers pero es la feature diferenciadora real.

**Bonus opcional:** E (Claude API chatbot) — impresiona en demo, muy poco código.

---

## Prerequisito para todas las propuestas

Antes de activar cualquier recomendador: **lanzar scraping masivo** para que la mayor parte de la colección tenga metadata. Sin descripciones/géneros, el modelo no tiene con qué trabajar.

También conviene persistir `genres_list` y `players` (migración de 2 columnas en `game_metadata`) — aportan señal útil para filtros y similitud.
