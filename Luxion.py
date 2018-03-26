import sublime_plugin
from datetime import datetime

from .utils import guard_path_to_root, line_endings_view_text

class WrapLuxionFunctionCommand(sublime_plugin.TextCommand):
  def wrap_regions(self, view, edit):
    nl = line_endings_view_text(view)
    line = "// " + "*" * 97 + nl

    for region in view.sel():
      if not region.empty():
        txt = view.substr(region)
        txt = line + txt
        if not txt.endswith(nl):
          txt += nl
        txt += line
        view.replace(r=region, text=txt, edit=edit)

  def run(self, edit):
    if not self.view.is_read_only() and self.view.size() > 0:
      self.wrap_regions(self.view, edit)

class LuxionInsertCppIncludeGuardCommand(sublime_plugin.TextCommand):
  """Inserts Luxion C++ include guard."""

  def run(self, edit):
    if not self.view.is_read_only():
      self.__insert_guard(edit)

  def __insert_guard(self, edit):
    guard = guard_path_to_root(self.view.file_name())
    year = datetime.today().year
    nl = line_endings_view_text(self.view)
    txt = "// (c) Copyright 2003-{} Luxion ApS - All Rights Reserved{}#ifndef {}{}#define {}{}{}".\
      format(year, nl, guard, nl, guard, nl, nl)
    self.view.insert(edit, 0, txt)
    self.view.insert(edit, self.view.size(), "{}{}#endif // {}{}".format(nl, nl, guard, nl))
