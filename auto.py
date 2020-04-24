import randr
import sys
import os
import math
import gnome_monitors
import string


# TODO support multiple external monitors
# TODO respect dpi settings
# TODO select fallback if preferred dpi is 4k, but not all screens are 4k
# TODO better detection of builtin display

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

def main(dry_run, setup_override, preferred_density,print_modes, gnome_save, gnome_save_file):
    cs = randr.connected_screens()
    if False:
        for s in cs:
            print(s)
            for m in s.supported_modes:
                print(m)
                pass        

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
        
        mode_requirements = {MODE_SELECT_DENSITY: preferred_density}
        mode_sort = [MODE_SELECT_RESOLUTION, MODE_SELECT_RATE]

        screen_builtin.set_enabled(False)

        # TODO respect dpi settings
        for s in screens_external:
            s.set_enabled(True)
            s.set_mode(select_mode_2(s.modes(), mode_requirements, mode_sort))
            s.set_position((0, 0))

    elif (selected_setup == EXTENAL_ON_RIGHT_ALIGN_BOTTOM):

        # Determine modes
        mode_requirements = {MODE_SELECT_DENSITY: preferred_density}
        mode_sort = [MODE_SELECT_RESOLUTION, MODE_SELECT_RATE]

        builtin_mode = select_mode_2(screen_builtin.modes(), mode_requirements, mode_sort)
        screen_builtin.set_enabled(True)
        screen_builtin.set_mode(builtin_mode)
        screen_builtin.set_position((0, 0))

        highest = builtin_mode.height
        for s in screens_external:
            s.set_enabled(True)
            mode = select_mode_2(s.modes(), mode_requirements, mode_sort)
            s.set_mode(mode)
            s.set_position((builtin_mode.width, 0))
            highest = max(highest, mode.height)

        # Apply vertical positions for bottom alignment
        for s in cs:
            current_position = s.set.position
            new_position = (current_position[0], highest - s.set.resolution[1])
            s.set_position(new_position)


    elif (selected_setup == EXTENAL_ON_LEFT_ALIGN_BOTTOM):

        # Determine modes
        mode_requirements = {MODE_SELECT_DENSITY: preferred_density}
        mode_sort = [MODE_SELECT_RESOLUTION, MODE_SELECT_RATE]

        builtin_mode = select_mode_2(screen_builtin.modes(), mode_requirements, mode_sort)
        screen_builtin.set_enabled(True)
        screen_builtin.set_mode(builtin_mode)

        highest = builtin_mode.height
        widest = 0
        for s in screens_external:
            s.set_enabled(True)
            mode = select_mode_2(s.modes(), mode_requirements, mode_sort)
            s.set_mode(mode)
            s.set_position((0, 0))
            highest = max(highest, mode.height)
            widest = max(widest, mode.width)

        screen_builtin.set_position((widest, 0))

        # Apply vertical positions for bottom alignment
        for s in cs:
            current_position = s.set.position
            new_position = (current_position[0], highest - s.set.resolution[1])
            s.set_position(new_position)

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
