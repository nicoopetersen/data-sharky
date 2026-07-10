# Instalar el Analista Cripto (skill + cerebro) en otra PC

Guía para dejar funcionando en otra máquina la skill **`analista-cripto`** y su memoria persistente (**`cerebro/`**), tal como en el proyecto original.

## Requisitos previos
- [Claude Code](https://claude.com/claude-code) instalado.
- Python 3.9+ y `git`.
- Una **API key de Dune** (dune.com → Settings → API).

---

## 1. Clonar el repo
```bash
git clone https://github.com/nicoopetersen/data-sharky.git
cd data-sharky
```
Al clonar ya obtenés:
- La skill en `.claude/skills/analista-cripto/SKILL.md` (Claude Code la detecta automáticamente al abrirse **dentro de esta carpeta**).
- El cerebro completo en `cerebro/` (perfil, watchlist, tesis, aprendizajes, queries útiles, diario).

## 2. Entorno de Python
```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 3. Configurar la API key (NO se sube al repo)
```bash
cp .env.example .env
# Editá .env y poné tu key real:
#   DUNE_API_KEY=tu_api_key
```
Verificá que quedó bien (no imprime la key, solo confirma conexión):
```bash
python scripts/dune_helper.py
# Debe terminar en: OK end-to-end: [{'ok': 1, ...}]
```

## 4. Usar la skill
Abrí Claude Code **desde la carpeta `data-sharky`** y escribí:
```
/analista-cripto
```
La skill se carga con su identidad completa y **lee todo `cerebro/` al arrancar**, así que recuerda el perfil, la watchlist y las tesis abiertas (ej.: el análisis de Sharky.fi). También se dispara sola cuando mencionás tokens, inversiones, análisis on-chain, Dune, etc.

---

## Opción: skill disponible en TODOS tus proyectos (global)
Por defecto la skill es **de este proyecto**. Si la querés disponible en cualquier carpeta:
```bash
mkdir -p ~/.claude/skills
cp -r .claude/skills/analista-cripto ~/.claude/skills/
```
⚠️ Ojo: la skill lee `cerebro/` **relativo al directorio actual**. Si la usás fuera de este repo, el cerebro no estará. Para memoria persistente, lo más simple es **ejecutar Claude Code siempre desde la carpeta del proyecto** (opción 1).

## Mantener el cerebro sincronizado entre PCs
El cerebro son archivos markdown versionados. Para llevar los aprendizajes de una PC a otra:
```bash
git pull        # traer lo último antes de trabajar
# ...trabajás, la skill actualiza cerebro/ sola...
git add cerebro/ && git commit -m "update cerebro" && git push
```

## Notas de seguridad
- `.env` (tu API key), `data/` y los `.html` pesados **están en `.gitignore`** — nunca se suben.
- El cerebro **no** guarda API keys, seeds ni direcciones de wallets (regla de higiene de la skill).
