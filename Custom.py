import sublime_plugin
from sublime import Region
import re

WS_RE = re.compile("(\\s)+")

class CycleSpacingCommand(sublime_plugin.TextCommand):
  """Cycles spacing such that if more than one white space exists at cursors they will be replaced
  with one space. If only one white space exists then remove that entirely."""

  def run(self, edit):
    if not self.view.is_read_only() and self.view.size() > 0:
      self.__cycle_spacing(self.view, edit)

  def __cycle_spacing(self, view, edit):
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

class DeleteBlankLinesCommand(sublime_plugin.TextCommand):
  """Delete blank lines before and after cursors but leaving one newline."""

  def run(self, edit):
    if not self.view.is_read_only() and self.view.size() > 0:
      self.__delete_blank_lines(self.view, edit)

  def __delete_blank_lines(self, view, edit):
    for region in view.sel():
      begin = region.begin()
      line_reg = view.full_line(begin)

      # Find point of upward-most newline.
      try_pos = begin - 1
      while True:
        line_up_reg = view.full_line(try_pos)
        line_text = view.substr(line_up_reg)
        if line_text == "\n":
          line_reg = line_up_reg
          try_pos -= 1
        else:
          break

      # Delete blank lines downwards.
      rem = False
      while True:
        line_text = view.substr(line_reg)
        if line_text == "\n":
          rem = True
          view.erase(edit, line_reg)
        else:
          break

      # Insert newline to give space if anything was removed but only if not at the end of the file.
      nl_pos = line_reg.begin()
      if rem and nl_pos != view.size():
        view.insert(edit, nl_pos, "\n")

class SmartBeginningOfLineCommand(sublime_plugin.TextCommand):
  """Go to first non white space on line. If that position is already the current position then move
  to beginning of line. Can be called in a cycling fashion."""

  def run(self, edit):
    if self.view.size() > 0:
      self.__goto_beginning(self.view, edit)

  def __goto_beginning(self, view, edit):
    sel = view.sel()
    for region in sel:
      begin = region.begin()
      line_reg = view.full_line(begin)
      line_text = view.substr(line_reg)
      if len(line_text) <= 1:
        continue

      m = WS_RE.match(line_text)

      # Go to beginning of line if no white space if found at the beginning of the line.
      if not m:
        self.__replace_region(sel, region, line_reg.begin())
        continue

      # If line position is not first non white space from the left then put cursor there, otherwise
      # put at the beginning.
      pos_line = begin - line_reg.begin()
      last_ws_pos = m.span()[1]
      new_pos = line_reg.begin()
      if pos_line > last_ws_pos or pos_line == 0:
        new_pos += last_ws_pos
        # If whole line is white space then move to EOL.
        if last_ws_pos == line_reg.size():
          new_pos -= 1
      self.__replace_region(sel, region, new_pos)

  def __replace_region(self, sel, region, new_pos):
    new_reg = Region(new_pos)
    sel.subtract(region)
    sel.add(new_reg)
