## Command `got-audit`

Display the current state of GOT table of the running process.

The `got-audit` command optionally takes function names and filters the output displaying only the
matching functions.

The command output will list symbols in the GOT along with the file providing the mapped memory
where the symbol's value points.

If the file providing the mapped memory doesn't export the symbol, `got-audit` will print an
error.  If multiple files export the named symbol, `got-audit` will print an error.

```text
gef➤ got-audit
```

![gef-got-audit](https://i.imgur.com/KWStygQ.png)

The applied filter partially matches the name of the functions, so you can do something like this.

```text
gef➤ got-audit str
gef➤ got-audit print
gef➤ got-audit read
```

![gef-got-audit-one-filter](https://i.imgur.com/YucJboD.png)

Example of multiple partial filters:

```text
gef➤ got-audit str get
```

![gef-got-audit-multi-filter](https://i.imgur.com/VhMvXYZ.png)
