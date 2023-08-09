<p align="center">
  <img src="https://i.imgur.com/KW9Bt8D.png" alt="logo"/>
</p>

<p align="center">
    <a href="https://discord.gg/HCS8Hg7"><img alt="Discord" src="https://img.shields.io/badge/Discord-BlahCats-yellow"></a>
  <a href="https://hugsy.github.io/gef-extras"><img alt="Docs" src="https://img.shields.io/badge/Docs-gh--pages-brightgreen"></a>
  <a title="Use the IDs: gef/gef-demo" href="https://demo.gef.blah.cat"><img alt="Try GEF" src="https://img.shields.io/badge/Demo-Try%20GEF%20Live-blue"></a>
</p>

## Extra goodies for [`GEF`](https://github.com/hugsy/gef)

This is an open repository of external scripts and structures to be used by
[GEF](https://github.com/hugsy/gef). As GEF aims to stay a one-file battery-included plugin for
GDB, it doesn't allow by nature to be extended with external Python library. GEF-Extras remediates
that providing some more extensibility to GEF through:

-  more commands and functions
-  publicly shared structures for the `pcustom` command
-  more operating system support
-  more file format support


## Quick start

The biggest requirement for GEF-Extras to work is of course `GEF`. Please refer to GEF
documentation to have it set up (spoiler alert: it's pretty easy 😉). Once GEF is up and running,
you can install GEF-Extras.

### Automated installation

Execute and run the installation script from GEF repository.

```bash
wget -q -O- https://github.com/hugsy/gef/raw/main/scripts/gef-extras.sh | sh
```

The script will download (via git) GEF-Extras, and set up your `~/.gef.rc` file so that you can
start straight away.

Refer to the [installation page](install.md) for more installation methods.


## Contribution

### Through Pull-Requests

This repository is open for anyone to contribute! Simply
[drop a PR](https://github.com/hugsy/gef-scripts/pulls) with the new command/function/feature. One
thing to note, GEF and GEF-Extras have become what they are today thanks to an up-to-date
documentation, so considering attaching a simple Markdown file to the `docs` folder explaining your
update. **IF** your code is complex and/or requires further scrutiny, adding CI tests would also be
asked during the review process of your PR.

For a complete rundown of the commands/functions GEF allows to use out of the box, check out
[GEF API page](https://gef.github.io/gef/api/) to start writing powerful GDB commands using GEF!

As a reward, your Github avatar will be immortalize in the list below of contributors to GEF-Extras

![[contributors-img](https://contrib.rocks/image?repo=hugsy/gef-extras)
](<https://github.com/hugsy/gef-extras/graphs/contributors>)


### Feature requests

Well, that's ok! Just create an [Issue](https://github.com/hugsy/gef-extras/issues) explaining what
cool feature/idea/command you had in mind! Even better, write the documentation (Markdown format)
for your command. It'll make easier for people who wants to integrate it!


### Sponsoring

Sponsoring is another way to help projects to thrive. You can sponsor GEF and GEF-Extras by
following [this link](https://github.com/sponsors/hugsy).


## Happy hacking 🍻
