# Sample CRIM metadata dictionary entry
#
# This is the structure produced when a CRIM Google Sheet is loaded with
# pandas and converted to a list of dicts via df.to_dict(orient='records').
# Each row in the sheet becomes one dict; keys are column headers.
#
# Usage:
#   df = pd.read_csv(google_sheet_csv_url).fillna('')
#   crim_metadata_dict_list = df.to_dict(orient='records')

sample_crim_metadata_entry = {
    'CRIM_ID':            'CRIM_Model_0001',
    'MEI_Name':           'CRIM_Model_0001.mei',
    'Title':              'Veni speciosam',
    'Mass Title':         '',
    'Genre':              'motet',
    'Composer_Name':      'Johannes Lupi',
    'CRIM_Person_ID':     'CRIM_Person_0004',
    'Composer_VIAF':      'http://viaf.org/viaf/42035469',
    'Composer_BNF_ID':    'https://data.bnf.fr/ark:/12148/cb139927263',
    'Piece_Date':         'before 1542',
    'Source_ID':          'CRIM_Source_0003',
    'Source_Short_Title': 'Musicae Cantiones',
    'Source_Title':       ('Chori Sacre Virginis Marie Cameracensis Magistri, Musicae Cantiones '
                           '(quae vulgo motetta nuncupantur) noviter omni studio ac diligentia in '
                           'lucem editae. (8, 6, 5, et 4 vocum.) Index quindecim Cantionum. '
                           'Liber tertius.'),
    'Source_Publisher_1': 'Pierre Attaingnant',
    'Publisher_1_VIAF':   'http://viaf.org/viaf/59135590',
    'Publisher_1_BNF_ID': 'https://data.bnf.fr/ark:/12148/cb12230232k',
    'Source_Publisher_2': '',
    'Publisher_2_VIAF':   '',
    'Publisher_2_BNF_ID': '',
    'Source_Date':        '1542',
    'Source_Reference':   'RISM A I, L 3089',
    'Source_Location':    'Wien',
    'Source_Institution': 'Österreichische Nationalbibliothek',
    'Source_Shelfmark':   'SA.78.C.1/3/1-4 Mus 19',
    'Editor':             'Marco Gurrieri | Bonnie Blackburn | Vincent Besson | Richard Freedman',
    'Last_Revised':       '2020_07_10',
    'Rights_Statement':   ('This work is licensed under a Creative Commons '
                           'Attribution-NonCommercial 4.0 International License'),
    'Copyright_Owner':    ("Centre d'Études Supérieures de la Renaissance | Haverford College | "
                           'Marco Gurrieri | Bonnie Blackburn | Vincent Besson | Richard Freedman'),
}
