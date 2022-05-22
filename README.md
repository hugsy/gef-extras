<p align="center">
  <img src="https://i.imgur.com/KW9Bt8D.png" alt="logo"/>
</p>


## Extra goodies for [`GEF`](https://github.com/hugsy/gef) 

| **Documentation** | **Community** | **Try it** |
|--|--|--|
| [![Documentation Status](https://readthedocs.org/projects/gef-extras/badge/?version=latest&token=05e48c43fba3df26ad1ccf33353180e4b515681b727e2f3011013a915f953084)](https://gef-extras.readthedocs.io/en/latest/?badge=latest) | [![Discord](https://img.shields.io/badge/Discord-GDB--GEF-yellow)](https://discordapp.com/channels/705160148813086841/705160148813086843) | [![live](https://img.shields.io/badge/GEF-Live-brightgreen)](https://demo.gef.blah.cat) (`gef`/`gef-demo`) |

This is an open repository of external scripts and structures to be used by [GDB Enhanced Features (GEF)](https://github.com/hugsy/gef). To use those scripts once `gef` is setup, simply clone this repository and update your GEF settings like this:


### How-to use ###

#### Run the install script ####
```bash
$ wget -q -O- https://github.com/hugsy/gef/raw/master/scripts/gef-extras.sh | sh
```

#### Do it manually ####

Start with cloning this repo:
```bash
$ git clone https://github.com/hugsy/gef-extras
```

Add the path to the external scripts to GEF's config:
```
gef➤  gef config gef.extra_plugins_dir /path/to/gef-extras/scripts
```

And same for the structures (to be used by [`pcustom` command](https://gef.readthedocs.io/en/master/commands/pcustom/)):
```
gef➤  gef config pcustom.struct_path /path/to/gef-extras/structs
```

And for the syscall tables:
```
gef➤  gef config syscall-args.path /path/to/gef-extras/syscall-tables
```

And finally for the glibc function call args definition:
```
gef➤  gef config context.libc_args True
gef➤  gef config context.libc_args_path /path/to/gef-extras/glibc-function-args
```

Check out the [complete doc](docs/glibc_function_args.md) on libc argument support.


Now run and enjoy all the fun!


Note that it is possible to specify multiple directories, separating the paths with
a semi-colon:

```
gef➤  gef config gef.extra_plugins_dir /path/to/dir1;/path/to/dir2
```

And don't forget to save your settings.

```
gef➤ gef save
```


### Contributions ###

#### I can code! ####

Good for you! This repository is open to anyone, no filtering is done! Simply [drop a PR](https://github.com/hugsy/gef-scripts/pulls) with the command you want to share :smile: And useful scripts will eventually be integrated directly to GEF.

Check out [GEF API page](https://gef.readthedocs.io/en/latest/api/) to start writing powerful GDB commands using GEF!


#### I can't code 🤔 ####

Well, that's ok! Just create an [Issue](https://github.com/hugsy/gef-extras/issues)
explaining what cool feature/idea/command you had in mind! Even better, write
the documentation (Markdown format) for your command. It'll make easier for
people who wants to integrate it!


### Enjoy and happy hacking ! ###
