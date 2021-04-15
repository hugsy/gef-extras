# error

A basic equivalent to WinDbg `!error` command.

If a debugging session is active, `error` can be used with no argument: the command will use the `return_register` of the current architecture associated to the binary.

```
[ Legend: Modified register | Code | Heap | Stack | String ]
─────────────────────────────────────────────────────────────────────────────────────── registers ────
$rax   : 0x1
[...]
gef➤ error
1 (0x1) : Operation not permitted
```

Otherwise, an argument is expected: this argument can be a debugging symbol (for instance a register) or the integer holding the error code to translate:

```
gef➤ error 42
42 (0x2a) : No message of desired type
```

```
gef➤ eq $sp 0x1337
gef➤ error *(int*)$sp
4919 (0x1337) : Unknown error 4919
```