"""
Desksor — Give your AI eyes. Let it see everything on your computer.

Windows accessibility tree automation library for AI agents.
"""

import sys

if sys.platform != "win32":
    print(
        "\n"
        "╔══════════════════════════════════════════════════════════════╗\n"
        "║                      Desksor Notice                         ║\n"
        "╠══════════════════════════════════════════════════════════════╣\n"
        "║  Desksor free version is Windows only.                      ║\n"
        "║  Mac and Linux support available at desksor.dev             ║\n"
        "╚══════════════════════════════════════════════════════════════╝\n"
    )
    raise ImportError(
        "Desksor requires Windows 10 or 11. "
        "Mac and Linux support is available at desksor.dev"
    )

from desksor.agent import Agent

__version__ = "0.1.0"
__author__ = "Aivorize"
__license__ = "MIT"
__all__ = ["Agent"]
