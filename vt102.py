import fcntl
import string
import struct

from control import *
from escape import *

class stream:
    basic = {
        BS: "backspace",
        HT: "tab",
        LF: "linefeed",
        VT: "linefeed",
        FF: "linefeed",
        CR: "carriage-return",
    }

    escape = {
        IND: "index",
        RI: "reverse-index",
        NEL: "linefeed",
        DECSC: "store-cursor",
        DECRC: "restore-cursor",
    }

    sequence = {
        CUU: "cursor-up",
        CUD: "cursor-down",
        CUF: "cursor-right",
        CUB: "cursor-left",
        CUP: "cursor-move",
        HVP: "cursor-move",
        EL: "erase-in-line",
        ED: "erase-in-display",
        DCH: "delete-characters",
        IL: "isert-lines",
        DL: "delete-lines",
    }

    def __init__(self):
        self.state = "stream"
        self.params = []
        self.current_param = ""

    def _escape_sequence(self, char):
        num = ord(char)
        if char == "[":
            self.state = "escape-lb"
        elif self.escape.has_key(num):
            self.dispatch(self.escape[num])

    def _end_escape_sequence(self, char):
        if sequence.has_key(char):
            self.dispatch(sequence[char], *self.params)

    def _escape_parameters(self, char):
        if char == ";":
            self.params.append(int(self.current_param))
        elif char not in string.digits:
            if len(self.current_param) > 0:
                self.params.append(int(self.current_param))

            # If we're in parameter parsing mode, but we see a non-numeric 
            # value, it must be the end of the control sequence.
            self._end_escape_sequence(char)
        else:
            self.current_param += char

    def _stream(self, char):
        num = ord(char)
        if self.basic.has_key(num):
            self.dispatch(self.basic[num])
        elif char in string.printable:
            self.dispatch("print", char)
        elif num == ESC:
            self.state = "escape"

    def consume(self, char):
        if self.state == "stream":
            self._stream(char)
        elif self.state == "escape":
            self._escape_sequence(char)
        elif self.state == "escape-lb":
            self._escape_parameters(char)

    def process(self, input):
        while len(input) > 0:
            self.consume(input[0])
            input = input[1:]

    def dispatch(event, *args):
        pass

