## Command ftrace ##


A quick'n dirty function tracer scripts for GEF.

To use:

```
gef➤ ftrace <function_name1>,<num_of_args> <function_name2>,<num_of_args>  ...
```

Example:

```
gef➤ ftrace malloc,1 calloc,2 free,1
```

