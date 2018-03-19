import sublime_plugin
from datetime import datetime

from .utils import guard_path_to_root

WRAP_LINE = "// " + "*" * 97 + "\n"

class WrapLuxionFunctionCommand(sublime_plugin.TextCommand):
  def wrap_regions(self, view, edit):
    for region in view.sel():
      if not region.empty():
        txt = view.substr(region)
        txt = WRAP_LINE + txt
        if not txt.endswith("\n"):
          txt += "\n"
        txt += WRAP_LINE
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
    txt = "// (c) Copyright 2003-{} Luxion ApS - All Rights Reserved\n#ifndef {}\n#define {}\n\n".\
      format(year, guard, guard)
    self.view.insert(edit, 0, txt)
    self.view.insert(edit, self.view.size(), "\n\n#endif // {}\n".format(guard))