class screen:
    def __init__(self, (rows, cols)):
        self.size = (rows, cols)
        self.x = 0
        self.y = 0
        self.irm = "insert"
        self.tabstops = []

        self.cursor_save_stack = []

        # Initialize the screen to completely empty.
        self.display = [" " * cols] * rows

    def __repr__(self):
        return repr(self.display)

    def cursor(self):
        return (self.x, self.y)

    def resize(self, (rows, cols)):
        # Honestly though, you can't trust anyone these days...
        assert(rows > 0 and cols > 0)

        # First resize the rows
        if self.size[0] < rows:
            # If the current display size is shorter than the requested screen
            # size, then add rows to the bottom. Note that the old column size
            # is used here so these new rows will get expanded/contracted as
            # necessary by the column resize when it happens next.
            self.display += [" " * self.size[1]] * (rows - self.size[0])
        elif self.size[0] > rows:
            # If the current display size is taller than the requested display,
            # then take rows off the top.
            self.display = self.display[self.size[0]-rows:]

        # Next, of course, resize the columns.
        if self.size[1] < cols:
            # If the current display size is thinner than the requested size,
            # expand each row to be the new size.
            self.display = [row + (" " * (cols - self.size[1])) for row in self.display]
        elif self.size[1] > cols:
            # If the current display size is fatter than the requested size,
            # then trim each row from the right to be the new size.
            self.display = [row[:cols-self.size[1]] for row in self.display]

        self.size = (rows, cols)
        return self.size

    def _print(self, char):
        row = self.display[self.y]
        self.display[self.y] = row[:self.x] + char + row[self.x+1:]
        self.x += 1

        if self.x >= self.size[1]:
            # If this was the last column in a row, move the cursor to the
            # next row.
            self._linefeed()

    def _carriage_return(self):
        self.x = 0

    def _index(self):
        if self.y + 1 >= self.size[1]:
            # If the cursor is currently on the last row, then spawn another
            # and scroll down (removing the top row).
            self.display = self.display[1:] + [" " * self.size[1]]
        else:
            # If the cursor is anywhere else, then just move it to the 
            # next line.
            self.y += 1

    def _reverse_index(self):
        if self.y == 0:
            # If the cursor is currently at the first row, then scroll the
            # screen up.
            self.display = [" " * self.size[1]] + self.display[:-1]
        else:
            # If the cursor is anywhere other than the first row than just move
            # it up by one row.
            self.y -= 1

    def _linefeed(self):
        self._index()
        self.x = 0

    def _next_tab_stop(self):
        for stop in sorted(self.tabstops):
            if self.x < stop:
                return stop
        return self.size[1] - 1

    def _tab(self):
        # Move to the next tab space, or the end of the screen if there aren't
        # anymore left.
        self.x = self._next_tab_stop()

    def _backspace(self):
        # Move cursor to the left one or keep it in it's position if it's at
        # the beginning of the line already.
        self.x = max(0, self.x-1)

    def _save_cursor(self):
        self.cursor_save_stack.append((self.x, self.y))

    def _restore_cursor(self):
        if len(self.cursor_save_stack):
            self.x, self.y = self.cursor_save_stack.pop()

    def _insert_line(self, count):
        # Inserts lines at line with cursor. Lines displayed below cursor move 
        # down. Lines moved past the bottom margin are lost. 
        trimmed = self.display[:self.y+1] + \
                  [" " * self.size[1]] * count + \
                  self.display[self.y+1:self.y+count+1]
        self.display = trimmed[:self.size[0]]

    def _delete_character(self, count):
        # Deletes count characters, starting with the character at cursor
        # position. When a character is deleted, all characters to the right 
        # of cursor move left.
        row = self.display[self.y]
        count = min(count, self.size[1] - self.x)
        row = row[:self.x] + row[self.x+count:] + " " * count
        self.display[self.y] = row

    def _erase(self, row, type):
        if type == 0x31:
            # Erase from the beginning of the line to the cursor, including it
            row = " " * (self.x+1) + row[self.x+1:]
        elif type == 0x32:
            # Erase the entire line.
            row = " " * self.size[1]
        else:
            # Erase from the cursor to the end of line, including the cursor
            row = row[:self.x] + " " * (self.size[1] - self.x)
        return row

    def _erase_in_line(self, type):
        row = self._erase(self.display[self.y], type)
        self.display[self.y] = row

    def _erase_in_display(self, type):
        self.display = [self._erase(r, type) for r in self.display]

    def _set_insert_mode(self):
        self.irm = "insert"

    def _set_replace_mode(self):
        self.irm = "replace"

    def _set_tab_stop(self):
        # Sets a horizontal tab stop at cursor position.
        self.tabstops.append(self.x)

    def _clear_tab_stop(self, type):
        if type == 0x30:
            # Clears a horizontal tab stop at cursor position.
            try: self.tabstops.remove(self.x) 
            except ValueError,e: pass
        else:
            # Clears all horizontal tab stops
            self.tabstops = []

    def _cursor_up(self, count):
        # Moves cursor up count lines in same column. Cursor stops at top 
        # margin.
        self.y = max(0, self.y - count)

    def _cursor_down(self, count):
        # Moves cursor down count lines in same column. Cursor stops at bottom 
        # margin.
        self.y = min(self.size[0] - 1, self.y + count)

    def _cursor_back(self, count):
        # Moves cursor left count columns. Cursor stops at left margin.
        self.x = max(0, self.x - count)

    def _cursor_forward(self, count):
        # Moves cursor right count columns. Cursor stops at right margin.
        self.x = min(self.size[1] - 1, self.x + count)

    def _cursor_position(self, row, column):
        # Obnoxiously row/column is 1 based, instead of zero based, so we need 
        # to compensate. I know I've created bugs in here somehow.
        # Confoundingly, inputs of 0 are still acceptable, and should move to
        # the beginning of the row/column as if they were 1. *sigh*
        if row == 0: row = 1
        if column == 0: column = 1
        
        self.y = min(row - 1, self.size[0] - 1)
        self.x = min(column - 1, self.size[1] - 1)

    def _home(self):
        self.y = self.x = 0
