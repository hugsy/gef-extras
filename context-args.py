"""
Display arguments when hitting a function call.

To use, place the script in the directory specified in `gef.extra_plugins_dir`
and add "args" to the `context.layout` variable.

For instance:
gef➤  gef config context.layout "regs code args"

Author: @_hugsy_
"""

size2type = {
    1: "BYTE",
    2: "WORD",
    4: "DWORD",
    8: "QWORD",
}


def __get_current_block_start_address():
    pc = current_arch.pc
    try:
        block_start = gdb.block_for_pc(pc).start
    except RuntimeError:
        # if stripped, let's roll back 5 instructions
        block_start = gdb_get_nth_previous_instruction_address(pc, 5)

    return block_start


def __get_ith_parameter(i):
    if is_x86_32():
        sp = current_arch.sp
        sz =  current_arch.ptrsize
        loc = sp + (i * sz) + sz
        val = read_int_from_memory(loc)
        key = "[sp + {:#x}]".format(i * sz)
    else:
        reg = current_arch.function_parameters[i]
        val = get_register(reg)
        key = reg
    return (key, val)


def print_guessed_arguments(ctx, function_name):
    ctx.context_title("arguments (guessed)")
    parameter_set = set()
    pc = current_arch.pc
    block_start = __get_current_block_start_address()
    use_capstone = ctx.has_setting("use_capstone") and ctx.get_setting("use_capstone")
    instruction_iterator = capstone_disassemble if use_capstone else gef_disassemble
    function_parameters = current_arch.function_parameters

    for insn in instruction_iterator(block_start, pc-block_start):
        if len(insn.operands) < 1:
            continue

        if is_x86_32():
            if insn.mnemonic == "push":
                parameter_set.add(insn.operands[0])
        else:
            # todo: ideally we want to test if the register is written to instead
            op = "$"+insn.operands[0]
            if op in function_parameters:
                parameter_set.add(op)

            if is_x86_64():
                # also consider extended registers
                extended_registers = { "$rdi": ["$edi", "$di"],
                                       "$rsi": ["$esi", "$si"],
                                       "$rdx": ["$edx", "$dx"],
                                       "$rcx": ["$ecx", "$cx"],
                                       # todo r8 , r9
                }
                for exreg in extended_registers:
                    if op in extended_registers[exreg]:
                        parameter_set.add(exreg)

    if is_x86_32():
        nb_argument = len(parameter_set)
    else:
        nb_argument = 0
        for p in parameter_set:
            nb_argument = max(nb_argument, function_parameters.index(p)+1)

    args = []
    for i in range(nb_argument):
        _key, _value = __get_ith_parameter(i)
        _value = right_arrow.join(DereferenceCommand.dereference_from(_value))
        args.append("{} = {}".format(_key, _value))

    print("{} (".format(function_name))
    if (len(args)):
        print("   "+",\n   ".join(args))
    print(")")
    return


def print_arguments_from_symbol(context, function_name, symbol):
    args = []

    for i, f in enumerate(symbol.type.fields()):
        _key, _value = __get_ith_parameter(i)
        _value = right_arrow.join(DereferenceCommand.dereference_from(_value))
        _name = f.name or "var_{}".format(i)
        _type = f.type.name or size2type[f.type.sizeof]
        args.append("{} {} = {}".format(_type, _name, _value))

    context.context_title("arguments")
    print("{} (".format(function_name))
    if len(args):
        print("   " + ",\n   ".join(args))
    print(")")
    return


def print_args(ctx):
    use_capstone = ctx.has_setting("use_capstone") and ctx.get_setting("use_capstone")
    insn = gef_current_instruction(current_arch.pc)
    if not current_arch.is_call(insn):
        return

    target = insn.operands[-1].split()[1]
    target = target.replace("<", "").replace(">", "")

    sym = gdb.lookup_global_symbol(target)
    if sym is None:
        print_guessed_arguments(ctx, target)
        return

    if sym.type.code != gdb.TYPE_CODE_FUNC:
        err("Symbol '{}' is not a function: type={}".format(target, sym.type.code))
        return

    print_arguments_from_symbol(ctx, target, sym)
    return


if __name__ == "__main__":

    # find the ContextCommand instance
    for name, cls, ins in __gef__.loaded_commands:
        if name == "context":
            # add a new entry to layout_mapping
            ins.layout_mapping["args"] = lambda: print_args(ins)
            break
