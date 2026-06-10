from unittest.mock import MagicMock, call
import pytest

from src.escpos_renderer import render_to_printer, _handle_tag


class TestRenderToPrinter:
    def _make_printer(self):
        printer = MagicMock()
        return printer

    def test_plain_text(self):
        printer = self._make_printer()
        render_to_printer(printer, "Hello World")
        printer.text.assert_called()
        # Check the text was passed through
        text_calls = [str(c) for c in printer.text.call_args_list]
        combined = " ".join(text_calls)
        assert "Hello World" in combined

    def test_bold_tag(self):
        printer = self._make_printer()
        render_to_printer(printer, "{{BOLD}}Bold text{{/BOLD}}")
        printer.set.assert_any_call(bold=True)
        printer.set.assert_any_call(bold=False)

    def test_big_tag(self):
        printer = self._make_printer()
        render_to_printer(printer, "{{BIG}}Big text{{/BIG}}")
        printer.set.assert_any_call(width=2, height=2)
        printer.set.assert_any_call(width=1, height=1)

    def test_underline_tag(self):
        printer = self._make_printer()
        render_to_printer(printer, "{{UNDERLINE}}Underlined{{/UNDERLINE}}")
        printer.set.assert_any_call(underline=1)
        printer.set.assert_any_call(underline=0)

    def test_center_tag(self):
        printer = self._make_printer()
        render_to_printer(printer, "{{CENTER}}Centered{{/CENTER}}")
        printer.set.assert_any_call(align="center")
        printer.set.assert_any_call(align="left")

    def test_right_tag(self):
        printer = self._make_printer()
        render_to_printer(printer, "{{RIGHT}}Right{{/RIGHT}}")
        printer.set.assert_any_call(align="right")
        printer.set.assert_any_call(align="left")

    def test_cut_tag(self):
        printer = self._make_printer()
        render_to_printer(printer, "{{CUT}}")
        printer.cut.assert_called_once()

    def test_open_drawer_tag(self):
        printer = self._make_printer()
        render_to_printer(printer, "{{OPEN_DRAWER}}")
        printer.cashdraw.assert_called_once_with(2)

    def test_feed_tag(self):
        printer = self._make_printer()
        render_to_printer(printer, "{{FEED:3}}")
        # Should produce 3 newlines
        newline_calls = [c for c in printer.text.call_args_list if c == call("\n")]
        assert len(newline_calls) >= 3

    def test_barcode_tag(self):
        printer = self._make_printer()
        render_to_printer(printer, "{{BARCODE:12345}}")
        printer.barcode.assert_called_once_with("12345", "CODE128", function_type="B")

    def test_multiple_copies(self):
        printer = self._make_printer()
        render_to_printer(printer, "Test\n{{CUT}}", {"copies": 3})
        # 3 copies: original CUT in each + 2 extra CUTs between copies
        assert printer.cut.call_count == 5  # 3 from template + 2 between copies

    def test_mixed_tags(self):
        printer = self._make_printer()
        text = "{{CENTER}}{{BOLD}}Title{{/BOLD}}{{/CENTER}}\nNormal text\n{{CUT}}"
        render_to_printer(printer, text)
        printer.set.assert_any_call(align="center")
        printer.set.assert_any_call(bold=True)
        printer.cut.assert_called()

    def test_empty_text(self):
        printer = self._make_printer()
        render_to_printer(printer, "")
        # Should not crash


class TestHandleTag:
    def test_unknown_tag(self):
        printer = MagicMock()
        result = _handle_tag(printer, "UNKNOWN_TAG", None)
        assert result is False
