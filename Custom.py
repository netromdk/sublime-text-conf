import sublime
import sublime_plugin
import re
from sublime import Region
from time import time

from .utils import guard_path_to_root, reset_viewport_to_left, line_at_pos, line_endings_view_text,\
  is_newline

WS_RE = re.compile("(\\s)+")

class CycleSpacingCommand(sublime_plugin.TextCommand):
  """Cycles spacing such that if more than one white space exists at cursors they will be replaced
  with one space. If only one white space exists then remove that entirely."""

  def run(self, edit):
    if not self.view.is_read_only() and self.view.size() > 0:
      self.__cycle_spacing(self.view, edit)

  def __cycle_spacing(self, view, edit):
    sel = view.sel()
    nl = line_endings_view_text(view)
    for region in sel:
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
            txt += nl

        # Replace the text.
        view.replace(edit, line_reg, txt)

        # Replace region so cursor appears at the right place.
        sel.subtract(region)
        sel.subtract(line_reg)
        sel.add(Region(line_reg.begin() + s[0]))
        break

class DeleteBlankLinesCommand(sublime_plugin.TextCommand):
  """Delete blank lines before and after cursors but leaving one newline."""

  def run(self, edit):
    if not self.view.is_read_only() and self.view.size() > 0:
      self.__delete_blank_lines(self.view, edit)

  def __delete_blank_lines(self, view, edit):
    nl = line_endings_view_text(view)
    for region in view.sel():
      begin = region.begin()
      line_reg = view.full_line(begin)

      # Find point of upward-most newline.
      try_pos = begin - 1
      while True:
        line_up_reg = view.full_line(try_pos)
        line_text = view.substr(line_up_reg)
        if is_newline(line_text):
          line_reg = line_up_reg
          try_pos -= 1
        else:
          break

      # Delete blank lines downwards.
      rem = False
      while True:
        line_text = view.substr(line_reg)
        if is_newline(line_text):
          rem = True
          view.erase(edit, line_reg)
        else:
          break

      # Insert newline to give space if anything was removed but only if not at the end of the file.
      nl_pos = line_reg.begin()
      if rem and nl_pos != view.size():
        view.insert(edit, nl_pos, nl)

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

    # Make sure the region is visible if there's horizontal scroll.
    reset_viewport_to_left(self.view)

class InsertCppIncludeGuardCommand(sublime_plugin.TextCommand):
  """Inserts C++ include guard."""

  def run(self, edit):
    if not self.view.is_read_only():
      self.__insert_guard(edit)

  def __insert_guard(self, edit):
    guard = guard_path_to_root(self.view.file_name())
    nl = line_endings_view_text(self.view)
    self.view.insert(edit, 0, "#ifndef {}{}#define {}{}{}".format(guard, nl, guard, nl, nl))
    self.view.insert(edit, self.view.size(), "{}{}#endif // {}{}".format(nl, nl, guard, nl))

class LineCountUpdateListener(sublime_plugin.EventListener):
  """Updates line count in status bar at intervals."""

  def __init__(self):
    super(LineCountUpdateListener).__init__()
    self.__last_change = 0  # Start at "never".
    self.__update_interval = 2.0  # s
    self.__status_key = "custom_line_count"

  def __update_line_count(self, view):
    line_count = line_at_pos(view.size(), view) + 1
    view.set_status(self.__status_key, "Lines: {}".format(line_count))

  def on_modified(self, view):
    now = time()
    if now > self.__last_change + self.__update_interval:
      self.__last_change = now
      interval = int(self.__update_interval * 1000)
      sublime.set_timeout(lambda: self.__update_line_count(view), interval)

  # When new buffer is created.
  on_new = __update_line_count

  # When a file finished loading.
  on_load = __update_line_count

class RecenterTopBottomCommand(sublime_plugin.TextCommand):
  """Places current line as center, top, and bottom in a cycling manner. Only works with one
  cursor/selection."""

  def run(self, edit):
    if self.view.size() > 0 and len(self.view.sel()) == 1:
      self.__cycle_placement()

  def __cycle_placement(self):
    view = self.view
    cur_line = line_at_pos(view.sel()[0].begin(), view)
    visible = view.visible_region()
    top_line = line_at_pos(visible.begin(), view)
    bottom_line = line_at_pos(visible.end(), view)
    half_lines = (bottom_line - top_line) // 2
    center_line = top_line + half_lines

    # Cycle between center, top, and bottom.
    if cur_line == center_line:
      choice = center_line + half_lines - 1  # Subract one to be visible.
    elif cur_line >= top_line - 1 and cur_line <= top_line + 1:
      choice = center_line - (half_lines * 2) + 2  # Add two to be visible.
    else:
      choice = cur_line

    # Set centered line from result.
    view.show_at_center(view.text_point(choice, 0))
