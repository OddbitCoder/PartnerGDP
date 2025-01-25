import re

def parse_kicad_pcb(file_path):
    mappings = []
    
    # Regular expression to find the desired pattern
    pattern = re.compile(
        r'\(footprint\s+"(?P<footprint>[^"]+)"\s*.*?'
        r'\(property\s+"Reference"\s+"(?P<reference>[^"]+)"',
        re.DOTALL
    )
    
    # Read the file content
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Find all matches
    for match in pattern.finditer(content):
        footprint = match.group("footprint")
        reference = match.group("reference")
        mappings.append(f"{reference} -> {footprint}")
    
    return mappings

# Specify the file path
file_path = "gdp.kicad_pcb"

# Parse the file and print the mappings
mappings = parse_kicad_pcb(file_path)
for mapping in mappings:
    print(mapping)
