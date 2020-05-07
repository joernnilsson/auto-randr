import randr
import sys
import os
import math
import gnome_monitors
import string
from functools import reduce

# TODO select fallback if preferred dpi is 4k, but not all screens are 4k
# TODO better detection of builtin display
# TODO align edge as cli argument
# TODO specify monitor order

# Setup
EXTENAL_ON_RIGHT_ALIGN_BOTTOM = "external_on_right_align_bottom"
EXTENAL_ON_LEFT_ALIGN_BOTTOM = "external_on_left_align_bottom"
MIRROR = "mirror"
BUILTIN_ONLY = "builtin_only"
EXTERNAL_ONLY = "external_only"

# Density
DENSITY_HD = "hd"
DENSITY_4K = "4k"

# Mode selectors
MODE_SELECT_RATE = 'rate'
MODE_SELECT_DENSITY = 'density'
MODE_SELECT_RESOLUTION = 'resolution'

# Align options
ALIGN_TOP = 'top'
ALIGN_BOTTOM = 'bottom'


DENSITIES = [
    DENSITY_HD,
    DENSITY_4K
]

SETUPS = [
	EXTENAL_ON_RIGHT_ALIGN_BOTTOM,
	EXTENAL_ON_LEFT_ALIGN_BOTTOM,
	MIRROR,
	BUILTIN_ONLY,
	EXTERNAL_ONLY
]

DENSITY_4K_THRESHOLD = 150.0

def is_builtin(screen):
    if screen.name == 'eDP-1':
        return True
    return False

def filter_mode(mode, requirements = {}):
    for key, val in requirements.items():
        if key == MODE_SELECT_DENSITY:
            if val == DENSITY_HD and mode.dpi > DENSITY_4K_THRESHOLD:
                return False
            if val == DENSITY_4K and mode.dpi < DENSITY_4K_THRESHOLD:
                return False
        elif key == MODE_SELECT_RATE and mode.freq < val:
            return False
    return True

def mode_sort_key(mode, order = []):
    keys = []
    for o in order:
        if o == MODE_SELECT_DENSITY:
            keys.append(mode.dpi)
        elif o == MODE_SELECT_RATE:
            keys.append(mode.freq)
        elif o == MODE_SELECT_RESOLUTION:
            keys.append(mode.width * mode.height)
    return tuple(keys)

def select_mode_2(modes, requirements = {}, sort = []):
    candidates = list(filter(lambda x: filter_mode(x, requirements), modes))
    a = sorted(candidates, key=lambda x: mode_sort_key(x, sort), reverse=True)

    return a[0]

def set_positions(screens, align):
        widest = reduce(lambda y, x : x.set.resolution[0] if (x.set.resolution[0] > y) else y, screens, 0)
        highest = reduce(lambda y, x : x.set.resolution[1] if (x.set.resolution[1] > y) else y, screens, 0)

        used_width = 0
        for s in screens:
            y = 0 if align == ALIGN_TOP else highest - s.set.resolution[1]
            s.set_position((used_width, y))
            used_width += s.set.resolution[0]


