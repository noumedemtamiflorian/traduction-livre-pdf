# 📚 `traduction-livre-pdf` — Universal AI Agent Skill

Un **Skill universel** (au standard ouvert `SKILL.md`) permettant à n'importe quel agent IA (**Google Antigravity**, **Claude Code**, **Cursor**, **OpenAI Codex**, **Gemini CLI**, **Windsurf**, **OpenCode**) et n'importe quel modèle (**Gemini**, **Claude**, **GPT**, etc.) de traduire intégralement un livre ou document PDF illustré et de générer un **livre PDF A4 éditorial** mis en page.

---

## ✨ Ce que fait ce Skill de bout en bout

1. **Extraction complète (`extract`)** : Extrait 100 % du texte page par page (`book_text.txt`) ainsi que toutes les illustrations originales du PDF (`images/`) avec un manifeste JSON précis.
2. **Charte éditoriale & Glossaire (`00_INDEX_ET_PLAN.md`)** : Identifie les termes clés et concepts de l'auteur, propose un glossaire et un plan de découpage par chapitres, et les fait valider par l'utilisateur avant de lancer la traduction.
3. **Traduction intégrale chapitre par chapitre** : Traduit chaque chapitre en entier (zéro résumé, zéro omission) dans un style fluide et naturel, sans jamais utiliser de blocs de code informatique parasites.
4. **Intégration des images + Traduction du texte interne aux images** : Inspecte visuellement chaque illustration extraite, l'insère à sa place exacte dans le chapitre, et ajoute juste en dessous un **encadré traduisant tous les textes visibles à l'intérieur même de l'image** (schémas, bulles, notes manuscrites sur tableau blanc, étiquettes, écrans d'applications, cartels de musée).
5. **Audit obligatoire d'intégrité et de complétude (`audit`)** : Compare mathématiquement le texte source et le texte traduit chapitre par chapitre (ratio de foisonnement, détection des sous-sections omises, images et blocs de code). Bloque la fusion si un chapitre est tronqué ou résumé.
6. **Fusion & Génération du PDF A4 (`merge` & `build-pdf`)** : Assemble tous les chapitres validés en un livre complet (`.md`) et génère un **PDF A4 prêt à lire ou imprimer** (avec typographie *Georgia* / *Segoe UI*, en-têtes courants, numérotation des pages, images centrées et encadrés de traduction ambrés solidaires de leur image).

---

## 🚀 Installation rapide (Sur n'importe quel ordinateur)

### Option A — Installation globale automatique (Recommandé)

Clonez ce dépôt GitHub, puis lancez le script d'installation correspondant à votre système :

**Sur Windows (PowerShell) :**
```powershell
git clone https://github.com/noumedemtamiflorian/traduction-livre-pdf.git
cd traduction-livre-pdf
.\install.ps1
```

**Sur macOS / Linux (Bash) :**
```bash
git clone https://github.com/noumedemtamiflorian/traduction-livre-pdf.git
cd traduction-livre-pdf
chmod +x install.sh
./install.sh
```

L'installeur copie automatiquement le skill dans les dossiers globaux de vos agents IA :
- **Antigravity (AGY)** : `~/.gemini/config/skills/traduction-livre-pdf`
- **Standard `.agents` / Codex / Cursor** : `~/.agents/skills/traduction-livre-pdf`
- **Claude Code** : `~/.claude/skills/traduction-livre-pdf`
- **OpenCode** : `~/.config/opencode/skills/traduction-livre-pdf`

### Option B — Installation locale dans un projet spécifique

Copiez simplement ce dossier dans `.agents/skills/traduction-livre-pdf/` à la racine de votre projet. Toute personne qui clonera votre projet bénéficiera automatiquement du skill !

---

## 💬 Comment l'utiliser avec votre Agent IA

Une fois installé, déposez votre fichier PDF dans votre dossier de travail et demandez simplement à votre agent :

> *« Utilise le skill `traduction-livre-pdf` pour traduire intégralement ce livre PDF en français, avec toutes ses images, la traduction du texte à l'intérieur de chaque image en dessous, et génère le PDF complet à la fin. »*

---

## 🛠️ Utilisation manuelle du script CLI (`scripts/book_pipeline.py`)

Le skill inclut un outil Python autonome utilisable directement en ligne de commande :

```bash
# 1. Extraire le texte et les images d'un PDF
python scripts/book_pipeline.py extract --pdf "The Right It.pdf" --out-dir "./Traduction_FR"

# 2. Auditer la complétude et l'intégrité de la traduction (bloque si résumé ou coupé)
python scripts/book_pipeline.py audit \
  --pdf "The Right It.pdf" \
  --chapters-dir "./Traduction_FR" \
  --min-ratio 1.05 \
  --strict

# 3. Fusionner les chapitres Markdown validés
python scripts/book_pipeline.py merge \
  --chapters-dir "./Traduction_FR" \
  --output "./Traduction_FR/LIVRE_COMPLET.md" \
  --title "LA BONNE IDÉE (THE RIGHT IT)" \
  --subtitle "Pourquoi tant d'idées échouent et comment vous assurer que la vôtre réussisse" \
  --author "Alberto Savoia"

# 4. Générer le livre PDF A4 final
python scripts/book_pipeline.py build-pdf \
  --input "./Traduction_FR/LIVRE_COMPLET.md" \
  --output "./LIVRE_COMPLET.pdf" \
  --title "La Bonne Idée (The Right It)" \
  --author "Alberto Savoia"
```

---

## 📁 Structure du dépôt

```text
traduction-livre-pdf/
├── SKILL.md                           # Instructions principales du Skill (standard universel)
├── README.md                          # Documentation et guide d'installation
├── LICENSE                            # Licence Open Source MIT
├── requirements.txt                   # Dépendances Python (pypdf, reportlab, Pillow)
├── install.ps1                        # Installeur automatique Windows
├── install.sh                         # Installeur automatique macOS / Linux
├── scripts/
│   └── book_pipeline.py               # Script CLI Python (extract, merge, build-pdf)
└── references/
    └── editorial_style_guide.md       # Charte éditoriale et format des encadrés d'images
```
