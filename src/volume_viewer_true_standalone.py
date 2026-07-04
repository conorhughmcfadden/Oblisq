import time
import pathlib
import tifffile
import numpy as np
from decimal import Decimal, InvalidOperation

import tkinter as tk
from tkinter import ttk
from tkinter import colorchooser

from tkinterdnd2 import DND_FILES, TkinterDnD

from gl_backend import GLVolumeViewBackend

WINDOW_DIMENSIONS = (400, 600)

DEFAULT_COLORS = [
    [255, 255, 255],
    [255,   0,   0],
    [  0, 255,   0],
    [  0,   0, 255],
    [255, 255,   0],
    [255,   0, 255],
    [  0, 255, 255],
]

def rgb_to_hex(color: list):
    r, g, b = color
    return f'#{r:02x}{g:02x}{b:02x}'


class ValidatedSpinbox(ttk.Spinbox):
    """A lightweight, dependency-free numeric Spinbox with keystroke/focusout validation.

    Restricts input to numbers within [from_, to] and no finer than the given
    increment's decimal precision, so the widget always holds a value tkinter's
    float()/int() can parse.
    """

    def __init__(self, master=None, from_=0, to=100, increment=1, textvariable=None, **kwargs):
        self.variable = textvariable if textvariable is not None else tk.DoubleVar()

        super().__init__(
            master,
            from_=from_,
            to=to,
            increment=increment,
            textvariable=self.variable,
            **kwargs,
        )

        resolution = str(increment)
        dot = resolution.find(".")
        self.precision = (-1) * len(resolution[dot + 1:]) if dot >= 0 else 0

        validate_cmd = self.register(self._validate_key)
        self.config(validate="key", validatecommand=(validate_cmd, "%P"))
        self.bind("<FocusOut>", self._validate_focusout)

    def _validate_key(self, proposed):
        if proposed in ("", "-"):
            return float(self.cget("from")) < 0
        if proposed == ".":
            return True

        try:
            value = Decimal(proposed)
        except InvalidOperation:
            return False

        value_precision = value.as_tuple().exponent
        if value_precision < self.precision:
            return False
        if value > Decimal(str(self.cget("to"))):
            return False

        return True

    def _validate_focusout(self, *args):
        try:
            value = Decimal(str(self.get()))
        except InvalidOperation:
            self.variable.set(self.cget("from"))
            return

        min_val = Decimal(str(self.cget("from")))
        max_val = Decimal(str(self.cget("to")))

        if value < min_val:
            self.variable.set(float(min_val))
        elif value > max_val:
            self.variable.set(float(max_val))


class LabelInput(tk.Frame):
    """A lightweight, dependency-free widget pairing a label with an input widget.

    Mirrors just enough of navigate's LabelInput/LabelInputWidgetFactory
    behaviour to support this standalone viewer: label placement above or
    beside the input, plain buttons (color swatch/autoscale), and
    ValidatedSpinbox numeric entries.
    """

    _BUTTON_CLASSES = (tk.Button, ttk.Button)

    def __init__(
        self,
        parent,
        label_pos="left",
        label="",
        input_class=ttk.Entry,
        input_var=None,
        input_args=None,
        label_args=None,
        **kwargs,
    ):
        super().__init__(parent, **kwargs)

        input_args = dict(input_args or {})
        label_args = label_args or {}

        self.variable = input_var
        self.input_class = input_class
        self.label = tk.Label(self, text=label, **label_args)

        if input_class not in self._BUTTON_CLASSES:
            input_args["textvariable"] = input_var

        self.widget = input_class(self, **input_args)

        if label_pos == "top":
            self.label.pack(side=tk.TOP, fill=tk.X)
            self.widget.pack(side=tk.TOP, fill=tk.X)
        else:
            self.label.pack(side=tk.LEFT)
            self.widget.pack(side=tk.LEFT)

    def get(self, default=None):
        try:
            if self.variable is not None:
                return self.variable.get()
            return self.widget.get()
        except (TypeError, tk.TclError):
            if default is not None:
                return default
            return ""

    def get_variable(self):
        return self.variable

    def set(self, value, *args, **kwargs):
        if self.variable is not None:
            self.variable.set(value, *args, **kwargs)
        else:
            self.widget.delete(0, tk.END)
            self.widget.insert(0, value)


class VolumeViewer:
    def __init__(self, root: tk.Tk=None, splash_screen: tk.Toplevel=None):
        """
        VolumeViewer wrapper class to be called from main.py. This class initializes
        the VolumeViewerStandalone view and the VVStandaloneController, which handles
        the OpenGL backend and the GUI interactions.

        Parameters:
            root (tk.Tk): Main root to be destroyed and replaced with VolumeViewerStandalone.
            splash_screen (tk.Toplevel, optional): The splash screen to be destroyed after initialization.
        """
        if root is not None and splash_screen is not None:
            time.sleep(1)  # Briefly let the splash screen show
            splash_screen.destroy()
            root.destroy()

        self.root = VolumeViewerStandalone()  # Creates a new TkinterDnD.Tk root for the volume viewer
        self.backend = GLVolumeViewBackend()  # Initializes the OpenGL backend for volume rendering
        self.controller = VVStandaloneController(self.root, self.backend)

    def mainloop(self):
        """
        Starts the main loop of the VolumeViewerStandalone application.
        """
        self.root.mainloop()

        # Close behaviour
        if self.backend.thread_is_running():
            self.backend.stop()

