"""
[vt102](http://github.com/samfoo/vt102) is an in memory vt1xx terminal
emulator. It supports all the most common terminal escape sequences, including
text attributes and color. 

It's an in memory vt1XX-compatible terminal emulator. The *XX* stands for a
series video terminals, developed by
[DEC](http://en.wikipedia.org/wiki/Digital_Equipment_Corporation) between 1970
and 1995. The first, and most famous one, was VT100 terminal, which is now a
de-facto standard for all virtual terminal emulators.
[vt102](http://github.com/samfoo/vt102) is one such emulator.

Why would you want to use a terminal emulator?

* Screen scraping some terminal or curses app.
* Writing your own graphical terminal emulator.
* ... seriously, that's about it.

Here's a quick example:

    >>> from vt102 import screen, stream
    >>> st = stream()
    >>> sc = screen((10, 10))
    >>> print(sc)
    ["          ",
     "          ",
     "          ",
     "          ",
     "          ",
     "          ",
     "          ",
     "          ",
     "          ",
     "          "]
    >>> sc.attach(st)
    >>> st.process("Text goes here")
    >>> print(sc)
    ["Text goes ",
     "here      ",
     "          ",
     "          ",
     "          ",
     "          ",
     "          ",
     "          ",
     "          ",
     "          "]
    >>> st.process("\\x1b[H\\x1b[K")
    >>> print(sc)
    ["          ",
     "here      ",
     "          ",
     "          ",
     "          ",
     "          ",
     "          ",
     "          ",
     "          ",
     "          "]
"""

import string
import codecs

from copy import copy

from .graphics import text, colors

from . import control as ctrl, escape as esc
# from .control import *
# from .escape import *

class StreamProcessError(Exception):
    pass

