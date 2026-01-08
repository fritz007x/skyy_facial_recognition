#!/usr/bin/env python3
"""
Setup script for Skyy Facial Recognition MCP Server

Install with: pip install -e .
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

setup(
    name="skyy-facial-recognition",
    version="1.0.0",
    description="Facial recognition system with MCP integration and voice assistant",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Team 5 - Miami Dade College",
    python_requires=">=3.11,<3.12",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "insightface==0.7.3",
        "numpy>=1.26.0,<2.0.0",
        "opencv-python>=4.10.0",
        "chromadb>=0.5.0",
        "pydantic>=2.0.0",
        "mcp>=1.3.0",
        "loguru>=0.7.0",
        "Pillow>=10.0.0",
        "onnxruntime>=1.18.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "voice": [
            "openai-whisper>=20231117",
            "pyaudio>=0.2.13",
            "pyttsx3>=2.90",
            "webrtcvad>=2.0.10",
            "pvporcupine>=3.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "skyy-mcp=skyy_facial_recognition_mcp:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Image Recognition",
    ],
)
