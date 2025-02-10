from setuptools import setup, find_packages

setup(
    name="miyo-builder",
    version="1.0.0",
    description="Automated Flatpak builder for GitHub projects",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/miyo-builder",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "miyo-builder=miyo_builder.builder:main",
        ],
    },
    install_requires=[
        "requests",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires=">=3.6",
)