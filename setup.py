import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="zoxy",
    version="0.0.1",
    author="Zonda Yang",
    author_email="u226699@gmail.com",
    description="python proxy",
    license="MIT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/zondatw/zoxy",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    keywords="proxy http",
    packages=["zoxy"],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "zoxy=zoxy.cli:main",
        ],
    },
)