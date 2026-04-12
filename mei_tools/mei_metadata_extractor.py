import os
import csv
import glob
from lxml import etree

# ---------------------------------------------------------------------------
# Shared column order for all extracted CSVs.
# The updater reads these same columns back when applying changes.
# ---------------------------------------------------------------------------
CSV_COLUMNS = [
    'filename',
    'source_type',
    'mei_version',
    # core bibliographic
    'title',
    'title_subordinate',        # mei-friend: subordinate/movement titles (pipe-sep)
    'composer_name',
    'composer_auth',            # authority system name, e.g. VIAF or GND
    'composer_auth_uri',        # base URI of authority, e.g. https://viaf.org/viaf/...
    'composer_codedval',        # coded value within authority (GND uses this)
    'editors',                  # pipe-separated "Name [role]" entries
    'encoding_date',
    'rights',
    'publisher',
    'distributor',              # musescore
    'genre',
    'encoding_application',     # app name + version; pipe-sep if multiple
    # workList fields
    'work_title',
    'movement_name',            # humdrum OMD
    # sourceDesc fields (humdrum)
    'source_title',
    'source_composer',
    'source_editor',            # EED
    'source_encoder',           # ENC
    'edition_version',          # EEV
    'encoding_annot',           # ONB
    'humdrum_id',               # !!!id reference key
]

# Map source_type → output CSV filename stem
SOURCE_TYPE_FILENAMES = {
    'musescore': 'muse_score_extracted_metadata.csv',
    'sibelius':  'sib_extracted_metadata.csv',
    'humdrum':   'hum_drum_extracted_metadata.csv',
    'mei_friend': 'mei_friend_extracted_metadata.csv',
    'unknown':   'unknown_extracted_metadata.csv',
}

# ---------------------------------------------------------------------------
# CRIM-specific column schema
# Matches the column names used in the existing CRIM metadata spreadsheet
# and MEI_Metadata_Updater.apply_metadata().  When crim_mode=True the
# extractor outputs this schema instead of the generic CSV_COLUMNS.
# ---------------------------------------------------------------------------
CRIM_CSV_COLUMNS = [
    'MEI_Name',            # basename of the MEI file (matching key)
    'Title',
    'Composer_Name',
    'Composer_VIAF',       # full VIAF URI, e.g. https://viaf.org/viaf/12345
    'Editor',              # pipe-separated editor names
    'Copyright_Owner',     # pipe-separated copyright holders / distributors
    'Rights_Statement',
    'Genre',
    # Source / edition provenance (written into manifestationList)
    'Source_Title',
    'Source_Publisher_1',
    'Publisher_1_VIAF',
    'Source_Date',
    'Source_Institution',
    'Source_Shelfmark',
    'Source_Location',
    'Source_Publisher_2',
    'Publisher_2_VIAF',
]


def _read_mei_bytes(filepath):
    """
    Read an MEI file and return its content as UTF-8 bytes.

    Sibelius exports are UTF-16 (with a BOM).  We detect the BOM, decode to
    a Python string, rewrite the XML declaration's encoding attribute, then
    re-encode as UTF-8 so lxml can parse it normally.  All other files are
    returned unchanged.
    """
    with open(filepath, 'rb') as fh:
        raw = fh.read()

    # UTF-16 BOM: 0xFF 0xFE (little-endian) or 0xFE 0xFF (big-endian)
    if raw[:2] in (b'\xff\xfe', b'\xfe\xff'):
        text = raw.decode('utf-16')
        # Update the XML declaration so lxml sees consistent encoding info
        text = text.replace('encoding="UTF-16"', 'encoding="UTF-8"')
        text = text.replace("encoding='UTF-16'", "encoding='UTF-8'")
        raw = text.encode('utf-8')

    return raw


