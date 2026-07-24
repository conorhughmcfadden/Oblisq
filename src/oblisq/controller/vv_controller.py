
import ast
import numpy as np
import tifffile
import pathlib
import dask.array as da

from tkinter import colorchooser, filedialog

from tkinterdnd2 import DND_FILES, TkinterDnD

from oblisq.view.viewer import ChannelWidgetBox
from oblisq.model.gl_backend import GLVolumeViewBackend

DEFAULT_COLORS = [
    [  0, 255,  50],
    [255, 255, 255],
    [255,   0,   0],
    [  0,   0, 255],
    [255, 255,   0],
    [255,   0, 255],
    [  0, 255, 255],
]

def rgb_to_hex(color: list):
    r, g, b = color
    return f'#{r:02x}{g:02x}{b:02x}'

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

        self.show = inputs["show"].variable
        self.gamma = inputs["gamma"].variable
        self.min   = inputs["min"].variable
        self.max   = inputs["max"].variable
 
        self.show.trace_add("write",  self.set_show)
        self.gamma.trace_add("write", self.update_gamma)
        self.min.trace_add("write",   self.update_min_max)
        self.max.trace_add("write",   self.update_min_max)

        inputs["color"].widget.configure(
            command=self.choose_color,
            bg=rgb_to_hex(self.color)
        )
        inputs["autoscale"].widget.configure(
            command=self.scale_volume_min_max
        )

    def set_show(self, *args):
        self._gl_set_show()

    def update_min_max(self, *args):
        self._gl_update_min_max()

    def update_gamma(self, *args):
        self._gl_update_gamma()

    def _gl_set_show(self):
        self.parent.backend.set_show(self.show.get(), self.id)

    def _gl_upload_stack_to_backend(self):

        self.parent.backend.set_volume_dimensions(
            self.resolution['dz'],
            self.resolution['px'],
            len(self.stack_data)
            )

        self._gl_update_color()
        self._gl_update_min_max()

        for z, img in enumerate(self.stack_data):
            self.parent.backend.submit_slice(img, z, self.id)

    def _gl_update_color(self):

        self.parent.backend.request_set_channel_color(
            self.id,
            [float(c)/255. for c in self.color] + [0.5] # alpha = 1 for now
            )

    def _gl_update_min_max(self):

        try:
            _min = float(1.5 * self.min.get())
            _max = float(0.5 * self.max.get())
        except Exception:
            return

        self.parent.backend.set_min_max([_min, _max], self.id)

    def _gl_update_gamma(self):
        try:
            _gamma = float(self.gamma.get())
        except Exception:
            return

        self.parent.backend.set_gamma(_gamma, self.id)

    def load_stack(self, stack_path: str) -> np.ndarray:
        # Get the stride value from the parent controller's inputs
        stride = int(self.parent.stride.get())
        self.parent.backend.stride = stride  # Update the backend's stride value
        
        with tifffile.TiffFile(stack_path) as tif:

            # z-spacing
            try:
                image_desc = dict(
                    ast.literal_eval(tif.pages[0].tags['ImageDescription'].value)
                )
                self.resolution['dz'] = image_desc['spacing']
                self.parent.view.inputs['dz'].set(self.resolution['dz'])
            except Exception:
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
            except Exception:
                self.resolution['px'] = float(self.parent.view.inputs['px'].get())

            # load the data
            use_cpp_tiff = True
            try:
                import cpptiff
            except ModuleNotFoundError:
                use_cpp_tiff = False
            
            if use_cpp_tiff and stride == 1:
                self.stack_data = cpptiff.read_tiff(stack_path)
            else:
                self.stack_data = self._lazy_load_downsampled_tif(stack_path, stride=stride)

    @staticmethod
    def _lazy_load_downsampled_tif(stack_path: str, stride: int=1) -> np.ndarray:
        """
        Lazily load a downsampled version of the TIFF stack using dask.

        Parameters:
        - stack_path: The path to the TIFF file.
        - stride: The downsampling factor. A stride of 1 means no downsampling.

        Returns:
        - A numpy array containing the downsampled stack.
        """
        dask_arr = da.from_zarr(tifffile.imread(stack_path, aszarr=True))  # Load the TIFF as a dask array
        downsampled = dask_arr[::stride, ::stride, ::stride]  # Downsample by a factor of stride in all dimensions
        
        return downsampled.compute()

    def choose_color(self):

        rgb, hex = colorchooser.askcolor(title=f"Select {self.channel_name} color...")

        self.color = list(rgb)
        self.view.inputs["color"].widget.configure(bg=hex)

        # Update on GL side
        self._gl_update_color()

    def scale_volume_min_max(self):

        self.min.set(int(1.5 * self.stack_data.min()))
        self.max.set(int(0.7 * self.stack_data.max()))

        self._gl_update_min_max()

