import re
import sys

def remove_nets_from_kicad_pcb(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as file:
        pcb_data = file.readlines()

    # Regular expression to match net attributes (e.g., (net 5 "GND") or (net 11))
    net_pattern = re.compile(r'\(net\s+\d+(\s+".*?")?\)')

    modified_lines = []
    for line in pcb_data:
        # Remove net attributes
        line = net_pattern.sub("", line).rstrip()
        modified_lines.append(line)

    # Save the modified PCB file
    with open(output_file, 'w', encoding='utf-8') as file:
        file.writelines(line + '\n' for line in modified_lines)

    print(f"Removed all nets from {input_file} and saved to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python remove_nets.py input.kicad_pcb output.kicad_pcb")
    else:
        remove_nets_from_kicad_pcb(sys.argv[1], sys.argv[2])
