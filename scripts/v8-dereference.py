def to_int32(v):
    """Cast a gdb.Value to int32"""
    return int(v.cast(gdb.Value(2**32-1).type))

def lookup_symbol_hack(symbol):
    """Hacky way to lookup symbol's address, I've tried other options like parse_and_eval but they
       throw errors like `No symbol "v8" in current context.`. I would like to replace this function
       once I figure out the proper way.
    """
    return int(gdb.execute("info address {}".format(symbol), to_string=True).split(" is at ")[1].split(" ")[0], 16)

isolate_root = None
def get_isolate_root():
    global isolate_root
    if isolate_root:
        return isolate_root
    else:
        try:
            isolate_key_addr = lookup_symbol_hack("v8::internal::Isolate::isolate_key_")
            isolate_key = to_int32(gdb.parse_and_eval("*(int *){}".format(isolate_key_addr)))
        except:
            err("Failed to get value of v8::internal::Isolate::isolate_key_")
            return None

        getthreadlocal_addr = lookup_symbol_hack("v8::base::Thread::GetThreadLocal")
        res = gdb.execute("call (void*){}({})".format(getthreadlocal_addr, isolate_key), to_string=True)
        isolate_root = int(res.split("0x")[1], 16)
        return isolate_root

def del_isolate_root(event):
    global isolate_root
    isolate_root = None

def format_compressed(addr):
    heap_color = get_gef_setting("theme.address_heap")
    return "{:s}{:s}".format(Color.colorify("0x{:08x}".format(addr>>32), "gray"),
                               Color.colorify("{:08x}".format(addr&0xffffffff), heap_color))
    
