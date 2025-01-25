import re

def replace_layer(input_file, output_file):
    with open(input_file, 'r') as file:
        content = file.read()

    # Regular expression to match the pattern
    pattern = r'(\(property \"Reference\" \".*?\"\n\t\t\t\(at [^\)]+\)\n\t\t\t\(layer )"F\.SilkS"'

    updated_content = re.sub(pattern, r'\1"F.Fab"', content)

    # Write the updated content back to the output file
    with open(output_file, 'w') as file:
        file.write(updated_content)

# Specify the input and output file paths
input_file = 'gdp.kicad_pcb'
output_file = 'output.kicad_pcb'

# Perform the replacement
replace_layer(input_file, output_file)

print(f"Layer replacement complete. Updated file saved to '{output_file}'.")
