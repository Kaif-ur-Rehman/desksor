from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="desksor",
    version="0.1.0",
    description="Give your AI eyes. Let it see everything on your computer.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Aivorize",
    author_email="hello@aivorize.com",
    url="https://github.com/aivorize/desksor",
    packages=find_packages(),
    install_requires=[
        "pywinauto>=0.6.8",
        "pyautogui>=0.9.54",
        "websockets>=11.0",
        "requests>=2.31.0",
        "openpyxl>=3.1.0",
        "aiofiles>=23.0.0",
        "psutil>=5.9.0",
        "pdfplumber>=0.9.0",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Operating System",
    ],
    keywords="automation accessibility ai agent windows pywinauto mcp",
    entry_points={
        "console_scripts": [
            "desksor-server=desksor.server:main",
        ],
    },
)
