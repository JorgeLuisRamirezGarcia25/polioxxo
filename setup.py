from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="polioxxo",
    version="1.0.0",
    author="Jorge Luis Ramirez Garcia",
    author_email="jorge.ramirez@example.com",
    description="Análisis geoespacial de tiendas Oxxo en Ciudad de México por alcaldías con datos electorales",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/JorgeLuisRamirezGarcia25/polioxxo",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: GIS",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "polioxxo=scripts.main:main",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/JorgeLuisRamirezGarcia25/polioxxo/issues",
        "Source": "https://github.com/JorgeLuisRamirezGarcia25/polioxxo",
        "Documentation": "https://github.com/JorgeLuisRamirezGarcia25/polioxxo#readme",
    },
)
