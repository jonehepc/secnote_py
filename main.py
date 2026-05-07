"""SecNotepad 应用入口: python main.py"""

import sys
from pathlib import Path

# 确保 src/ 在导入路径中
sys.path.insert(0, str(Path(__file__).parent / "src"))

from secnotepad.__main__ import main

if __name__ == "__main__":
    main()
