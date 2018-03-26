import re
import sublime
from uuid import uuid4
from os.path import split
from os import listdir

VC_FILES = [".git", ".hg", ".fslckout", ".bzr", "_darcs", ".svn"]

def guard_path_to_root(path):
  if path is None:
    return uuid4().hex
  elms = []
  while True:
    (path, file) = split(path)
    if path == "" or path == "/" or file == "":
      break
    elms.insert(0, re.sub(r"[\.\\\/\s-]", "_", file.upper()))
    if len(set(listdir(path)).intersection(VC_FILES)) > 0:
      break
  return "_".join(elms)

def reset_viewport_to_left(view):
  pos_y = view.viewport_position()[1]
  view.set_viewport_position((0.0, pos_y))

def line_at_pos(pos, view):
  return view.rowcol(pos)[0]

def line_endings_text(endings):
  endings = endings.lower()
  if endings == "unix":
    return "\n"
  elif endings == "windows":
    return "\r\n"

  # elif endings == "system":
  plat = sublime.platform()
  return line_endings_text(plat if plat == "windows" else "unix")

def line_endings_view_text(view):
  return line_endings_text(view.settings().get("default_line_ending"))

def is_newline(text):
  return text in ["\n", "\r\n"]
