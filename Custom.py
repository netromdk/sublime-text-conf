import sublime_plugin
import re

WS_RE = re.compile("(\\s)+")

class CycleSpacingCommand(sublime_plugin.TextCommand):
  """Cycles spacing such that if more than one white space exists at cursors they will be replaced
  with one space. If only one white space exists then remove that entirely."""

  def cycle_spacing(self, view, edit):
    for region in view.sel():
      begin = region.begin()
      line_reg = view.full_line(begin)
      line_text = view.substr(line_reg)
      pos_line = begin - line_reg.begin()

      # Find all white space in text of line, and if cursor is inside a chunk of white space, then
      # remove those and replace the line text.
      for m in WS_RE.finditer(line_text):
        if not m:
          continue

        s = m.span()
        if pos_line < s[0] or pos_line > s[1]:
          continue

        # If line is only a white space and a newline, let it become the newline.
        if len(line_text) == 2 and line_text.endswith("\n"):
          txt = line_text[1:]

        # Otherwise replace white spaces.
        else:
          keep = " " if (s[1] - s[0]) > 1 else ""
          txt = line_text[0:s[0]] + keep + line_text[s[1]:]

          # Maintain newline at end of line.
          if line_text.endswith("\n") and not txt.endswith("\n"):
            txt += "\n"

        view.replace(r=line_reg, text=txt, edit=edit)
        break

  def run(self, edit):
    if not self.view.is_read_only() and self.view.size() > 0:
      self.cycle_spacing(self.view, edit)
