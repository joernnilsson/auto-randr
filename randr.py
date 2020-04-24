#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Cihangir Akturk <cihangir.akturk@tubitak.gov.tr>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import subprocess as sb
from util import hex2bytes
from edid import Edid

class Mode(object):
    """docstring for Mode"""
    def __init__(self, width, height, freq, current, preferred):
        super(Mode, self).__init__()
        self.width = width
        self.height = height
        self.freq = freq
        self.current = current
        self.preferred = preferred
        self.dpi = 100.0

    def resolution(self):
        return (self.width, self.height)

    def __str__(self):
        return "{}\t{:.2f} hz\t{:.1f} dpi\t preferred: {}\tcurrent: {}".format(
            "{}x{}".format(self.width, self.height).ljust(10), 
            self.freq, 
            self.dpi, 
            self.current, 
            self.preferred)


    def cmd_str(self, arg1):
        return '{0}x{1}'.format(self.width, self.height)

    __repr__ = __str__

class ScreenSettings(object):
    """docstring for ScreenSettings"""
    def __init__(self):
        super(ScreenSettings, self).__init__()
        self.reset()

    def reset(self):
        self.resolution = None
        self.is_primary = False
        self.is_enabled = True
        self.rotation = None
        self.position = None
        self.dirty = False
        self.freq = None

class Screen(object):
    def __init__(self, name, primary, rot, modes, manufacturer_id, manufacturer, model, physical_width, physical_height, product_id, serial_no):
        super(Screen, self).__init__()

        self.name = name
        self.primary = primary
        self.manufacturer_id = manufacturer_id
        self.manufacturer = manufacturer
        self.model = model
        self.product_id = product_id
        self.serial_no = serial_no

        self.physical_width = physical_width
        self.physical_height = physical_height

        # dirty hack
        self.rotation = None
        for r in modes:
            if r.current:
                self.rotation = rot
                self.curr_mode = r
                break

        # list of Modes (width, height)
        self.supported_modes = modes

        self.set = ScreenSettings()
        self.set.is_enabled = self.is_enabled()

    def is_connected(self):
        return len(self.supported_modes) != 0

    def is_enabled(self):
        for m in self.supported_modes:
            if m.current:
                return True
        return False

    def available_resolutions(self):
        return [(r.width, r.height) for r in self.supported_modes]

    def check_resolution(self, newres):
        if newres not in self.available_resolutions():
            raise ValueError('Requested resolution is not supported', newres)

    def modes(self):
        return self.supported_modes

    def set_resolution(self, newres):
        """Sets the resolution of this screen to the supplied
           @newres parameter.

        :newres: must be a tuple in the form (width, height)

        """
        #if not self.is_enabled():
        #    raise ValueError('The Screen is off')

        self.check_resolution(newres)
        self.set.resolution = newres
    
    def set_mode(self, mode):
        if type(mode) == tuple:
            self.set_resolution((mode[0], mode[1]))
            if len(mode) > 2:
                self.set.freq = mode[2]
        else:
            self.set_resolution((mode.width, mode.height))
            self.set.freq = mode.freq

    def set_as_primary(self,  is_primary):
        """Set this monitor as primary

        :is_primary: bool

        """
        self.set.is_primary = is_primary

    def set_enabled(self, enable):
        """Enable or disable the output

        :enable: bool

        """
        self.set.is_enabled = enable

    def rotate(self, direction):
        """Rotate the output in the specified direction

        :direction: one of (normal, left, right, inverted)

        """
        self.set.rotation = direction

    def set_position(self, pos):
        """Position the output relative to the position
        of another output.

        :relation: TODO
        :relative_to: output name (LVDS1, HDMI eg.)
        """
        self.set.position = pos

    def build_cmd(self):
        if not self.name:
            raise ValueError('Cannot apply settings without screen name', \
                             self.name)

        if self.set.resolution:
            self.check_resolution(self.set.resolution)

        has_changed = False

        cmd = ['--output', self.name]

        if self.set.is_enabled:

            cmd.append('--auto')
            cmd.extend(['--mode', '{0}x{1}'.format(self.set.resolution[0], self.set.resolution[1])])
            cmd.extend(['--pos', "x".join(str(x) for x in self.set.position)])

            if self.set.freq:
                cmd.extend(["--rate", str(self.set.freq)])

        else:
            
            cmd.append('--off')

        return cmd
        
        # set resolution
        if self.is_enabled() \
                and self.curr_mode.resolution() == self.set.resolution \
                or not self.set.resolution:
            cmd.append('--auto')
        else:
            res = self.set.resolution
            cmd.extend(['--mode', '{0}x{1}'.format(res[0], res[1])])
            has_changed = True

        # Check if this screen is already primary
        if not self.primary and self.set.is_primary:
            cmd.append('--primary')
            has_changed = True

        if self.set.rotation and self.set.rotation is not self.rotation:
            rot = rot_to_str(self.set.rotation)
            if not rot:
                raise ValueError('Invalid rotation value', \
                                 rot, self.set.rotation)
            cmd.extend(['--rotate', rot])
            has_changed = True

        if self.set.position:
            cmd.extend(['--pos', "x".join(str(x) for x in self.set.position)])
            has_changed = True

        if self.is_enabled() and not self.set.is_enabled:
            if has_changed:
                raise Exception('--off: this option cannot be combined ' \
                                'with other options')
            cmd.append('--off')
            has_changed = True

        return cmd

    def apply_settings(self):
        print(self.build_cmd())
        #exec_cmd(self.build_cmd())
        self.set.reset()

    def __str__(self):
        return '{}: {} ({} {}) primary: {}, modes: {}, conn: {}, rot: {}, enabled: {}'.format( \
                    self.name, \
                    self.manufacturer, \
                    self.manufacturer_id, \
                    self.model, \
                    self.primary, \
                    len(self.supported_modes), 
                    self.is_connected(), \
                    rot_to_str(self.rotation), \
                    self.is_enabled())

    __repr__ = __str__

