"""
mei_metadata_updater_generic.py
================================
Source-type-aware MEI metadata updater.

Reads a CSV produced (and hand-edited) by MEI_Metadata_Extractor, then
applies the values to every MEI file in a corpus folder.  The update
logic mirrors the extraction logic: each source type (musescore, sibelius,
humdrum, mei_friend) stores metadata in different locations, and this
module writes to those same locations.

Design principles
-----------------
* Non-destructive: fields whose CSV cell is empty are left as-is in the
  MEI file.  Only non-empty CSV values trigger a change.
* Pipe-separated lists (editors, distributors) are split and written as
  individual elements.
* UTF-16 Sibelius files are silently converted to UTF-8 on read; all
  output is always UTF-8.
* No project-specific hardcoding: publisher, rights, etc. all come from
  the CSV.

CRIM mode
---------
Pass crim_mode=True to process_folder() when working with the CRIM
project.  In this mode:

* The CSV is expected to use CRIM column names (MEI_Name, Title,
  Composer_VIAF, Editor, Copyright_Owner, Rights_Statement, Genre,
  Source_Title, Source_Publisher_1 … Publisher_2_VIAF) — exactly the
  schema produced by MEI_Metadata_Extractor(crim_mode=True).
* Each file is matched by its MEI_Name column rather than filename.
* Processing is delegated to MEI_Metadata_Updater.apply_metadata(),
  which writes the full CRIM header including manifestationList.

Usage
-----
    # Generic (non-CRIM) workflow
    updater = MEI_Metadata_Updater_Generic(verbose=True)
    updater.process_folder(
        input_folder='mei_to_process',
        csv_source='updated_metadata_csv_files/sib_updated_metadata.csv',
        output_folder='mei_updated'
    )

    # CRIM workflow — uses existing CRIM processor internally
    updater = MEI_Metadata_Updater_Generic(verbose=True)
    updater.process_folder(
        input_folder='mei_to_process',
        csv_source='crim_updated_metadata.csv',   # or a Google Sheets URL
        output_folder='mei_updated',
        crim_mode=True
    )
"""

import os
import csv
import glob
import urllib.request
from copy import deepcopy
from datetime import datetime
from lxml import etree

from .mei_metadata_extractor import _read_mei_bytes, CSV_COLUMNS

MEI_NS  = 'http://www.music-encoding.org/ns/mei'
HUM_NS  = 'http://www.humdrum.org/ns/humxml'
XML_NS  = 'http://www.w3.org/XML/1998/namespace'


def _ns(tag):
    """Return a Clark-notation MEI tag, e.g. '{http://...}title'."""
    return f'{{{MEI_NS}}}{tag}'


def _find_or_create(parent, tag, namespaces=None):
    """
    Find *tag* (MEI-namespaced) as a direct child of *parent*.
    Create and append it if absent.  Returns the element.
    """
    ns_tag = _ns(tag)
    el = parent.find(f'mei:{tag}', namespaces={'mei': MEI_NS})
    if el is None:
        el = etree.SubElement(parent, ns_tag)
    return el


