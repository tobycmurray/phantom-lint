from setuptools import setup, find_packages
from setuptools.command.install import install
import subprocess

class CustomInstall(install):
    def run(self):
        install.run(self)
        subprocess.check_call(["python", "-m", "spacy", "download", "en_core_web_sm"])

setup(
    name="phantomlint",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "spacy",
        "pytesseract",
        "PyMuPDF",  # maps to PyMuPDF
        "Pillow",
        "sentence-transformers",
        "opencv-python",
        "playwright",
        "pikepdf"
    ],
    cmdclass={
        'install': CustomInstall,
    },
    entry_points={
        'console_scripts': [
            'phantomlint=phantomlint.cli:main'
        ]
    },
    author="Toby Murray",
    description="Detect unwanted hidden phrases in documents.",
    python_requires=">=3.8",
)
