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

        if line.startswith("#"):
            continue

        # Check for default ref line like: (IC7)
        m = re.match(r"^\((\w+)\)$", line)
        if m:
            default_ref = m.group(1)
            continue

        parts = line.split()
        if len(parts) != 2:
            print(parts)
            assert False
            # continue

        a, b = parts

        if b == "NC":
            continue

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
    final_nets = [
        {item for item in net if "/" in item}
        for net in merged_sets
        if any("/" in i for i in net)
    ]

    return final_nets


def find_best_matches(sch_nets: dict[str, set], vld_nets: list[set]):
    results = []

    for i, vld_net in enumerate(vld_nets):
        best_match_name = None
        best_match_score = 0
        best_match_sch_set = set()

        for name, sch_set in sch_nets.items():
            intersection = vld_net & sch_set
            union = vld_net | sch_set
            score = len(intersection) / len(union) if union else 0

            if score > best_match_score:
                best_match_score = score
                best_match_name = name
                best_match_sch_set = sch_set

        if best_match_score == 1.0:
            result = f"vld_net[{i}] PERFECT MATCH with sch_net '{best_match_name}'\n"
        else:
            only_in_vld = vld_net - best_match_sch_set
            only_in_sch = best_match_sch_set - vld_net
            result = f"vld_net[{i}] best match: '{best_match_name}' ({best_match_score:.2%} overlap)\n"
            if only_in_vld:
                result += f"  Only in vld_net[{i}]: {only_in_vld}\n"
            if only_in_sch:
                result += f"  Only in sch_net['{best_match_name}']: {only_in_sch}\n"

        results.append(result)

    return results


def swap(name: str, vld_nets: list[set]):
    for net in vld_nets:
        for pin in list(net):  # use list to avoid modifying set during iteration
            if pin.startswith(name + "/"):
                net.remove(pin)
                parts = pin.split("/")
                assert len(parts) == 2
                pin_number = parts[1]
                if pin_number == "1":
                    other_pin_number = "2"
                elif pin_number == "2":
                    other_pin_number = "1"
                else:
                    assert False
                new_pin = f"{parts[0]}/{other_pin_number}"
                net.add(new_pin)


def rmv(name: str, vld_nets: list[set]):
    for net in vld_nets:
        for pin in list(net):
            if pin.startswith(name + "/"):
                net.remove(pin)


if __name__ == "__main__":
    sch_nets = process_kicad_file("../gdp/gdp.net")
    vld_nets = process_file("gdp_validacija.txt")
    # incorrect pin assignment for resistors and capacitors
    for comp in {
        "CK40",
        "CK52",
        "CK55",
        "R8",
        "R9",
        "R10",
        "R11",
        "R12",
        "R13",
        "R14",
        "R15",
        "R21",
        "R25",
        "R27",
        "R29",
        "R30",
        "R37",
        "R39",
        "R40",
        "R43",
        "R46",
        "R47",
        "R48",
        "O1",
    }:
        swap(comp, vld_nets)
    for comp in {"SH3"}:
        rmv(comp, vld_nets)
    results = find_best_matches(sch_nets, vld_nets)
    for r in results:
        # if "Only in vld_net" in r:
        print(r)
