# Guide de Style Éditorial et Formatage des Illustrations (`traduction-livre-pdf`)

Ce document de référence précise les règles de mise en page, de traduction et d'intégration des illustrations pour le skill `traduction-livre-pdf`.

---

## 1. Principes de Traduction Littéraire et Non-Fiction

1. **Traduction intégrale (Zéro résumé) :**
   - Chaque paragraphe, anecdote, dialogue, note ou tableau de l'ouvrage original doit être traduit intégralement.
   - Ne condensez jamais un chapitre long : traduisez-le par sections successives en vérifiant les numéros de pages dans `book_text.txt`.
2. **Fluidité et naturel :**
   - Adaptez les tournures idiomatiques pour qu'elles sonnent de manière fluide, percutante et naturelle dans la langue cible, tout en conservant le terme original en italique entre parenthèses lors de sa première apparition clé — par exemple : **avoir sa peau en jeu** *(skin in the game)*.
3. **Zéro bloc de code informatique (` ``` `) dans le texte du livre :**
   - Sauf s'il s'agit véritablement d'un livre de programmation contenant du code source, **n'utilisez jamais** de blocs de code (` ``` `) ni d'indentation à 4 espaces pour encadrer des formules, des hypothèses ou des exemples.
   - Utilisez exclusivement :
     - Des blocs de citation (`>`) pour les formules, règles d'or, lettres, e-mails ou encadrés ;
     - Des tableaux Markdown (`| Col 1 | Col 2 |`) pour les comparaisons et bilans ;
     - Du **gras** et de l'*italique* pour la hiérarchie visuelle.

---

## 2. Format Standard des Illustrations et de leur Traduction Visuelle

Chaque image extraite du PDF doit être :
1. Inspectée visuellement par le modèle d'IA afin de relever **toutes les inscriptions visibles dans l'image** ;
2. Insérée à son emplacement exact dans le fil du texte ;
3. Accompagnée d'une légende en italique juste en dessous ;
4. Suivie immédiatement d'un bloc de citation commençant par `> **Traduction du texte présent dans l’image` (ou `> **Traduction des inscriptions présentes dans l’image`).

### Exemple type à respecter :

```markdown
![Affiche sur la porte de la librairie d'ancien d'Antonia](images/fig_05_08_fausse_porte_librairie_antonia.jpg)
*L'affiche du prétotype de Fausse Porte sur la porte de la librairie d'ancien d'Antonia.*

> **Traduction du texte présent dans l’image :**
> * **ANTONIA’S ANTIQUE BOOKS** → *LIBRAIRIE D’ANCIEN D’ANTONIA*
> * **— GRAND OPENING —** → *— GRANDE OUVERTURE —*
> * **KNOCK for ENTRANCE** → *FRAPPEZ POUR ENTRER*
```

> **Pourquoi cette syntaxe exacte est importante :**  
> Le générateur PDF (`scripts/book_pipeline.py build-pdf`) détecte automatiquement tout bloc `>` situé juste après une image et contenant l'expression `Traduction du texte` ou `Traduction des inscriptions`. Il le transforme alors en un **encadré ambré élégant** et le lie à l'image via un conteneur insécable (`KeepTogether`), garantissant que l'image et sa traduction ne soient jamais séparées par un saut de page.
