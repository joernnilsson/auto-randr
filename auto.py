import randr
import sys
import os
import math

eDP_1 = 'eDP-1'         # builtin display
eDP_1_1 = 'eDP-1-1'     # builtin display
DP_1_1_1 = 'DP-1-1-1'   # docking station (HDMI)
HDMI_1_1 = 'HDMI-1-1'   # builtin hdmi

SELECT_HIGHEST_RES = 1

# Monitors
UNKNOWN = "unknown"
BUILTIN = "builtin"
SAMSUNG_34_WIDE = "samsung_34_wide"
LG_BYTE = "lg_byte"

# Setup
EXTENAL_ON_RIGHT_BOTTM_FLUSH = "external_on_right_bottom_flush"
MIRROR = "mirror"

def identify(screen):
    mon = UNKNOWN

    if screen.name == eDP_1_1 or screen.name == eDP_1:
        mon = BUILTIN

    elif select_mode(SELECT_HIGHEST_RES, screen.available_resolutions()) == (3440, 1440):
        mon = SAMSUNG_34_WIDE
    
    elif has_mode(screen, 4096, 2160, 24) and has_mode(screen, 1920, 1080, 120):
        mon = LG_BYTE

    print("Detected monitor:", mon)
    return mon

def has_mode(screen, w, h, r):
    for m in screen.supported_modes:
        if m.width == w and m.height == h and abs(r - m.freq) <= 0.015:
            return True
    return False

def select_mode(sort, modes):
    if(sort == SELECT_HIGHEST_RES):
        a = sorted(modes, key=lambda x: x[0]*x[1], reverse=True)
        return a[0]

def main(dry_run, mirror):
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

    #print screens

    # Identify monitors
    monitors = {}
    for s in cs:
        ident = identify(s)
        if ident in monitors:
            raise("Detected multiple unknown monitors")
        monitors[ident] = s

    # Determine setup
    if (mirror):
        print("Using setup:", MIRROR)

        lowest =  (99999,99999)
        for s in cs:
            res = select_mode(SELECT_HIGHEST_RES, s.available_resolutions())
            if res[0] < lowest[0]:
                lowest = res

        for s in cs:
            s.set_enabled(True)
            s.set_mode(lowest)
            s.set_position((0, 0))

    elif SAMSUNG_34_WIDE in monitors.keys():
        print("Using setup:", EXTENAL_ON_RIGHT_BOTTM_FLUSH)

        monitors[SAMSUNG_34_WIDE].set_enabled(True)
        monitors[SAMSUNG_34_WIDE].set_resolution(select_mode(SELECT_HIGHEST_RES, monitors[SAMSUNG_34_WIDE].available_resolutions()))
        monitors[SAMSUNG_34_WIDE].set_position((1920, 0))

        monitors[BUILTIN].set_enabled(True)
        monitors[BUILTIN].set_resolution((1920, 1080))
        monitors[BUILTIN].set_position((0, 360))

    elif LG_BYTE in monitors.keys():
        print("Using setup:", EXTENAL_ON_RIGHT_BOTTM_FLUSH)

        monitors[LG_BYTE].set_enabled(True)
        monitors[LG_BYTE].set_mode((1920, 1080, 60.0))
        monitors[LG_BYTE].set_position((1920, 0))

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
        screens[DP_1_1_1].set_resolution(select_mode(SELECT_HIGHEST_RES, screens[DP_1_1_1].available_resolutions()))
        screens[DP_1_1_1].set_position((1920, 0))

        screens[eDP_1_1].set_enabled(True)
        screens[eDP_1_1].set_resolution((1920, 1080))
        screens[eDP_1_1].set_position((0, 360))

    else:
        print("Unknown setup")
        print(screens)
        sys.exit(1)
    
    #print(screens[DP_1_1_1])

    randr.xrandr_apply(cs, dry_run)


if(__name__ == "__main__"):
    dry = False
    mirror = False
    if "-d" in sys.argv:
        dry = True
    if "-m" in sys.argv:
        mirror = True
    main(dry, mirror)