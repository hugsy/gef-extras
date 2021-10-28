## Command retdec ##

`gef` uses the RetDec decompiler (https://github.com/avast/retdec)
to decompile parts of or entire binary. The command, `retdec`, also has a
default alias, `decompile` to make it easier to remember.

To use the command, you need to provide `gef` the path to a retdec installation. The compiled source can be found on the [releases](https://github.com/avast/retdec/releases) page. 

```
cd /opt
wget https://github.com/avast/retdec/releases/download/v4.0/retdec-v4.0-ubuntu-64b.tar.xz
tar xvf retdec-v4.0-ubuntu-64b.tar.xz
```

Then enter the path the `gef config` command:

```
gef➤ gef config retdec.retdec_path /opt/retdec
```

You can have `gef` save this path by saving the current configuration settings.

```
gef➤ gef save
```

`retdec` can be used in 3 modes:

   * By providing the option `-a`, `gef` will submit the entire binary being
     debugged to RetDec. For example,
```
gef➤ decompile -a
```
![gef-retdec-full](https://i.imgur.com/58VSHt0.png)

   * By providing the option `-r START:END`, `gef` will submit only the raw
     bytes contained within the range specified as argument.

   * By providing the option `-s SYMBOL`, `gef` will attempt to reach a specific
     function symbol, dump the function in a temporary file, and submit it to
     RetDec. For example,
```
gef➤ decompile -s main
```
![gef-retdec-symbol-main](https://i.imgur.com/QXaTqyM.png)


## Syntax Highlighting

Retdec now supports syntax highlighting for all C decompilations with the use of Pygments.

Supported themes are: 
```
default, emacs, friendly, colorful, autumn, murphy, manni, material, monokai, perldoc, pastie, borland, trac, native, fruity, bw, vim, vs, tango, rrt, xcode, igor, paraiso-light, paraiso-dark, lovelace, algol, algol_nu, arduino, rainbow_dash, abap, solarized-dark, solarized-light, sas, stata, stata-light, stata-dark, inkpot, zenburn, gruvbox-dark, gruvbox-light
```

You can change themes by running
```py
gef config retdec.theme <THEME_NAME>
gef save # remember to save your config!
```
