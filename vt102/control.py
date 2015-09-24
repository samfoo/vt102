"""Backspace: Moves cursor to the left one character position; if cursor is at 
left margin, no action occurs."""
BS = 0x08

"""Horizontal tab: Moves cursor to the next tab stop, or right margin if there 
are no more tab stops."""
HT = 0x09

"""Linefeed: Causes a linefeed."""
LF = 0x0a

"""Vertical tab: Processed as LF."""
VT = 0x0b

"""Form feed: Process as LF."""
FF = 0x0c

"""Carriage return: Moves cursor to left margin on current line."""
CR = 0x0d

"""Device control 1: Processed as XON. DC1 causes terminal to continue 
transmitting characters."""
DC1 = 0x11

"""Device control 3: Processed as XOFF. DC3 causes terminal to stop
transmitting all characters except XOFF and XON."""
DC3 = 0x13

"""Cancel: If received during an escape or control sequence, cancels the
sequence and displays substitution character"""
CAN = 0x18

"""Substitute: Processed as CAN"""
SUB = 0x1a

"""Escape: Processed as a sequence introducer."""
ESC = 0x1b

"""Shift in: Switch to the G0 character set."""
SI = 0x0f

"""Shift out: Switch to the G1 character set."""
SO = 0x0e

"""Bell: Generates bell tone."""
BEL = 0x07
