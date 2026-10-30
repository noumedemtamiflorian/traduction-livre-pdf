---
name: traduction-livre-pdf
description: >-
  Traduit intégralement un livre ou document PDF illustré vers une langue cible
  (ex. anglais vers français) avec une qualité éditoriale professionnelle. Extrait
  le texte et toutes les images originales, établit un glossaire et une charte
  éditoriale, traduit chaque chapitre en Markdown structuré, insère toutes les
  illustrations avec la traduction complète des textes présents à l'intérieur
  même des images, fusionne l'ouvrage et génère un livre PDF A4 mis en page.
  À utiliser dès que l'utilisateur demande de traduire un livre PDF, un ouvrage
  illustré ou un document complet de bout en bout.
---

# Traduction Intégrale de Livre PDF Illustré (`traduction-livre-pdf`)

## Overview

Ce skill permet à n'importe quel agent IA de traduire un livre ou document PDF complet de manière professionnelle, sans résumé ni omission, tout en préservant l'intégralité des illustrations originales et en traduisant tous les textes visuels inscrits à l'intérieur des images (schémas, bulles, tableaux blancs, étiquettes, captures d'écran, cartels). Il produit à la fois les chapitres Markdown individuels, le livre complet unifié (`.md` et `.html`) et le livre final mis en page au format **PDF A4**.

## Dependencies

Aucune dépendance externe complexe : le script intégré utilise Python 3 avec trois bibliothèques standards légères (`pypdf`, `reportlab`, `Pillow`), déclarées dans [requirements.txt](./requirements.txt).

Si ces paquets ne sont pas encore installés sur la machine, installez-les avec :

```bash
python -m pip install -r requirements.txt
```

*(Ou via `uv pip install -r requirements.txt` si `uv` est utilisé).*

## Quick Start

1. **Extraire le texte et les images du PDF source :**
   ```bash
   python scripts/book_pipeline.py extract --pdf "Mon_Livre.pdf" --out-dir "./Traduction_FR"
   ```
2. **Créer et faire valider le plan & glossaire (`00_INDEX_ET_PLAN.md`)**, puis traduire chaque chapitre en intégrant les images et leurs encadrés de traduction.
3. **Fusionner tous les chapitres traduits :**
   ```bash
   python scripts/book_pipeline.py merge --chapters-dir "./Traduction_FR" --output "./Traduction_FR/LIVRE_COMPLET.md" --title "Titre du Livre" --author "Nom de l'Auteur"
   ```
4. **Générer le PDF éditorial A4 (et sa version HTML) :**
   ```bash
   python scripts/book_pipeline.py build-pdf --input "./Traduction_FR/LIVRE_COMPLET.md" --output "./LIVRE_COMPLET.pdf" --title "Titre du Livre" --author "Nom de l'Auteur"
   ```

---

## Utility Scripts

Le script principal est [scripts/book_pipeline.py](./scripts/book_pipeline.py). Il écrit systématiquement ses résultats dans des fichiers et affiche un court résumé d'exécution.

### 1. `extract` — Extraction du texte et des illustrations du PDF original

Extrait l'intégralité du texte page par page dans `book_text.txt`, extrait toutes les images intégrées dans `<out-dir>/images/`, et génère un fichier `extraction_manifest.json` indiquant le numéro de page et les dimensions de chaque image.

```bash
python scripts/book_pipeline.py extract \
  --pdf "chemin/vers/livre_original.pdf" \
  --out-dir "chemin/vers/Traduction_FR"
```

### 2. `merge` — Assemblage des chapitres Markdown en un livre complet

Regroupe tous les fichiers de chapitres numérotés (`00_Introduction.md`, `01_Chapitre_1...`, etc. — en excluant `00_INDEX_ET_PLAN.md` et le fichier complet lui-même) avec une table des matières automatique, et vérifie que chaque image référencée existe bien.

```bash
python scripts/book_pipeline.py merge \
  --chapters-dir "chemin/vers/Traduction_FR" \
  --output "chemin/vers/Traduction_FR/LIVRE_COMPLET.md" \
  --title "Titre Français du Livre" \
  --subtitle "Sous-titre du livre" \
  --author "Nom de l'Auteur"
```

### 3. `build-pdf` — Génération du livre PDF A4 et HTML

Convertit le fichier Markdown complet en un **PDF A4 éditorial** (avec détection multi-plateforme des polices Windows/macOS/Linux, en-têtes courants, numérotation des pages, tableaux stylisés, images centrées et encadrés de traduction ambrés solidaires de leur image via `KeepTogether`) ainsi qu'en un fichier **HTML autonome** (images encodées en Base64).

```bash
python scripts/book_pipeline.py build-pdf \
  --input "chemin/vers/Traduction_FR/LIVRE_COMPLET.md" \
  --output "chemin/vers/LIVRE_COMPLET.pdf" \
  --title "Titre Français du Livre" \
  --author "Nom de l'Auteur"
```

---

## Workflow Complet en 5 Étapes (À suivre par l'Agent IA)

