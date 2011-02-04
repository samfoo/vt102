import unittest

from vt102 import *
from vt102.control import *

class TestStream(unittest.TestCase):
    class counter:
        def __init__(self):
            self.count = 0

        def __call__(self, **args):
            self.count += 1

    def test_multi_param_params(self):
        s = stream()
        s.state = "escape-lb"
        input = "5;25"
        s.process(input)
        assert s.params == [5]
        assert s.current_param == "25"

    def test_cursor_down(self):
        class argcheck:
            def __init__(self):
                self.count = 0
            def __call__(self, distance):
                self.count += 1
                assert distance == 5

        s = stream()
        input = "\000" + chr(ESC) + "[5" + chr(CUD)
        e = argcheck()
        s.add_event_listener("cursor-down", e)
        s.process(input)

        assert e.count == 1
        assert s.state == "stream"

    def test_cursor_up(self):
        class argcheck:
            def __init__(self):
                self.count = 0
            def __call__(self, distance):
                self.count += 1
                assert distance == 5

        s = stream()
        input = "\000" + chr(ESC) + "[5" + chr(CUU)
        e = argcheck()
        s.add_event_listener("cursor-up", e)
        s.process(input)

        assert e.count == 1
        assert s.state == "stream"

    def test_basic_escapes(self):
        s = stream()

        for cmd, event in stream.escape.iteritems():
            c = self.counter()
            s.add_event_listener(event, c)
            s.consume(chr(ESC))
            assert s.state == "escape"
            s.consume(chr(cmd))
            assert c.count == 1
            assert s.state == "stream"

    def test_backspace(self):
        s = stream()

        c = self.counter()
        s.add_event_listener("backspace", c)
        s.consume(chr(BS))

        assert c.count == 1
        assert s.state == "stream"

    def test_tab(self):
        s = stream()

        c = self.counter()
        s.add_event_listener("tab", c)
        s.consume(chr(HT))

        assert c.count == 1
        assert s.state == "stream"

    def test_linefeed(self):
        s = stream()

        c = self.counter()
        s.add_event_listener("linefeed", c)
        s.process(chr(LF) + chr(VT) + chr(FF))
        
        assert c.count == 3
        assert s.state == "stream"

    def test_carriage_return(self):
        s = stream()

        c = self.counter()
        s.add_event_listener("carriage-return", c)
        s.consume(chr(CR))
        
        assert c.count == 1 
        assert s.state == "stream"