class ChannelWidgetBox(tk.Frame):
    def __init__(self, master, channel_name):
        super().__init__(master)

        self.channel_name = channel_name
        self.label = tk.Label(self, text=channel_name, wraplength=WINDOW_DIMENSIONS[0]-20, justify=tk.LEFT)
        self.label.pack()

        widget_frame = tk.Frame(self)

        self.inputs = {
            "color": LabelInput(
                widget_frame,
                label_pos="top",
                label="Color:",
                input_class=tk.Button
                ),
            "min": LabelInput(
                parent=self,
                label="Min:",
                input_class=ValidatedSpinbox,
                input_var=tk.IntVar(value=0),
                input_args={"from_": 0, "to": 65535, "increment": 255, "width": 8},
                label_pos="top",
            ),
            "max": LabelInput(
                parent=self,
                label="Max:",
                input_class=ValidatedSpinbox,
                input_var=tk.IntVar(value=500),
                input_args={"from_": 0, "to": 65535, "increment": 255, "width": 8},
                label_pos="top",
            ),
            "autoscale": LabelInput(
                parent=self,
                label="AUTO",
                label_pos="top",
                input_class=tk.Button,
            ),
        }

        for input_widget in self.inputs.values():
            input_widget.pack(padx=5, side=tk.LEFT)

        widget_frame.pack()