Consultez également [references/editorial_style_guide.md](./references/editorial_style_guide.md) pour les règles typographiques détaillées.

### Étape 1 : Extraction et Analyse Initiale
1. Exécutez la sous-commande `extract` sur le PDF fourni par l'utilisateur.
2. Lisez `extraction_manifest.json` et parcourez le début de `book_text.txt` (table des matières, introduction, structure des chapitres) pour identifier :
   - Le titre, le sous-titre et l'auteur ;
   - La liste complète des parties et chapitres ;
   - Les concepts, néologismes, acronymes et formules récurrentes de l'auteur ;
   - Le nombre total d'images extraites et les pages où elles apparaissent.

### Étape 2 : Charte Éditoriale, Glossaire et Validation Utilisateur
1. Créez le fichier `00_INDEX_ET_PLAN.md` dans le dossier de sortie contenant :
   - **La charte éditoriale** : style fluide, naturel et moderne dans la langue cible ; **zéro bloc de code informatique (` ``` `)** pour mettre en forme du texte courant ou des formules (utiliser uniquement des citations `>`, du gras, de l'italique et des tableaux Markdown).
   - **Le glossaire des termes clés** : tableau associant chaque terme/concept original à sa traduction choisie.
   - **Le découpage complet des chapitres** avec leurs noms de fichiers (`00_Introduction.md`, `01_Chapitre_1_...md`, etc.).
2. **Validation obligatoire :** Présentez ce glossaire et ce plan à l'utilisateur et attendez sa confirmation (ou ses ajustements terminologiques) avant de traduire l'intégralité des chapitres.

### Étape 3 : Traduction Intégrale Chapitre par Chapitre
1. Pour chaque chapitre, lisez les pages correspondantes dans `book_text.txt`.
2. Traduisez **100 % du texte** sans jamais résumer, tronquer ni sauter de paragraphe.
3. Respectez scrupuleusement le glossaire validé à l'Étape 2 afin de garantir une cohérence terminologique absolue du premier au dernier chapitre.

### Étape 4 : Intégration des Images et Traduction du Texte Interne aux Images
1. **Renommage explicite (recommandé) :** Renommez ou copiez les images extraites dans `<out-dir>/images/` avec des noms clairs par chapitre (ex. `00_couverture.jpg`, `fig_04_01_...jpg`, `fig_05_01_...jpg`).
2. **Inspection visuelle :** Utilisez votre outil de lecture d'image (`read_file` / vision) sur **chacune des images** pour lire tous les textes, étiquettes, bulles, boutons, notes manuscrites ou légendes qu'elle contient.
3. **Insertion et encadré de traduction obligatoire :** À l'endroit exact où l'illustration apparaît dans le chapitre, insérez :
   - L'image : `![Description de l'image](images/nom_image.jpg)`
   - La légende en italique sur la ligne suivante : `*Légende explicative de la figure.*`
   - **Juste en dessous**, un bloc de citation traduisant **intégralement** tous les textes visibles à l'intérieur de l'image :
     ```markdown
     ![Description de l'image](images/fig_exemple.jpg)
     *Légende explicative de la figure.*

     > **Traduction du texte présent dans l’image :**
     > * **Texte original 1** → *Traduction française 1*
     > * **Texte original 2** → *Traduction française 2*
     ```
   - *(Note : L'intitulé exact `> **Traduction du texte présent dans l’image` ou `> **Traduction des inscriptions présentes dans l’image` déclenche automatiquement le style d'encadré ambré solidaire de l'image lors de la génération du PDF).*

### Étape 5 : Fusion, Génération du PDF et Vérification Qualité
1. Exécutez la sous-commande `merge` pour assembler tous les chapitres dans `LIVRE_COMPLET_<Nom>.md`.
2. Exécutez la sous-commande `build-pdf` pour générer le fichier PDF final (`LIVRE_COMPLET_<Nom>.pdf`) ainsi que la version HTML.
3. Vérifiez que le rapport JSON de `build-pdf` confirme :
   - Le nombre total de pages générées ;
   - La présence de 100 % des images attendues dans le PDF final.
4. Présentez à l'utilisateur les liens cliquables vers les chapitres Markdown, le fichier complet et le PDF final.

---

## Common Mistakes (Erreurs fréquentes à éviter)

1. **Résumer ou condenser un chapitre long :** Ne résumez jamais. Si un chapitre est très long, lisez-le et traduisez-le par tranches successives de pages jusqu'à la dernière ligne.
2. **Utiliser des blocs de code (` ``` `) pour encadrer des formules ou exemples dans le livre :** Dans un livre non-informatique, les blocs de code produisent une police monospace disgracieuse. Utilisez toujours des blocs de citation (`>`), des listes à puces ou des tableaux Markdown.
3. **Oublier de regarder l'image avec l'outil de vision :** Ne devinez jamais le texte contenu dans une image uniquement à partir du texte du chapitre. Inspectez toujours visuellement le fichier `.jpg`/`.png` pour traduire fidèlement chaque mot, chiffre, flèche ou cartel de musée figurant dans l'image.
