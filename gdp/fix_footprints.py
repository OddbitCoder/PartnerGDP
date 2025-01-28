import re

def read_mapping_table(file_path):
    """Reads the mapping table from the specified file."""
    mapping = {}
    with open(file_path, 'r') as file:
        for line in file:
            if " -> " in line:
                key, value = line.strip().split(" -> ")
                mapping[key] = value
    return mapping

def update_kicad_schema(schema_file, mapping, output_file):
    """Updates the footprint values in the KiCad schema file based on the mapping."""
    with open(schema_file, 'r') as file:
        schema_content = file.read()

    # Regular expression to match a "property Reference" section
    pattern = re.compile(
        r'\(property "Reference" "([^"]*).*?'
        r'\(property "Footprint" "([^"]*)"',
        re.DOTALL
    )

    def replacer(match):
        reference = match.group(1)
        current_footprint = match.group(2)
        # Update the footprint if reference is in the mapping
        if reference in mapping and current_footprint:
            print(f"Found {reference} {current_footprint}")
            new_footprint = mapping[reference]
            return match.group(0).replace(current_footprint, new_footprint)
        return match.group(0)

    # Replace the content using the mapping
    updated_content = pattern.sub(replacer, schema_content)

    # Write the updated content to a new file
    with open(output_file, 'w') as file:
        file.write(updated_content)

if __name__ == "__main__":
    for n in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]:
        # Input file paths
        mapping_file_path = "footprints.txt"
        schema_file_path = f"{n}.kicad_sch"
        output_file_path = f"{n}.kicad_sch"

        # Read the mapping table
        mapping_table = read_mapping_table(mapping_file_path)

        # Update the KiCad schema
        update_kicad_schema(schema_file_path, mapping_table, output_file_path)

        print(f"Updated schema written to: {output_file_path}")
