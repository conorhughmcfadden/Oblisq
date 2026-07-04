import tkinter as tk
from tkinter import ttk

from decimal import Decimal, InvalidOperation

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
