import randr
import sys
import os
import math

eDP_1 = 'eDP-1'         # builtin display
eDP_1_1 = 'eDP-1-1'     # builtin display (nvidia)
DP_1_1_1 = 'DP-1-1-1'   # docking station (HDMI)
HDMI_1_1 = 'HDMI-1-1'   # external hdmi

SELECT_HIGHEST_RES = 1
SELECT_HIGHEST_RATE = 2

# Monitors
UNKNOWN = "unknown"
BUILTIN = "builtin"
SAMSUNG_34_WIDE = "samsung_34_wide"
LG_BYTE = "lg_byte"
HD_TV = "ht_tv"

# Setup
EXTENAL_ON_RIGHT_ALIGN_BOTTOM = "external_on_right_align_bottom"
MIRROR = "mirror"
BUILTIN_ONLY = "builtin_only"
EXTERNAL_ONLY = "external_only"

SETUPS = [
	EXTENAL_ON_RIGHT_ALIGN_BOTTOM,
	MIRROR,
	BUILTIN_ONLY,
	EXTERNAL_ONLY
]

# Detect the specific displays
def identify(screen):
    mon = UNKNOWN

    #if screen.name == eDP_1_1 or screen.name == eDP_1:
    if screen.manufacturer == "Sharp Corporation":
        mon = BUILTIN

    elif screen.manufacturer == "Samsung Electric Company" and has_mode(screen, 3440, 1440, 49.99):
        mon = SAMSUNG_34_WIDE
    
    elif has_mode(screen, 4096, 2160, 24) and has_mode(screen, 1920, 1080, 120):
        mon = LG_BYTE

    elif has_mode(screen, 1920, 1080, 60):
        mon = HD_TV

    print("Detected monitor:", mon, "("+screen.manufacturer+(" "+screen.model if screen.model else "")+")")
    return mon







def has_mode(screen, w, h, r):
    for m in screen.supported_modes:
        if m.width == w and m.height == h and abs(r - m.freq) <= 0.015:
            return True
    return False

def select_mode(sort, modes):
    if(sort == SELECT_HIGHEST_RES):
        a = sorted(modes, key=lambda x: x.width*x.height, reverse=True)
        return a[0]

    if sort == SELECT_HIGHEST_RATE:
        a = sorted(modes, cmp=lambda x: x.freq*1e9 + x.width*x.height, reverse=True)
        return a[0]



