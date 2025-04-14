import re

def move_non_hv_segments_to_in3(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex to match each full (segment ...) block
    segment_pattern = re.compile(
        r"\(segment\s*"
        r"\(start\s+([-+]?\d*\.?\d+)\s+([-+]?\d*\.?\d+)\)\s*"
        r"\(end\s+([-+]?\d*\.?\d+)\s+([-+]?\d*\.?\d+)\)\s*"
        r"\(width\s+([-+]?\d*\.?\d+)\)\s*"
        r'\(layer\s+"([^"]+)"\)\s*'
        r"\(net\s+\d+\)\s*"
        r"\(uuid\s+\"[^\"]+\"\)\s*"
        r"\)",
        re.MULTILINE
    )

    def is_non_hv(x1, y1, x2, y2):
        return not (x1 == x2 or y1 == y2)

    def replace_if_needed(match):
        x1, y1, x2, y2 = map(float, match.group(1, 2, 3, 4))
        width = float(match.group(5))
        layer = match.group(6)

        segment_text = match.group(0)
        if width == 0.25 and layer == "In1.Cu" and is_non_hv(x1, y1, x2, y2):
            # Replace layer string
            return segment_text.replace('(layer "In1.Cu")', '(layer "In3.Cu")')
        return segment_text

    # Update content
    updated_content = segment_pattern.sub(replace_if_needed, content)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)

# Example usage
move_non_hv_segments_to_in3("gdp.kicad_pcb", "gdp.kicad_pcb")
