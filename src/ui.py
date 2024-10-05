from __future__ import annotations
from pprint import pformat
from pyscript import window, document, when, display

from project_types import Line, MalformedLine, EmptyLine
from validator import WarOutputValidator


VERSION = "v0.1"


class LineConverter:
    def line_to_html(self, line: Line | None) -> str:
        match line:
            case MalformedLine():
                status = "wrong"

            case EmptyLine():
                status = "ignore"

            case _:
                status = "correct"

        return f'<span class="{status}">{line}</span>'


class HtmlView:
    @classmethod
    def default(cls):
        converter = LineConverter()

        return HtmlView(converter)

    def __init__(self, converter: LineConverter):
        self._converter = converter

    def handle_click(self, event):
        # Validator is stateful; must be recreated/reset every time
        validator = WarOutputValidator.default()

        input_elem = event.target
        str_lines = input_elem.value.split('\n')
        parsed_lines = validator.parse_lines(str_lines)
        verdict = validator.validate_lines(str_lines)

        self._render_lines(parsed_lines)

        verdict_elem = document.querySelector("#verdict")

        if verdict.error is None:
            verdict_elem.innerHTML = f'<span class="correct">{verdict}</span>'
        else:
            verdict_elem.innerHTML = f'<span class="wrong">{verdict}</span>'

    def _render_lines(self, lines: list[Line]):
        numbered_lines = enumerate(lines, start=1)

        erroneous_line_nums = [
            n for n, line in numbered_lines
            if isinstance(line, MalformedLine)
        ]

        if erroneous_line_nums:
            summary_output = f'Erroneous lines: {
                ', '.join(
                    [str(n) for n, line in numbered_lines
                    if isinstance(line, MalformedLine)]
                )
            }'
        else:
            summary_output = 'All lines are correctly formatted'

        lines_output = "<br />".join(
            f'{n}: {self._converter.line_to_html(line)}'
            for n, line in enumerate(lines, start=1)
        )

        output_elem = document.querySelector("#output")
        output_elem.innerHTML = f'{summary_output}<br />{lines_output}'


view = HtmlView.default()

@when("change", "#input")
def click_handler(event):
    view.handle_click(event)


loading_elem = document.querySelector("#loading")
loading_elem.innerHTML = ''

version_elem = document.querySelector("#version")
version_elem.innerHTML = VERSION
