import re
import sys

instructions = {
    "halt": 0,
    "add": 1,
    "sub": 9,
    "or": 2,
    "and": 10,
    "loadw": 3,
    "loadi": 11,
    "storew": 4,
    "br_equal": 5,
    "br_not_eq": 13,
    "br_less_th": 5,
    "br_less_th_or_eq": 13,
    "br_great_th": 5,
    "br_great_th_or_eq": 13,
    "jump": 5,
}

branch_types = {
    "br_equal": 0,
    "br_not_eq": 0,
    "br_less_th": 1,
    "br_less_th_or_eq": 1,
    "br_great_th": 2,
    "br_great_th_or_eq": 2,
    "jump": 3,
}


def build_instruction(*args):
    size = 0
    instruction = ""
    for arg in args:
        if type(arg) is not tuple:
            raise TypeError(arg)

        width = arg[1]
        value = arg[0]

        bin_value = isa_binary(value, width)
        instruction = bin_value + instruction
        size += width

        if size > 16:
            raise TypeError

    return instruction


def isa_binary(n, width):
    neg = False
    if n < 0:
        neg = True
        n = abs(n)

    binary = bin(n)[2:].zfill(width)

    inv_binary = ""
    for b in binary:
        if neg:
            b = "0" if b == "1" else "1"

        inv_binary += b
    return binary


def assembly_to_machine_code(file):
    assembly = []
    machine_code = []
    with open(file) as input_file:
        for line in input_file:
            assembly.append(line)

    code, labels = get_lines_and_labels(assembly)

    for line in code:
        split_line = line.split(" ")

        ins = split_line[0]

        machine_code.append(parse_instruction(ins, split_line, labels))

    return machine_code


def get_lines_and_labels(input_file):
    labels = {}
    code = []

    pc = 0
    for line in input_file:
        if line[0] == " ":
            code.append(line.lstrip().replace('\n', ''))
            pc += 1
        else:
            labels[line.split(":")[0]] = pc

    return code, labels


def parse_instruction(ins, split_line, labels):
    ins = ins.lower()

    if ins == "add" or ins == "sub" or ins == "or" or ins == "and":
        src1 = parse_register(split_line[2])
        src2 = parse_register(split_line[3])
        dest = parse_register(split_line[1])
        return build_instruction((instructions[ins], 4), (dest, 4), (src1, 4), (src2, 4))
    elif ins == "loadw":
        match = re.match(r"(-?\d+)\((.+)\)", split_line[2])
        dest = parse_register(split_line[1])
        if match:
            src1 = parse_register(match.group(2))
            offset = int(match.group(1))
            return build_instruction((instructions[ins], 4), (dest, 4), (src1, 4), (offset, 4))
        else:
            raise ValueError
    elif ins == "loadi":
        dest = parse_register(split_line[1])
        if split_line[2].isnumeric():
            imm = int(split_line[2])
        else:
            imm = labels[split_line[2]]

        return build_instruction((instructions[ins], 4), (dest, 4), (imm, 8))
    elif ins == "storew":
        match = re.match(r"(-?\d+)\((.+)\)", split_line[1])
        if match:
            offset = int(match.group(1))
            src1 = parse_register(match.group(2))
            src2 = parse_register(split_line[2])
            return build_instruction((instructions[ins], 4), (offset, 4), (src1, 4), (src2, 4))
        else:
            raise ValueError
    elif ins.startswith("br"):
        src1 = parse_register(split_line[2])
        src2 = parse_register(split_line[3])
        branch_reg = parse_register(split_line[1], use_short=True)
        branch_type = branch_types[ins]
        return build_instruction((instructions[ins], 4), (branch_type, 2), (branch_reg, 2), (src1, 4), (src2, 4))
    elif ins == "jump":
        src1 = parse_register(split_line[2])
        src2 = 0
        branch_reg = 0
        branch_type = branch_types[ins]
        return build_instruction((instructions[ins], 4), (branch_type, 2), ((branch_reg, 2), src1, 4), (src2, 4))
    elif ins == "halt":
        return build_instruction((0, 16))
    else:
        raise Exception("Invalid instruction: %s" % ins)


def parse_register(register_handle, use_short=False):
    reg_value = -1
    if register_handle[0] == "!":
        reg_value = int(register_handle[1:])
    else:
        reg_type = register_handle[1]
        reg_type.lower()
        if reg_type == 't':
            reg_value = int(register_handle[2]) + 3
        elif reg_type == 's':
            reg_value = int(register_handle[2]) + 9
        elif reg_type == 's':
            reg_value = 1
        elif reg_type == 'r':
            reg_value = 2
        elif reg_type == 'b':
            number = int(register_handle[2])

            if use_short:
                reg_value = int(number)
            elif number == 0:
                reg_value = 7
            elif number == 1:
                reg_value = 8
            elif number == 2:
                reg_value = 14
            elif number == 3:
                reg_value = 15
            else:
                raise TypeError

    return reg_value


def print_verilog(code):
    ndx = 0
    for line in code:
        print("mem[%s] = 16'b%s;" % (ndx, line))
        ndx = ndx + 1

    print("mem[%s] = 16'b%s;" % (ndx, 0))

def print_code(code):
    for line in code:
        print(line)


if __name__ == "__main__":
    verilog = False

    if len(sys.argv) == 1 or sys.argv[1].lower() == "-h":
        print("jisa.py [input file]")
        quit(0)

    path = sys.argv[1]

    if len(sys.argv) > 2 and sys.argv[2] == "-v":
        verilog = True

    assembly_code = assembly_to_machine_code(path)

    if verilog:
        print_verilog(assembly_code)
    else:
        print_code(assembly_code)
