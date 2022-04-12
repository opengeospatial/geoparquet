from setuptools import setup, find_packages

setup(
    name="geoparquet_validator",
    version="0.0.1",
    install_requires=[
        "jsonschema==4.4.0",
        "pyarrow==7.0.0",
        "fsspec==2022.3.0",
        "requests==2.27.1",
        "aiohttp==3.8.1",
        "click==8.1.2",
        "colorama==0.4.4"
    ],
    packages=find_packages(),
    package_data={
        "geoparquet_validator": ["schema.json"]
    },
    entry_points={
        "console_scripts": [
            "geoparquet_validator=geoparquet_validator:main"
        ]
    }
)
