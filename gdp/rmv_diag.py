import re
import math

def move_segments_by_length_and_width(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex to match segment blocks
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

    def should_move(x1, y1, x2, y2, width, layer):
        if layer != "In1.Cu" or width != 0.25:
            return False
        length = math.hypot(x2 - x1, y2 - y1)
        return 0.635 <= length <= 1.905

    def replace_if_needed(match):
        x1, y1, x2, y2 = map(float, match.group(1, 2, 3, 4))
        width = float(match.group(5))
        layer = match.group(6)
        segment_text = match.group(0)

        if should_move(x1, y1, x2, y2, width, layer):
            return segment_text.replace('(layer "In1.Cu")', '(layer "In3.Cu")')
        return segment_text

    # Apply transformation
    updated_content = segment_pattern.sub(replace_if_needed, content)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)

# Example usage
move_segments_by_length_and_width("gdp.kicad_pcb", "gdp.kicad_pcb")
