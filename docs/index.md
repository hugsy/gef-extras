## GEF Scripts ##

[![](https://readthedocs.org/projects/gef-scripts/badge/?version=master)](http://gef-scripts.readthedocs.io/en/master/)

## How-to

Open repositories of external scripts
for [GDB Enhanced Features (GEF)](https://github.com/hugsy/gef). To use those
scripts once `gef` is setup, simply clone this repository and update your GEF
settings like this:


```
gef➤  gef config gef.extra_plugins_dir /path/to/gef-scripts/directory
```

You can now load manually any script from this repo, or restart GDB to make GEF
load them automatically.

Note that it is possible to specify multiple directories, separating the paths with 
a semi-colon:

```
gef➤  gef config gef.extra_plugins_dir /path/to/dir1;/path/to/dir2
```


## Contributions

### I can code! ###

This repository is open to anyone, no filtering is done! Simply [drop a PR](https://github.com/hugsy/gef-scripts/pulls) with
the command you want to share :smile: And useful scripts will eventually be 
integrated directly to GEF.

Check out [GEF API page](https://gef.readthedocs.io/en/latest/api/) to start
writing powerful GDB commands using GEF!


### I can't code :weary: ###

Well, that's ok! Just create an [Issue](https://github.com/hugsy/gef-scripts/issues) 
explaining what cool feature/idea/command you had in mind!


## Thanks & enjoy !
