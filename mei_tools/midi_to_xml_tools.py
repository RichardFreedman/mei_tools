
# converting midi to xml with musescore 
# Import necessary libraries
import os
import subprocess
from pathlib import Path
import sys
import glob

# Display the current working directory (helpful for reference)
print(f"Current working directory: {os.getcwd()}")

# Set the source and destination directories
# Update these paths to your actual directories
source_dir = "MIDI_for_XML"  # Directory containing your MIDI files
dest_dir = "XML_from_MIDI"

# Create the destination directory if it doesn't exist
os.makedirs(dest_dir, exist_ok=True)

# Check if MuseScore is installed and accessible
try:
    # On Mac, the MuseScore executable might be at this location
    mscore_path = "/Applications/MuseScore 4.app/Contents/MacOS/mscore"
    
    # If the above path doesn't exist, try the command 'mscore' directly
    if not os.path.exists(mscore_path):
        mscore_path = "mscore"
    
    # Test if MuseScore is accessible
    result = subprocess.run([mscore_path, "--version"], 
                           capture_output=True, text=True)
    print(f"MuseScore version: {result.stdout.strip()}")
except Exception as e:
    print(f"Error checking MuseScore: {e}")
    print("Please ensure MuseScore is installed and accessible")
    sys.exit(1)

# Function to convert a MIDI file to MusicXML
def convert_midi_to_musicxml(file_path):
    """
    Convert a MIDI file to MusicXML using MuseScore
    
    Parameters:
    file_path (Path): Path to the MIDI file
    
    Returns:
    bool: True if conversion was successful, False otherwise
    """
    output_file = os.path.join(dest_dir, Path(file_path).stem + ".musicxml")
    print(f"Converting {os.path.basename(file_path)} to MusicXML...")
    try:
        result = subprocess.run([mscore_path, str(file_path), "-o", output_file], 
                               capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Successfully converted to {output_file}")
            return True
        else:
            print(f"✗ Error converting {os.path.basename(file_path)}: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Exception while converting {os.path.basename(file_path)}: {e}")
        return False

# Find all MIDI files in the source directory
def find_midi_files(source_directory):
    """
    Find all MIDI files in the specified directory
    
    Parameters:
    source_directory (str): Directory to search for MIDI files
    
    Returns:
    list: List of paths to MIDI files
    """
    # Use glob to find all .mid and .midi files
    midi_files = glob.glob(os.path.join(source_directory, "*.mid"))
    midi_files.extend(glob.glob(os.path.join(source_directory, "*.midi")))
    
    return midi_files

# Process all MIDI files in the directory
def process_midi_files(source_directory):
    """
    Convert all MIDI files in the specified directory to MusicXML
    
    Parameters:
    source_directory (str): Directory containing MIDI files
    
    Returns:
    tuple: (successful_count, failed_count)
    """
    # Find all MIDI files
    midi_files = find_midi_files(source_directory)
    print(f"Found {len(midi_files)} MIDI files to convert")
    
    successful = 0
    failed = 0
    
    for midi_file in midi_files:
        # Convert the MIDI file to MusicXML
        if convert_midi_to_musicxml(midi_file):
            successful += 1
        else:
            failed += 1
    
    # Print summary
    print("\n=== Conversion Summary ===")
    print(f"Total files: {len(midi_files)}")
    print(f"Successfully converted: {successful}")
    print(f"Failed conversions: {failed}")
    
    return successful, failed

# Run the conversion process
if __name__ == "__main__":
    process_midi_files(source_dir)


# clean up extra clefs in xml from musescore
import os
from pathlib import Path
import xml.etree.ElementTree as ET
import glob
import shutil

def load_musicxml_files(input_folder):
    """Load all MusicXML files from the specified folder."""
    files = glob.glob(os.path.join(input_folder, "*.musicxml"))
    if not files:
        raise FileNotFoundError(f"No MusicXML files found in {input_folder}")
    return files

def process_clefs_in_part(part):
    """
    Process a part element to keep only the first clef.
    Returns the number of clefs removed.
    """
    # Find all attributes elements that contain clefs
    attributes_with_clefs = []
    
    # First, find all measures in the part
    for measure in part.findall("./measure"):
        # Find all attributes elements in this measure
        for attributes in measure.findall("./attributes"):
            # Check if this attributes element has clefs
            clefs = attributes.findall("./clef")
            if clefs:
                attributes_with_clefs.append((measure, attributes, clefs))
    
    # If we have 0 or 1 clef total, nothing to do
    if len(attributes_with_clefs) <= 1:
        return 0
    
    # Keep track of the first clef we've seen
    first_measure, first_attributes, first_clefs = attributes_with_clefs[0]
    
    # If the first attributes has multiple clefs, keep only the first one
    removed_count = 0
    if len(first_clefs) > 1:
        for clef in first_clefs[1:]:
            first_attributes.remove(clef)
            removed_count += 1
    
    # Remove all clefs from all other attributes elements
    for measure, attributes, clefs in attributes_with_clefs[1:]:
        for clef in clefs:
            attributes.remove(clef)
            removed_count += 1
    
    return removed_count

def process_musicxml_file(input_file, output_file):
    """
    Process a MusicXML file to keep only the first clef in each part.
    Returns the total number of clefs removed.
    """
    # Parse the XML file
    tree = ET.parse(input_file)
    root = tree.getroot()
    
    # Find all parts
    parts = root.findall(".//part")
    
    # Process each part
    total_removed = 0
    for part in parts:
        part_id = part.get("id", "unknown")
        print(f"Processing part with ID: {part_id}")
        removed = process_clefs_in_part(part)
        total_removed += removed
        print(f"Removed {removed} clefs from part {part_id}")
    
    # Save the modified XML
    tree.write(output_file, encoding="utf-8", xml_declaration=True)
    print(f"Saved modified file to {output_file}")
    
    return total_removed

def main(input_folder, output_folder):
    """Main processing function."""
    # Create output folder if it doesn't exist
    Path(output_folder).mkdir(exist_ok=True)
    
    # Process all MusicXML files in the input folder
    files = load_musicxml_files(input_folder)
    print(f"Found {len(files)} MusicXML files to process")
    
    for input_file in files:
        print(f"\nProcessing: {input_file}")
        
        # Create output file path
        base_name = os.path.basename(input_file)
        output_name = f"{os.path.splitext(base_name)[0]}_rev.musicxml"
        output_file = os.path.join(output_folder, output_name)
        
        # Process the file
        try:
            # Count clefs before processing
            with open(input_file, 'r', encoding='utf-8') as f:
                content = f.read()
                original_clef_count = content.count('<clef>')
                print(f"Original file has {original_clef_count} clefs")
            
            # Process the file
            removed = process_musicxml_file(input_file, output_file)
            
            # Count clefs after processing
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
                new_clef_count = content.count('<clef>')
                print(f"Modified file has {new_clef_count} clefs")
            
            if removed > 0:
                print(f"✓ Successfully removed {removed} clefs")
            else:
                print("⚠️ No clefs were removed")
                
        except Exception as e:
            print(f"Error processing {input_file}: {str(e)}")

# Example usage
input_dir = "XML_from_MIDI"
output_dir = "Clean_XML"

main(input_dir, output_dir)