class RotateDirection(object):
    Normal, Left, Inverted, Right = range(1, 5)
    valtoname = {Normal:'normal', Left:'left', Inverted:'inverted', \
            Right:'right'}
    nametoval = dict((v, k) for k, v in valtoname.items())

def rot_to_str(rot):
    if rot in RotateDirection.valtoname:
        return RotateDirection.valtoname[rot]
    return None

def str_to_rot(s):
    if s in RotateDirection.nametoval:
        return RotateDirection.nametoval[s]
    return RotateDirection.Normal

class PostitonType(object):
    LeftOf, RightOf, Above, Below, SameAs = range(1, 6)
    valtoname = {LeftOf:'--left-of', RightOf:'--right-of', Above:'--above', \
                 Below:'--below', SameAs:'--same-as'}
    nametoval = dict((v, k) for k, v in valtoname.items())

def pos_to_str(n):
    return PostitonType.valtoname[n]

def str_to_pos(s):
    return PostitonType.nametoval[s]

def exec_cmd(cmd):
    # throws exception CalledProcessError
    s = sb.check_output(cmd, stderr=sb.STDOUT)
    return s.decode("utf-8").split('\n')

def xrandr_apply(screens, dryrun):
    cmd = ['xrandr']
    for s in screens:
        cmd = cmd + s.build_cmd()
    print(" ".join(cmd))
    if not dryrun:
        exec_cmd(cmd)

def create_screen(sc_line, modes, edid_data):

    name = sc_line.split(' ')[0]
    model = ""
    manufacturer_id = ""
    manufacturer = ""
    product_id = 0
    serial_no = 0
    physical_width = 30.0
    physical_height = 30.0
    if(len(edid_data) > 0):
        bytes = hex2bytes("".join(edid_data[0:8]))
        parsed_edid = Edid(bytes)
        model = parsed_edid.name if parsed_edid.name else ""
        manufacturer_id = parsed_edid.manufacturer_id
        manufacturer = parsed_edid.manufacturer
        physical_width = parsed_edid.width
        physical_height = parsed_edid.height
        product_id = parsed_edid.product
        serial_no = parsed_edid.serial_no

    # Set dpi of modes
    for mode in modes:
        mode.dpi = mode.height / (physical_height/2.54)

    # if connected
    rot = None
    if modes:
        fr = sc_line.split(' ')
        if len(fr) > 2:
            rot = str_to_rot(sc_line.split(' ')[3])

    return Screen(name, 'primary' in sc_line, rot, modes, manufacturer_id, manufacturer, model, physical_width, physical_height, product_id, serial_no)

def parse_xrandr(lines):
    import re
    #rx = re.compile('^\s+(\d+)x(\d+)\s+((?:\d+\.)?\d+)([* ]?)([+ ]?)')
    rx = re.compile('^\s+(\d+)x(\d+)\s+')
    #rxfreq = re.compile('\s((?:\d+\.)?\d+)([* ]?)([+ ]?)')
    rxfreq = re.compile('\s([0-9]*[.]?[0-9]+|[0-9]+)([x]?)([* ]?)([+ ]?)')
    rxconn = re.compile(r'\bconnected\b')
    rxdisconn = re.compile(r'\bdisconnected\b')

    sc_name_line = None
    sc_name = None
    width = None
    height = None
    freq = None
    current = False
    preferred = False

    screens = []
    modes = []
    edid_data = []

    parsing_mode = None

    for i in lines:
        #print(i)
        if re.search(rxconn, i) or re.search(rxdisconn, i):
            if sc_name_line:

                newscreen = create_screen(sc_name_line, modes, edid_data)
                screens.append(newscreen)
                modes = []
                edid_data = []

            sc_name_line = i

        else:
            r = re.search(rx, i)
            parts = i.strip().split(" ")
            if r:
                width = int(r.group(1))
                height = int(r.group(2))

                parsing_mode = [width, height, 0.0]

            elif parsing_mode:
                if(parts[0] == "v:"):
                    #print(parts[-1][0:-2])
                    parsing_mode[2] = float(parts[-1][0:-2])
                    newmode = Mode(parsing_mode[0], parsing_mode[1], parsing_mode[2], False, False)
                    modes.append(newmode)
                    parsing_mode = None
            
            elif len(parts) == 1 and len(parts[0]) == 32:
                edid_data.append(parts[0])

    if sc_name_line:
        screens.append(create_screen(sc_name_line, modes, edid_data))

    return screens

def connected_screens():
    """Get connected screens
    """
    #return [s for s in parse_xrandr(exec_cmd('xrandr')) if s.is_connected()]
    return [s for s in parse_xrandr(exec_cmd(['xrandr', '--verbose'])) if s.is_connected()]

def enabled_screens():
    return [s for s in connected_screens() if s.is_enabled()]

if __name__ == "__main__":
    print(parse_xrandr(exec_cmd('xrandr')))
    print("--------------------------------------------------------------------------")
    print(parse_xrandr(exec_cmd(['xrandr', '--verbose'])))