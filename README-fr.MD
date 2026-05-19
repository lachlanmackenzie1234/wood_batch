# Générateur de panneaux Wood Batch

Pour la première installation sous Windows, exécutez une fois le fichier `setup.bat`. Pour les exportations suivantes, utilisez le fichier `run.bat`.

Ce projet génère des panneaux PNG prêts pour l'impression sur bois, magnets ou supports similaires.

Le fonctionnement habituel est :

```text
1. Placer les images source dans images/
2. Modifier jobs.csv avec les noms de fichiers, les quantités et les tailles finales d'impression
3. Choisir un format de panneau dans config.csv, ou saisir une taille personnalisée
4. Lancer run.sh sur macOS, ou run.bat sur Windows
5. Récupérer le panneau généré dans output/
```

## Fichiers du projet

```text
wood_batch/
├── images/              Images source à utiliser
├── output/              Panneaux générés
├── jobs.csv             Liste de production : image, quantité, taille de l'objet
├── config.csv           Réglages d'export : DPI, marges, espaces, format de panneau
├── panels.csv           Formats de panneaux réutilisables
├── packing.py           Algorithmes de placement : grid, shelf, guillotine, maxrects
├── planner.py           Rapport de capacité et recommandations de panneaux
├── requirements.txt     Dépendances Python
├── run.sh               Script de lancement macOS / Linux
├── run.bat              Script de lancement Windows
└── template.py          Script de génération du panneau
```

## Installer Python

Python doit être installé avant d'utiliser ce projet.

### macOS

Installer Python depuis :

```text
https://www.python.org/downloads/macos/
```

Ou avec Homebrew :

```bash
brew install python
```

### Windows

Installer Python depuis :

```text
https://www.python.org/downloads/windows/
```

Pendant l'installation, cocher :

```text
Add python.exe to PATH
```

Puis fermer et rouvrir le dossier avant de lancer `run.bat`.

## Première installation

`requirements.txt` doit contenir :

```txt
Pillow>=10.4,<12
```

`Pillow` est la bibliothèque d'image utilisée par `template.py`. Dans le code Python, elle est importée sous le nom `PIL`, mais le paquet à installer s'appelle `Pillow`.

Les scripts de lancement installent automatiquement cette dépendance dans un dossier local `.venv`.

## Modifier `jobs.csv`

Chaque ligne décrit un lot d'images.

```csv
file,quantity,width_mm,height_mm
image_1.png,10,25,25
image_2.png,25,25,25
image_3.png,8,50,50
```

Signification :

```text
file       Image source dans images/
quantity   Nombre d'exemplaires à placer sur le panneau
width_mm   Largeur finale imprimée de chaque objet, pas la largeur du fichier source
height_mm  Hauteur finale imprimée de chaque objet, pas la hauteur du fichier source
```

Les noms de fichiers dans `jobs.csv` doivent correspondre exactement aux fichiers présents dans `images/`.

## Modifier `config.csv`

`config.csv` contrôle les réglages généraux de l'export.

```csv
key,value
panel_preset,standard_600x1200
dpi,300
panel_width_mm,
panel_height_mm,
outer_margin_mm,5
gap_mm,3
output_file,output/panel.png
fit_mode,cover
packing_mode,auto
show_capacity_report,true
recommend_panel,false
draw_cut_guides,false
draw_labels,false
```

Signification :

```text
panel_preset      Nom d'un format défini dans panels.csv.
dpi               Résolution d'impression. MIPP recommande 300 DPI minimum pour une bonne qualité.
panel_width_mm    Largeur personnalisée du panneau. Laisser vide pour utiliser panel_preset.
panel_height_mm   Hauteur personnalisée du panneau. Laisser vide pour utiliser panel_preset.
outer_margin_mm   Marge de sécurité autour du panneau complet.
gap_mm            Espace entre chaque image pour la découpe ou le sciage.
output_file       Chemin d'export. Les fichiers existants ne sont pas écrasés ; un numéro est ajouté automatiquement.
fit_mode            cover recadre pour remplir ; contain garde l'image entière avec une marge si besoin.
packing_mode        auto, grid, shelf, guillotine ou maxrects.
show_capacity_report true/false. Affiche le nombre d'objets, l'utilisation du panneau et les estimations de grille.
recommend_panel     true/false. Teste les formats de panels.csv et affiche des recommandations.
draw_cut_guides     true/false. Ajoute des contours légers autour de chaque objet.
draw_labels         true/false. Ajoute les noms de fichiers sur les images pour les tests.
```

Si `panel_width_mm` ou `panel_height_mm` sont renseignés, ces valeurs remplacent le format choisi dans `panel_preset`.

Pour un premier test, il peut être utile de régler :

```csv
draw_cut_guides,true
draw_labels,true
```

