import time
import tkinter as tk

# Local imports
from model.gl_backend import GLVolumeViewBackend
from view.viewer import VolumeViewerStandalone
from controller.vv_controller import VVStandaloneController

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

if __name__ == "__main__":
    volume_viewer = VolumeViewer()
    volume_viewer.mainloop()