import re

def find_reference_changes(file_path):
    pattern = re.compile(r'-\s*\(reference \"(.*?)\"\)\n\+\s*\(reference \"(.*?)\"\)')

    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    matches = pattern.findall(content)
    
    if matches:
        for old_ref, new_ref in matches:
            if old_ref.startswith("#"):
                continue
            print(f"Old reference: {old_ref}, New reference: {new_ref}")
            for target_fn in ["1.kicad_sch", "2.kicad_sch", "3.kicad_sch", "4.kicad_sch", "5.kicad_sch", "6.kicad_sch", "7.kicad_sch", "8.kicad_sch", "9.kicad_sch", "10.kicad_sch", "11.kicad_sch", "12.kicad_sch", "13.kicad_sch", "14.kicad_sch"]:
                replace_references(target_fn, new_ref, old_ref)  # Replace 'target_file.txt' with your target file
    else:
        print("No matches found.")

def replace_references(target_file, new_ref, old_ref):
    with open(target_file, 'r+', encoding='utf-8') as file:
        print(f"Changing {new_ref} to {old_ref} in {target_file}...")
        content = file.read()
        updated_content = content.replace(f'(reference "{new_ref}")', f'(reference  "{old_ref}")')
        file.seek(0)
        file.write(updated_content)
        file.truncate()

# Example usage
file_path = 'diff.txt'  # Replace with your diff file path
find_reference_changes(file_path)
