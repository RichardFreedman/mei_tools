# MEI Tools in Google Colab

This guide walks through the complete workflow for extracting, editing, and updating metadata in a corpus of MEI files, using Google Colab as the environment.

The workflow has three stages:

1. **Extract** — scan a folder of MEI files and write a CSV of their current metadata
2. **Edit** — review and correct the CSV (in Google Sheets, Excel, or any text editor)
3. **Update** — apply the corrected CSV back to every MEI file in the corpus

---

## Before You Begin

You need:

- A Google account with Google Drive
- A folder of MEI files (any mix of MuseScore, Sibelius, Humdrum/Verovio, or mei-friend exports) uploaded to Drive
- A Colab notebook (or open `01_MEI_Updating_2025.ipynb` from this repository directly in Colab)

---

## Step 1 — Install MEI Tools

```python
!pip install git+https://github.com/RichardFreedman/mei_tools.git@main
```

> **Note:** To test a development branch, replace `@main` with the branch name, e.g. `@dev-26`.

---

## Step 2 — Mount Drive and Set Up Folders

Run this single setup cell. You only need to set **one path** — the base folder where your MEI files live. All output folders are created automatically beneath it.

```python
import os
from google.colab import drive

drive.mount('/content/drive')

# ── Set this to the folder in your Drive that contains your .mei files ──
input_folder = '/content/drive/MyDrive/my_mei_corpus'

# All output folders are derived from the base and created automatically
base         = os.path.dirname(input_folder)
corpus_name  = os.path.basename(input_folder)

folders = {
    'input':    input_folder,
    'csv':      os.path.join(base, corpus_name + '_csv'),
    'updated':  os.path.join(base, corpus_name + '_updated'),
    'features': os.path.join(base, corpus_name + '_features'),
}

for name, path in folders.items():
    os.makedirs(path, exist_ok=True)
    print(f'{name:10s}  →  {path}')
```

For a corpus at `MyDrive/my_mei_corpus/` this produces:

```
input       →  /content/drive/MyDrive/my_mei_corpus
csv         →  /content/drive/MyDrive/my_mei_corpus_csv
updated     →  /content/drive/MyDrive/my_mei_corpus_updated
features    →  /content/drive/MyDrive/my_mei_corpus_features
```

All four folders are now available as `folders['input']`, `folders['csv']`, etc. for the remaining steps.

---

## Step 3 — Extract Metadata to CSV

```python
from mei_tools import MEI_Metadata_Extractor

extractor = MEI_Metadata_Extractor(verbose=True)
extractor.save_csvs(
    input_folder=folders['input'],
    output_folder=folders['csv']
)
```

### What this produces

One CSV file is written for each source type found in your corpus:

| Source type | CSV filename |
|---|---|
| MuseScore | `muse_score_extracted_metadata.csv` |
| Sibelius | `sib_extracted_metadata.csv` |
| Humdrum / Verovio | `hum_drum_extracted_metadata.csv` |
| mei-friend | `mei_friend_extracted_metadata.csv` |

If all your files come from the same application you will get just one CSV.

### CSV columns

| Column | What it contains |
|---|---|
| `filename` | basename of the .mei file — **do not edit this** |
| `source_type` | auto-detected application type |
| `mei_version` | MEI schema version from the file |
| `title` | main title (fileDesc/titleStmt) |
| `title_subordinate` | subordinate/movement titles, pipe-separated (mei-friend) |
| `composer_name` | composer's name |
| `composer_auth` | authority system, e.g. `VIAF` or `GND` |
| `composer_auth_uri` | full URI, e.g. `https://viaf.org/viaf/12304462/` |
| `composer_codedval` | coded value within authority (GND) |
| `editors` | pipe-separated list of `Name [role]` entries, e.g. `Jane Smith [editor]\|Bob Jones [encoder]` |
| `encoding_date` | date of encoding, ISO format |
| `rights` | rights/copyright statement |
| `publisher` | publisher name (MuseScore) |
| `distributor` | distributor(s), pipe-separated (MuseScore) |
| `genre` | genre term from workList |
| `encoding_application` | application name(s) and version(s) |
| `work_title` | title from workList/work |
| `movement_name` | movement name, Humdrum OMD field |
| `source_title` | title of the physical source (Humdrum) |
| `source_composer` | composer as recorded in sourceDesc (Humdrum) |
| `source_editor` | editor(s) from EED field (Humdrum) |
| `source_encoder` | encoder(s) from ENC field (Humdrum) |
| `edition_version` | edition version, EEV field (Humdrum) |
| `encoding_annot` | encoding annotation, ONB field (Humdrum) |
| `humdrum_id` | value of the `!!!id` reference key (Humdrum) |

**Editing rules:**

- Leave any cell **blank** to keep the existing MEI content unchanged — only non-empty cells are applied.
- For fields that accept multiple values (`editors`, `distributor`), separate entries with a pipe character: `Name One [role]|Name Two [role]`
- The `filename` and `source_type` columns are used to match rows to files — do not change them.

---

## Step 4 — Edit the CSV

Open the CSV from your Drive in **Google Sheets**, **Excel**, or any text editor. Fill in or correct the metadata values, then save it back to Drive (keep the same filename or update the path in Step 6).

### Using Google Sheets as a live metadata source

