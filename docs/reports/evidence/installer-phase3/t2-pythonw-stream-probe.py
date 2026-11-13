import os
from pathlib import Path
import sys

Path(os.environ["ULTIMA_STREAM_PROBE"]).write_text(
    f"stdout={sys.stdout!r};stderr={sys.stderr!r}",
    encoding="utf-8",
)
sys.stdout.write("OUT")
sys.stderr.write("ERR")
