import sublime_plugin

# NOTE: Run `sublime.log_commands(True)` while testing to see what's going on.

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
