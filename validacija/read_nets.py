import re


def extract_nets(file_content):
    # Match whole net blocks: starts with (net ...) and continues with indented lines
    net_pattern = re.compile(
        r'\(net\s+\(code\s+".*?"\)\s+\(name\s+"(.*?)"\).*?(?:\n {6}.*)+', re.MULTILINE
    )
    return net_pattern.findall(file_content), net_pattern.finditer(file_content)


def extract_nodes(net_block):
    # Extract all (node ...) entries and their ref/pin
    return re.findall(r'\(node\s+\(ref\s+"([^"]+)"\)\s+\(pin\s+"([^"]+)"\)', net_block)


def process_kicad_file(filename):
    with open(filename, "r", encoding="utf-8") as f:
        content = f.read()

    names, net_matches = extract_nets(content)

    net_dict = {}

    for name, match in zip(names, net_matches):
        net_block = match.group()
        nodes = extract_nodes(net_block)
        node_set = {f"{ref}/{pin}" for ref, pin in nodes}
        net_dict[name] = node_set

    return net_dict


def parse_lines_to_sets(lines):
    networks = []
    default_ref = None

    for line in lines:
        line = line.strip()

        # Check for default ref line like: (IC7)
        m = re.match(r"^\((\w+)\)$", line)
        if m:
            default_ref = m.group(1)
            continue

        parts = line.split()
        if len(parts) != 2:
            continue

        a, b = parts

        # If a is just a number, prepend default_ref
        if re.fullmatch(r"\d+", a) and default_ref:
            a = f"{default_ref}/{a}"
        if re.fullmatch(r"\d+", b) and default_ref:
            b = f"{default_ref}/{b}"

        networks.append(set([a, b]))

    return networks


def merge_networks(networks):
    """Merge all networks that share at least one element."""
    merged = []
    while networks:
        base = networks.pop()
        changed = True
        while changed:
            changed = False
            i = 0
            while i < len(networks):
                if base & networks[i]:  # If intersection is not empty
                    base |= networks.pop(i)
                    changed = True
                else:
                    i += 1
        merged.append(base)
    return merged


def process_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    initial_sets = parse_lines_to_sets(lines)
    merged_sets = merge_networks(initial_sets)

    # Now, strip out anything that's not a pin (i.e., doesn't contain a '/')
    # final_nets = [
    #     sorted(item for item in net if "/" in item)
    #     for net in merged_sets
    #     if any("/" in i for i in net)
    # ]

    # return final_nets
    return merged_sets


if __name__ == "__main__":
    sch_nets = process_kicad_file("../gdp/gdp.net")
    nets = process_file("gdp_validacija.txt")
    for i, net in enumerate(nets, 1):
        print(f"Net {i}: {net}")