class stream:
    """
    A stream is the state machine that parses a stream of terminal characters
    and dispatches events based on what it sees. This can be attached to a 
    screen object and it's events, or can be used some other way.

    `stream.basic`, `stream.escape`, and `stream.sequence` are the relevant 
    events that get thrown with one addition: `print`. For details on the
    event parameters, see the [vt102 user's
    guide](http://vt100.net/docs/vt102-ug/)

    Quick example:

        >>> s = stream()
        >>> class Cursor:
        ...     def __init__(self):
        ...         self.x = 10; self.y = 10
        ...     def up(self, count):
        ...         self.y -= count
        ...
        >>> c = Cursor()
        >>> s.add_event_listener("cursor-up", c.up)
        >>> s.process(u"\\x00\\x1b[5A") # Move the cursor up 5 rows.
        >>> print(c.y)
        5
    """

    basic = {
        ctrl.BS: "backspace",
        ctrl.HT: "tab",
        ctrl.LF: "linefeed",
        ctrl.VT: "linefeed",
        ctrl.FF: "linefeed",
        ctrl.CR: "carriage-return",
        ctrl.SI: "shift-in",
        ctrl.SO: "shift-out",
        ctrl.BEL: "bell"
    }

    escape = {
        esc.IND: "index",
        esc.RI: "reverse-index",
        esc.NEL: "linefeed",
        esc.DECSC: "store-cursor",
        esc.DECRC: "restore-cursor",
        esc.RLF: "reverse-linefeed",
    }

    sequence = {
        esc.CUU: "cursor-up",
        esc.CUD: "cursor-down",
        esc.CUF: "cursor-right",
        esc.CUB: "cursor-left",
        esc.CUP: "cursor-move",
        esc.HVP: "cursor-move",
        esc.EL: "erase-in-line",
        esc.ED: "erase-in-display",
        esc.DCH: "delete-characters",
        esc.IL: "insert-lines",
        esc.DL: "delete-lines",
        esc.SGR: "select-graphic-rendition",
        esc.DECSTBM: "set-margins",
        esc.IRMI: "set-insert",
        esc.IRMR: "set-replace",
    }

    def __init__(self, fail_on_unknown_esc=True):
        self.state = "stream"
        self.params = []
        self.current_param = ""
        self.listeners = {} 
        self.fail_on_unknown_esc = fail_on_unknown_esc

    def _escape_sequence(self, char):
        """
        Handle characters seen when in an escape sequence. Most non-vt52
        commands start with a left-bracket after the escape and then a 
        stream of parameters and a command.
        """

        num = ord(char)
        if char == "[":
            self.state = "escape-lb"
        elif char == "(":
            self.state = "charset-g0"
        elif char == ")":
            self.state = "charset-g1"
        elif num in self.escape:
            self.dispatch(self.escape[num])
            self.state = "stream"
        elif self.fail_on_unknown_esc:
            raise StreamProcessError("Unexpected character '%c' == '0x%02x'" % (char, ord(char)))

    def _end_escape_sequence(self, char):
        """
        Handle the end of an escape sequence. The final character in an escape
        sequence is the command to execute, which corresponds to the event that
        is dispatched here.
        """

        num = ord(char)
        if num in self.sequence:
            self.dispatch(self.sequence[num], *self.params)
        self.state = "stream"
        self.current_param = ""
        self.params = []

    def _escape_parameters(self, char):
        """
        Parse parameters in an escape sequence. Parameters are a list of
        numbers in ascii (e.g. '12', '4', '42', etc) separated by a semicolon
        (e.g. "12;4;42").
        
        See the [vt102 user guide](http://vt100.net/docs/vt102-ug/) for more
        details on the formatting of escape parameters. 
        """

        if char == ";":
            self.params.append(int(self.current_param))
            self.current_param = ""
        elif char == "?":
            self.state = "mode"
        elif not char.isdigit():
            if len(self.current_param) > 0:
                self.params.append(int(self.current_param))

            # If we're in parameter parsing mode, but we see a non-numeric 
            # value, it must be the end of the control sequence.
            self._end_escape_sequence(char)
        else:
            self.current_param += char

    def _mode(self, char):
        if char in "lh":
            # 'l' or 'h' designates the end of a mode stream. We don't
            # really care about mode streams so anything else seen while
            # in the mode state, is just ignored.
            self.state = "stream"

    def _charset_g0(self, char):
        self.dispatch("charset-g0", char)
        self.state = "stream"

    def _charset_g1(self, char):
        self.dispatch("charset-g1", char)
        self.state = "stream"

    def _stream(self, char):
        """
        Process a character when in the
        default 'stream' state.
        """

        num = ord(char)
        if num in self.basic:
            self.dispatch(self.basic[num])
        elif num == ctrl.ESC:
            self.state = "escape"
        elif num == 0x00:
            # nulls are just ignored.
            pass
        else: 
            self.dispatch("print", char) 

    def consume(self, char):
        """
        Consume a single character and advance the state as necessary.
        """

        if self.state == "stream":
            self._stream(char)
        elif self.state == "escape":
            self._escape_sequence(char)
        elif self.state == "escape-lb":
            self._escape_parameters(char)
        elif self.state == "mode":
            self._mode(char)
        elif self.state == "charset-g0":
            self._charset_g0(char)
        elif self.state == "charset-g1":
            self._charset_g1(char)

    def process(self, chars):
        """
        Consume a string of  and advance the state as necessary.
        """

        while len(chars) > 0:
            self.consume(chars[0])
            chars = chars[1:]

    def add_event_listener(self, event, function):
        """
        Add an event listen for a particular event. Depending on the event
        there may or may not be parameters passed to function. Most escape 
        streams also allow for an empty set of parameters (with a default
        value). Providing these default values and accepting variable arguments
        is the responsibility of function.

        More than one listener may be added for a single event. Each listener
        will be called.
        
        * **event** The event to listen for.
        * **function** The callable to invoke.
        """

        if event not in self.listeners:
            self.listeners[event] = []

        self.listeners[event].append(function)

    def dispatch(self, event, *args):
        """
        Dispatch an event where `args` is a tuple of the arguments to send to 
        any callbacks. If any callback throws an exception, the subsequent 
        callbacks will be aborted.
        """

        for callback in self.listeners.get(event, []):
            if len(args) > 0:
                callback(*args)
            else:
                callback()

