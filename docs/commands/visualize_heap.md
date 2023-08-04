## `visualize-libc-heap-chunks` ##

_Alias_: `heap-view`


This plugin aims to provide an ASCII-based simplistic representation of the heap layout.

Currently only the glibc heap support is implemented. The command doesn't take argument, and display the heap layout. It also aggregates similar lines for better readability:

```
gef➤  visualize-libc-heap-chunks
```

![img](https://i.imgur.com/jQYaiyB.png)
