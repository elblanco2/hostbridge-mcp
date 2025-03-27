from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = f.read().splitlines()

setup(
    name="arc-mcp",
    version="0.1.0",
    author="Arc Contributors",
    author_email="youremail@example.com",
    description="MCP server for simplified framework deployments on shared hosting environments",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/elblanco2/arc-mcp",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "arc=arc.server:main",
        ],
    },
)