class screen:
    """
    A screen is an in memory buffer of strings that represents the screen
    display of the terminal. It can be instantiated on it's own and given 
    explicit commands, or it can be attached to a stream and will respond to
    events.

    The screen buffer can be accessed through the screen's `display` property.
    """

    #: Default colors and styling. The value of this attribute should
    #: always be immutable, since shallow copies are made when resizing /
    #: applying / deleting / printing.
    #:
    #: Attributes are represented by a three-tuple that consists of the
    #: following:
    #:
    #:     1. A tuple of all the text attributes: `bold`, `underline`, etc
    #:     2. The foreground color as a string, see
    #:        :attr:`vt102.graphics.colors`
    #:     3. The background color as a string, see
    #:        :attr:`vt102.graphics.colors`
    default_attributes = (), "default", "default"

    def __init__(self, shape, encoding="utf-8"):
        rows, cols = shape

        self.encoding = encoding
        self.decoder = codecs.getdecoder(encoding)
        self.size = (rows, cols)
        self.x = 0
        self.y = 0
        self.irm = "insert"
        self.tabstops = []

        self.g0 = None
        self.g1 = None
        self.current_charset = "g0" 

        self.cursor_save_stack = []

        # Initialize the screen to completely empty.
        self.display = [u" " * cols] * rows

        # Initialize the attributes to completely empty, but the same size as
        # the screen.
        self.attributes = [[self.default_attributes] * cols] * rows
        self.cursor_attributes = self.default_attributes

    def __repr__(self):
        return repr(self.display)

    def __str__(self):
        lines = ['"%s"' % l for l in self.display]

        return "[" + ",\n ".join(lines) + "]"

    def attach(self, events):
        """
        Attach this screen to a events that processes commands and dispatches 
        events. Sets up the appropriate event handlers so that the screen will
        update itself automatically as the events processes data.
        """

        if events is not None:
            events.add_event_listener("print", self._print)
            events.add_event_listener("backspace", self._backspace)
            events.add_event_listener("tab", self._tab)
            events.add_event_listener("linefeed", self._linefeed)
            events.add_event_listener("reverse-linefeed", 
                                      self._reverse_linefeed)
            events.add_event_listener("carriage-return", self._carriage_return)
            events.add_event_listener("index", self._index)
            events.add_event_listener("reverse-index", self._reverse_index)
            events.add_event_listener("store-cursor", self._save_cursor)
            events.add_event_listener("restore-cursor", self._restore_cursor)
            events.add_event_listener("cursor-up", self._cursor_up)
            events.add_event_listener("cursor-down", self._cursor_down)
            events.add_event_listener("cursor-right", self._cursor_forward)
            events.add_event_listener("cursor-left", self._cursor_back)
            events.add_event_listener("cursor-move", self._cursor_position)
            events.add_event_listener("erase-in-line", self._erase_in_line)
            events.add_event_listener("erase-in-display", 
                                      self._erase_in_display)
            events.add_event_listener("delete-characters", 
                                      self._delete_character)
            events.add_event_listener("insert-lines", self._insert_line)
            events.add_event_listener("delete-lines", self._delete_line)
            events.add_event_listener("select-graphic-rendition",
                                      self._select_graphic_rendition)
            events.add_event_listener("charset-g0", self._charset_g0)
            events.add_event_listener("charset-g1", self._charset_g1)
            events.add_event_listener("shift-in", self._shift_in)
            events.add_event_listener("shift-out", self._shift_out)
            events.add_event_listener("bell", self._bell)

    def cursor(self):
        """
        The current location of the cursor.
        """
        return (self.x, self.y)

    def resize(self, shape):
        """
        Resize the screen. If the requested screen size has more rows than the
        existing screen, rows will be added at the bottom. If the requested
        size has less rows than the existing screen rows will be clipped at the
        top of the screen.

        Similarly if the existing screen has less columns than the requested 
        size, columns will be added at the right, and it it has more, columns 
        will be clipped at the right.
        """
        rows, cols = shape

        # Honestly though, you can't trust anyone these days...
        assert(rows > 0 and cols > 0)

        # First resize the rows
        if self.size[0] < rows:
            # If the current display size is shorter than the requested screen
            # size, then add rows to the bottom. Note that the old column size
            # is used here so these new rows will get expanded/contracted as
            # necessary by the column resize when it happens next.
            self.display += [u" " * self.size[1]] * (rows - self.size[0])
            self.attributes += [[self.default_attributes] * self.size[1]] * \
                    (rows - self.size[0])
        elif self.size[0] > rows:
            # If the current display size is taller than the requested display,
            # then take rows off the top.
            self.display = self.display[self.size[0]-rows:]
            self.attributes = self.attributes[self.size[0]-rows:]

        # Next, of course, resize the columns.
        if self.size[1] < cols:
            # If the current display size is thinner than the requested size,
            # expand each row to be the new size.
            self.display = \
                [row + (u" " * (cols - self.size[1])) for row in self.display]
            self.attributes = \
                [row + ([self.default_attributes] * (cols - self.size[1])) for row in self.attributes]
        elif self.size[1] > cols:
            # If the current display size is fatter than the requested size,
            # then trim each row from the right to be the new size.
            self.display = [row[:cols-self.size[1]] for row in self.display]
            self.attributes = [row[:cols-self.size[1]] for row in self.attributes]

        self.size = (rows, cols)
        return self.size

    def _shift_in(self):
        self.current_charset = "g0"

    def _shift_out(self):
        self.current_charset = "g1"

    def _bell(self):
        pass

    def _charset_g0(self, cs):
        if cs == '0':
            self.g0 = graphics.dsg
        else:
            # TODO: Officially support UK/US/intl8 charsets
            self.g0 = None

    def _charset_g1(self, cs):
        if cs == '0':
            self.g1 = graphics.dsg
        else:
            # TODO: Officially support UK/US/intl8 charsets
            self.g1 = None

    def _print(self, char):
        """
        Print a character at the current cursor position and advance the
        cursor.
        """

        # Don't make bugs where we try to print a screen. 
        assert len(char) == 1

        try:
            try:
                # Python 3
                char = self.decoder(bytes(char, self.encoding))[0]
            except TypeError:
                # Python 2.x
                char = self.decoder(char)[0]

        except UnicodeDecodeError:
            char = "?"

        if self.current_charset == "g0" and self.g0 is not None:
            char = char.translate(self.g0)
        elif self.current_charset == "g1" and self.g1 is not None:
            char = char.translate(self.g1)

        row = self.display[self.y]
        self.display[self.y] = row[:self.x] + char + row[self.x+1:]

        attrs = self.attributes[self.y]
        self.attributes[self.y] = attrs[:self.x] + [self.cursor_attributes] + \
                attrs[self.x+1:]

        self.x += 1

        if self.x >= self.size[1]:
            # If this was the last column in a row, move the cursor to the
            # next row.
            self._linefeed()

    def _carriage_return(self):
        """
        Move the cursor to the beginning of the current row.
        """

        self.x = 0

    def _index(self):
        """
        Move the cursor down one row in the same column. If the cursor is at 
        the last row, create a new row at the bottom.
        """

        if self.y + 1 >= self.size[0]:
            # If the cursor is currently on the last row, then spawn another
            # and scroll down (removing the top row).
            self.display = self.display[1:] + [u" " * self.size[1]]
        else:
            # If the cursor is anywhere else, then just move it to the 
            # next line.
            self.y += 1

    def _reverse_index(self):
        """
        Move the cursor up one row in the same column. If the cursor is at the
        first row, create a new row at the top.
        """
        if self.y == 0:
            # If the cursor is currently at the first row, then scroll the
            # screen up.
            self.display = [u" " * self.size[1]] + self.display[:-1]
        else:
            # If the cursor is anywhere other than the first row than just move
            # it up by one row.
            self.y -= 1

    def _linefeed(self):
        """
        Performs an index and then a carriage return.
        """

        self._index()
        self.x = 0

    def _reverse_linefeed(self):
        """
        Performs a reverse index and then a carriage return.
        """

        self._reverse_index()
        self.x = 0

    def _next_tab_stop(self):
        """
        Return the x value of the next available tabstop or the x value of the 
        margin if there are no more tabstops.
        """

        for stop in sorted(self.tabstops):
            if self.x < stop:
                return stop
        return self.size[1] - 1

    def _tab(self):
        """
        Move to the next tab space, or the end of the screen if there aren't
        anymore left.
        """
        self.x = self._next_tab_stop()

    def _backspace(self):
        """
        Move cursor to the left one or keep it in it's position if it's at
        the beginning of the line already.
        """

        self.x = max(0, self.x-1)

    def _save_cursor(self):
        """
        Push the current cursor position onto the stack.
        """

        self.cursor_save_stack.append((self.x, self.y))

    def _restore_cursor(self):
        """
        Set the current cursor position to whatever cursor is on top of the 
        stack.
        """

        if len(self.cursor_save_stack):
            self.x, self.y = self.cursor_save_stack.pop()

    def _insert_line(self, count=1):
        """
        Inserts lines at line with cursor. Lines displayed below cursor move 
        down. Lines moved past the bottom margin are lost. 
        """
        trimmed = self.display[:self.y+1] + \
                  [u" " * self.size[1]] * count + \
                  self.display[self.y+1:self.y+count+1]
        self.display = trimmed[:self.size[0]]

    def _delete_line(self, count=1):
        """
        Deletes count lines, starting at line with cursor. As lines are 
        deleted, lines displayed below cursor move up. Lines added to bottom of
        screen have spaces with same character attributes as last line moved 
        up.
        """
        self.display = self.display[:self.y] + \
                       self.display[self.y+1:]
        self.display.append([u" " * self.size[1]] * count)
        self.attributes = self.attributes[:self.y] + \
                       self.attributes[self.y+1:]
        last_attributes = self.attributes[-1]
        for _ in xrange(count):
            self.attributes.append(copy(last_attributes))

    def _delete_character(self, count=1):
        """
        Deletes count characters, starting with the character at cursor
        position. When a character is deleted, all characters to the right 
        of cursor move left.
        """

        # First resize the text display
        row = self.display[self.y]
        count = min(count, self.size[1] - self.x)
        row = row[:self.x] + row[self.x+count:] + u" " * count
        self.display[self.y] = row

        # Then resize the attribute array too
        attrs = self.attributes[self.y]
        attrs = attrs[:self.x] + attrs[self.x+count:] + [self.default_attributes] * count
        self.attributes[self.y] = attrs

    def _erase_in_line(self, type_of=0):
        """
        Erases the row in a specific way, depending on the type_of.
        """

        row = self.display[self.y]
        attrs = self.attributes[self.y]
        if type_of == 0:
            # Erase from the cursor to the end of line, including the cursor
            row = row[:self.x] + u" " * (self.size[1] - self.x)
            attrs = attrs[:self.x] + [self.default_attributes] * (self.size[1] - self.x)
        elif type_of == 1:
            # Erase from the beginning of the line to the cursor, including it
            row = u" " * (self.x+1) + row[self.x+1:]
            attrs = [self.default_attributes] * (self.x+1) + attrs[self.x+1:]
        elif type_of == 2:
            # Erase the entire line.
            row = u" " * self.size[1]
            attrs = [self.default_attributes] * self.size[1]

        self.display[self.y] = row
        self.attributes[self.y] = attrs

    def _erase_in_display(self, type_of=0):
        if type_of == 0:
            # Erase from cursor to the end of the display, including the 
            # cursor.
            self.display = self.display[:self.y] + \
                    [u" " * self.size[1]] * (self.size[0] - self.y)
            self.attributes = self.attributes[:self.y] + \
                    [[self.default_attributes] * self.size[1]] * (self.size[0] - self.y)
        elif type_of == 1:
            # Erase from the beginning of the display to the cursor, including 
            # it.
            self.display = [u" " * self.size[1]] * (self.y + 1) + \
                    self.display[self.y+1:]
            self.attributes = [[self.default_attributes] * self.size[1]] * (self.y + 1) + \
                    self.attributes[self.y+1:]
        elif type_of == 2:
            # Erase the whole display.
            self.display = [u" " * self.size[1]] * self.size[0]
            self.attributes = [[self.default_attributes] * self.size[1]] * self.size[0]

    def _set_insert_mode(self):
        self.irm = "insert"

    def _set_replace_mode(self):
        self.irm = "replace"

    def _set_tab_stop(self):
        """
        Sets a horizontal tab stop at cursor position.
        """
        self.tabstops.append(self.x)

    def _clear_tab_stop(self, type_of=0x33):
        if type_of == 0x30:
            # Clears a horizontal tab stop at cursor position.
            try: 
                self.tabstops.remove(self.x) 
            except ValueError: 
                # If there is no tabstop at the current position, then just do
                # nothing.
                pass
        elif type_of == 0x33:
            # Clears all horizontal tab stops
            self.tabstops = []

    def _cursor_up(self, count=1):
        """
        Moves cursor up count lines in same column. Cursor stops at top 
        margin.
        """
        self.y = max(0, self.y - count)

    def _cursor_down(self, count=1):
        """
        Moves cursor down count lines in same column. Cursor stops at bottom 
        margin.
        """
        self.y = min(self.size[0] - 1, self.y + count)

    def _cursor_back(self, count=1):
        """
        Moves cursor left count columns. Cursor stops at left margin.
        """
        self.x = max(0, self.x - count)

    def _cursor_forward(self, count=1):
        """
        Moves cursor right count columns. Cursor stops at right margin.
        """
        self.x = min(self.size[1] - 1, self.x + count)

    def _cursor_position(self, row=0, column=0):
        """
        Set the cursor to a specific row and column. 

        Obnoxiously row/column is 1 based, instead of zero based, so we need 
        to compensate. I know I've created bugs in here somehow.
        Confoundingly, inputs of 0 are still acceptable, and should move to
        the beginning of the row/column as if they were 1. *sigh*
        """

        if row == 0: 
            row = 1
        if column == 0: 
            column = 1
        
        self.y = min(row - 1, self.size[0] - 1)
        self.x = min(column - 1, self.size[1] - 1)

    def _home(self):
        """
        Set the cursor to (0, 0)
        """
        self.y = self.x = 0

    def _remove_text_attr(self, attr):
        current = set(self.cursor_attributes[0])
        if attr in current:
            current.remove(attr)
        return tuple(current) + self.cursor_attributes[1:]

    def _add_text_attr(self, attr):
        current = set(self.cursor_attributes[0])
        current.add(attr)
        attrs = self.cursor_attributes[1:]
        return (tuple(current), attrs[0], attrs[1]) 

    def _text_attr(self, attr):
        """
        Given a text attribute, set the current cursor appropriately.
        """
        attr = text[attr]
        if attr == "reset":
            self.cursor_attributes = self.default_attributes
        elif attr == "underline-off":
            self.cursor_attributes = self._remove_text_attr("underline")
        elif attr == "blink-off":
            self.cursor_attributes = self._remove_text_attr("blink")
        elif attr == "reverse-off":
            self.cursor_attributes = self._remove_text_attr("reverse")
        else:
            self.cursor_attributes = self._add_text_attr(attr)

    def _color_attr(self, ground, attr):
        """
        Given a color attribute, set the current cursor appropriately.
        """
        attr = colors[ground][attr] 
        attrs = self.cursor_attributes
        if ground == "foreground":
            self.cursor_attributes = (attrs[0], attr, attrs[2])
        elif ground == "background":
            self.cursor_attributes = (attrs[0], attrs[1], attr)

    def _set_attr(self, attr):
        """
        Given some text attribute, set the current cursor attributes 
        appropriately.
        """
        if attr in text:
            self._text_attr(attr)
        elif attr in colors["foreground"]:
            self._color_attr("foreground", attr)
        elif attr in colors["background"]:
            self._color_attr("background", attr)

    def _select_graphic_rendition(self, *attrs):
        """
        Set the current text attribute.
        """

        if len(attrs) == 0:
            # No arguments means that we're really trying to do a reset.
            attrs = [0]

        for attr in attrs:
            self._set_attr(attr)
