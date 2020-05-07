# auto-randr
```
usage: auto.py [-h] [--setup SETUP] [--dry-run] [--density DENSITY]
               [--print-modes] [--disable-gnome-save]
               [--gnome-save-file GNOME_SAVE_FILE] [--align ALIGN]

Autoconfigure monitor setup

optional arguments:
  -h, --help            show this help message and exit
  --setup SETUP, -s SETUP
                        override setup autoselection, must be one of:
                        [external_on_right, external_on_left, mirror,
                        builtin_only, external_only]
  --dry-run, -d         dry run, only print xrandr command
  --density DENSITY, -n DENSITY
                        pereferred density, [hd, 4k]
  --print-modes, -p     print available modes
  --disable-gnome-save, -g
                        disable saving to gnome xml backend
  --gnome-save-file GNOME_SAVE_FILE
                        gnome xml backend file to use
                        [/home/joern/.config/monitors.xml]
  --align ALIGN, -a ALIGN
                        align display edges [bottom, top]

```

