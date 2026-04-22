# MEI Tools: Overview and User Guide

MEI Tools is a Python package for curating and correcting [Music Encoding Initiative (MEI)](https://music-encoding.org/) files. It is designed for projects that produce MEI files from notation software such as **Sibelius** or **MuseScore**, and need to standardize metadata and correct common encoding issues before analysis or publication.

The tools are used as part of the [CRIM (Citations: The Renaissance Imitation Mass)](http://crimproject.org) project and are suitable for any MEI corpus project.

---

## Table of Contents

1. [Subprojects and Tools](#1-subprojects-and-tools)
   - [Metadata Updates](#11-metadata-updates)
   - [Music Feature Corrections](#12-music-feature-corrections)
   - [Encoding Guidelines: Sibelius](#13-encoding-guidelines-sibelius)
   - [Encoding Guidelines: MuseScore](#14-encoding-guidelines-musescore)
2. [Installation](#2-installation)
3. [Running the Tools](#3-running-the-tools)
   - [Local Environment](#31-local-environment-jupyter-notebook)
   - [Google Colab](#32-google-colab)

---

## 1. Subprojects and Tools

### 1.1 Metadata Updates

**Key files:** `mei_tools/mei_metadata_extractor.py`, `mei_tools/mei_metadata_updater_generic.py`, `mei_tools/mei_metadata_processor.py`

**Detailed guides:** [README.md](README.md), [MEI_Tools_in_Google_Colab.md](MEI_Tools_in_Google_Colab.md)

The metadata workflow follows three stages:

```
Extract  →  Edit  →  Update
```

**Stage 1 — Extract**

`MEI_Metadata_Extractor` scans a folder of MEI files and writes one CSV per source type found:

| Source type | CSV filename |
|---|---|
| MuseScore | `muse_score_extracted_metadata.csv` |
| Sibelius | `sib_extracted_metadata.csv` |
| Humdrum / Verovio | `hum_drum_extracted_metadata.csv` |
| mei-friend | `mei_friend_extracted_metadata.csv` |

Source type is auto-detected. If your corpus uses only one application, you get one CSV.

**Stage 2 — Edit**

Open the CSV in Google Sheets, Excel, or any text editor. The key editing rules:

- Leave any cell **blank** to keep the existing MEI content unchanged — only non-empty cells are applied.
- For fields that accept multiple values (`editors`, `distributor`), separate entries with a **pipe character**: `Name One [role]|Name Two [role]`
- The `filename` and `source_type` columns are used to match rows to files — **do not change them**.

The CSV columns produced by extraction are:

| Column | What it contains |
|---|---|
| `filename` | basename of the `.mei` file — **do not edit** |
| `source_type` | auto-detected application type |
| `mei_version` | MEI schema version |
| `title` | main title |
| `title_subordinate` | subordinate or movement titles |
| `composer_name` | composer's name |
| `composer_auth` | authority system, e.g. `VIAF` |
| `composer_auth_uri` | full URI, e.g. `https://viaf.org/viaf/12304462/` |
| `composer_codedval` | coded value within authority (GND) |
| `editors` | pipe-separated list of `Name [role]` entries |
| `encoding_date` | date of encoding, ISO format |
| `rights` | rights / copyright statement |
| `publisher` | publisher name |
| `distributor` | distributor(s), pipe-separated |
| `genre` | genre term |
| `encoding_application` | application name(s) and version(s) |
| `work_title` | title from workList |
| `movement_name` | movement name |
| `source_title` | title of the physical source |
| `source_composer` | composer as recorded in sourceDesc |
| `source_editor` | editor(s) |
| `source_encoder` | encoder(s) |
| `edition_version` | edition version |
| `encoding_annot` | encoding annotation |
| `humdrum_id` | value of the `!!!id` reference key (Humdrum only) |

**Stage 3 — Update**

`MEI_Metadata_Updater_Generic` reads the edited CSV and applies non-empty values back to each MEI file. The CSV can be supplied as:

- A local file path
- A **Google Sheets published URL** (`File → Share → Publish to web → CSV`)
- A **raw GitHub URL**

Updated files are written to the output folder with `_rev` appended to the filename. Original files are never modified.

**CRIM project mode**

If you are working with the CRIM project schema, use `crim_mode=True` for both extraction and update. This uses the CRIM column schema (`MEI_Name`, `Title`, `Composer_VIAF`, `Editor`, etc.) and builds a full MEI header including `manifestationList`.

The CRIM metadata is normally maintained in a Google Sheet and loaded as a list of Python dictionaries — one dict per piece, where keys are column headers and values are cell contents. See [sample_crim_metadata_dict.py](sample_crim_metadata_dict.py) for a complete example entry. Here is what a single dict looks like:

```python
{
    'CRIM_ID':            'CRIM_Model_0001',
    'MEI_Name':           'CRIM_Model_0001.mei',
    'Title':              'Veni speciosam',
    'Mass Title':         '',
    'Genre':              'motet',
    'Composer_Name':      'Johannes Lupi',
    'Composer_VIAF':      'http://viaf.org/viaf/42035469',
    'Piece_Date':         'before 1542',
    'Source_Short_Title': 'Musicae Cantiones',
    'Source_Title':       'Chori Sacre Virginis Marie Cameracensis Magistri ...',
    'Source_Publisher_1': 'Pierre Attaingnant',
    'Publisher_1_VIAF':   'http://viaf.org/viaf/59135590',
    'Source_Date':        '1542',
    'Source_Location':    'Wien',
    'Source_Institution': 'Österreichische Nationalbibliothek',
    'Source_Shelfmark':   'SA.78.C.1/3/1-4 Mus 19',
    'Editor':             'Marco Gurrieri | Bonnie Blackburn | Vincent Besson | Richard Freedman',
    'Rights_Statement':   'This work is licensed under a Creative Commons Attribution-NonCommercial 4.0 International License',
    'Copyright_Owner':    "Centre d'Études Supérieures de la Renaissance | Haverford College | ...",
}
```

To load the full sheet into this format:

```python
import pandas as pd

csv_url = 'https://docs.google.com/spreadsheets/d/e/YOURKEY/pub?output=csv'
df = pd.read_csv(csv_url).fillna('')
crim_metadata_dict_list = df.to_dict(orient='records')
```

---

### 1.2 Music Feature Corrections

**Key file:** `mei_tools/mei_music_feature_processor.py`

**Detailed guide:** [README.md](README.md)

`MEI_Music_Feature_Processor` corrects common encoding issues in MEI files. Each correction is an independently toggleable Boolean parameter — you choose which ones to apply.

```python
music_feature_processor = MEI_Music_Feature_Processor()

for mei_path in sorted(glob.glob('mei_to_process/*.mei')):
    music_feature_processor.process_music_features(
        mei_path,
        output_folder='mei_updated',
        remove_incipit=True,
        fix_elisions=True,
        correct_ficta=True,
        voice_labels=True,
        # ... see full table below
    )
```

**Parameter reference**

| Parameter | Default | Description |
|---|---|---|
| `resolve_multibar_ties` | `True` | Converts `<tie>` chains to `@tie="i/m/t"` attributes on notes |
| `remove_incipit` | `True` | Removes prefatory incipit bar (`label="0"`) and renumbers measures from 1 |
| `remove_incipit_leuven` | `False` | Removes Leuven-style invisible incipit measures |
| `remove_pb` | `True` | Removes `<pb>` page break elements |
| `remove_sb` | `True` | Removes `<sb>` section break elements |
| `remove_annotation` | `True` | Removes `<annot>` annotation elements |
| `remove_ligature_bracket` | `True` | Removes `<bracketSpan>` ligature bracket elements (CMME exports) |
| `remove_dir` | `True` | Removes `<dir>` direction elements |
| `remove_variants` | `True` | Flattens `<app>`/`<lem>`/`<rdg>` apparatus, keeping only lemma notes |
| `remove_anchored_text` | `True` | Removes `<anchoredText>` elements that can distort Verovio rendering |
| `remove_timestamp` | `True` | Strips `tstamp.real` and `vel` attributes from notes, rests, and mRests |
| `remove_chord` | `True` | Removes `<chord>` elements |
| `check_for_chords` | `True` | Reports any remaining `<chord>` elements by measure number (does not remove) |
| `remove_senfl_bracket` | `False` | Removes `<line type="bracket">` elements used in the Senfl Edition |
| `remove_empty_verse` | `False` | Removes empty `<verse>` elements that can distort Verovio layout |
| `remove_lyrics` | `False` | Removes all `<verse>` (lyrics) elements — use when text underlay must be redone |
| `fix_elisions` | `True` | Merges double `<syl>` elements (Sibelius exports) into a single tag with `=` separator |
| `fix_musescore_elisions` | `True` | Fixes MuseScore `con="b"` elision encoding with correct `wordpos` and `con` attributes |
| `slur_to_tie` | `True` | Converts `<slur>` elements to `<tie>` (when editors mistakenly encode ties as slurs) |
| `collapse_layers` | `False` | Merges all non-layer-1 content into layer 1 within each staff |
| `correct_ficta` | `True` | Converts red-colored notes with accidentals into proper MEI `<supplied>` elements |
| `voice_labels` | `True` | Moves `<label>` child text to `@label` attribute on `<staffDef>` (needed for Verovio and CRIM Intervals) |
| `correct_cmme_time_signatures` | `False` | Moves time signature attributes from `<staffDef>` to `<scoreDef>` (CMME files) |
| `correct_jrp_time_signatures` | `False` | Moves `meterSig` elements from JRP `<staffDef>` elements up to `<scoreDef>` |
| `correct_mrests` | `True` | Expands `<mRest>` elements into three semibreve rests (fixes music21 issue under 3/1 mensuration) |

> Note: additional modules can be added based on your experience with particular MEI files.

**Module descriptions**

##### `fix_elisions`
Fixes syllable elisions in MEI files exported from Sibelius. The sibmei plugin produces two `<syl>` elements per elided note. This module merges them into a single tag connected with an underscore (`_`), which is valid MEI and renders correctly in Verovio.

##### `fix_musescore_elisions`
Fixes syllable elisions in MEI files exported from MuseScore. MuseScore encodes elisions with a Unicode character but sets incorrect `wordpos` and `con` attributes on both the affected note and the one preceding it. This module corrects the encoding.

##### `slur_to_tie`
Replaces `<slur>` elements with `<tie>` elements where editors have mistakenly encoded ties as slurs.

##### `correct_ficta`
Converts editorial accidentals to proper `<supplied>` elements. The sibmei plugin stores musica ficta as plain text rather than as a `<supplied>` element. This module finds accidentals associated with red-colored notes and rewrites them as `<supplied reason="edit"><accid .../></supplied>`.

##### `remove_variants`
Removes `<app>`/`<lem>`/`<rdg>` apparatus elements, retaining only the lemma reading. Useful when only a single reading is needed, for example for analysis with CRIM Intervals.

##### `remove_chord`
Removes `<chord>` elements, which are sometimes present in files converted from MusicXML or other formats.

##### `collapse_layers`
Merges all content from non-layer-1 `<layer>` elements into layer 1 within each staff. Useful for files that mistakenly encode notes as being in separate voices on the same staff.

##### `remove_anchored_text`
Removes `<anchoredText>` elements, which can produce unexpected layout effects when files are rendered with Verovio.

##### `remove_incipit`
Removes the prefatory incipit measure (identified by `label="0"` or `n="1"` at the opening) and renumbers all remaining measures so that they start from 1. Incipits typically show original clef and notehead information but disrupt regular measure numbering throughout the rest of the score.

##### `remove_timestamp`
Strips `tstamp.real` and `vel` attributes from notes, rests, and `mRest` elements. These attributes are produced by some conversion routines and are not needed for analysis or rendering.

##### `remove_senfl_bracket`
Removes `<line type="bracket">` elements inserted by editors of the Senfl Edition.

##### `remove_empty_verse`
Removes `<verse>` elements that contain no content. Empty verse elements can distort layout when files are rendered with Verovio.

##### `remove_lyrics`
Removes all `<verse>` elements (lyrics) from the file. Use this when text underlay from a conversion pathway is too corrupted to correct incrementally — the cleaned file can then be reopened in MuseScore for fresh text entry.

##### `voice_labels`
Moves the `<label>` child text of each `<staffDef>` to a `@label` attribute on the `<staffDef>` element itself. This is required for voice names to be recognized by Verovio and CRIM Intervals.

##### `correct_cmme_time_signatures`
For files produced by the CMME project: moves time signature attributes from `<staffDef>` elements to `<scoreDef>`.

##### `correct_jrp_time_signatures`
For files produced by the JRP project: promotes `<meterSig>` elements from `<staffDef>` elements up to `<scoreDef>`.

##### `remove_ligature_bracket`
Removes `<bracketSpan>` elements used for ligatures and coloration in CMME exports.

##### `remove_dir`
Removes `<dir>` direction elements.

##### `check_for_chords`
Reports the location (by measure number) of any `<chord>` elements remaining in the file. Does not remove them — use `remove_chord` for that.

##### `correct_mrests`
music21 does not correctly interpret `<mRest>` values under 3/1 mensuration. This module finds those `<mRest>` elements and replaces each with three explicit semibreve (whole-note) rests.

##### `resolve_multibar_ties`
Converts chains of `<tie>` elements spanning multiple measures into `@tie="i"`, `@tie="m"`, and `@tie="t"` attributes directly on the affected notes.

---

### 1.3 Encoding Guidelines: Sibelius

**Detailed guide:** [Sib_to_MEI_Guide.md](Sib_to_MEI_Guide.md)

**Plugin required:** [sibmei](https://github.com/music-encoding/sibmei) (exports Sibelius files as valid MEI)

**Two Sibelius files per piece**

Unlike MuseScore, Sibelius requires two files:
- An **engraver copy** used to make the final PDF
- An **E-file** used to create the MEI (contains special ficta treatment; may omit incipits)

**Key preparation steps**

| Topic | Guidance |
|---|---|
| **Metadata** | Enter title and composer in Sibelius. For Mass movements, include the movement in the title: `Missa Ave Maria: Kyrie` |
| **Staff names** | Use Sibelius *instrument names* (not staff objects). Use the name given in the source; if unnamed, use `[  ]` |
| **Transposing instruments** | Set transposition in the Sibelius instrument definition. Test by playing the first note — it should sound in the correct octave. For G8va clef parts, define the instrument as "Tenor" then rename it for display |
| **Incipits** | Incipit bar must be numbered "0"; first true measure = "1". MEI Tools can retain or remove the incipit |
| **Measure numbers** | For Mass movements, use continuous bar numbers across all movements (Kyrie, Christe, Kyrie II as a single file) |
| **First/second endings** | Entered normally via Notations > Lines. Measure numbers are continuous across both endings |
| **Time signatures** | CRIM uses unreduced note values. The time signature must match the total notational value count per bar (e.g., `4/2` for Cut C, `3/1` for triple meter). To show `Cut C` in the engraved PDF: hide the real time signature and place a symbol from Notations > Symbols |
| **Rests in 3/1** | Use **three semibreve rests**, not a breve rest — the latter is misread by analysis software. MEI Tools can correct this |
| **Musica ficta** | For the E-file: color the note red, then apply the "Add Ficta Above Note" plug-in (Notations menu). MEI Tools converts these to `<supplied reason="edit">` elements |
| **Lyrics** | Attach each syllable to a note (never a rest or barline). Encode a second verse as "lyrics line 2". Elisions (e.g., `ky-ri-e_e-le-i_son`) use Sibelius's curved line; sibmei exports these as two syllables per note — MEI Tools corrects them to the `_` separator |
| **Ligatures/coloration** | Brackets are exported as `<annot>` elements; MEI Tools can preserve or remove them |
| **Metronome markings** | Hidden in engraving; retained in sibmei output; MEI Tools can remove them |

---

### 1.4 Encoding Guidelines: MuseScore

**Detailed guide:** [MuseScore_to_MEI_Guide.md](MuseScore_to_MEI_Guide.md)

**Assets required** (download from this repository):
- `crim_25.mss` — CRIM style sheet for MuseScore 4 (copy to `MuseScore 4 > Styles` folder)
- `musicaFicta_color.qml` — plug-in for marking musica ficta notes red (copy to `MuseScore 4 > Plugins` folder, then install via the Plug-in Manager)

**One file does it all**

Unlike the Sibelius workflow, a single MuseScore file is used for both PDF export and MEI export — no separate E-file is needed.

**Key preparation steps**

| Topic | Guidance |
|---|---|
| **Style sheet** | Apply `crim_25.mss` via `Format > Load Style`, or set as default under `MuseScore > Preferences > Import` |
| **Metadata** | Add composer, title, and copyright via `File > Project Properties`. Also add `Add > Text > Title` and `Add > Text > Composer` text objects so they appear in the PDF |
| **Staff names** | Name parts after the original source. Use `[  ]` for unnamed parts; distinguish duplicates as `Tenor [1]` and `Tenor [2]`. Double-click a staff name and use the *Replace instrument* button to select a vocal type, then edit the display name |
| **Transposing instruments** | MuseScore's G8va clef exports correctly to MEI with the appropriate octave shift (unlike Sibelius) |
| **Incipits** | Incipit bar = "0"; first true measure = "1". MEI Tools can retain or remove the incipit |
| **Doubling note values** | If importing from a reduced-values MusicXML: select all, `Edit > Copy`, then `Edit > Paste double duration`. For pieces with multiple time signatures, work section by section |
| **Time signatures** | Reset to actual bar values (`4/2` for Cut C, `3/1` for triple). To display `Cut C` in the PDF: right-click the time signature, open *Time Signature Properties*, and choose a display symbol. The underlying meter is preserved in the MEI |
| **Stem directions** | After adjusting durations: select all, then `Format > Reset shapes and positions` |
| **Rhythmic groupings** | To resolve ties to dotted notes: select all, then `Tools > Regroup Rhythms` |
| **Musica ficta** | Select the note, add the accidental via `Palettes > Accidentals`, then apply the `musicaFicta_color` plug-in (`Plugins > Music/arranging tools`). This moves the accidental above the staff and colors the note red. MEI Tools converts these to `<supplied>` elements |
| **Lyrics** | Add via `Add > Text > Lyrics`. For elisions: while in the lyric text box, right-click > *Add Symbols* and choose the small curving connector, then type the second syllable. Post-process with MEI Tools (`fix_musescore_elisions=True`) |
| **First/second endings** | `Palettes > Repeats and Jumps` |
| **Metronome markings** | Delete before export to PDF and MEI; MEI Tools can also remove them |
| **Export** | MEI: `File > Export > MEI`. PDF: `File > Export > PDF`. Both can also be done in batch via the `mscore` command line |

---

## 2. Installation

MEI Tools requires **Python 3.7+**. Install it from GitHub using pip:

```bash
pip install git+https://github.com/RichardFreedman/mei_tools
```

To install a specific branch (e.g., for testing):

```bash
pip install git+https://github.com/RichardFreedman/mei_tools.git@dev-26
```

**Verify the installation** from the terminal:

```bash
python -c "import mei_tools; print('import successful')"
```

Or in a Jupyter notebook cell:

```python
import mei_tools
```

No error message means you are ready to go.

**Dependencies** (installed automatically): `lxml 5.1.0`, `datetime`

---

## 3. Running the Tools

### 3.1 Local Environment (Jupyter Notebook)

Open `01_MEI_Updating_2025.ipynb` from this repository in JupyterLab or VS Code. The notebook contains all steps below in runnable cells.

#### Step 1 — Import libraries

```python
import mei_tools
from mei_tools import MEI_Metadata_Extractor, MEI_Metadata_Updater_Generic, MEI_Music_Feature_Processor
import glob
import os
```

#### Step 2 — Extract metadata to CSV

```python
extractor = MEI_Metadata_Extractor(verbose=True)
extractor.save_csvs(
    input_folder='mei_to_process',
    output_folder='extracted_metadata_csv'
)
```

One CSV is written per source type found. Edit the CSV(s) in Google Sheets, Excel, or any text editor (see [editing rules](#stage-2--edit) above).

#### Step 3 — Apply updated metadata

```python
updater = MEI_Metadata_Updater_Generic(verbose=True)
updater.process_folder(
    input_folder='mei_to_process',
    csv_source='updated_metadata_csv_files/hum_drum_extracted_metadata.csv',
    output_folder='mei_with_updated_metadata'
)
```

The `csv_source` can also be a Google Sheets published URL or a raw GitHub URL.

#### Step 4 — Apply music feature corrections

```python
processor = MEI_Music_Feature_Processor()

for mei_path in sorted(glob.glob('mei_with_updated_metadata/*.mei')):
    processor.process_music_features(
        mei_path,
        output_folder='mei_with_updated_music_features',
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
        fix_musescore_elisions=False,   # set True for MuseScore files
        slur_to_tie=True,
        correct_ficta=True,
        voice_labels=True,
        correct_mrests=True,
        resolve_multibar_ties=True,
        remove_senfl_bracket=False,
        remove_empty_verse=False,
        remove_lyrics=False,
        collapse_layers=False,
        correct_cmme_time_signatures=False,
        correct_jrp_time_signatures=False,
        remove_incipit_leuven=False,
    )
```

Adjust the Boolean flags to match the source type and needs of your corpus. Updated files are saved with `_rev` appended to the filename.

#### CRIM project mode

```python
# Extract with CRIM column schema
extractor = MEI_Metadata_Extractor(verbose=True, crim_mode=True)
extractor.save_csvs(input_folder='mei_to_process', output_folder='extracted_metadata_csv')

# Apply from CRIM Google Sheet published URL
updater = MEI_Metadata_Updater_Generic(verbose=True)
updater.process_folder(
    input_folder='mei_to_process',
    csv_source='https://docs.google.com/spreadsheets/d/e/YOURKEY/pub?output=csv',
    output_folder='mei_with_updated_metadata',
    crim_mode=True
)
```

---

### 3.2 Google Colab

Open `MEI_Tools_in_Google_Colab.ipynb` from this repository directly in Google Colab. The full guide is in [MEI_Tools_in_Google_Colab.md](MEI_Tools_in_Google_Colab.md).

#### Step 1 — Install MEI Tools

```python
!pip install git+https://github.com/RichardFreedman/mei_tools.git@main
```

#### Step 2 — Mount Drive and set up folders

Run this once. Set `input_folder` to the path in your Drive where your `.mei` files live — all output folders are created automatically.

```python
import os
from google.colab import drive

drive.mount('/content/drive')

input_folder = '/content/drive/MyDrive/my_mei_corpus'

base        = os.path.dirname(input_folder)
corpus_name = os.path.basename(input_folder)

folders = {
    'input':         input_folder,
    'extracted_csv': os.path.join(base, corpus_name + '_extracted_csv'),
    'revised_csv':   os.path.join(base, corpus_name + '_revised_csv'),
    'updated_mei':   os.path.join(base, corpus_name + '_updated_mei'),
}

for name, path in folders.items():
    os.makedirs(path, exist_ok=True)
    print(f'{name:15s}  →  {path}')
```

#### Step 3 — Extract metadata to CSV

```python
from mei_tools import MEI_Metadata_Extractor

extractor = MEI_Metadata_Extractor(verbose=True)
extractor.save_csvs(
    input_folder=folders['input'],
    output_folder=folders['extracted_csv']
)
```

#### Step 4 — Edit the CSV

Open the extracted CSV from your Drive in Google Sheets (`File → Import`). Edit the metadata values, then:
- Save back to Drive and use the file path in Step 5 (Option A), **or**
- Publish the sheet as CSV (`File → Share → Publish to web → CSV`) and use the URL in Step 5 (Option B)

#### Step 5 — Apply updated metadata

**Option A — local Drive file:**

```python
from mei_tools import MEI_Metadata_Updater_Generic
import os

csv_source = os.path.join(folders['revised_csv'], 'hum_drum_extracted_metadata.csv')

updater = MEI_Metadata_Updater_Generic(verbose=True)
updater.process_folder(
    input_folder=folders['input'],
    csv_source=csv_source,
    output_folder=folders['updated_mei']
)
```

**Option B — Google Sheets published URL:**

```python
from mei_tools import MEI_Metadata_Updater_Generic

csv_source = 'https://docs.google.com/spreadsheets/d/e/YOURKEY/pub?output=csv'

updater = MEI_Metadata_Updater_Generic(verbose=True)
updater.process_folder(
    input_folder=folders['input'],
    csv_source=csv_source,
    output_folder=folders['updated_mei']
)
```

**Option C — raw GitHub URL:**

```python
csv_source = 'https://raw.githubusercontent.com/yourorg/yourrepo/main/metadata/hum_drum_metadata.csv'

updater = MEI_Metadata_Updater_Generic(verbose=True)
updater.process_folder(
    input_folder=folders['input'],
    csv_source=csv_source,
    output_folder=folders['updated_mei']
)
```

#### Step 6 — Apply music feature corrections (optional)

```python
from mei_tools import MEI_Music_Feature_Processor
import glob

processor = MEI_Music_Feature_Processor()

for mei_path in sorted(glob.glob(folders['updated_mei'] + '/*.mei')):
    processor.process_music_features(
        mei_path,
        folders['updated_mei'],
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
        remove_senfl_bracket=False,
        remove_empty_verse=False,
        remove_lyrics=False,
        collapse_layers=False,
        correct_cmme_time_signatures=False,
        correct_jrp_time_signatures=False,
        remove_incipit_leuven=False,
    )
```

---

## Troubleshooting

**"No .mei files found"** — Check that the input folder path points to the correct location and that `.mei` files are directly in that folder (not in subfolders).

**Changes not appearing after code edits** — In Colab: restart the runtime (`Runtime → Restart runtime`) to clear the cached module, then re-run the install and import cells.

**Composer not appearing in titleStmt** — Make sure the `composer_name` column in your CSV is filled in. Blank cells are intentionally ignored by the updater.

**Wrong source type detected** — You can override auto-detection by setting the `source_type` column in the CSV to one of: `musescore`, `sibelius`, `humdrum`, `mei_friend`.

**Sibelius files: encoding issues after export** — Make sure you are exporting the E-file (not the engraver copy) for MEI. The E-file should have red notes for musica ficta and no decorative symbols in the incipit.

---

## Repository Structure

```
mei_tools/
├── mei_tools/                        # Python package
│   ├── mei_metadata_extractor.py     # Stage 1: extract metadata to CSV
│   ├── mei_metadata_updater_generic.py  # Stage 3: apply CSV back to MEI
│   ├── mei_metadata_processor.py     # CRIM-specific full header writer
│   └── mei_music_feature_processor.py   # Music feature corrections
│
├── 01_MEI_Updating_2025.ipynb        # Main notebook (local use)
├── MEI_Tools_in_Google_Colab.ipynb   # Colab-optimized notebook
│
├── MuseScore Style Sheet and Plug In/
│   ├── crim_25.mss                   # CRIM style sheet for MuseScore 4
│   └── musicaFicta_color.qml         # Plug-in for marking ficta notes red
│
├── sample_mei_files/                 # Sample MEI files for testing
├── sample_extracted_metadata_csv_files/  # Pre-generated CSV samples
├── mei_to_process/                   # Input directory for workflows
├── mei_with_updated_metadata/        # Output: after metadata update
├── mei_with_updated_music_features/  # Output: after music feature corrections
│
├── README.md                         # Full metadata and music feature reference
├── MEI_Tools_in_Google_Colab.md      # Complete Google Colab guide
├── Sib_to_MEI_Guide.md               # Sibelius encoding guidelines
└── MuseScore_to_MEI_Guide.md         # MuseScore encoding guidelines
```

---

## Credits and License

- Richard Freedman (Haverford College, USA)
- Vincent Besson (CESR, Tours, France)

Package version: 2.0.3

This work is licensed under [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/).
