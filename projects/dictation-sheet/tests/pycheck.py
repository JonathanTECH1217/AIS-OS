"""Parse build_desktop.py and the server script embedded in it."""
import ast
import re

path = r"C:\Users\sumre\Documents\GitHub\AIS-OS\projects\dictation-sheet\build_desktop.py"
src = open(path, encoding="utf-8").read()
ast.parse(src)
m = re.search(r"SERVE_SRC = '''(.*?)'''", src, re.S)
assert m, "SERVE_SRC not found"
ast.parse(m.group(1).replace("__PORT__", "8765").replace("__VERSION__", "x"))
print("build_desktop.py and the embedded serve.py parse ok")