def main(dry_run, setup_override):
    cs = randr.connected_screens()
    if False:
        for s in cs:
            print(s)
            for m in s.supported_modes:
                print(m)
                pass


    screens = {}
    for s in cs:
        screens[s.name] = s

    #print(screens)

    # Identify monitors
    monitors = {}
    for s in cs:
        ident = identify(s)
        if ident in monitors:
            raise("Detected multiple unknown monitors")
        monitors[ident] = s
    # Determine setup
    if (setup_override == MIRROR):
        print("Using setup:", setup_override)

        lowest =  (1920,1080)
        for s in cs:
            res = select_mode(SELECT_HIGHEST_RES, s.modes())
            if res.width < lowest[0]:
                lowest = (res.width, res.height)

        for s in cs:
            s.set_enabled(True)
            s.set_mode(lowest)
            s.set_position((0, 0))

    elif (setup_override == BUILTIN_ONLY):
        print("Using setup:", setup_override)
        for ident, s in monitors.items():
            if ident == BUILTIN:
                s.set_enabled(True)
                s.set_resolution((1920, 1080))
                s.set_position((0, 0))
            else:
                s.set_enabled(False)

    elif (setup_override == EXTERNAL_ONLY):
        print("Using setup:", setup_override)
        for ident, s in monitors.items():
            if ident == BUILTIN:
                s.set_enabled(False)
            else:
                s.set_enabled(True)
                s.set_mode(select_mode(SELECT_HIGHEST_RES, s.modes()))
                s.set_position((0, 0))

    elif SAMSUNG_34_WIDE in monitors.keys():
        print("Using setup:", EXTENAL_ON_RIGHT_ALIGN_BOTTOM)

        monitors[SAMSUNG_34_WIDE].set_enabled(True)
        monitors[SAMSUNG_34_WIDE].set_mode(select_mode(SELECT_HIGHEST_RES, monitors[SAMSUNG_34_WIDE].modes()))
        monitors[SAMSUNG_34_WIDE].set_position((1920, 0))

        monitors[BUILTIN].set_enabled(True)
        monitors[BUILTIN].set_resolution((1920, 1080))
        monitors[BUILTIN].set_position((0, 360))

    elif LG_BYTE in monitors.keys():
        print("Using setup:", EXTENAL_ON_RIGHT_ALIGN_BOTTOM)

        monitors[LG_BYTE].set_enabled(True)
        monitors[LG_BYTE].set_mode((1920, 1080, 60.0))
        monitors[LG_BYTE].set_position((1920, 0))

        monitors[BUILTIN].set_enabled(True)
        monitors[BUILTIN].set_resolution((1920, 1080))
        monitors[BUILTIN].set_position((0, 360))

    elif HD_TV in monitors.keys():
        print("Using setup:", EXTENAL_ON_RIGHT_ALIGN_BOTTOM)

        monitors[HD_TV].set_enabled(True)
        monitors[HD_TV].set_mode((1920, 1080, 60.0))
        monitors[HD_TV].set_position((1920, 0))

        monitors[BUILTIN].set_enabled(True)
        monitors[BUILTIN].set_resolution((1920, 1080))
        monitors[BUILTIN].set_position((0, 360))

    elif eDP_1_1 in screens.keys() and HDMI_1_1 in screens.keys():

        screens[HDMI_1_1].set_enabled(True)
        screens[HDMI_1_1].set_resolution(screens[HDMI_1_1].available_resolutions()[0])
        screens[HDMI_1_1].set_position((1920, 0))

        screens[eDP_1_1].set_enabled(True)
        screens[eDP_1_1].set_resolution((1920, 1080))
        screens[eDP_1_1].set_position((0, 360))

    elif eDP_1_1 in screens.keys() and DP_1_1_1 in screens.keys():

        screens[DP_1_1_1].set_enabled(True)
        screens[DP_1_1_1].set_mode(select_mode(SELECT_HIGHEST_RES, screens[DP_1_1_1].modes()))
        screens[DP_1_1_1].set_position((1920, 0))

        screens[eDP_1_1].set_enabled(True)
        screens[eDP_1_1].set_resolution((1920, 1080))
        screens[eDP_1_1].set_position((0, 360))

    elif eDP_1 in screens.keys() and len(screens.keys()) == 1:

        screens[eDP_1].set_enabled(True)
        screens[eDP_1].set_resolution((1920, 1080))
        screens[eDP_1].set_position((0, 0))

    elif eDP_1_1 in screens.keys() and len(screens.keys()) == 1:

        screens[eDP_1_1].set_enabled(True)
        screens[eDP_1_1].set_resolution((1920, 1080))
        screens[eDP_1_1].set_position((0, 0))

    else:
        print("Unknown setup")
        print(screens)
        sys.exit(1)
    
    randr.xrandr_apply(cs, dry_run)


if(__name__ == "__main__"):

    import argparse
    parser = argparse.ArgumentParser(description='Autoconfigure montitor setup')

    parser.add_argument("--setup", "-s", help='override setup autoselection, must be one of:\n['+", ".join(SETUPS)+']', default = EXTENAL_ON_RIGHT_ALIGN_BOTTOM, type=str)
    parser.add_argument("--dry-run", "-d", help='dry run, only print xrandr command', action='store_true')

    args = parser.parse_args()

    if args.setup is not None and args.setup not in SETUPS:
        parser.error("--setup must be one of: "+", ".join(SETUPS))

    main(args.dry_run, args.setup)
