## GEF Extras: more goodies for [`GEF`](https://github.com/hugsy/gef) ##

[![Documentation Status](https://readthedocs.org/projects/gef-extras/badge/?version=latest)](http://gef-extras.readthedocs.io/en/latest/?badge=latest)

This is an open repository of external scripts and structures to be used by
[GDB Enhanced Features (GEF)](https://github.com/hugsy/gef). To use those
scripts once `gef` is setup, simply clone this repository and update your GEF
settings like this:


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

Good for you! This repository is open to anyone, no filtering is done!
Simply [drop a PR](https://github.com/hugsy/gef-scripts/pulls) with
the command you want to share :smile: And useful scripts will eventually be
integrated directly to GEF.

Check out [GEF API page](https://gef.readthedocs.io/en/latest/api/) to start
writing powerful GDB commands using GEF!


#### I can't code :weary: ####

Well, that's ok! Just create an [Issue](https://github.com/hugsy/gef-extras/issues)
explaining what cool feature/idea/command you had in mind! Even better, write
the documentation (Markdown format) for your command. It'll make easier for
people who wants to integrate it!


### Enjoy and happy hacking ! ###
