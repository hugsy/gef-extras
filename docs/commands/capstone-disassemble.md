## Command capstone-disassemble

If you have installed the [`capstone`](http://capstone-engine.org) library and
its Python bindings, you can use it to disassemble any memory in your debugging
session. This plugin was created to offer an alternative to `GDB`'s disassemble
function which sometimes gets things mixed up.

You can use its alias `cs-disassemble` or just `cs` with the location to
disassemble at. If not specified, it will use `$pc`.

```text
gef➤ cs main+0x10
```

![cs-disassemble](https://i.imgur.com/JG7aVRP.png)

Disassemble more instructions

```text
gef➤ cs --length 20
```

Show opcodes next to disassembly

```text
gef➤ cs --show-opcodes
```
