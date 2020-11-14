## glibc function call arguments definition ##

This tree holds json used to print better definition of glibc function arguments.

Arguments' definitions are taken from glibc manual, and can be used as a kind reminder.

Function is catched if they end with @plt.  
This means that static binaries won't benefit from this.

User has to set two context configurations:
* context.libc_args: boolean True/False, set to True to use this feature
* context.libc_args_path: string, must be set to the directory where json files is placed

File generate_glibc_args_json.py is used to create given json files.  
It works by parsing glibc manual txt, that should be download from https://www.gnu.org/software/libc/manual/text/libc.txt.gz and saved in current directory.