Pour la production, remettre les deux valeurs à `false`, sauf si les repères ou les noms sont demandés.

## Modes de placement

`packing_mode` contrôle la manière dont les objets sont placés sur le panneau.

```text
auto        Choisit automatiquement un mode selon jobs.csv.
grid        Idéal pour une seule taille d'objet, par exemple 288 × 100×100 mm.
shelf       Placement simple et prévisible par lignes.
guillotine  Placement orienté découpe, utile pour des tailles divisibles comme 25, 50 et 100 mm.
maxrects    Placement plus dense pour les tailles mélangées, mais moins orienté découpe.
```

Réglage recommandé :

```csv
packing_mode,auto
```

Pour la plupart des templates avec une seule taille, `auto` devrait choisir `grid`. Pour des tailles mélangées mais divisibles, `auto` devrait choisir `guillotine`.

Le script peut aussi afficher un rapport de capacité :

```csv
show_capacity_report,true
```

Pour comparer tous les formats de `panels.csv`, régler :

```csv
recommend_panel,true
```

Cela ne change pas automatiquement le panneau sélectionné ; cela affiche seulement des recommandations dans le terminal.

## Modifier `panels.csv`

`panels.csv` contient les formats de panneaux réutilisables.

```csv
name,width_mm,height_mm,notes
standard_600x1200,600,1200,Format général par défaut
large_720x1500,720,1500,Correspond à visualpanel_foot_001 si interprété en taille physique à 240 DPI
extra_large_1250x2500,1250,2500,Correspond à visualpanel_kit_5x5_72 et panel_10x10_001_pilat en taille physique
wide_2000x1000,2000,1000,Format paysage large pour dispositions horizontales
square_1200x1200,1200,1200,Format carré de test
```

Pour utiliser un format, régler `panel_preset` dans `config.csv` :

```csv
panel_preset,extra_large_1250x2500
```

Pour utiliser une taille personnalisée ponctuelle, laisser `panel_preset` vide et renseigner `panel_width_mm` et `panel_height_mm` dans `config.csv` :

```csv
panel_preset,
panel_width_mm,1200
panel_height_mm,1200
```

## Lancer sur macOS

Depuis le Terminal :

```bash
cd ~/Downloads/wood_batch
chmod +x run.sh
./run.sh
```

`run.sh` crée un environnement local `.venv`, installe les dépendances et lance `template.py`.

## Lancer sur Windows

Double-cliquer sur :

```text
run.bat
```

Ou lancer depuis PowerShell :

```powershell
.\run.bat
```

`run.bat` crée un environnement local `.venv`, installe les dépendances et lance `template.py`.

## Export

Les panneaux générés sont enregistrés dans :

```text
output/
```

L'export par défaut est un PNG à la résolution définie dans `config.csv`.

Les fichiers existants ne sont pas écrasés. Par exemple, si ce fichier existe déjà :

```text
output/panel.png
```

Le prochain export sera enregistré sous :

```text
output/panel_1.png
```

Puis :

```text
output/panel_2.png
```

## Rapport de capacité

Quand `show_capacity_report` vaut `true`, le script affiche un résumé après chaque lancement.

Exemple :

```text
Capacity report
---------------
Panel: 1250 × 2500 mm
Requested items: 288
Placed items: 288
Unplaced items: 0
Packing mode: grid
Approx. item area usage: 92.2%
Grid estimate: 12 × 24 = 288 items
```

Ce rapport sert à vérifier le format du panneau, les quantités et les tailles avant l'envoi en impression.

## Réglages d'impression

Réglage par défaut actuel :

```text
DPI: 300
```

Conversion utile :

```text
pixels = millimètres / 25.4 × DPI
```

Exemples à 300 DPI :

```text
25 mm  = 295 px
50 mm  = 591 px
100 mm = 1181 px
120 mm = 1417 px
```

## Notes techniques MIPP

La fiche technique MIPP recommande :

```text
300 DPI minimum pour les images haute résolution
3 mm minimum de fond perdu autour du format final de découpe
5 mm de zone de sécurité intérieure à partir du bord de coupe
```

Ce générateur utilise actuellement `gap_mm` comme espace entre les images pour la découpe ou le sciage, et `outer_margin_mm` comme marge de sécurité autour du panneau complet.

Avant la production, lancer une fois avec `draw_cut_guides,true` et vérifier le format du panneau, le nombre d'objets et les espacements.

## Notes

- Utiliser des images source en haute résolution lorsque c'est possible.
- Le PNG est recommandé car il est sans perte.
- Le JPEG peut créer des artefacts de compression et ne devrait être utilisé que si demandé.
- ImageMagick est optionnel et sert uniquement à inspecter les métadonnées d'images existantes. Il n'est pas nécessaire pour générer les panneaux.

---
