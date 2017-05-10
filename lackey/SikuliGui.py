""" Gui helper classes for Lackey

"""

try:
    import Tkinter as tk
    import ttk
except ImportError:
    import tkinter as tk
    from tkinter import ttk

from .SettingsDebug import Settings

class PopupInput(tk.Frame):
    """ A basic popup dialog with a text input """
    def __init__(self, parent, msg, title, hidden, text_variable):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.parent.protocol("WM_DELETE_WINDOW", self.cancel_function)
        self.parent.bind('<Return>', self.ok_function)
        self.parent.title(title)
        self.input_text = text_variable
        if Settings.PopupLocation:
            self.parent.geometry("+{}+{}".format(
                Settings.PopupLocation.x,
                Settings.PopupLocation.y))
        self.msg = tk.Message(self.parent, text=msg)
        self.msg.grid(row=0, sticky="NSEW", padx=10, pady=10)
        self.input_entry = tk.Entry(self.parent, width=50, textvariable=self.input_text)
        if hidden:
            self.input_entry.config(show="*")
        self.input_entry.grid(row=1, sticky="EW", padx=10)
        self.button_frame = tk.Frame(self.parent)
        self.button_frame.grid(row=2, sticky="E")
        self.cancel = tk.Button(
            self.button_frame,
            text="Cancel",
            command=self.cancel_function,
            width=10)
        self.cancel.grid(row=0, column=0, padx=10, pady=10)
        self.ok_button = tk.Button(
            self.button_frame,
            text="Ok",
            command=self.ok_function,
            width=10)
        self.ok_button.grid(row=0, column=1, padx=10, pady=10)
        self.input_entry.focus_set()

    def cancel_function(self):
        """ Handler for cancel button """
        self.input_text.set("")
        self.parent.destroy()
    def ok_function(self, event=None):
        """ Handler for ok button """
        #pylint: disable=unused-argument
        self.parent.destroy()

class PopupList(tk.Frame):
    """ A basic popup dialog with a list dropdown """
    def __init__(self, parent, msg, title, options, default, text_variable):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.parent.protocol("WM_DELETE_WINDOW", self.cancel_function)
        self.parent.bind('<Return>', self.ok_function)
        self.parent.title(title)
        self.input_text = text_variable
        self.input_text.set(default)
        if Settings.PopupLocation:
            self.parent.geometry("+{}+{}".format(
                Settings.PopupLocation.x,
                Settings.PopupLocation.y))
        self.msg = tk.Message(self.parent, text=msg)
        self.msg.grid(row=0, sticky="NSEW", padx=10, pady=10)
        self.input_list = ttk.Combobox(
            self.parent,
            textvariable=self.input_text,
            state="readonly",
            values=options)
        #self.input_list.activate(options.index(default))
        self.input_list.grid(row=1, sticky="EW", padx=10)
        self.button_frame = tk.Frame(self.parent)
        self.button_frame.grid(row=2, sticky="E")
        self.cancel = tk.Button(
            self.button_frame,
            text="Cancel",
            command=self.cancel_function,
            width=10)
        self.cancel.grid(row=0, column=0, padx=10, pady=10)
        self.ok_button = tk.Button(
            self.button_frame,
            text="Ok",
            command=self.ok_function,
            width=10)
        self.ok_button.grid(row=0, column=1, padx=10, pady=10)
        self.input_list.focus_set()

    def cancel_function(self):
        """ Handler for cancel button """
        self.input_text.set("")
        self.parent.destroy()
    def ok_function(self, event=None):
        """ Handler for ok button """
        #pylint: disable=unused-argument
        #self.input_text.set(self.input_list.get(self.input_list.cur_selection()[0]))
        self.parent.destroy()

class PopupTextarea(tk.Frame):
    """ A basic popup dialog with a textarea input """
    def __init__(self, parent, message, title, lines, width, input_text):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.parent.protocol("WM_DELETE_WINDOW", self.cancel_function)
        #self.parent.bind('<Return>', self.ok_function)
        self.parent.title(title)
        self.input_text = input_text
        if Settings.PopupLocation:
            self.parent.geometry("+{}+{}".format(
                Settings.PopupLocation.x,
                Settings.PopupLocation.y))

        self.input_entry = TextExtension(
            self.parent,
            textvariable=self.input_text,
            width=width,
            height=lines)
        self.input_entry.grid(row=1, sticky="EW", padx=10, pady=10)

        self.msg = tk.Message(self.parent, text=message)
        self.msg.grid(row=0, sticky="NSEW", padx=10)

        self.button_frame = tk.Frame(self.parent)
        self.button_frame.grid(row=2, sticky="E")
        self.cancel = tk.Button(
            self.button_frame,
            text="Cancel",
            command=self.cancel_function,
            width=10)
        self.cancel.grid(row=0, column=0, padx=10, pady=10)
        self.ok_button = tk.Button(
            self.button_frame,
            text="Ok",
            command=self.ok_function,
            width=10)
        self.ok_button.grid(row=0, column=1, padx=10, pady=10)
        self.input_entry.focus()
    def cancel_function(self):
        """ Handler for cancel button """
        self.input_text.set("")
        self.parent.destroy()
    def ok_function(self, event=None):
        """ Handler for ok button """
        #pylint: disable=unused-argument
        self.parent.destroy()

class TextExtension(tk.Frame):
    """Extends Frame.  Intended as a container for a Text field.  Better related data handling
    and has Y scrollbar."""

    def __init__(self, master, textvariable=None, *args, **kwargs):

        tk.Frame.__init__(self, master)
        # Init GUI

        self._y_scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)

        self._text_widget = tk.Text(self, yscrollcommand=self._y_scrollbar.set, *args, **kwargs)
        self._text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        self._y_scrollbar.config(command=self._text_widget.yview)
        self._y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        if textvariable is not None:
            if not isinstance(textvariable, tk.Variable):
                raise TypeError("tkinter.Variable type expected, {} given.".format(
                    type(textvariable)))
            self._text_variable = textvariable
            self.var_modified()
            self._text_trace = self._text_widget.bind('<<Modified>>', self.text_modified)
            self._var_trace = textvariable.trace("w", self.var_modified)

    def text_modified(self):
        #pylint: disable=unused-argument
        if self._text_variable is not None:
            self._text_variable.trace_vdelete("w", self._var_trace)
            self._text_variable.set(self._text_widget.get(1.0, tk.END))
            self._var_trace = self._text_variable.trace("w", self.var_modified)
            self._text_widget.edit_modified(False)

    def var_modified(self):
        #pylint: disable=unused-argument
        self.set_text(self._text_variable.get())
        self._text_widget.edit_modified(False)

    def unhook(self):
        if self._text_variable is not None:
            self._text_variable.trace_vdelete("w", self._var_trace)


    def clear(self):
        self._text_widget.delete(1.0, tk.END)

    def set_text(self, _value):
        self.clear()
        if _value is not None:
            self._text_widget.insert(tk.END, _value)

    def focus(self):
        self._text_widget.focus_set()
