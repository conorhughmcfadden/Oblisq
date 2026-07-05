import numpy as np
import tkinter as tk

from tkinterdnd2 import TkinterDnD

from volumeviewer.view.widgets import LabelInput, ValidatedSpinbox

WINDOW_DIMENSIONS = (400, 600)

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
            "gamma": LabelInput(
                parent=self,
                label="Gamma:",
                input_class=ValidatedSpinbox,
                input_var=tk.DoubleVar(value=0.7),
                input_args={"from_": 0.1, "to": 5.0, "increment": 0.05, "width": 8},
                label_pos="top",
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
        camera_settings_frame = tk.Frame(self.main_frame, borderwidth=2, relief="sunken")

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
                input_args={"from_": 0.01, "to": np.inf, "increment": 0.01, "width": 8},
                label_pos="top",
            ),
            "px": LabelInput(
                parent=volume_settings_frame,
                label="Pixel Size",
                input_class=ValidatedSpinbox,
                input_var=tk.DoubleVar(value=0.1478),
                input_args={"from_": 0.0001, "to": np.inf, "increment": 0.0001, "width": 8},
                label_pos="top",
            ),
            "opacity": LabelInput(
                parent=render_settings_frame,
                label="Opacity",
                input_class=ValidatedSpinbox,
                input_var=tk.DoubleVar(value=0.25),
                input_args={"from_": 0.01, "to": 1.0, "increment": 0.01, "width": 8},
                label_pos="top",
            ),
            "world_step": LabelInput(
                parent=render_settings_frame,
                label="World Step",
                input_class=ValidatedSpinbox,
                input_var=tk.DoubleVar(value=0.5),
                input_args={"from_": 0.05, "to": 10.0, "increment": 0.05, "width": 8},
                label_pos="top",
            ),
            "downsample": LabelInput(
                parent=render_settings_frame,
                label="Downsample",
                input_class=ValidatedSpinbox,
                input_var=tk.IntVar(value=1),
                input_args={"from_": 1, "to": 16, "increment": 1, "width": 8},
                label_pos="top",
            )
        }

        self.buttons = {
            "x": tk.Button(camera_settings_frame, text="X", width=5),
            "y": tk.Button(camera_settings_frame, text="Y", width=5),
            "z": tk.Button(camera_settings_frame, text="Z", width=5),
            "reset": tk.Button(camera_settings_frame, text="Reset", width=5),
            "save": tk.Button(camera_settings_frame, text="SAVE", width=5),
        }

        for input_widget in self.inputs.values():
            input_widget.pack(side=tk.LEFT, expand=True)

        for button in self.buttons.values():
            button.pack(side=tk.LEFT, expand=True)

        volume_settings_frame.pack(fill=tk.X)
        render_settings_frame.pack(fill=tk.X)
        camera_settings_frame.pack(fill=tk.X)        

        self.channels_frame = tk.Frame(self.main_frame, borderwidth=2, relief="sunken")
        self.channels_frame.pack(fill=tk.BOTH)

