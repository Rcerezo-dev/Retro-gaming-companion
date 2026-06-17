# Obsidian Skills — Quick Start Guide

> 🎯 **Este es tu cheat sheet** — Consulta aquí cuando uses Claude Code con los Obsidian skills

---

## 5 Skills Disponibles

### 1️⃣ **obsidian-markdown** — Notas & Documentación
**Cuándo**: 🔚 Final de sesión, cuando documentes features
```bash
/obsidian-markdown create-note [[feature-name]]     # Nueva nota
/obsidian-markdown update-note [[STATE.md]]         # Actualizar existente
/obsidian-markdown add-embed [[otra-nota]]          # Ligar notas
/obsidian-markdown add-callout "NOTE" "Mensaje"    # Destacar info
/obsidian-markdown read-note [[nombre]]             # Leer completa
```

---

### 2️⃣ **obsidian-cli** — Diagnosticar Vault
**Cuándo**: 🔍 Inicio sesión, para chequear estado
```bash
/obsidian-cli status                                # Ver estado general
/obsidian-cli plugin list                          # Plugins instalados
/obsidian-cli config get vault.name                # Obtener config
```

---

### 3️⃣ **json-canvas** — Diagramas & Mind Maps
**Cuándo**: 🎨 Planificación, documentación visual
```bash
/json-canvas create-canvas "Diagram Name"          # Canvas nuevo
/json-canvas add-node "Text" --position 0,0        # Nodo/caja
/json-canvas add-edge "NodeA" "NodeB"              # Conectar
/json-canvas add-group "Group Name"                # Agrupar
```

---

### 4️⃣ **obsidian-bases** — Bases de Datos
**Cuándo**: 📊 Cuando necesites datos tabulares, filtering, etc
```bash
/obsidian-bases create-base "Database Name"        # Base nueva
/obsidian-bases add-view "View Name" --type gallery # Nueva vista
/obsidian-bases add-property "name" --type text    # Nueva columna
/obsidian-bases add-filter "Rule" --property col   # Filtrar datos
```

---

### 5️⃣ **defuddle** — Limpiar Web Pages
**Cuándo**: 📰 Research, guardar artículos sin clutter
```bash
/defuddle clean-url "https://example.com"         # Limpiar sitio
/defuddle save-to-note [[ref-name]] --url "..."   # Guardar en nota
/defuddle extract-markdown --url "https://..."    # Solo markdown
```

---

## 🎯 Flujo de Sesión Típica

### ☀️ INICIO
```
1. Claude: /obsidian-cli status
           ↓ Verifica vault
2. Claude: /obsidian-markdown read-note [[STATE.md]]
           ↓ Lee qué pasó última vez
3. Trabajar en la tarea
```

### 🌙 FINAL
```
1. Tu: "Documenta los cambios de hoy"
2. Claude: /obsidian-markdown update-note [[STATE.md]]
3. Claude: /obsidian-markdown create-note [[S36-Feature]] (si aplica)
4. git commit + git push
```

---

## ⚡ Comandos Más Usados

| Momento | Comando |
|---------|---------|
| Inicio sesión | `/obsidian-cli status` |
| Revisar estado | `/obsidian-markdown read-note [[STATE.md]]` |
| Documentar feature | `/obsidian-markdown create-note [[feature-name]]` |
| Dibujar arquitectura | `/json-canvas create-canvas "Diagram"` |
| Actualizar estado | `/obsidian-markdown update-note [[STATE.md]]` |
| Guardar artículo | `/defuddle save-to-note [[ref]] --url "..."` |

---

## 📌 Reglas de Oro

✅ **HACER:**
- Usa wikilinks: `[[mi-nota]]`
- Frontmatter YAML en cada nota
- Actualiza STATE.md al final de cada sesión
- Busca [[nota-existente]] antes de crear duplicados

❌ **NO HACER:**
- Editar nota en dos lugares a la vez
- Crear sin frontmatter
- Wikilinks con mayúsculas o espacios
- Ignorar STATE.md

---

## 🗂️ Notas Importantes en Obsidian

```
/proyectos/retro-vault/
├── 📌 STATE.md              ← LEE ESTO PRIMERO (estado actual)
├── 📌 Skills-Guide.md       ← Esta guía (más detallado)
├── Roadmap.md               ← Próximas features
├── overview.md              ← Descripción proyecto
├── S35-Implementation.md    ← Última implementación
├── Cambios-Recientes.md     ← Changelog
└── Obsidian-Skills.md       ← Detalles de cada skill
```

**👉 CONSULTA AQUÍ PRIMERO** — `Skills-Guide.md` en Obsidian tiene todo más detallado.

---

## 🆘 Quick Troubleshooting

- **"Skill no existe"** → Reinicia Claude Code
- **Links no funcionan** → Usa kebab-case: `[[mi-nota-importante]]`
- **Nota no se crea** → Verifica ruta `C:\Users\Ruben\Obsidian Vault\`
- **Vault lento** → `/obsidian-cli status` para diagnosticar

---

**Version**: 1.0 (2026-03-21)
**Ubicación**: `Retro-gaming-companion/docs/SKILLS-QUICK-START.md`
**Uso**: Consulta cuando uses skills en Claude Code

Guía detallada en: `/proyectos/retro-vault/Skills-Guide.md` (Obsidian Vault)
