"""pytest conftest — 设置 sys.path 使 packages/ 下的测试能导入 platform_core。"""

import os
import sys

# 将 packages/ 目录加入 sys.path，使 `import platform_core` 可用
PKG_DIR = os.path.dirname(os.path.abspath(__file__))
if PKG_DIR not in sys.path:
    sys.path.insert(0, PKG_DIR)