class VVStandaloneController:
    def __init__(self, view: TkinterDnD.Tk, backend: GLVolumeViewBackend):
        self.view = view
        self.backend = backend

        self.view.main_frame.drop_target_register(DND_FILES)
        self.view.main_frame.dnd_bind('<<Drop>>', self.on_drop)

        self.working_directory = None

        # trace adds for inputs
        # Trace adds for volume display widgets
        def volume_setting_callback(field):
            return lambda *args: self._gl_on_volume_settings_changed(field, *args)

        self.inputs = self.view.inputs
        
        self.stride = self.inputs["downsample"].get_variable()

        for key, widget in self.inputs.items():
            widget.get_variable().trace_add("write", volume_setting_callback(key))

        buttons = self.view.buttons
        # Button commands for camera orientation
        buttons["x"].configure(command=lambda: self.backend.camera.set_angular_position(0, 0))
        buttons["y"].configure(command=lambda: self.backend.camera.set_angular_position(0, 90))
        buttons["z"].configure(command=lambda: self.backend.camera.set_angular_position(90, 0))
        buttons["reset"].configure(command=lambda: self.backend.camera.set_angular_position(45, 45))

        # save screen button
        buttons["save"].configure(command=self._gl_save_viewport_screenshot)

        # dict: holds Channels objects
        self.channels = {}

    def _gl_save_viewport_screenshot(self):
        # Get the current viewport image from the backend
        viewport_image = self.backend.get_viewport_as_npimage()

        save_path = filedialog.asksaveasfilename(
            initialdir=self.working_directory,
            defaultextension=".tif",
            filetypes=[("TIFF files", "*.tif*")],
        )

        # Save the image using tifffile
        tifffile.imwrite(save_path, viewport_image)

        print(f"Viewport screenshot saved to {save_path}")

    def _gl_on_volume_settings_changed(self, field, *args):
        """Hook for OpenGL-based views to trigger a re-render when display settings are changed."""

        variable = self.inputs[field].get_variable()

        try:
            value = float(variable.get())
        except Exception:
            # Handle "" and other such invalid inputs
            return

        try:
            exec(f"self.backend.set_{field}({value})")
        except AttributeError:
            pass

    def on_drop(self, event):
        dropped_files = list(self.view.tk.splitlist(event.data))
        dropped_files.sort()

        # Destroy existing channel widgets before building new ones
        for cc in self.channels.values():
            cc.view.destroy()
        self.channels.clear()

        # Reset if running
        # if self.backend.thread_is_running():
        #     self.backend.stop()

        # Start GL backend
        if not self.backend.thread_is_running():
            self.backend.start()

        for i, file_path in enumerate(dropped_files):
            path = pathlib.Path(file_path)

            working_dir = path.parent
            if working_dir != self.working_directory:
                self.working_directory = working_dir

            if path.suffix.lower() in ['.tif', '.tiff']:
                channel_name = path.name.split('.')[0]

                # Create a channel for this stack
                self.channels[channel_name] = ChannelController(self, channel_name, i)

                # Load the stack data/metadata into memory
                self.channels[channel_name].load_stack(file_path)

                # Queue a stack upload for this channel
                self.view.after(100, self.channels[channel_name]._gl_upload_stack_to_backend)

                # Autoscale the min/max values for this channel
                self.view.after(150, self.channels[channel_name].scale_volume_min_max)

                # Initial update gamma
                self.view.after(200, self.channels[channel_name].update_gamma)

                # Set view to z using invoked button press
                self.view.after(500, lambda: self.view.buttons["z"].invoke())

        # Reinitialize shader uniforms on-load
        for key in self.view.inputs:
            self._gl_on_volume_settings_changed(key)