def main(dry_run, setup_override, preferred_density,print_modes, gnome_save, gnome_save_file):
    cs = randr.connected_screens()

    # Print info
    for s in cs:
        print(s)
        if print_modes:
            for m in s.modes():
                print(m)

    # Classify internal/external
    screen_builtin = None
    screens_external = []
    for s in cs:
        if is_builtin(s):
            screen_builtin = s
        else:
            screens_external.append(s)

    # TODO auto select from available setups
    selected_setup = setup_override if setup_override is not None else EXTENAL_ON_RIGHT_ALIGN_BOTTOM

    # Apply setup
    print("Using setup:", selected_setup)
    if (selected_setup == MIRROR):

        mode_requirements = {MODE_SELECT_DENSITY: preferred_density}
        mode_sort = [MODE_SELECT_RESOLUTION, MODE_SELECT_RATE]

        builtin_mode = select_mode_2(screen_builtin.modes(), mode_requirements, mode_sort)

        lowest = (builtin_mode.width, builtin_mode.height)
        for s in screens_external:
            res = select_mode_2(s.modes(), mode_requirements, mode_sort)
            if res.width < lowest[0]:
                lowest = (res.width, res.height)

        # TODO use lowest resolution as mode requirement
        for s in cs:
            s.set_enabled(True)
            s.set_mode(lowest)
            s.set_position((0, 0))

    elif (selected_setup == BUILTIN_ONLY):
        
        mode_requirements = {MODE_SELECT_DENSITY: preferred_density}
        mode_sort = [MODE_SELECT_RESOLUTION, MODE_SELECT_RATE]

        builtin_mode = select_mode_2(screen_builtin.modes(), mode_requirements, mode_sort)

        screen_builtin.set_enabled(True)
        screen_builtin.set_mode(builtin_mode)
        screen_builtin.set_position((0, 0))

        for s in screens_external:
            s.set_enabled(False)
                
    elif (selected_setup == EXTERNAL_ONLY):
        
        # Sort screens
        screens_sorted = []
        for s in screens_external:
            screens_sorted.append(s)

        # Disable unused screens
        screen_builtin.set_enabled(False)

        # Determine modes
        mode_requirements = {MODE_SELECT_DENSITY: preferred_density}
        mode_sort = [MODE_SELECT_RESOLUTION, MODE_SELECT_RATE]
        for s in screens_sorted:
            mode = select_mode_2(s.modes(), mode_requirements, mode_sort)
            s.set_enabled(True)
            s.set_mode(mode)

        # Set positions
        set_positions(screens_sorted, ALIGN_BOTTOM)

    elif (selected_setup == EXTENAL_ON_RIGHT_ALIGN_BOTTOM):

        # Sort screens
        screens_sorted = []
        screens_sorted.append(screen_builtin)
        for s in screens_external:
            screens_sorted.append(s)

        # Disable unused screens

        # Determine modes
        mode_requirements = {MODE_SELECT_DENSITY: preferred_density}
        mode_sort = [MODE_SELECT_RESOLUTION, MODE_SELECT_RATE]
        for s in screens_sorted:
            mode = select_mode_2(s.modes(), mode_requirements, mode_sort)
            s.set_enabled(True)
            s.set_mode(mode)

        # Set positions
        set_positions(screens_sorted, ALIGN_BOTTOM)

    elif (selected_setup == EXTENAL_ON_LEFT_ALIGN_BOTTOM):

        # Sort screens
        screens_sorted = []
        for s in screens_external:
            screens_sorted.append(s)
        screens_sorted.append(screen_builtin)

        # Disable unused screens

        # Determine modes
        mode_requirements = {MODE_SELECT_DENSITY: preferred_density}
        mode_sort = [MODE_SELECT_RESOLUTION, MODE_SELECT_RATE]
        for s in screens_sorted:
            mode = select_mode_2(s.modes(), mode_requirements, mode_sort)
            s.set_enabled(True)
            s.set_mode(mode)

        # Set positions
        set_positions(screens_sorted, ALIGN_BOTTOM)

    randr.xrandr_apply(cs, dry_run)

    if gnome_save and not dry_run:
        print("Saving to: "+gnome_save_file)
        gnome_monitors.save(cs, gnome_save_file)
        


if(__name__ == "__main__"):

    import argparse
    parser = argparse.ArgumentParser(description='Autoconfigure monitor setup')

    default_backend_path = string.Template("$HOME/.config/monitors.xml").substitute(os.environ)

    parser.add_argument("--setup", "-s", help='override setup autoselection, must be one of:\n['+", ".join(SETUPS)+']', default = None, type=str)
    parser.add_argument("--dry-run", "-d", help='dry run, only print xrandr command', action='store_true')
    parser.add_argument("--density", "-n", help='pereferred density, [hd, 4k]', default = DENSITY_HD, type=str)
    parser.add_argument("--print-modes", "-p", help="print available modes", action='store_true')
    parser.add_argument("--disable-gnome-save", "-g", help="disable saving to gnome xml backend", action='store_true')
    parser.add_argument("--gnome-save-file", help='gnome xml backend file to use ['+default_backend_path+']', default = default_backend_path, type=str)

    args = parser.parse_args()

    if args.setup is not None and args.setup not in SETUPS:
        parser.error("--setup must be one of: "+", ".join(SETUPS))

    if args.density is not None and args.density not in DENSITIES:
        parser.error("--density must be one of: "+", ".join(DENSITIES))

    main(args.dry_run, args.setup, args.density, args.print_modes, not(args.disable_gnome_save), args.gnome_save_file)