class TestScreen(unittest.TestCase):
    def test_remove_non_existant_attribute(self):
        s = screen((2,2))
        assert s.attributes == [[s._default(), s._default()]] * 2
        s._remove_text_attr("underline")
        assert s.attributes == [[s._default(), s._default()]] * 2

    def test_attributes(self):
        s = screen((2,2))
        assert s.attributes == [[s._default(), s._default()]] * 2
        s._select_graphic_rendition(1) # Bold

        # Still default, since we haven't written anything.
        assert s.attributes == [[s._default(), s._default()]] * 2
        assert s.cursor_attributes == (("bold",), "default", "default")

        s._print("f")
        assert s.attributes == [
            [(("bold",), "default", "default"), s._default()],
            [s._default()                     , s._default()]
        ] 

    def test_colors(self):
        s = screen((2,2))
        assert s.attributes == [[s._default(), s._default()]] * 2
        s._select_graphic_rendition(30) # black foreground
        s._select_graphic_rendition(40) # black background

        assert s.cursor_attributes == ((), "black", "black")
        s._select_graphic_rendition(31) # red foreground
        assert s.cursor_attributes == ((), "red", "black")

    def test_reset_resets_colors(self):
        s = screen((2,2))
        assert s.attributes == [[s._default(), s._default()]] * 2
        s._select_graphic_rendition(30) # black foreground
        s._select_graphic_rendition(40) # black background
        assert s.cursor_attributes == ((), "black", "black")
        s._select_graphic_rendition(0)
        assert s.cursor_attributes == s._default()

    def test_multi_attribs(self):
        s = screen((2,2))
        assert s.attributes == [[s._default(), s._default()]] * 2
        s._select_graphic_rendition(1) # Bold
        s._select_graphic_rendition(5) # Blinke 

        assert s.cursor_attributes == (("bold", "blink"), "default", "default")

    def test_attributes_reset(self):
        s = screen((2,2))
        assert s.attributes == [[s._default(), s._default()]] * 2
        s._select_graphic_rendition(1) # Bold
        s._print("f")
        s._print("o")
        s._print("o")
        assert s.attributes == [
            [(("bold",), "default", "default"), (("bold",), "default", "default")],
            [(("bold",), "default", "default"),                      s._default()],
        ] 

        s._home()
        s._select_graphic_rendition(0) # Reset
        s._print("f")
        assert s.attributes == [
            [s._default()                  , (("bold",), "default", "default")],
            [(("bold",), "default", "default"),                   s._default()],
        ] 

    def test_resize(self):
        s = screen((2,2))
        assert s.display == ["  ", "  "]
        assert s.attributes == [[s._default(), s._default()]] * 2

        s.resize((3,3))
        assert s.display == ["   ", "   ", "   "]
        assert s.attributes == [[s._default(), s._default(), s._default()]] * 3

    def test_print(self):
        s = screen((3,3))
        s._print("s")

        assert s.display == ["s  ", "   ", "   "]
        assert s.cursor() == (1, 0)

        s.x = 1; s.y = 1
        s._print("a")

        assert s.display == ["s  ", " a ", "   "]

    def test_carriage_return(self):
        s = screen((3,3))
        s.x = 2
        s._carriage_return()
        
        assert s.x == 0

    def test_index(self):
        s = screen((2,2))
        s.display = ["bo", "sh"]
        s.x = 1
        s._index()

        # Indexing on a row that isn't the last should just move the cursor
        # down.
        assert s.y == 1
        assert s.x == 1

        s._index()

        # Indexing on the last row should push everything up and create a new
        # row at the bottom.
        assert s.display == ["sh", "  "]
        assert s.y == 1

    def test_reverse_index(self):
        s = screen((2,2))
        s.display = ["bo", "sh"]
        s.x = 1
        s._reverse_index()

        # Reverse indexing on the first row should push rows down and create a
        # new row at the top.
        assert s.y == 0 
        assert s.x == 1
        assert s.display == ["  ", "bo"]

        s.y = 1
        s._reverse_index()

        assert s.display == ["  ", "bo"]
        assert s.y == 0 

    def test_line_feed(self):
        # Line feeds are the same as indexes, except they move the cursor to
        # the first character on the created/next line
        s = screen((2,2))
        s.display = ["bo", "sh"]
        s.x = 1; s.y = 0
        s._linefeed()

        assert s.x == 0
        assert s.y == 1

    def test_tabstops(self):
        s = screen((10,10))
        s.x = 1
        s._set_tab_stop()
        s.x = 8
        s._set_tab_stop()

        s.x = 0
        s._tab()
        assert s.x == 1
        s._tab()
        assert s.x == 8
        s._tab()
        assert s.x == 9
        s._tab()
        assert s.x == 9

    def test_clear_tabstops(self):
        s = screen((10, 10))
        s.x = 1
        s._set_tab_stop()
        s._clear_tab_stop(0x30)

        assert len(s.tabstops) == 0

        s._set_tab_stop()
        s.x = 5
        s._set_tab_stop()
        s.x = 9
        s._set_tab_stop()

        assert len(s.tabstops) == 3

        s._clear_tab_stop(0x33)

        assert len(s.tabstops) == 0

    def test_resize_shifts_horizontal(self):
        # If the current display is thinner than the requested size...
        s = screen((2,2))
        s.display = ["bo", "sh"]
        # New columns should get added to the right.
        s.resize((2,3))

        assert s.display == ["bo ", "sh "]

        # If the current display is wider than the requested size...
        s = screen((2,2))
        s.display = ["bo", "sh"]
        # Columns should be removed from the right...
        s.resize((2, 1))

        assert s.display == ["b", "s"]

    def test_backspace(self):
        s = screen((2,2))
        assert s.x == 0
        s._backspace()
        assert s.x == 0
        s.x = 1
        s._backspace()
        assert s.x == 0

    def test_save_cursor(self):
        s = screen((10,10))
        s._save_cursor()

        s.x = 3
        s.y = 5
        s._save_cursor()
        s.x = 4
        s.y = 4
        s._restore_cursor()

        assert s.x == 3
        assert s.y == 5

        s._restore_cursor()

        assert s.x == 0
        assert s.y == 0

    def test_restore_cursor_with_none_saved(self):
        s = screen((10, 10))
        s.x = 5
        s.y = 5
        s._restore_cursor()

        assert s.x == 5
        assert s.y == 5

    def test_insert_line(self):
        s = screen((3,3))
        s.display = ["sam", "is ", "   "]

        assert s.x == 0
        assert s.y == 0

        s._insert_line(1)

        assert s.display == ["sam", "   ", "is "]

        assert s.x == 0
        assert s.y == 0

        s.display = ["sam", "is ", "foo"]
        s._insert_line(2)

        assert s.display == ["sam", "   ", "   "]

    def test_delete_characters(self):
        s = screen((3,3))
        s.display = ["sam", "is ", "foo"]
        s.x = 0
        s.y = 0
        s._delete_character(2)

        assert s.display == ["m  ", "is ", "foo"]

        s.y = 2
        s.x = 2
        s._delete_character(1)

        assert s.display == ["m  ", "is ", "fo "]

    def test_erase_in_line(self):
        s = screen((5,5))
        s.display = ["sam i", 
                     "s foo", 
                     "but a", 
                     "re yo", 
                     "u?   "]
        s.x = 2
        s.y = 0

        # Erase from cursor to the end of line
        s._erase_in_line(0)
        assert s.display == ["sa   ",
                             "s foo", 
                             "but a", 
                             "re yo", 
                             "u?   "]

        # Erase from the beginning of the line to the cursor
        s.display = ["sam i", 
                     "s foo", 
                     "but a", 
                     "re yo", 
                     "u?   "]
        s._erase_in_line(1)
        assert s.display == ["    i",
                             "s foo", 
                             "but a", 
                             "re yo", 
                             "u?   "]

        s.y = 1
        # Erase the entire line
        s.display = ["sam i", 
                     "s foo", 
                     "but a", 
                     "re yo", 
                     "u?   "]
        s._erase_in_line(2)
        assert s.display == ["sam i",
                             "     ", 
                             "but a", 
                             "re yo", 
                             "u?   "]

    def test_erase_in_display(self):
        s = screen((5,5))
        s.display = ["sam i", 
                     "s foo", 
                     "but a", 
                     "re yo", 
                     "u?   "]
        s.y = 2 

        # Erase from the cursor to the end of the display.
        s._erase_in_display(0)
        assert s.display == ["sam i",
                             "s foo", 
                             "     ", 
                             "     ", 
                             "     "]

        # Erase from cursor to the beginning of the display. 
        s.display = ["sam i", 
                     "s foo", 
                     "but a", 
                     "re yo", 
                     "u?   "]
        s._erase_in_display(1)
        assert s.display == ["     ",
                             "     ", 
                             "     ", 
                             "re yo", 
                             "u?   "]

        s.y = 1
        # Erase the entire screen
        s._erase_in_display(2)
        assert s.display == ["     ",
                             "     ", 
                             "     ", 
                             "     ", 
                             "     "]

    def test_cursor_up(self):
        s = screen((10, 10))

        # Moving the cursor up at the top doesn't do anything
        s._cursor_up(1)
        assert s.y == 0

        s.y = 1

        # Moving the cursor past the top moves it to the top
        s._cursor_up(10)
        assert s.y == 0

        s.y = 5
        # Can move the cursor more than one up.
        s._cursor_up(3)
        assert s.y == 2

    def test_cursor_down(self):
        s = screen((10, 10))

        # Moving the cursor down at the bottom doesn't do anything
        s.y = 9
        s._cursor_down(1)
        assert s.y == 9

        s.y = 8 

        # Moving the cursor past the bottom moves it to the bottom
        s._cursor_down(10)
        assert s.y == 9 

        s.y = 5
        # Can move the cursor more than one down.
        s._cursor_down(3)
        assert s.y == 8

    def test_cursor_back(self):
        s = screen((10, 10))

        # Moving the cursor left at the margin doesn't do anything
        s.x = 0 
        s._cursor_back(1)
        assert s.x == 0

        s.x = 3 

        # Moving the cursor past the left margin moves it to the left margin
        s._cursor_back(10)
        assert s.x == 0 

        s.x = 5
        # Can move the cursor more than one back.
        s._cursor_back(3)
        assert s.x == 2

    def test_cursor_forward(self):
        s = screen((10, 10))

        # Moving the cursor right at the margin doesn't do anything
        s.x = 9 
        s._cursor_forward(1)
        assert s.x == 9 

        # Moving the cursor past the right margin moves it to the right margin
        s.x = 8 
        s._cursor_forward(10)
        assert s.x == 9

        # Can move the cursor more than one forward.
        s.x = 5
        s._cursor_forward(3)
        assert s.x == 8 

    def test_cursor_position(self):
        s = screen((10, 10))

        # Rows/columns are backwards of x/y and are 1-indexed instead of 0-indexed
        s._cursor_position(5, 10)
        assert s.x == 9
        assert s.y == 4

        # Confusingly enough, however, 0-inputs are acceptable and should be
        # the same a 1
        s._cursor_position(0, 10)
        assert s.x == 9
        assert s.y == 0

        # Moving outside the margins constrains to within the margins.
        s._cursor_position(20, 20)
        assert s.x == 9
        assert s.y == 9

    def test_home(self):
        s = screen((10, 10))
        s.x = 5
        s.y = 5
        s._home()

        assert s.x == 0
        assert s.y == 0

    def test_resize_shifts_vertical(self):
        # If the current display is shorter than the requested screen size... 
        s = screen((2,2))
        s.display = ["bo", "sh"]
        # New rows should get added on the bottom...
        s.resize((3,2))

        assert s.display == ["bo", "sh", "  "]

        # If the current display is taller than the requested screen size...
        s = screen((2,2))
        s.display = ["bo", "sh"]
        # Rows should be removed from the top...
        s.resize((1,2))

        assert s.display == ["sh"]

if __name__ == "__main__":
    unittest.main()