If you prefer to maintain metadata in a Google Sheet:

1. Upload the CSV to Google Sheets (`File → Import`)
2. When ready, publish it as CSV: `File → Share → Publish to web → select the sheet → CSV`
3. Copy the published URL — you can pass this directly to the updater in Step 6 instead of a file path

---

## Step 5 — Apply Updated Metadata to MEI Files

### Option A — from a local Drive file

```python
from mei_tools import MEI_Metadata_Updater_Generic
import os

# Adjust the filename for the source type you updated, e.g.:
#   hum_drum_extracted_metadata.csv
#   muse_score_extracted_metadata.csv
#   sib_extracted_metadata.csv
#   mei_friend_extracted_metadata.csv
csv_source = os.path.join(folders['csv'], 'hum_drum_extracted_metadata.csv')

updater = MEI_Metadata_Updater_Generic(verbose=True)
updater.process_folder(
    input_folder=folders['input'],
    csv_source=csv_source,
    output_folder=folders['updated']
)
```

### Option B — from a Google Sheets published URL

```python
from mei_tools import MEI_Metadata_Updater_Generic

csv_source = 'https://docs.google.com/spreadsheets/d/e/YOURKEY/pub?output=csv'

updater = MEI_Metadata_Updater_Generic(verbose=True)
updater.process_folder(
    input_folder=folders['input'],
    csv_source=csv_source,
    output_folder=folders['updated']
)
```

### Option C — from a raw GitHub URL

```python
from mei_tools import MEI_Metadata_Updater_Generic

csv_source = 'https://raw.githubusercontent.com/yourorg/yourrepo/main/metadata/hum_drum_metadata.csv'

updater = MEI_Metadata_Updater_Generic(verbose=True)
updater.process_folder(
    input_folder=folders['input'],
    csv_source=csv_source,
    output_folder=folders['updated']
)
```

### Output

Each matching MEI file is written to `folders['updated']` with `_rev` appended to the filename, e.g. `Ror0101_rev.mei`. The original files in `folders['input']` are never modified.

---

## Step 6 (Optional) — CRIM Project Workflow

If you are working with the **CRIM (Citations: The Renaissance Imitation Mass)** project, use `crim_mode=True`. This expects the CRIM column schema (`MEI_Name`, `Title`, `Composer_VIAF`, `Editor`, etc.) and delegates processing to the full CRIM metadata writer, which includes the `manifestationList`.

```python
import os
from mei_tools import MEI_Metadata_Extractor, MEI_Metadata_Updater_Generic

# Extract using CRIM column names — produces crim_extracted_metadata.csv
extractor = MEI_Metadata_Extractor(verbose=True, crim_mode=True)
extractor.save_csvs(
    input_folder=folders['input'],
    output_folder=folders['csv']
)

# (Edit the CSV, then apply)
updater = MEI_Metadata_Updater_Generic(verbose=True)
updater.process_folder(
    input_folder=folders['input'],
    csv_source=os.path.join(folders['csv'], 'crim_extracted_metadata.csv'),
    output_folder=folders['updated'],
    crim_mode=True
)
```

---

## Step 7 (Optional) — Music Feature Corrections

After updating metadata, you can apply music feature corrections to the revised files:

```python
from mei_tools import MEI_Music_Feature_Processor
import glob

music_feature_processor = MEI_Music_Feature_Processor()

for mei_path in sorted(glob.glob(folders['updated'] + '/*.mei')):
    music_feature_processor.process_music_features(
        mei_path,
        folders['features'],
        # --- most common corrections (True = apply) ---
        remove_incipit=True,
        remove_pb=True,
        remove_sb=True,
        remove_annotation=True,
        remove_ligature_bracket=True,
        remove_dir=True,
        remove_variants=True,
        remove_anchored_text=True,
        remove_timestamp=True,
        remove_chord=True,
        check_for_chords=True,
        fix_elisions=True,
        fix_musescore_elisions=False,
        slur_to_tie=True,
        correct_ficta=True,
        voice_labels=True,
        correct_mrests=True,
        # --- less common corrections (False = skip) ---
        remove_senfl_bracket=False,
        remove_empty_verse=False,
        remove_lyrics=False,
        collapse_layers=False,
        correct_cmme_time_signatures=False,
        correct_jrp_time_signatures=False,
        remove_incipit_leuven=False,
    )
```

See the [README](README.md) for a full description of each parameter.

---

## Troubleshooting

### "No .mei files found"
Check that `folders['input']` points to the correct Drive location and that the `.mei` files are directly in that folder (not in subfolders). Re-run the setup cell and confirm the printed paths are correct.

### Changes not appearing after code edits
If you modify mei_tools code locally and re-install, restart the Colab runtime (`Runtime → Restart runtime`) before re-running cells to clear the cached module.

### Composer not appearing in titleStmt
Make sure the `composer_name` column in your CSV is filled in. Blank cells are intentionally ignored. The updater writes the composer as `fileDesc/titleStmt/persName[@role='composer']` (or inside a `respStmt` for MuseScore, Sibelius, and mei-friend files).

### Wrong encoding detected
If a file is classified as the wrong source type, you can override detection by setting the `source_type` column in the CSV to one of: `musescore`, `sibelius`, `humdrum`, `mei_friend`.