@register_command
class V8DereferenceCommand(GenericCommand):
    """(v8) Dereference recursively from an address and display information. Handles v8 specific values like tagged and compressed pointers"""

    _cmdline_ = "vereference"
    _syntax_  = "{:s} [LOCATION] [l[NB]]".format(_cmdline_)
    _aliases_ = ["v8"]
    _example_ = "{:s} $sp l20".format(_cmdline_)

    def __init__(self):
        super(V8DereferenceCommand, self).__init__(complete=gdb.COMPLETE_LOCATION)
        self.add_setting("max_recursion", 7, "Maximum level of pointer recursion")
        gef_on_exit_hook(del_isolate_root)
        return

    @staticmethod
    def pprint_dereferenced(addr, off):
        base_address_color = get_gef_setting("theme.dereference_base_address")
        registers_color = get_gef_setting("theme.dereference_register_value")

        regs = [(k, get_register(k)) for k in current_arch.all_registers]

        sep = " {:s} ".format(RIGHT_ARROW)
        memalign = current_arch.ptrsize

        offset = off * memalign
        current_address = align_address(addr + offset)
        addrs = V8DereferenceCommand.dereference_from(current_address)
        if addrs[1]:
            l  = ""
            addr_l0 = format_address(int(addrs[0][0], 16))
            l += "{:s}{:s}+{:#06x}: {:{ma}s}".format(Color.colorify(addr_l0, base_address_color),
                                                     VERTICAL_LINE, offset,
                                                     sep.join(addrs[0][1:]), ma=(memalign*2 + 2))
            addr_l1 = " "*len(addr_l0)
            l += "\n"
            l += "{:s}{:s}+{:#06x}: {:{ma}s}".format(Color.colorify(addr_l1, base_address_color),
                                                     VERTICAL_LINE, offset+4,
                                                     sep.join(addrs[1][1:]), ma=(memalign*2 + 2))

            """
            TODO: Get register hints working for this as well (but not super impt imo)
            register_hints = []

            for regname, regvalue in regs:
                if current_address == regvalue:
                    register_hints.append(regname)

            if register_hints:
                m = "\t{:s}{:s}".format(LEFT_ARROW, ", ".join(list(register_hints)))
                l += Color.colorify(m, registers_color)
            """

            offset += memalign
            pass
        else:
            l  = ""
            addr_l = format_address(int(addrs[0][0], 16))
            l += "{:s}{:s}+{:#06x}: {:{ma}s}".format(Color.colorify(addr_l, base_address_color),
                                                     VERTICAL_LINE, offset,
                                                     sep.join(addrs[0][1:]), ma=(memalign*2 + 2))

            register_hints = []

            for regname, regvalue in regs:
                if current_address == regvalue:
                    register_hints.append(regname)

            if register_hints:
                m = "\t{:s}{:s}".format(LEFT_ARROW, ", ".join(list(register_hints)))
                l += Color.colorify(m, registers_color)

            offset += memalign
        return l


    @only_if_gdb_running
    def do_invoke(self, argv):
        target = "$sp"
        nb = 10

        for arg in argv:
            if arg.isdigit():
                nb = int(arg)
            elif arg[0] in ("l", "L") and arg[1:].isdigit():
                nb = int(arg[1:])
            else:
                target = arg

        addr = safe_parse_and_eval(target)
        if addr is None:
            err("Invalid address")
            return

        addr = int(addr)
        # Remove tagging (tagged pointers)
        addr = addr & (2**(8*current_arch.ptrsize)-2)
        if process_lookup_address(addr) is None:
            err("Unmapped address")
            return

        if get_gef_setting("context.grow_stack_down") is True:
            from_insnum = nb * (self.repeat_count + 1) - 1
            to_insnum = self.repeat_count * nb - 1
            insnum_step = -1
        else:
            from_insnum = 0 + self.repeat_count * nb
            to_insnum = nb * (self.repeat_count + 1)
            insnum_step = 1

        start_address = align_address(addr)

        for i in range(from_insnum, to_insnum, insnum_step):
            gef_print(V8DereferenceCommand.pprint_dereferenced(start_address, i))

        return


    @staticmethod
    def dereference_from(addr):
        if not is_alive():
            return ([format_address(addr),], None)

        code_color = get_gef_setting("theme.dereference_code")
        string_color = get_gef_setting("theme.dereference_string")
        max_recursion = get_gef_setting("dereference.max_recursion") or 10
        addr = lookup_address(align_address(int(addr)))
        msg = ([format_address(addr.value),], [])
        seen_addrs = set()#tuple(set(), set())

        # Is this address pointing to a normal pointer?
        deref = addr.dereference()
        if deref is None:
            pass # Regular execution if so
        else:
            # Is this address pointing to compressed pointers instead?
            # Only for valid for 64-bit address space
            if current_arch.ptrsize == 8:
                isolate_root = get_isolate_root()
                addr0 = lookup_address(align_address(isolate_root + (deref & 0xffffffff)))
                addr1 = lookup_address(align_address(isolate_root + (deref >> 32)))
                compressed = [False, False]
                compressed[0] = addr0.dereference() and addr0.value > isolate_root + 0x0c000 and addr0.value & 1
                compressed[1] = addr1.dereference() and addr1.value > isolate_root + 0x0c000 and addr1.value & 1
                if True in compressed:
                    msg[1].append(format_address(addr.value+4))
                    for i in range(2):
                        if compressed[i]:
                            msg[i].append(format_compressed(addr0.value if not i else addr1.value))
                        else:
                            val = int(deref & 0xffffffff) if not i else int(deref >> 32)
                            if not (val & 1): # Maybe SMI
                                msg[i].append("        {:#0{ma}x} (SMI: {:#x})".format( val, val >> 1, ma=( 10 )) )
                            else:
                                msg[i].append("        {:#0{ma}x}".format( val, ma=( 10 )) )
                    return msg
                    
                
        while addr.section and max_recursion:
            if addr.value in seen_addrs:
                msg[0].append("[loop detected]")
                break
            seen_addrs.add(addr.value)

            max_recursion -= 1

            # Is this value a pointer or a value?
            # -- If it's a pointer, dereference
            deref = addr.dereference()
            if deref is None:
                # if here, dereferencing addr has triggered a MemoryError, no need to go further
                msg[0].append(str(addr))
                break

            new_addr = lookup_address(deref)
            if new_addr.valid:
                addr = new_addr
                msg[0].append(str(addr))
                continue

            # -- Otherwise try to parse the value
            if addr.section:
                if addr.section.is_executable() and addr.is_in_text_segment() and not is_ascii_string(addr.value):
                    insn = gef_current_instruction(addr.value)
                    insn_str = "{} {} {}".format(insn.location, insn.mnemonic, ", ".join(insn.operands))
                    msg[0].append(Color.colorify(insn_str, code_color))
                    break

                elif addr.section.permission.value & Permission.READ:
                    if is_ascii_string(addr.value):
                        s = read_cstring_from_memory(addr.value)
                        if len(s) < get_memory_alignment():
                            txt = '{:s} ("{:s}"?)'.format(format_address(deref), Color.colorify(s, string_color))
                        elif len(s) > 50:
                            txt = Color.colorify('"{:s}[...]"'.format(s[:50]), string_color)
                        else:
                            txt = Color.colorify('"{:s}"'.format(s), string_color)

                        msg[0].append(txt)
                        break

            # if not able to parse cleanly, simply display and break
            val = "{:#0{ma}x}".format(int(deref & 0xFFFFFFFFFFFFFFFF), ma=(current_arch.ptrsize * 2 + 2))
            msg[0].append(val)
            break

        return msg

register_external_command(V8DereferenceCommand())
