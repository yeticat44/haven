from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Union, Mapping

from qtpy.QtCore import Slot
from pydm.application import PyDMApplication
from pydm.display import load_file
from pydm.utilities.stylesheet import apply_stylesheet

from .main_window import FireflyMainWindow


__all__ = ["ui_dir", "FireflyApplication"]


ui_dir = Path(__file__).parent


# @dataclass
# class WindowShower():
#     __name__ = ""
#     WindowClass: type
#     ui_file: Union[Path, str]
#     name: Optional[str] = None
#     macros: Mapping = field(default_factory=dict)

#     def __set_name__(self, obj, name):
#         self.__name__ = name
    
#     def __get__(self, obj, *args, **kwargs):
#         print(self.__call__)
#         return self.__call__
    
#     @Slot(bool)
#     def __call__(self, val, *args, **kwargs):
#         print(self.__name__, self.obj)
#         self.obj.show_window(WindowClass=self.WindowClass,
#                              ui_file=self.ui_file, name=self.name,
#                              macros=self.macros)



class FireflyApplication(PyDMApplication):
    xafs_scan_window = None

    def __init__(self, ui_file=None, use_main_window=False, *args, **kwargs):
        # Instantiate the the parent class
        # (*ui_file* and *use_main_window* let us render the window here instead)
        super().__init__(ui_file = None, use_main_window=use_main_window, *args, **kwargs)
        self.windows = {}
        self.show_status_window()
        # self.connect_menu_signals(window=self.windows['beamline_status'])        
        # self.windows['beamline_status'].actionShow_Xafs_Scan.triggered.emit()        

    def connect_menu_signals(self, window):
        """Connects application-level signals to the associated slots.

        These signals should generally be applicable to multiple
        windows. If the signal and/or slot is specific to a given
        window, then it should be in that widnow's class definition
        and setup code.

        """
        window.actionShow_Log_Viewer.triggered.connect(self.show_log_viewer_window)
        window.actionShow_Xafs_Scan.triggered.connect(self.show_xafs_scan_window)
        window.actionShow_Voltmeters.triggered.connect(self.show_voltmeters_window)
        window.actionShow_Sample_Viewer.triggered.connect(self.show_sample_viewer_window)

    def show_window(self, WindowClass, ui_file, name=None, macros={}):
        # Come up with the default key for saving in the windows dictionary
        if name is None:
            name = f"{WindowClass.__name__}_{ui_file.name}"
        # Check if the window has already been created
        if (w := self.windows.get(name)) is None:
            # Window is not yet created, so create one
            w = self.create_window(WindowClass, ui_dir / ui_file, macros=macros)
            self.windows[name] = w
        else:
            # Window already exists so just bring it to the front
            w.show()
            w.activateWindow()
        return w

    def create_window(self, WindowClass, ui_file, macros={}):
        # Create and save this window
        main_window = WindowClass(hide_nav_bar=self.hide_nav_bar,
                                  hide_menu_bar=self.hide_menu_bar,
                                  hide_status_bar=self.hide_status_bar)
        # Make it look pretty
        apply_stylesheet(self.stylesheet_path, widget=main_window)
        main_window.update_tools_menu()
        # Load the UI file for this window
        display = main_window.open(str(ui_file.resolve()), macros=macros)
        self.connect_menu_signals(window=main_window)
        # Show the display
        if self.fullscreen:
            main_window.enter_fullscreen()
        else:
            main_window.show()
        return main_window

    def show_status_window(self, stylesheet_path=None):
        """Instantiate a new main window for this application."""
        self.show_window(FireflyMainWindow, ui_dir / "status.ui", name="beamline_status")

    make_main_window = show_status_window

    @Slot()
    def show_log_viewer_window(self):
        self.show_window(FireflyMainWindow, ui_dir / "log_viewer.ui", name="log_viewer")

    @Slot()
    def show_xafs_scan_window(self):
        self.show_window(FireflyMainWindow, ui_dir / "xafs_scan.ui", name="xafs_scan")

    @Slot()
    def show_voltmeters_window(self):
        self.show_window(FireflyMainWindow, ui_dir / "voltmeters.py", name="voltmeters")

    @Slot()
    def show_sample_viewer_window(self):
        self.show_window(FireflyMainWindow, ui_dir / "sample_viewer.ui", name="sample_viewer")
