import os
import xml.etree.ElementTree as ET
from lxml import etree
from datetime import datetime
from copy import deepcopy

class MEI_Metadata_Updater:
    """
    A class for processing and updating metadata in MEI (Music Encoding Initiative) files.
    """
    
    def __init__(self, input_folder=None, output_folder=None, namespace=None, verbose=False):
        """
        Initialize the MEI Metadata Processor.
        
        Args:
            input_folder (str, optional): Path to the folder containing MEI files to process.
            output_folder (str, optional): Path to the folder where updated MEI files will be saved.
                                          If not provided, will use input_folder.
            namespace (dict, optional): XML namespace dictionary for MEI files.
                                       Defaults to {'mei': 'http://www.music-encoding.org/ns/mei'}.
            verbose (bool, optional): Whether to print detailed processing information. Defaults to False.
        """
        self.input_folder = input_folder
        self.output_folder = output_folder if output_folder else input_folder
        
        # Ensure output folder exists
        if self.output_folder and not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
            
        # Set default namespace if not provided
        self.namespace = namespace if namespace else {'mei': 'http://www.music-encoding.org/ns/mei'}
        
        # Verbose mode for debugging
        self.verbose = verbose
        
        # Initialize counters for processing statistics
        self.processed_files = 0
        self.successful_updates = 0
        self.failed_updates = 0

    # now the functions
    def apply_metadata(self, mei_path, matching_dict, output_folder):
        """Updates metadata in an MEI file based on the provided matching dictionary.
        
        Args:
            mei_path (str): Path to the MEI file to update
            matching_dict (dict): Dictionary containing metadata values to apply
            output_folder (str): Path to the output folder for the updated file
        
        Returns:
            str: Formatted XML string of the updated MEI file
        """
        # get the file and build revised name
        full_path = os.path.basename(mei_path)
        basename = os.path.splitext(os.path.basename(full_path))[0]
        revised_name = basename + "_rev.mei"
        print('Getting ' + basename)
        
        try:
            # Parse the MEI file using lxml.etree
            mei_doc = etree.parse(mei_path)
            root = mei_doc.getroot()
        except etree.ParseError as e:
            print(f"Error parsing {mei_path}: {e}")
            return f"Error: Could not parse {mei_path}. Make sure it contains valid XML."
        
        # define namespace for mei
        ns = {'mei': 'http://www.music-encoding.org/ns/mei'}

        # new ID removal 
        def remove_ids_from_head_children(element):
            # Remove xml:id if present
            attrib_key = "{http://www.w3.org/XML/1998/namespace}id"
            if attrib_key in element.attrib:
                del element.attrib[attrib_key]
                
            # Recursively process children
            for child in element:
                remove_ids_from_head_children(child)

        # work on fileDesc
        head_el = root.find('mei:meiHead', namespaces=ns)
        fileDesc_el = head_el.find('mei:fileDesc', namespaces=ns)
        
        # titleStmt
        titleStmt_el = fileDesc_el.find('mei:titleStmt', namespaces=ns)
        if titleStmt_el is None:
            titleStmt_el = etree.SubElement(fileDesc_el, 'titleStmt')
        
        # Add title
        title = etree.SubElement(titleStmt_el, 'title')
        title.set('type', 'main')
        title.text = matching_dict['Title']
        
        respStmt_el = etree.SubElement(titleStmt_el, 'respStmt')
        
        # composer
        composer = respStmt_el.find('mei:persName', namespaces=ns)
        if composer is None:
            composer = etree.SubElement(respStmt_el, 'persName')
        composer.set('role', 'composer')
        composer.set('auth', 'VIAF')
        composer.set('auth.uri', matching_dict['Composer_VIAF'])
        composer.text = matching_dict['Composer_Name']
        
        # editors
        editors = matching_dict['Editor'].split('|')
        for editor in editors:
            editor_elem = respStmt_el.find('mei:persName', namespaces=ns)
            if editor_elem is None:
                editor_elem = etree.SubElement(respStmt_el, 'persName')
            editor_elem.set('role', 'editor')
            editor_elem.text = editor.strip()

        # pubStmt
        pubStmt_el = fileDesc_el.find('mei:pubStmt', namespaces=ns)
        if pubStmt_el is None:
            pubStmt_el = etree.SubElement(fileDesc_el, 'pubStmt')
        
        # Add publication information
        publisher = etree.SubElement(pubStmt_el, 'publisher')
        publisher.text = 'Citations: The Renaissance Imitation Mass Project  https://crimproject.org'
        
        for distributor in matching_dict['Copyright_Owner'].split('|'):
            distributor_elem = etree.SubElement(pubStmt_el, 'distributor')
            distributor_elem.text = distributor
        
        current_date = datetime.now().isoformat()
        date_elem = etree.SubElement(pubStmt_el, 'date')
        date_elem.set('isodate', current_date)
        
        availability_elem = etree.SubElement(pubStmt_el, 'availability')
        availability_elem.text = matching_dict["Rights_Statement"]

        # appInfo
        appInfo_el = head_el.find('mei:encodingDesc/mei:appInfo', namespaces=ns)
        if appInfo_el is None:
            appInfo_el = etree.SubElement(head_el, 'appInfo')
            appInfo_el.set('n', 'Y4:0')

        # Remove all existing application tags
        for app in appInfo_el.findall('mei:application', namespaces=ns):
            appInfo_el.remove(app)

        # Add the new application tag
        application = """<application version="2.0.3">
            <name>MEI Updater 2025</name>
        </application>"""
        appInfo_el.append(etree.fromstring(application))
        
        # work data
        worklist_el = head_el.find('mei:workList', namespaces=ns)
        if worklist_el is None:
            worklist_el = etree.SubElement(head_el, 'workList')
        work_el = worklist_el.find('mei:work', namespaces=ns)
        if work_el is None:
            work_el = etree.SubElement(worklist_el, 'work')

        # title
        title_elem = work_el.find('mei:title', namespaces=ns)
        if title_elem is None:
            title_elem = etree.SubElement(work_el, 'title')
        title_elem.set('type', 'main')
        title_elem.text = matching_dict['Title']

        # composer
        composer_elem = work_el.find('mei:composer', namespaces=ns)
        if composer_elem is None:
            composer_elem = etree.SubElement(work_el, 'composer')
        composer_elem.set('role', 'composer')
        composer_elem.set('auth', 'VIAF')
        composer_elem.set('auth.uri', matching_dict['Composer_VIAF'])
        composer_elem.text = matching_dict['Composer_Name']

        # genre
        classification_elem = work_el.find('mei:classification', namespaces=ns)
        if classification_elem is None:
            classification_elem = etree.SubElement(work_el, 'classification')
            term_elem = etree.SubElement(classification_elem, 'termList')
            term_elem = etree.SubElement(term_elem, 'term')
            term_elem.text = matching_dict["Genre"].strip()

        # Create a new manifestationList without any attributes
        new_manifestation_list = etree.Element("manifestationList")

        # Create the manifestation element
        manifestation = etree.SubElement(new_manifestation_list, "manifestation")

        # Add titleStmt with proper structure
        title_stmt = etree.SubElement(manifestation, "titleStmt")
        title = etree.SubElement(title_stmt, "title")
        title.text = matching_dict['Source_Title']

        # Add pubStmt with proper structure
        pub_stmt = etree.SubElement(manifestation, "pubStmt")
        publisher = etree.SubElement(pub_stmt, "publisher")
        pers_name = etree.SubElement(publisher, "persName")
        pers_name.set("auth", "VIAF")
        pers_name.set("auth.uri", matching_dict['Publisher_1_VIAF'])
        pers_name.text = matching_dict['Source_Publisher_1']

        # Add date element
        date = etree.SubElement(pub_stmt, "date")
        date.text = matching_dict['Source_Date']

        # Add physLoc with proper structure
        phys_loc = etree.SubElement(manifestation, "physLoc")
        repository = etree.SubElement(phys_loc, "repository")
        corp_name = etree.SubElement(repository, "corpName")
        corp_name.text = matching_dict['Source_Institution']

        # Add shelfmark with proper structure
        identifier = etree.SubElement(repository, "identifier")
        identifier.text = matching_dict['Source_Shelfmark']

        # Add geogName with proper structure
        geog_name = etree.SubElement(repository, "geogName")
        geog_name.text = matching_dict['Source_Location']

        # Check for second publisher
        second_publisher_elem = manifestation.find('mei:persName', namespaces=ns)
        if second_publisher_elem is None:
            second_publisher_elem = etree.SubElement(manifestation, 'persName')
        second_publisher_elem.set('auth', 'VIAF')
        second_publisher_elem.set('auth.uri', matching_dict['Publisher_2_VIAF'])
        second_publisher_elem.text = matching_dict['Source_Publisher_2']

        # pub date
        date_elem = manifestation.find('mei:date', namespaces=ns)
        if date_elem is None:
            date_elem = etree.SubElement(manifestation, 'date')
        date_elem.text = matching_dict['Source_Date']

        # now we REMOVE the ids from anywhere in the head
        head_el = root.find('mei:meiHead', namespaces=ns)
        if head_el is not None:
            # Skip root meiHead but process its children
            for child in head_el:
                remove_ids_from_head_children(child)
        
        # save the result
        output_file_path = os.path.join(output_folder, revised_name)
        
        # Get the MEI namespace
        mei_ns = "http://www.music-encoding.org/ns/mei"
        
        # Modify the existing root element instead of creating a new one
        root.attrib["meiversion"] = root.get("meiversion", "4.0.0")
        
        # Remove any existing xml:id if it exists
        if "{http://www.w3.org/XML/1998/namespace}id" in root.attrib:
            del root.attrib["{http://www.w3.org/XML/1998/namespace}id"]
        
        # Format the XML with proper indentation
        etree.indent(root, space="    ")

        
        # Serialize to string with XML declaration
        formatted_xml = etree.tostring(
            root,
            pretty_print=True,
            encoding='utf-8',
            xml_declaration=True
        )
        
        # Write to file
        with open(output_file_path, 'wb') as f:
            f.write(formatted_xml)
        
        print(f'Saved updated {revised_name}')
        return formatted_xml
