Verifica que el schema de la base de datos y el código de acceso están sincronizados y son correctos.

Lee estos archivos:
- `src/rom_manager/database/schema.py`
- `src/rom_manager/database/repository.py`
- `src/rom_manager/web/server.py` (solo las queries SQL directas con `conn.execute`)
- `src/rom_manager/scanner/rom_scanner.py` (queries directas)

Comprueba los siguientes puntos:

### 1. Columnas declaradas vs columnas usadas
Para cada columna en `SCHEMA_STATEMENTS` y `_GAMES_MIGRATIONS`, verifica que existe al menos un lugar en el código que la lea o escriba. Reporta columnas declaradas pero nunca usadas.

### 2. Columnas usadas pero no declaradas
Busca todas las queries SQL en el código. Para cada `SELECT col`, `INSERT INTO ... (col)`, `UPDATE ... SET col`, verifica que `col` existe en el schema. Reporta columnas referenciadas que no están declaradas.

### 3. Migraciones pendientes
Comprueba que todas las columnas añadidas después del schema inicial están en `_GAMES_MIGRATIONS` o `_ASSETS_MIGRATIONS`. Si hay columnas en `SCHEMA_STATEMENTS` que podrían faltar en BDs existentes, sugiere añadirlas a las listas de migración.

### 4. Índices faltantes
Identifica columnas que se usan frecuentemente en cláusulas `WHERE` sin índice. En especial: `source_path`, `platform`, `canonical_title`, `file_type`, `play_status`, `last_played_at`.

### 5. Queries sin parámetros ligados (SQL injection risk)
Busca queries que usen f-strings o concatenación de strings en lugar de `?` con parámetros. Reporta cualquier caso encontrado.

Formato del informe:

## DB Check
### ❌ Problemas (deben corregirse)
### ⚠️ Advertencias (revisar)
### ✅ OK

Al final: "La BD está en buen estado" o "Hay N problemas que corregir".