class MEI_Metadata_Updater_Generic:
    """
    Apply metadata edits from a CSV file to a corpus of MEI files.

    Each row in the CSV must have a 'filename' column matching the
    basename of an MEI file in the input folder.  Only columns with
    non-empty values are applied; blank cells leave the existing MEI
    content untouched.
    """

    def __init__(self, verbose=False):
        self.verbose = verbose

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def process_folder(self, input_folder, csv_source, output_folder,
                       crim_mode=False):
        """
        Update every MEI file in *input_folder* that has a matching row
        in *csv_source*, writing results to *output_folder*.

        Parameters
        ----------
        input_folder : str
            Folder containing MEI files to process.
        csv_source : str
            Local file path **or** URL to a CSV file (e.g. Google Sheets
            "publish as CSV" link).
        output_folder : str
            Destination folder.  Created if absent.
        crim_mode : bool
            When True, match rows by the 'MEI_Name' column and delegate
            each file to MEI_Metadata_Updater.apply_metadata(), which
            writes the full CRIM header including manifestationList.
            The CSV must use CRIM column names (as produced by
            MEI_Metadata_Extractor(crim_mode=True)).
        """
        os.makedirs(output_folder, exist_ok=True)

        metadata = self.load_csv(csv_source)
        if not metadata:
            print('No metadata rows loaded from', csv_source)
            return

        # Choose key column based on mode
        key_col = 'MEI_Name' if crim_mode else 'filename'
        lookup  = {row[key_col]: row for row in metadata if row.get(key_col)}

        mei_files = sorted(glob.glob(os.path.join(input_folder, '*.mei')))
        if not mei_files:
            print('No .mei files found in', input_folder)
            return

        if crim_mode:
            # Import here to avoid circular dependency at module level
            from .mei_metadata_processor import MEI_Metadata_Updater
            crim_updater = MEI_Metadata_Updater(verbose=self.verbose)

        matched = skipped = 0
        for filepath in mei_files:
            basename = os.path.basename(filepath)
            if basename not in lookup:
                if self.verbose:
                    print(f'  No CSV row for {basename} — skipping')
                skipped += 1
                continue
            try:
                if crim_mode:
                    crim_updater.apply_metadata(
                        filepath, lookup[basename], output_folder
                    )
                else:
                    self._update_file(filepath, lookup[basename], output_folder)
                matched += 1
            except Exception as exc:
                print(f'  ERROR updating {basename}: {exc}')
                skipped += 1

        print(f'Done. Updated {matched} file(s), skipped {skipped}.')

    def load_csv(self, csv_source):
        """
        Load a CSV from a local path or a URL.

        Returns a list of dicts (one per row), using CSV_COLUMNS as the
        expected field names.  Extra columns in the CSV are preserved so
        user annotations are not lost.

        Parameters
        ----------
        csv_source : str
            Local file path or http(s):// URL.
        """
        if csv_source.startswith('http://') or csv_source.startswith('https://'):
            with urllib.request.urlopen(csv_source) as resp:
                content = resp.read().decode('utf-8')
            rows = list(csv.DictReader(content.splitlines()))
        else:
            with open(csv_source, encoding='utf-8', newline='') as fh:
                rows = list(csv.DictReader(fh))

        if self.verbose:
            print(f'Loaded {len(rows)} row(s) from {csv_source}')
        return rows

    # ------------------------------------------------------------------
    # Internal: single-file update
    # ------------------------------------------------------------------

    def _update_file(self, filepath, update_dict, output_folder):
        basename = os.path.basename(filepath)
        stem     = os.path.splitext(basename)[0]
        out_name = stem + '_rev.mei'
        out_path = os.path.join(output_folder, out_name)

        if self.verbose:
            print(f'Updating {basename} …')

        raw  = _read_mei_bytes(filepath)
        root = etree.fromstring(raw)

        source_type = update_dict.get('source_type', '').lower()
        # Allow auto-detection if the CSV cell is blank
        if not source_type:
            source_type = self._detect_source_type(root)

        dispatch = {
            'musescore':  self._update_musescore,
            'sibelius':   self._update_sibelius,
            'humdrum':    self._update_humdrum,
            'mei_friend': self._update_mei_friend,
        }
        update_fn = dispatch.get(source_type, self._update_generic)
        update_fn(root, update_dict)

        # Stamp the updater in appInfo
        self._stamp_appinfo(root)

        # Remove xml:id attributes from the entire meiHead
        ns = {'mei': MEI_NS}
        head = root.find('mei:meiHead', namespaces=ns)
        if head is not None:
            self._remove_ids(head)

        etree.indent(root, space='    ')
        xml_bytes = etree.tostring(
            root,
            pretty_print=True,
            encoding='utf-8',
            xml_declaration=True,
        )
        with open(out_path, 'wb') as fh:
            fh.write(xml_bytes)

        print(f'  Saved {out_name}')

    # ------------------------------------------------------------------
    # Source-type detection  (mirrors mei_metadata_extractor)
    # ------------------------------------------------------------------

    def _detect_source_type(self, root):
        ns = {'mei': MEI_NS}
        app_names, app_ids, p_texts = [], [], []

        for app in root.findall('.//mei:appInfo/mei:application', namespaces=ns):
            app_ids.append(
                app.get(f'{{{XML_NS}}}id', '').lower()
            )
            name_el = app.find('mei:name', namespaces=ns)
            if name_el is not None and name_el.text:
                app_names.append(name_el.text.lower())
            for p in app.findall('mei:p', namespaces=ns):
                if p.text:
                    p_texts.append(p.text.lower())

        if any('mei-friend' in n for n in app_names):
            return 'mei_friend'
        if any('sibmei' in i for i in app_ids) or any('sibelius' in n for n in app_names):
            return 'sibelius'
        if root.find(f'.//{{{HUM_NS}}}frames') is not None:
            return 'humdrum'
        if any('humdrum' in p for p in p_texts):
            return 'humdrum'
        if root.find('.//mei:extMeta', namespaces=ns) is not None:
            return 'humdrum'
        if any('musescore' in n for n in app_names):
            return 'musescore'
        if 'basic' in root.get('meiversion', '').lower():
            return 'musescore'
        return 'unknown'

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _val(update_dict, key):
        """Return stripped value from dict; empty string if absent/blank."""
        return (update_dict.get(key) or '').strip()

    @staticmethod
    def _remove_ids(element):
        """Recursively remove xml:id attributes from *element* and its children."""
        attrib_key = f'{{{XML_NS}}}id'
        if attrib_key in element.attrib:
            del element.attrib[attrib_key]
        for child in element:
            MEI_Metadata_Updater_Generic._remove_ids(child)

    def _stamp_appinfo(self, root):
        """Add / replace an MEI Metadata Updater entry in encodingDesc/appInfo."""
        ns = {'mei': MEI_NS}
        head = root.find('mei:meiHead', namespaces=ns)
        if head is None:
            return

        enc_desc = _find_or_create(head, 'encodingDesc')
        app_info = _find_or_create(enc_desc, 'appInfo')

        # Remove any pre-existing updater stamp to avoid duplicates
        for app in app_info.findall('mei:application', namespaces=ns):
            name_el = app.find('mei:name', namespaces=ns)
            if name_el is not None and 'MEI Metadata Updater' in (name_el.text or ''):
                app_info.remove(app)

        stamp = etree.SubElement(app_info, _ns('application'))
        stamp.set('version', '2.0.3')
        stamp.set('isodate', datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))
        name_el = etree.SubElement(stamp, _ns('name'))
        name_el.text = 'MEI Metadata Updater Generic'

    # ------------------------------------------------------------------
    # Shared helper: composer in titleStmt/respStmt
    # ------------------------------------------------------------------

    def _write_composer_to_titlestmt(self, title_stmt, d, ns):
        """
        Ensure the composer is recorded as
            titleStmt/respStmt/persName[@role='composer']
        with authority attributes if provided.

        This is required by Music21 and CRIM Intervals for all source types.
        Called by every per-source update method so the location is consistent
        regardless of where else the composer may be recorded natively.
        """
        if not self._val(d, 'composer_name'):
            return

        resp_stmt = _find_or_create(title_stmt, 'respStmt')

        # Find existing composer persName or create one
        comp_pn = None
        for pn in resp_stmt.findall('mei:persName', namespaces=ns):
            if pn.get('role') == 'composer':
                comp_pn = pn
                break
        if comp_pn is None:
            # Insert before any editor entries so composer comes first
            comp_pn = etree.Element(_ns('persName'))
            resp_stmt.insert(0, comp_pn)

        comp_pn.set('role', 'composer')
        comp_pn.text = self._val(d, 'composer_name')
        if self._val(d, 'composer_auth'):
            comp_pn.set('auth', self._val(d, 'composer_auth'))
        if self._val(d, 'composer_auth_uri'):
            comp_pn.set('auth.uri', self._val(d, 'composer_auth_uri'))
        if self._val(d, 'composer_codedval'):
            comp_pn.set('codedval', self._val(d, 'composer_codedval'))

    # ------------------------------------------------------------------
    # Per-source update methods
    # ------------------------------------------------------------------

    def _update_musescore(self, root, d):
        """
        Update a MuseScore-origin MEI file.

        Writable fields
        ---------------
        title, composer_name / composer_auth / composer_auth_uri,
        editors (pipe-separated "Name [role]"),
        publisher, distributor (pipe-separated), encoding_date, rights,
        work_title, genre
        """
        ns = {'mei': MEI_NS}
        head = root.find('mei:meiHead', namespaces=ns)
        file_desc = _find_or_create(head, 'fileDesc')

        # ---- titleStmt -----------------------------------------------
        title_stmt = _find_or_create(file_desc, 'titleStmt')

        if self._val(d, 'title'):
            title_el = _find_or_create(title_stmt, 'title')
            title_el.text = self._val(d, 'title')

        self._write_composer_to_titlestmt(title_stmt, d, ns)

        resp_stmt = _find_or_create(title_stmt, 'respStmt')

        if self._val(d, 'editors'):
            # Remove existing non-composer persNames then rebuild
            for pn in list(resp_stmt.findall('mei:persName', namespaces=ns)):
                if pn.get('role') != 'composer':
                    resp_stmt.remove(pn)
            for entry in self._val(d, 'editors').split('|'):
                entry = entry.strip()
                if not entry:
                    continue
                name, role = self._parse_editor_entry(entry)
                pn = etree.SubElement(resp_stmt, _ns('persName'))
                pn.text = name
                if role:
                    pn.set('role', role)

        # ---- pubStmt -------------------------------------------------
        pub_stmt = _find_or_create(file_desc, 'pubStmt')

        if self._val(d, 'publisher'):
            pub_el = _find_or_create(pub_stmt, 'publisher')
            pub_el.text = self._val(d, 'publisher')

        if self._val(d, 'distributor'):
            # Remove existing distributors, then rebuild
            for dist in list(pub_stmt.findall('mei:distributor', namespaces=ns)):
                pub_stmt.remove(dist)
            for item in self._val(d, 'distributor').split('|'):
                item = item.strip()
                if item:
                    dist_el = etree.SubElement(pub_stmt, _ns('distributor'))
                    dist_el.text = item

        if self._val(d, 'encoding_date'):
            date_el = _find_or_create(pub_stmt, 'date')
            date_el.set('isodate', self._val(d, 'encoding_date'))

        if self._val(d, 'rights'):
            avail_el = _find_or_create(pub_stmt, 'availability')
            avail_el.text = self._val(d, 'rights')

        # ---- workList ------------------------------------------------
        self._update_worklist_basic(root, d, ns)

    def _update_sibelius(self, root, d):
        """
        Update a Sibelius-origin MEI file.

        Writable fields
        ---------------
        title, composer_name,
        editors (pipe-separated, written into respStmt),
        rights (written to pubStmt/availability/useRestrict),
        work_title
        """
        ns = {'mei': MEI_NS}
        head = root.find('mei:meiHead', namespaces=ns)
        file_desc = _find_or_create(head, 'fileDesc')
        title_stmt = _find_or_create(file_desc, 'titleStmt')

        if self._val(d, 'title'):
            title_el = _find_or_create(title_stmt, 'title')
            title_el.text = self._val(d, 'title')

        if self._val(d, 'composer_name'):
            # Keep the native Sibelius <composer> element
            comp_el = _find_or_create(title_stmt, 'composer')
            comp_el.text = self._val(d, 'composer_name')

        # Also write composer into titleStmt/respStmt/persName[@role='composer']
        # so Music21 and CRIM Intervals can locate it consistently
        self._write_composer_to_titlestmt(title_stmt, d, ns)

        if self._val(d, 'editors'):
            resp_stmt = _find_or_create(title_stmt, 'respStmt')
            # Clear existing non-empty persNames
            for pn in list(resp_stmt.findall('mei:persName', namespaces=ns)):
                if self._text_of(pn):
                    resp_stmt.remove(pn)
            for entry in self._val(d, 'editors').split('|'):
                entry = entry.strip()
                if not entry:
                    continue
                name, role = self._parse_editor_entry(entry)
                pn = etree.SubElement(resp_stmt, _ns('persName'))
                pn.text = name
                if role:
                    pn.set('role', role)

        if self._val(d, 'rights'):
            pub_stmt  = _find_or_create(file_desc, 'pubStmt')
            avail_el  = _find_or_create(pub_stmt,  'availability')
            restrict_el = _find_or_create(avail_el, 'useRestrict')
            restrict_el.text = self._val(d, 'rights')

        if self._val(d, 'work_title'):
            work = root.find('.//mei:workList/mei:work', namespaces=ns)
            if work is not None:
                wt = _find_or_create(work, 'title')
                wt.text = self._val(d, 'work_title')
                wc = work.find('mei:composer', namespaces=ns)
                if wc is not None and self._val(d, 'composer_name'):
                    wc.text = self._val(d, 'composer_name')

    def _update_humdrum(self, root, d):
        """
        Update a Humdrum/Verovio-origin MEI file.

        Writable fields
        ---------------
        title, source_title, source_composer / composer_name,
        source_editor (EED), source_encoder (ENC), edition_version (EEV),
        encoding_date, rights, encoding_annot (ONB),
        work_title, movement_name, genre
        """
        ns = {'mei': MEI_NS}
        head = root.find('mei:meiHead', namespaces=ns)
        file_desc = _find_or_create(head, 'fileDesc')

        # Primary titleStmt title + composer
        ts = _find_or_create(file_desc, 'titleStmt')
        if self._val(d, 'title'):
            _find_or_create(ts, 'title').text = self._val(d, 'title')

        # Write composer DIRECTLY into titleStmt/persName[@role='composer'].
        # Humdrum/Verovio format places persName as a direct child of titleStmt
        # (not inside respStmt).  Music21 and CRIM Intervals locate it via the
        # role attribute regardless of the wrapper.
        composer_name = self._val(d, 'composer_name')
        if composer_name:
            # Find or create persName[@role='composer'] directly in titleStmt
            comp_pn = None
            for pn in ts.findall('mei:persName', namespaces=ns):
                if pn.get('role') == 'composer':
                    comp_pn = pn
                    break
            if comp_pn is None:
                comp_pn = etree.SubElement(ts, _ns('persName'))
            comp_pn.set('role', 'composer')
            comp_pn.text = composer_name
            if self._val(d, 'composer_auth'):
                comp_pn.set('auth', self._val(d, 'composer_auth'))
            if self._val(d, 'composer_auth_uri'):
                comp_pn.set('auth.uri', self._val(d, 'composer_auth_uri'))
            if self._val(d, 'composer_codedval'):
                comp_pn.set('codedval', self._val(d, 'composer_codedval'))

        # sourceDesc/source/bibl
        source_desc = _find_or_create(file_desc, 'sourceDesc')
        source = source_desc.find('mei:source', namespaces=ns)
        if source is None:
            source = etree.SubElement(source_desc, _ns('source'))
            source.set('type', 'digital')
        bibl = _find_or_create(source, 'bibl')

        if self._val(d, 'source_title'):
            _find_or_create(bibl, 'title').text = self._val(d, 'source_title')

        composer_name = self._val(d, 'composer_name') or self._val(d, 'source_composer')
        if composer_name:
            comp_el   = _find_or_create(bibl, 'composer')
            pers_name = _find_or_create(comp_el, 'persName')
            pers_name.text = composer_name

        # Write editors from the unified 'editors' column (pipe-separated
        # "Name [role]" entries).  Each entry becomes its own <persName>
        # element in a <respStmt> within the <bibl>.  We also keep the
        # legacy <editor> element for Humdrum compatibility when the
        # source_editor cell is still populated.
        if self._val(d, 'editors'):
            # Remove any pre-existing editor/respStmt people entries so we
            # don't accumulate duplicates on repeated runs.
            old_editor = bibl.find('mei:editor', namespaces=ns)
            if old_editor is not None:
                bibl.remove(old_editor)
            old_resp = bibl.find('mei:respStmt', namespaces=ns)
            if old_resp is not None:
                bibl.remove(old_resp)

            resp_stmt = etree.SubElement(bibl, _ns('respStmt'))
            for entry in self._val(d, 'editors').split('|'):
                entry = entry.strip()
                if not entry:
                    continue
                name, role = self._parse_editor_entry(entry)
                pn = etree.SubElement(resp_stmt, _ns('persName'))
                pn.text = name
                if role:
                    pn.set('role', role)
                    # Preserve Humdrum analog attributes for known roles
                    if role == 'editor':
                        pn.set('analog', 'humdrum:EED')
                    elif role == 'encoder':
                        pn.set('analog', 'humdrum:ENC')

        elif self._val(d, 'source_editor') or self._val(d, 'source_encoder'):
            # Fallback: user only filled the source_* columns (not editors).
            # Write them individually using the same <respStmt> pattern.
            resp_stmt = _find_or_create(bibl, 'respStmt')
            if self._val(d, 'source_editor'):
                for name in self._parse_name_list(self._val(d, 'source_editor')):
                    pn = etree.SubElement(resp_stmt, _ns('persName'))
                    pn.text = name
                    pn.set('role', 'editor')
                    pn.set('analog', 'humdrum:EED')
            if self._val(d, 'source_encoder'):
                for name in self._parse_name_list(self._val(d, 'source_encoder')):
                    pn = etree.SubElement(resp_stmt, _ns('persName'))
                    pn.text = name
                    pn.set('role', 'encoder')
                    pn.set('analog', 'humdrum:ENC')

        if self._val(d, 'edition_version'):
            ed_el = bibl.find('mei:edition', namespaces=ns)
            if ed_el is None:
                ed_el = etree.SubElement(bibl, _ns('edition'))
                ed_el.set('type', 'version')
                ed_el.set('analog', 'humdrum:EEV')
            ed_el.text = self._val(d, 'edition_version')

        if self._val(d, 'encoding_date'):
            imprint = _find_or_create(bibl, 'imprint')
            date_el = imprint.find('mei:date', namespaces=ns)
            if date_el is None:
                date_el = etree.SubElement(imprint, _ns('date'))
                date_el.set('type', 'encodingDate')
                date_el.set('analog', 'humdrum:END')
            date_el.set('isodate', self._val(d, 'encoding_date'))
            date_el.text = self._val(d, 'encoding_date')

        if self._val(d, 'rights'):
            avail = _find_or_create(bibl, 'availability')
            restrict_el = avail.find('mei:useRestrict', namespaces=ns)
            if restrict_el is None:
                restrict_el = etree.SubElement(avail, _ns('useRestrict'))
                restrict_el.set('type', 'copyright')
                restrict_el.set('analog', 'humdrum:YEC')
            restrict_el.text = self._val(d, 'rights')

        if self._val(d, 'encoding_annot'):
            annot = _find_or_create(bibl, 'annot')
            lg    = _find_or_create(annot, 'lg')
            l_el  = lg.find('mei:l', namespaces=ns)
            if l_el is None:
                l_el = etree.SubElement(lg, _ns('l'))
                l_el.set('type', 'humdrum:ONB')
            l_el.text = self._val(d, 'encoding_annot')

        # workList
        work = root.find('.//mei:workList/mei:work', namespaces=ns)
        if work is not None:
            if self._val(d, 'work_title'):
                title_el = work.find('mei:title', namespaces=ns)
                if title_el is None:
                    title_el = etree.SubElement(work, _ns('title'))
                    title_el.set('type', 'uniform')
                main_part = title_el.find(
                    'mei:titlePart[@type="main"]', namespaces=ns)
                if main_part is None:
                    main_part = etree.SubElement(title_el, _ns('titlePart'))
                    main_part.set('type', 'main')
                    main_part.set('analog', 'humdrum:OTL')
                main_part.text = self._val(d, 'work_title')

            if self._val(d, 'movement_name'):
                title_el = work.find('mei:title', namespaces=ns)
                if title_el is not None:
                    mvt_part = title_el.find(
                        'mei:titlePart[@type="movementName"]', namespaces=ns)
                    if mvt_part is None:
                        mvt_part = etree.SubElement(title_el, _ns('titlePart'))
                        mvt_part.set('type', 'movementName')
                        mvt_part.set('analog', 'humdrum:OMD')
                    mvt_part.text = self._val(d, 'movement_name')

            if self._val(d, 'genre'):
                classif = _find_or_create(work, 'classification')
                term_list = _find_or_create(classif, 'termList')
                term_el = term_list.find('mei:term', namespaces=ns)
                if term_el is None:
                    term_el = etree.SubElement(term_list, _ns('term'))
                    term_el.set('label', 'genre')
                    term_el.set('analog', 'humdrum:AGN')
                term_el.text = self._val(d, 'genre')

    def _update_mei_friend(self, root, d):
        """
        Update a mei-friend-origin MEI file.

        Writable fields
        ---------------
        title, title_subordinate (pipe-separated),
        composer_name / composer_auth / composer_auth_uri / composer_codedval,
        editors (pipe-separated), encoding_date
        """
        ns = {'mei': MEI_NS}
        head = root.find('mei:meiHead', namespaces=ns)
        file_desc = _find_or_create(head, 'fileDesc')
        title_stmt = _find_or_create(file_desc, 'titleStmt')

        if self._val(d, 'title'):
            # Update the first title element without a @type attribute
            main_found = False
            for t in title_stmt.findall('mei:title', namespaces=ns):
                if t.get('type') is None:
                    t.text = self._val(d, 'title')
                    main_found = True
                    break
            if not main_found:
                t = etree.SubElement(title_stmt, _ns('title'))
                t.text = self._val(d, 'title')

        if self._val(d, 'title_subordinate'):
            # Remove existing typed titles, rebuild from pipe-separated value
            for t in list(title_stmt.findall('mei:title', namespaces=ns)):
                if t.get('type') is not None:
                    title_stmt.remove(t)
            for i, sub in enumerate(self._val(d, 'title_subordinate').split('|'), 1):
                sub = sub.strip()
                if sub:
                    t = etree.SubElement(title_stmt, _ns('title'))
                    t.set('type', 'subordinate')
                    t.set('n', str(i))
                    t.text = sub

        self._write_composer_to_titlestmt(title_stmt, d, ns)

        resp_stmt = _find_or_create(title_stmt, 'respStmt')

        if self._val(d, 'editors'):
            # Remove existing encoder entries, rebuild
            for pn in list(resp_stmt.findall('mei:persName', namespaces=ns)):
                if pn.get('role') != 'composer':
                    resp_stmt.remove(pn)
            for entry in self._val(d, 'editors').split('|'):
                entry = entry.strip()
                if not entry:
                    continue
                name, role = self._parse_editor_entry(entry)
                pn = etree.SubElement(resp_stmt, _ns('persName'))
                pn.text = name
                if role:
                    pn.set('role', role)
                if self._val(d, 'encoding_date') and role == 'encoder':
                    pn.set('enddate', self._val(d, 'encoding_date'))

    def _update_generic(self, root, d):
        """Minimal fallback: update title only."""
        ns = {'mei': MEI_NS}
        head = root.find('mei:meiHead', namespaces=ns)
        if head is None:
            return
        file_desc = _find_or_create(head, 'fileDesc')
        title_stmt = _find_or_create(file_desc, 'titleStmt')
        if self._val(d, 'title'):
            _find_or_create(title_stmt, 'title').text = self._val(d, 'title')

    # ------------------------------------------------------------------
    # Shared workList helper
    # ------------------------------------------------------------------

    def _update_worklist_basic(self, root, d, ns):
        """Update workList title and genre for simpler header types."""
        work = root.find('.//mei:workList/mei:work', namespaces=ns)
        if work is None:
            return

        if self._val(d, 'work_title'):
            wt = _find_or_create(work, 'title')
            wt.text = self._val(d, 'work_title')

        if self._val(d, 'genre'):
            classif   = _find_or_create(work, 'classification')
            term_list = _find_or_create(classif, 'termList')
            term_el   = term_list.find('mei:term', namespaces=ns)
            if term_el is None:
                term_el = etree.SubElement(term_list, _ns('term'))
            term_el.text = self._val(d, 'genre')

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_editor_entry(entry):
        """
        Parse a pipe-list entry like "Name [role]" into (name, role).
        Returns (entry, '') if no brackets are present.
        """
        if '[' in entry and entry.endswith(']'):
            name = entry[:entry.rfind('[')].strip()
            role = entry[entry.rfind('[') + 1:-1].strip()
            return name, role
        return entry.strip(), ''

    @staticmethod
    def _parse_name_list(raw):
        """
        Split a raw string of one or more person names joined by " and " or
        "; " into individual name strings.  Used when the caller only has the
        raw source_editor / source_encoder value.
        """
        import re
        parts = re.split(r'\s+and\s+|;\s*', raw)
        return [p.strip() for p in parts if p.strip()]

    @staticmethod
    def _text_of(element):
        return (element.text or '').strip()