class VolumeViewerStandalone(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()

        self.title("Volume Viewer Standalone")
        self.geometry(f"{WINDOW_DIMENSIONS[0]}x{WINDOW_DIMENSIONS[1]}")

        self.main_frame = tk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        volume_settings_frame = tk.Frame(self.main_frame, borderwidth=2, relief="sunken")
        render_settings_frame = tk.Frame(self.main_frame, borderwidth=2, relief="sunken")

        self.inputs = {
            "shear_angle": LabelInput(
                parent=volume_settings_frame,
                label="Shear Angle",
                input_class=ValidatedSpinbox,
                input_var=tk.DoubleVar(value=45.0),
                input_args={"from_": -90.0, "to": 90.0, "increment": 0.5, "width": 8},
                label_pos="top",
            ),
            "dz": LabelInput(
                parent=volume_settings_frame,
                label="Z-Step Size",
                input_class=ValidatedSpinbox,
                input_var=tk.DoubleVar(value=0.4),
                input_args={"from_": 0.01, "to": np.Inf, "increment": 0.01, "width": 8},
                label_pos="top",
            ),
            "px": LabelInput(
                parent=volume_settings_frame,
                label="Pixel Size",
                input_class=ValidatedSpinbox,
                input_var=tk.DoubleVar(value=0.1478),
                input_args={"from_": 0.0001, "to": np.Inf, "increment": 0.0001, "width": 8},
                label_pos="top",
            ),
            "opacity": LabelInput(
                parent=render_settings_frame,
                label="Opacity",
                input_class=ValidatedSpinbox,
                input_var=tk.DoubleVar(value=0.15),
                input_args={"from_": 0.01, "to": 1.0, "increment": 0.01, "width": 8},
                label_pos="top",
            ),
            "world_step": LabelInput(
                parent=render_settings_frame,
                label="World Step",
                input_class=ValidatedSpinbox,
                input_var=tk.DoubleVar(value=1.0),
                input_args={"from_": 0.05, "to": 10.0, "increment": 0.05, "width": 8},
                label_pos="top",
            )
        }

        for input_widget in self.inputs.values():
            input_widget.pack(side=tk.LEFT, expand=True)

        volume_settings_frame.pack(fill=tk.X)
        render_settings_frame.pack(fill=tk.X)

        self.channels_frame = tk.Frame(self.main_frame, borderwidth=2, relief="sunken")
        self.channels_frame.pack(fill=tk.BOTH)

class ChannelController:

    def __init__(self, parent, channel_name: str, id: int=0):

        self.parent = parent

        self.id = id
        self.channel_name = channel_name

        self.view = ChannelWidgetBox(parent.view.channels_frame, channel_name)
        self.view.pack(pady=5)

        # Variables
        self.color = DEFAULT_COLORS[id]
        self.stack_data: np.ndarray = None
        self.resolution = {'dz': 1, 'px': 1}
        self.min = 0
        self.max = 3000

        # Widget command binds
        inputs = self.view.inputs

        self.min = inputs["min"].variable
        self.max = inputs["max"].variable

        self.min.trace_add("write", self.update_min_max)
        self.max.trace_add("write", self.update_min_max)

        inputs["color"].widget.configure(
            command=self.choose_color,
            bg=rgb_to_hex(self.color)
        )
        inputs["autoscale"].widget.configure(
            command=self.scale_volume_min_max
        )

    def update_min_max(self, *args):
        self._gl_update_min_max()

    def _gl_upload_stack_to_backend(self):

        self.parent.backend.set_volume_dimensions(
            self.resolution['dz'],
            self.resolution['px'],
            len(self.stack_data)
            )

        self._gl_update_color()
        self._gl_update_min_max()

        for z, img in enumerate(self.stack_data):
            self.parent.backend.data_q.put_nowait((img, z, self.id))

    def _gl_update_color(self):

        self.parent.backend.request_set_channel_color(
            self.id,
            [float(c)/255. for c in self.color] + [0.5] # alpha = 1 for now
            )

    def _gl_update_min_max(self):

        try:
            _min = float(self.min.get())
            _max = float(self.max.get())
        except:
            return

        self.parent.backend.set_min_max([_min, _max], self.id)

    def load_stack(self, stack_path: str) -> np.ndarray:
        with tifffile.TiffFile(stack_path) as tif:

            # z-spacing
            try:
                image_desc = dict(eval(tif.pages[0].tags['ImageDescription'].value))
                self.resolution['dz'] = image_desc['spacing']
                self.parent.view.inputs['dz'].set(self.resolution['dz'])
            except:
                self.resolution['dz'] = float(self.parent.view.inputs['dz'].get())

            # xy-resolution
            try:
                pixels, microns = tif.pages[0].tags.get('XResolution').value
                resolution_unit = tif.pages[0].tags.get('ResolutionUnit').value

                if resolution_unit == 3:  # 3 corresponds to centimeters
                    microns *= 10000  # Convert cm to microns
                elif resolution_unit == 2:  # 2 corresponds to inches
                    microns *= 25400  # Convert inches to microns

                self.resolution['px'] = microns / pixels
                self.parent.view.inputs['px'].set(self.resolution['px'])
            except:
                self.resolution['px'] = float(self.parent.view.inputs['px'].get())

            # load the data
            self.stack_data = tif.asarray()

    def choose_color(self):

        rgb, hex = colorchooser.askcolor(title=f"Select {self.channel_name} color...")

        self.color = list(rgb)
        self.view.inputs["color"].widget.configure(bg=hex)

        # Update on GL side
        self._gl_update_color()

    def scale_volume_min_max(self):

        self.min.set(int(self.stack_data.min()))
        self.max.set(int(self.stack_data.max()))

        self._gl_update_min_max()

class VVStandaloneController:
    def __init__(self, view: TkinterDnD.Tk, backend: GLVolumeViewBackend):
        self.view = view
        self.backend = backend

        self.view.main_frame.drop_target_register(DND_FILES)
        self.view.main_frame.dnd_bind('<<Drop>>', self.on_drop)

        # trace adds for inputs
        # Trace adds for volume display widgets
        def volume_setting_callback(field):
            return lambda *args: self._gl_on_volume_settings_changed(field, *args)

        for key, widget in self.view.inputs.items():
            widget.get_variable().trace_add("write", volume_setting_callback(key))

        # dict: holds Channels objects
        self.channels = {}

    def _gl_on_volume_settings_changed(self, field, *args):
        """Hook for OpenGL-based views to trigger a re-render when display settings are changed."""

        variable = self.view.inputs[field].get_variable()

        try:
            value = float(variable.get())
        except:
            # Handle "" and other such invalid inputs
            return

        exec(f"self.backend.set_{field}({value})")

    def on_drop(self, event):
        dropped_files = event.data.split()
        dropped_files.sort()

        # Destroy existing channel widgets before building new ones
        for cc in self.channels.values():
            cc.view.destroy()
        self.channels.clear()

        # Reset if running
        if self.backend.thread_is_running():
            self.backend.stop()

        # Start GL backend
        self.backend.start()

        for i, file_path in enumerate(dropped_files):
            path = pathlib.Path(file_path)

            if path.suffix.lower() in ['.tif', '.tiff']:
                channel_name = path.name.split('.')[0]

                # Create a channel for this stack
                self.channels[channel_name] = ChannelController(self, channel_name, i)

                # Load the stack data/metadata into memory
                self.channels[channel_name].load_stack(file_path)

                # Queue a stack upload for this channel
                self.view.after(100, self.channels[channel_name]._gl_upload_stack_to_backend)

                # Autoscale the min/max values for this channel
                self.view.after(200, self.channels[channel_name].scale_volume_min_max)

        # Reinitialize shader uniforms on-load
        for key in self.view.inputs:
            self._gl_on_volume_settings_changed(key)

if __name__ == "__main__":
    volume_viewer = VolumeViewer()
    volume_viewer.mainloop()
