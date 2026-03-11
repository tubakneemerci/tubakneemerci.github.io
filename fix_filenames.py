import os
import re
import unicodedata
import urllib.parse

# --- CONFIGURATION ---
# Set this to the path of your directory, e.g., '/path/to/your/folder'
# '.' means the current directory where the script is run.
TARGET_DIR = '.' 

# The types of files the script will open to update text/href references
TEXT_EXTENSIONS = {'.html', '.htm', '.txt', '.md', '.css', '.js', '.xml', '.json', '.php'}
# ---------------------

def sanitize_name(name):
    """Converts accents to standard characters and replaces spaces with underscores."""
    # 1. Separate characters from their accents (NFD normalization)
    nfd_string = unicodedata.normalize('NFD', name)
    # 2. Drop the accents, keeping only ASCII characters
    ascii_string = nfd_string.encode('ASCII', 'ignore').decode('utf-8')
    # 3. Replace spaces and unsafe characters with underscores
    safe_name = re.sub(r'[^a-zA-Z0-9.\-]', '_', ascii_string)
    # 4. Clean up any accidental double underscores
    safe_name = re.sub(r'_+', '_', safe_name)
    return safe_name

def main():
    renames = {} # Keeps track of { old_name : new_name }
    
    print(f"--- STEP 1: Renaming files in '{TARGET_DIR}' ---")
    for root, dirs, files in os.walk(TARGET_DIR):
        for filename in files:
            new_name = sanitize_name(filename)
            
            if new_name != filename:
                old_path = os.path.join(root, filename)
                new_path = os.path.join(root, new_name)
                
                # Prevent accidentally overwriting a file that already exists
                if os.path.exists(new_path):
                    print(f"  [!] Warning: '{new_name}' already exists. Skipping '{filename}'.")
                    continue
                
                os.rename(old_path, new_path)
                print(f"  [+] Renamed: '{filename}' -> '{new_name}'")
                renames[filename] = new_name

    if not renames:
        print("No files needed renaming. Exiting.")
        return

    print("\n--- STEP 2: Updating references in text/HTML files ---")
    for root, dirs, files in os.walk(TARGET_DIR):
        for filename in files:
            ext = os.path.splitext(filename)[1].lower()
            if ext in TEXT_EXTENSIONS:
                filepath = os.path.join(root, filename)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()

                    original_content = content
                    
                    for old_name, new_name in renames.items():
                        # Create all possible ways the old filename might appear in the text
                        nfc_name = unicodedata.normalize('NFC', old_name) # Standard composed (é)
                        nfd_name = unicodedata.normalize('NFD', old_name) # Decomposed (e + ´)
                        url_encoded_nfc = urllib.parse.quote(nfc_name)    # URL Encoded (%C3%A9)
                        url_encoded_nfd = urllib.parse.quote(nfd_name)
                        
                        # Replace all variations with the safe new name
                        for variant in {old_name, nfc_name, nfd_name, url_encoded_nfc, url_encoded_nfd}:
                            content = content.replace(variant, new_name)

                    # Only write to the file if we actually changed something
                    if content != original_content:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(content)
                        print(f"  [*] Updated links in: {filepath}")
                        
                except UnicodeDecodeError:
                    print(f"  [!] Skipped {filepath} (Not a standard UTF-8 text file)")
                except Exception as e:
                    print(f"  [!] Could not process {filepath}: {e}")
                    
    print("\nDone!")

if __name__ == '__main__':
    main()
