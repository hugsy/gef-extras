## glibc function call arguments definition ##

This tree holds json used to print better definition of glibc function arguments.

Arguments' definitions are taken from glibc manual, and can be used as a kind reminder.

For example, the arguments for a `read@plt` would currently look like this:  

![read](https://user-images.githubusercontent.com/1745802/98736103-aed90900-23a4-11eb-8c8d-f1ae41e772f8.png)

but using this feature, it will instead look like this:

![read](https://user-images.githubusercontent.com/1745802/98736838-a7662f80-23a5-11eb-89b4-7f732713d64b.png)

Functions are detected if they end with `@plt`, which means that static binaries won't benefit from this.

User has to set two context configurations:
* `context.libc_args`: boolean, set to `True` to use this feature
* `context.libc_args_path`: string, must be set to the directory where the libc definition json files can be found

The script _generate_glibc_args_json.py_ is used to create provided json files. It works by parsing glibc manual text, can be downloaded from https://www.gnu.org/software/libc/manual/text/libc.txt.gz and saved in the current directory.  