class MEI_Metadata_Extractor:
    """
    Extracts metadata from MEI files produced by four different notation
    applications and writes one CSV per source type.

    Supported source types
    ----------------------
    musescore   – MuseScore 4 MEI export (meiversion 5.1+basic)
    sibelius    – Sibelius MEI export via sibmei plug-in (UTF-16, meiversion 4.x)
    humdrum     – Humdrum/Verovio conversion (rich sourceDesc + extMeta frames)
    mei_friend  – mei-friend editor (GND auth, multiple title elements)

    Usage
    -----
    extractor = MEI_Metadata_Extractor(verbose=True)
    extractor.save_csvs(
        input_folder='path/to/mei/corpus',
        output_folder='path/to/csv/output'
    )
    """

    MEI_NS = 'http://www.music-encoding.org/ns/mei'
    HUM_NS = 'http://www.humdrum.org/ns/humxml'

    def __init__(self, verbose=False, crim_mode=False):
        """
        Parameters
        ----------
        verbose : bool
            Print per-file progress messages.
        crim_mode : bool
            When True, output a single CSV using the CRIM project column
            names (MEI_Name, Title, Composer_VIAF, Editor, …) that match
            the existing CRIM metadata spreadsheet and
            MEI_Metadata_Updater.apply_metadata().  All files in the
            corpus go into one CSV called crim_extracted_metadata.csv
            rather than being split by source type.
        """
        self.verbose = verbose
        self.crim_mode = crim_mode

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def save_csvs(self, input_folder, output_folder):
        """
        Process every .mei file in *input_folder* and write CSV(s) into
        *output_folder*.

        Generic mode  – one CSV per detected source type, using the
                        25-column generic schema (CSV_COLUMNS).
        CRIM mode     – a single crim_extracted_metadata.csv covering all
                        files, using the CRIM project column names
                        (CRIM_CSV_COLUMNS).

        Parameters
        ----------
        input_folder : str
            Folder containing MEI files (searched non-recursively).
        output_folder : str
            Folder where CSV files will be written.  Created if absent.
        """
        os.makedirs(output_folder, exist_ok=True)

        if self.crim_mode:
            self._save_crim_csv(input_folder, output_folder)
            return

        grouped = self._process_folder(input_folder)

        if not grouped:
            print('No MEI files found in', input_folder)
            return

        for source_type, rows in grouped.items():
            csv_name = SOURCE_TYPE_FILENAMES.get(source_type,
                                                  f'{source_type}_extracted_metadata.csv')
            csv_path = os.path.join(output_folder, csv_name)
            with open(csv_path, 'w', newline='', encoding='utf-8') as fh:
                writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
                writer.writeheader()
                writer.writerows(rows)
            print(f'Saved {len(rows)} row(s) → {csv_path}')

    # ------------------------------------------------------------------
    # CRIM mode: single CSV with CRIM column names
    # ------------------------------------------------------------------

    def _save_crim_csv(self, input_folder, output_folder):
        """Extract CRIM-schema metadata from all MEI files in one CSV."""
        mei_files = sorted(glob.glob(os.path.join(input_folder, '*.mei')))
        if not mei_files:
            print('No MEI files found in', input_folder)
            return

        rows = []
        for filepath in mei_files:
            if self.verbose:
                print(f'Processing {os.path.basename(filepath)} …')
            try:
                raw  = _read_mei_bytes(filepath)
                root = etree.fromstring(raw)
                rows.append(self._extract_crim_row(root, os.path.basename(filepath)))
            except Exception as exc:
                print(f'  ERROR processing {os.path.basename(filepath)}: {exc}')

        csv_path = os.path.join(output_folder, 'crim_extracted_metadata.csv')
        with open(csv_path, 'w', newline='', encoding='utf-8') as fh:
            writer = csv.DictWriter(fh, fieldnames=CRIM_CSV_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
        print(f'Saved {len(rows)} row(s) → {csv_path}')

    def _extract_crim_row(self, root, filename):
        """
        Extract metadata from a single MEI file into a CRIM-schema dict.

        Fields that were not present in the source file (e.g. manifestation
        provenance in a fresh MuseScore export) are left as empty strings for
        the user to fill in.

        XPaths mirror what MEI_Metadata_Updater.apply_metadata() writes, so
        a CSV produced here can feed directly back into that processor.
        """
        ns  = {'mei': self.MEI_NS}
        row = {col: '' for col in CRIM_CSV_COLUMNS}
        row['MEI_Name'] = filename

        head = root.find('mei:meiHead', namespaces=ns)
        if head is None:
            return row

        file_desc = head.find('mei:fileDesc', namespaces=ns)
        if file_desc is None:
            return row

        # ---- Title ---------------------------------------------------
        # Accept title with or without @type='main'
        ts = file_desc.find('mei:titleStmt', namespaces=ns)
        if ts is not None:
            for t in ts.findall('mei:title', namespaces=ns):
                text = self._text(t)
                if text:
                    row['Title'] = text
                    break

        # ---- Composer + Editors from titleStmt/respStmt --------------
        if ts is not None:
            editors = []
            for pn in ts.findall('.//mei:respStmt/mei:persName', namespaces=ns):
                role = pn.get('role', '')
                name = self._text(pn)
                if role == 'composer':
                    row['Composer_Name'] = name
                    # CRIM stores the full VIAF URI in Composer_VIAF
                    row['Composer_VIAF'] = pn.get('auth.uri', '')
                elif name:
                    editors.append(name)
            # Also handle <composer> directly in titleStmt (Sibelius)
            direct_comp = ts.find('mei:composer', namespaces=ns)
            if direct_comp is not None and not row['Composer_Name']:
                row['Composer_Name'] = self._text(direct_comp)
            row['Editor'] = '|'.join(editors)

        # Also check workList/work/composer for composer if not yet found
        work = root.find('.//mei:workList/mei:work', namespaces=ns)
        if work is not None and not row['Composer_Name']:
            wc = work.find('mei:composer', namespaces=ns)
            if wc is not None:
                row['Composer_Name'] = self._text(wc)
                if not row['Composer_VIAF']:
                    row['Composer_VIAF'] = wc.get('auth.uri', '')

        # ---- pubStmt: Copyright_Owner + Rights_Statement -------------
        pub = file_desc.find('mei:pubStmt', namespaces=ns)
        if pub is not None:
            owners = [
                self._text(d)
                for d in pub.findall('mei:distributor', namespaces=ns)
                if self._text(d)
            ]
            row['Copyright_Owner'] = '|'.join(owners)
            row['Rights_Statement'] = self._text(
                pub.find('mei:availability', namespaces=ns)
            )
            # Sibelius stores rights in availability/useRestrict
            if not row['Rights_Statement']:
                row['Rights_Statement'] = self._text(
                    pub.find('.//mei:availability/mei:useRestrict', namespaces=ns)
                )

        # ---- Genre from workList -------------------------------------
        if work is not None:
            row['Genre'] = self._text(
                work.find('.//mei:classification/mei:termList/mei:term',
                          namespaces=ns)
            )

        # ---- manifestationList (present after a previous CRIM run) ---
        mf_list = root.find('.//mei:manifestationList', namespaces=ns)
        if mf_list is not None:
            mf = mf_list.find('mei:manifestation', namespaces=ns)
            if mf is not None:
                row['Source_Title'] = self._text(
                    mf.find('.//mei:titleStmt/mei:title', namespaces=ns)
                )
                pub1_pn = mf.find('.//mei:pubStmt/mei:publisher/mei:persName',
                                  namespaces=ns)
                if pub1_pn is not None:
                    row['Source_Publisher_1'] = self._text(pub1_pn)
                    row['Publisher_1_VIAF']   = pub1_pn.get('auth.uri', '')

                date_el = mf.find('.//mei:pubStmt/mei:date', namespaces=ns)
                row['Source_Date'] = self._text(date_el)

                repo = mf.find('.//mei:physLoc/mei:repository', namespaces=ns)
                if repo is not None:
                    row['Source_Institution'] = self._text(
                        repo.find('mei:corpName', namespaces=ns))
                    row['Source_Shelfmark']   = self._text(
                        repo.find('mei:identifier', namespaces=ns))
                    row['Source_Location']    = self._text(
                        repo.find('mei:geogName', namespaces=ns))

                # Second publisher is stored directly on manifestation
                pub2_pn = mf.find('mei:persName', namespaces=ns)
                if pub2_pn is not None:
                    row['Source_Publisher_2'] = self._text(pub2_pn)
                    row['Publisher_2_VIAF']   = pub2_pn.get('auth.uri', '')

        return row

    # ------------------------------------------------------------------
    # Internal: folder scan
    # ------------------------------------------------------------------

    def _process_folder(self, input_folder):
        """
        Scan *input_folder* for .mei files, extract metadata, and return a
        dict keyed by source_type, each value being a list of row dicts.
        """
        mei_files = sorted(glob.glob(os.path.join(input_folder, '*.mei')))
        if not mei_files:
            return {}

        grouped = {}
        for filepath in mei_files:
            if self.verbose:
                print(f'Processing {os.path.basename(filepath)} …')
            try:
                row = self._extract_file(filepath)
                stype = row['source_type']
                grouped.setdefault(stype, []).append(row)
            except Exception as exc:
                print(f'  ERROR processing {os.path.basename(filepath)}: {exc}')

        return grouped

    # ------------------------------------------------------------------
    # Internal: single-file extraction
    # ------------------------------------------------------------------

    def _extract_file(self, filepath):
        raw = _read_mei_bytes(filepath)
        root = etree.fromstring(raw)
        filename = os.path.basename(filepath)
        source_type = self._detect_source_type(root)

        dispatch = {
            'musescore': self._extract_musescore,
            'sibelius':  self._extract_sibelius,
            'humdrum':   self._extract_humdrum,
            'mei_friend': self._extract_mei_friend,
        }
        extractor_fn = dispatch.get(source_type, self._extract_generic)
        return extractor_fn(root, filename)

    # ------------------------------------------------------------------
    # Source-type detection
    # ------------------------------------------------------------------

    def _detect_source_type(self, root):
        """
        Infer which application produced this MEI file by inspecting the
        appInfo section and structural markers.

        Priority order:
          1. mei-friend  – application name contains "mei-friend"
          2. sibelius    – application xml:id is "sibmei", or name contains
                           "Sibelius"
          3. humdrum     – extMeta element present, or any <p> contains
                           "Humdrum"
          4. musescore   – application name contains "MuseScore", or
                           meiversion contains "basic"
          5. unknown
        """
        ns = {'mei': self.MEI_NS}

        app_names = []
        app_ids = []
        p_texts = []

        for app in root.findall('.//mei:appInfo/mei:application', namespaces=ns):
            xml_id = app.get(f'{{{self.MEI_NS.replace(self.MEI_NS, "http://www.w3.org/XML/1998/namespace")}}}id', '')
            # xml:id lives in the XML namespace, not MEI namespace
            xml_id = app.get('{http://www.w3.org/XML/1998/namespace}id', '')
            app_ids.append(xml_id.lower())

            name_el = app.find('mei:name', namespaces=ns)
            if name_el is not None and name_el.text:
                app_names.append(name_el.text.lower())

            for p in app.findall('mei:p', namespaces=ns):
                if p.text:
                    p_texts.append(p.text.lower())

        # 1. mei-friend
        if any('mei-friend' in n for n in app_names):
            return 'mei_friend'

        # 2. sibelius
        if any('sibmei' in i for i in app_ids) or any('sibelius' in n for n in app_names):
            return 'sibelius'

        # 3. humdrum – structural marker
        if root.find(f'.//{{{self.HUM_NS}}}frames') is not None:
            return 'humdrum'
        if any('humdrum' in p for p in p_texts):
            return 'humdrum'
        if root.find('.//mei:extMeta', namespaces=ns) is not None:
            return 'humdrum'

        # 4. musescore
        if any('musescore' in n for n in app_names):
            return 'musescore'
        meiversion = root.get('meiversion', '').lower()
        if 'basic' in meiversion:
            return 'musescore'

        return 'unknown'

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _empty_row(self, filename, source_type):
        row = {col: '' for col in CSV_COLUMNS}
        row['filename'] = filename
        row['source_type'] = source_type
        return row

    @staticmethod
    def _text(element):
        """Return stripped text of *element*, or '' if None/empty."""
        if element is None:
            return ''
        return (element.text or '').strip()

    @staticmethod
    def _split_names(raw, role=''):
        """
        Split a raw string containing one or more person names into a
        pipe-separated list of "Name [role]" entries suitable for the
        *editors* CSV column.

        Some sources (Humdrum in particular) concatenate multiple people in
        a single element using " and " or ", " as separators, e.g.
        "Jessie Ann Owens and Scott Metcalfe".  This helper normalises those
        into individual entries so the updater can write each as its own
        <persName> element.

        Parameters
        ----------
        raw : str
            The raw text from the MEI element.
        role : str
            Role label to attach to each name, e.g. 'editor' or 'encoder'.

        Returns
        -------
        list[str]
            E.g. ["Jessie Ann Owens [editor]", "Scott Metcalfe [editor]"]
        """
        if not raw:
            return []

        # Split on " and " first, then on "; " — stop before splitting on ","
        # because surnames can include commas in inverted form ("Owens, Jessie").
        import re
        parts = re.split(r'\s+and\s+|;\s*', raw)
        parts = [p.strip() for p in parts if p.strip()]

        if role:
            return [f'{p} [{role}]' for p in parts]
        return parts

    # ------------------------------------------------------------------
    # Per-source extraction methods
    # ------------------------------------------------------------------

    def _extract_musescore(self, root, filename):
        """
        MuseScore MEI structure
        -----------------------
        fileDesc/titleStmt/title
        fileDesc/titleStmt/respStmt/persName[@role='composer']  ← VIAF auth
        fileDesc/titleStmt/respStmt/persName  (other roles)
        fileDesc/pubStmt/publisher
        fileDesc/pubStmt/distributor
        fileDesc/pubStmt/date[@isodate]
        fileDesc/pubStmt/availability
        encodingDesc/appInfo/application/name
        workList/work/title
        workList/work/composer
        """
        ns = {'mei': self.MEI_NS}
        row = self._empty_row(filename, 'musescore')
        row['mei_version'] = root.get('meiversion', '')

        # Title
        el = root.find('.//mei:fileDesc/mei:titleStmt/mei:title', namespaces=ns)
        row['title'] = self._text(el)

        # People in titleStmt/respStmt
        editors = []
        for pn in root.findall(
                './/mei:fileDesc/mei:titleStmt/mei:respStmt/mei:persName',
                namespaces=ns):
            role = pn.get('role', '')
            name = self._text(pn)
            if role == 'composer':
                row['composer_name'] = name
                row['composer_auth'] = pn.get('auth', '')
                row['composer_auth_uri'] = pn.get('auth.uri', '')
            else:
                if name:
                    editors.append(f'{name} [{role}]' if role else name)
        row['editors'] = '|'.join(editors)

        # pubStmt
        pub = root.find('.//mei:fileDesc/mei:pubStmt', namespaces=ns)
        if pub is not None:
            row['publisher'] = self._text(pub.find('mei:publisher', namespaces=ns))
            distributors = [
                self._text(d)
                for d in pub.findall('mei:distributor', namespaces=ns)
                if self._text(d)
            ]
            row['distributor'] = '|'.join(distributors)
            date_el = pub.find('mei:date', namespaces=ns)
            if date_el is not None:
                row['encoding_date'] = date_el.get('isodate', '') or self._text(date_el)
            row['rights'] = self._text(pub.find('mei:availability', namespaces=ns))

        # Encoding application
        app = root.find('.//mei:encodingDesc/mei:appInfo/mei:application', namespaces=ns)
        if app is not None:
            name_el = app.find('mei:name', namespaces=ns)
            version = app.get('version', '')
            row['encoding_application'] = (
                f'{self._text(name_el)} {version}'.strip() if name_el is not None else ''
            )

        # workList
        work = root.find('.//mei:workList/mei:work', namespaces=ns)
        if work is not None:
            row['work_title'] = self._text(work.find('mei:title', namespaces=ns))
            comp = work.find('mei:composer', namespaces=ns)
            if comp is not None and not row['composer_name']:
                row['composer_name'] = self._text(comp)
                row['composer_auth'] = comp.get('auth', '')
                row['composer_auth_uri'] = comp.get('auth.uri', '')

        return row

    def _extract_sibelius(self, root, filename):
        """
        Sibelius (sibmei) MEI structure
        --------------------------------
        fileDesc/titleStmt/title
        fileDesc/titleStmt/composer          ← direct element, no persName wrapper
        fileDesc/titleStmt/respStmt/persName
        fileDesc/pubStmt/availability/useRestrict
        encodingDesc/appInfo/application[@xml:id='sibmei']
        workList/work/title
        workList/work/composer
        """
        ns = {'mei': self.MEI_NS}
        row = self._empty_row(filename, 'sibelius')
        row['mei_version'] = root.get('meiversion', '')

        # Title
        row['title'] = self._text(
            root.find('.//mei:fileDesc/mei:titleStmt/mei:title', namespaces=ns)
        )

        # Composer (Sibelius places <composer> directly in <titleStmt>)
        row['composer_name'] = self._text(
            root.find('.//mei:fileDesc/mei:titleStmt/mei:composer', namespaces=ns)
        )

        # Other people in respStmt
        editors = []
        for pn in root.findall(
                './/mei:fileDesc/mei:titleStmt/mei:respStmt/mei:persName',
                namespaces=ns):
            role = pn.get('role', '')
            name = self._text(pn)
            if name:
                editors.append(f'{name} [{role}]' if role else name)
        row['editors'] = '|'.join(editors)

        # Rights
        row['rights'] = self._text(
            root.find(
                './/mei:fileDesc/mei:pubStmt/mei:availability/mei:useRestrict',
                namespaces=ns)
        )

        # Encoding application – prefer the sibmei plug-in entry
        for app in root.findall(
                './/mei:encodingDesc/mei:appInfo/mei:application',
                namespaces=ns):
            xml_id = app.get('{http://www.w3.org/XML/1998/namespace}id', '')
            if 'sibmei' in xml_id.lower():
                name_el = app.find('mei:name', namespaces=ns)
                version = app.get('version', '')
                row['encoding_application'] = (
                    f'{self._text(name_el)} {version}'.strip()
                )
                break

        # workList
        work = root.find('.//mei:workList/mei:work', namespaces=ns)
        if work is not None:
            row['work_title'] = self._text(work.find('mei:title', namespaces=ns))
            wl_comp = work.find('mei:composer', namespaces=ns)
            if wl_comp is not None and not row['composer_name']:
                row['composer_name'] = self._text(wl_comp)

        return row

    def _extract_humdrum(self, root, filename):
        """
        Humdrum/Verovio MEI structure
        --------------------------------
        fileDesc/titleStmt/title
        fileDesc/pubStmt/unpub                          (usually a placeholder)
        fileDesc/sourceDesc/source/bibl/title
        fileDesc/sourceDesc/source/bibl/composer/persName
        fileDesc/sourceDesc/source/bibl/editor          (EED)
        fileDesc/sourceDesc/source/bibl/respStmt/persName  (ENC)
        fileDesc/sourceDesc/source/bibl/edition         (EEV)
        fileDesc/sourceDesc/source/bibl/imprint/date
        fileDesc/sourceDesc/source/bibl/availability/useRestrict
        fileDesc/sourceDesc/source/bibl/annot/lg/l      (ONB)
        encodingDesc/appInfo/application/name
        workList/work/title/titlePart[@type='main']
        workList/work/title/titlePart[@type='movementName']
        workList/work/composer/persName
        workList/work/classification/termList/term
        extMeta/frames/metaFrame (referenceKey='id')
        """
        ns = {'mei': self.MEI_NS}
        row = self._empty_row(filename, 'humdrum')
        row['mei_version'] = root.get('meiversion', '')

        # Primary title
        row['title'] = self._text(
            root.find('.//mei:fileDesc/mei:titleStmt/mei:title', namespaces=ns)
        )

        # sourceDesc/bibl
        bibl = root.find(
            './/mei:fileDesc/mei:sourceDesc/mei:source/mei:bibl',
            namespaces=ns)
        if bibl is not None:
            row['source_title'] = self._text(bibl.find('mei:title', namespaces=ns))

            src_comp = bibl.find('.//mei:composer/mei:persName', namespaces=ns)
            if src_comp is not None:
                row['source_composer'] = self._text(src_comp)
                if not row['composer_name']:
                    row['composer_name'] = row['source_composer']

            row['source_editor'] = self._text(bibl.find('mei:editor', namespaces=ns))

            src_enc = bibl.find('.//mei:respStmt/mei:persName', namespaces=ns)
            row['source_encoder'] = self._text(src_enc)

            date_el = bibl.find('.//mei:imprint/mei:date', namespaces=ns)
            if date_el is not None:
                row['encoding_date'] = (
                    date_el.get('isodate', '') or self._text(date_el)
                )

            row['edition_version'] = self._text(bibl.find('mei:edition', namespaces=ns))

            row['rights'] = self._text(
                bibl.find('.//mei:availability/mei:useRestrict', namespaces=ns)
            )

            row['encoding_annot'] = self._text(
                bibl.find('.//mei:annot/mei:lg/mei:l', namespaces=ns)
            )

        # Build a unified editors column by splitting any "and"-separated names
        # from the source_editor and source_encoder fields so that each person
        # becomes a separate "Name [role]" pipe entry.  The updater then writes
        # each entry as its own <persName> element.
        editor_entries = self._split_names(row['source_editor'], role='editor')
        encoder_entries = self._split_names(row['source_encoder'], role='encoder')
        all_entries = editor_entries + encoder_entries
        if all_entries:
            row['editors'] = '|'.join(all_entries)

        # Encoding application
        app = root.find(
            './/mei:encodingDesc/mei:appInfo/mei:application',
            namespaces=ns)
        if app is not None:
            name_el = app.find('mei:name', namespaces=ns)
            version = app.get('version', '')
            row['encoding_application'] = (
                f'{self._text(name_el)} {version}'.strip() if name_el is not None else ''
            )

        # workList
        work = root.find('.//mei:workList/mei:work', namespaces=ns)
        if work is not None:
            main_part = work.find(
                './/mei:title/mei:titlePart[@type="main"]', namespaces=ns)
            if main_part is not None:
                row['work_title'] = self._text(main_part)
            else:
                row['work_title'] = self._text(work.find('mei:title', namespaces=ns))

            mvt_part = work.find(
                './/mei:title/mei:titlePart[@type="movementName"]', namespaces=ns)
            row['movement_name'] = self._text(mvt_part)

            wl_comp = work.find('.//mei:composer/mei:persName', namespaces=ns)
            if wl_comp is not None and not row['composer_name']:
                row['composer_name'] = self._text(wl_comp)

            genre_el = work.find(
                './/mei:classification/mei:termList/mei:term', namespaces=ns)
            row['genre'] = self._text(genre_el)

        # humdrum_id from extMeta frames
        hum_ns = self.HUM_NS
        for frame in root.findall(f'.//{{{hum_ns}}}metaFrame'):
            fi = frame.find(f'{{{hum_ns}}}frameInfo')
            if fi is None:
                continue
            ref_key = fi.find(f'{{{hum_ns}}}referenceKey')
            ref_val = fi.find(f'{{{hum_ns}}}referenceValue')
            if ref_key is not None and ref_key.text == 'id':
                row['humdrum_id'] = (ref_val.text or '').strip() if ref_val is not None else ''
                break

        return row

    def _extract_mei_friend(self, root, filename):
        """
        mei-friend MEI structure
        ------------------------
        fileDesc/titleStmt/title           (no @type = main title)
        fileDesc/titleStmt/title[@type]    (subordinate titles, pipe-separated)
        fileDesc/titleStmt/respStmt/persName[@role='composer']  ← GND auth
        fileDesc/titleStmt/respStmt/persName[@role='encoder']
        fileDesc/pubStmt/respStmt/persName[@role='encoder']
        encodingDesc/appInfo/application   (multiple: Verovio + mei-friend)
        """
        ns = {'mei': self.MEI_NS}
        row = self._empty_row(filename, 'mei_friend')
        row['mei_version'] = root.get('meiversion', '')

        # Titles
        main_titles, sub_titles = [], []
        for t in root.findall(
                './/mei:fileDesc/mei:titleStmt/mei:title', namespaces=ns):
            text = self._text(t)
            if not text:
                continue
            if t.get('type') is None:
                main_titles.append(text)
            else:
                sub_titles.append(text)
        if main_titles:
            row['title'] = main_titles[0]
        if sub_titles:
            row['title_subordinate'] = '|'.join(sub_titles)

        # People in titleStmt/respStmt
        editors = []
        for pn in root.findall(
                './/mei:fileDesc/mei:titleStmt/mei:respStmt/mei:persName',
                namespaces=ns):
            role = pn.get('role', '')
            name = self._text(pn)
            if role == 'composer':
                row['composer_name'] = name
                row['composer_auth'] = pn.get('auth', '')
                row['composer_auth_uri'] = pn.get('auth.uri', '')
                row['composer_codedval'] = pn.get('codedval', '')
            elif role == 'encoder':
                if name:
                    editors.append(f'{name} [encoder]')
                # encoding date may be stored as @enddate on the encoder element
                enddate = pn.get('enddate', '')
                if enddate and not row['encoding_date']:
                    row['encoding_date'] = enddate[:10]
            else:
                if name:
                    editors.append(f'{name} [{role}]' if role else name)

        # Also check pubStmt/respStmt for additional encoder entries
        for pn in root.findall(
                './/mei:fileDesc/mei:pubStmt/mei:respStmt/mei:persName',
                namespaces=ns):
            role = pn.get('role', '')
            name = self._text(pn)
            if name:
                entry = f'{name} [{role}]' if role else name
                if entry not in editors:
                    editors.append(entry)

        row['editors'] = '|'.join(editors)

        # Encoding applications – list all (Verovio + mei-friend typically)
        app_entries = []
        for app in root.findall(
                './/mei:encodingDesc/mei:appInfo/mei:application',
                namespaces=ns):
            name_el = app.find('mei:name', namespaces=ns)
            version = app.get('version', '')
            if name_el is not None and name_el.text:
                app_entries.append(f'{self._text(name_el)} {version}'.strip())
        row['encoding_application'] = '|'.join(app_entries)

        return row

    def _extract_generic(self, root, filename):
        """
        Fallback extractor for unrecognised source types.
        Pulls whatever common fields it can find.
        """
        ns = {'mei': self.MEI_NS}
        row = self._empty_row(filename, 'unknown')
        row['mei_version'] = root.get('meiversion', '')
        row['title'] = self._text(
            root.find('.//mei:fileDesc/mei:titleStmt/mei:title', namespaces=ns)
        )
        return row
