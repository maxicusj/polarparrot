from setuptools import setup, find_packages

# Read the contents of your README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="polarparrot",  
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    author="Roman Maxymchuk",
    author_email="rom555@me.com",
    description="Modular YAML based portfolio analytics calculation engine",
    long_description=long_description,  # Use the README.md file as the long description
    long_description_content_type="text/markdown",  # README format
    url="https://github.com/maxicusj/polarparrot",  # GitHub repo URL
    project_urls={
        "Bug Tracker": "https://github.com/maxicusj/polarparrot/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",  # Replace with your license
        "Operating System :: OS Independent",
    ],
    packages=find_packages(include=["polarparrot", "polarparrot.*"]),
    python_requires=">=3.11",  # Minimum Python version required
    install_requires=[
        "pyodbc>=5.2.0",  # Add your dependencies here (e.g., 'requests>=2.25.1')
        "PyYAML>=6.0.2",
        "pyarrow>=18.0.0",
        "polars>=1.14.0"
    ],
    # entry_points={
    #     "console_scripts": [
    #         "my-command=my_package.module:main",  # Replace with your CLI commands
    #     ],
    # },
    include_package_data=True  # Include files listed in MANIFEST.in
)
