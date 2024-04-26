## Installing GEF-Extras

This page explains to how set up GEF-Extras to work alongside of GEF.

## Prerequisites

### GDB

Only [GDB 8 and higher](https://www.gnu.org/s/gdb) is required. It must be compiled with Python 3.6
or higher support. For most people, simply using your distribution package manager should be enough.

GEF will then only work for Python 3. If you absolutely require GDB + Python 2, please use
[GEF-Legacy](https://github.com/hugsy/gef-legacy) instead. Note that `gef-legacy` won't provide new
features, and only functional bugs will be handled.

You can verify it with the following command:

```bash
b -nx -ex 'pi print(sys.version)' -ex quit
```

This should display your version of Python compiled with `gdb`.

```bash
$ gdb -nx -ex 'pi print(sys.version)' -ex quit
3.6.9 (default, Nov  7 2019, 10:44:02)
[GCC 8.3.0]
```

### GEF

For a quick installation of GEF, you can get started with the following commands:

```bash
# via the install script
## using curl
$ bash -c "$(curl -fsSL https://gef.blah.cat/sh)"

## using wget
$ bash -c "$(wget https://gef.blah.cat/sh -O -)"
```

For more advanced installation methods, refer
[the installation chapter of the GEF documentation](https://hugsy.github.io/gef/install).

### Python dependencies

Because GEF-Extras allows external dependencies, you must make sure to have the adequate Python
libraries installed before you can use the features.

Thankfully this is easily done in Python, as such:

```text
wget -O /tmp/requirements.txt https://raw.githubusercontent.com/hugsy/gef-extras/main/requirements.txt
python -m pip install --user --upgrade -r /tmp/requirements.txt
```


### Installation using Git

Start with cloning this repo:

```bash
git clone https://github.com/hugsy/gef-extras
```

Add syscall_args and libc_function_args to context layout:

```text
gef➤  pi gef.config['context.layout'] += ' syscall_args'
gef➤  pi gef.config['context.layout'] += ' libc_function_args'
```

Add the path to the external scripts to GEF's config:

```text
gef➤  gef config gef.extra_plugins_dir /path/to/gef-extras/scripts
```

And same for the structures (to be used by
[`pcustom` command](https://hugsy.github.io/gef/commands/pcustom/)):

```text
gef➤  gef config pcustom.struct_path /path/to/gef-extras/structs
```

And for the syscall tables:

```text
gef➤  gef config syscall-args.path /path/to/gef-extras/syscall-tables
```

And finally for the glibc function call args definition:

```text
gef➤  gef config context.libc_args True
gef➤  gef config context.libc_args_path /path/to/gef-extras/glibc-function-args
```

And don't forget to save your settings.

```text
gef➤ gef save
```

Check out the [complete documentation](commands/glibc_function_args.md) on libc argument support.

Note that it is possible to specify multiple directories, separating the paths with
a semi-colon:

```text
gef➤  gef config gef.extra_plugins_dir /path/to/dir1;/path/to/dir2
```

Now run and enjoy all the fun!


