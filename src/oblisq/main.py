import sys
import time
import tkinter as tk

# Local imports
from oblisq.model.gl_backend import GLVolumeViewBackend

# The standalone viewer's view/controller layers require the [app] extra
# (tkinterdnd2, tifffile, dask, etc.) -- oblisq's console script is registered
# unconditionally by pip/setuptools regardless of which extras were installed
# (pyproject.toml has no way to make an entry point conditional on an extra),
# so a bare `pip install oblisq` still gets the `oblisq` command on PATH. Guard
# the import here so running it without [app] gives an actionable message
# instead of a raw traceback.
try:
    from oblisq.view.viewer import VolumeViewerStandalone
    from oblisq.controller.vv_controller import VVStandaloneController
    _APP_IMPORT_ERROR = None
except ModuleNotFoundError as _import_error:
    VolumeViewerStandalone = None
    VVStandaloneController = None
    _APP_IMPORT_ERROR = _import_error

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

def main():
    if _APP_IMPORT_ERROR is not None:
        missing = getattr(_APP_IMPORT_ERROR, "name", None) or str(_APP_IMPORT_ERROR)
        print(
            "\n".join(
                [
                    "Unable to start the Oblisq standalone viewer.",
                    f"Missing dependency: {missing}",
                    "",
                    "The standalone viewer requires the [app] extra. Install it with:",
                    '  pip install "oblisq[app]"'
                ]
            ),
            file=sys.stderr,
        )
        sys.exit(1)

    volume_viewer = VolumeViewer()
    volume_viewer.mainloop()

if __name__ == "__main__":
    main()