from setuptools import setup, find_packages

setup(
    name="geoparquet_validator",
    version="0.0.1",
    install_requires=[
        "jsonschema>=4.4",
        "pyarrow>=7.0",
        "fsspec>=2022.3",
        "requests>=2.27",
        "aiohttp>=3.8",
        "click>=8.1",
        "colorama>=0.4"
    ],
    extras_require={
        "s3": ["s3fs"],
        "gcs": ["gcsfs"]
    },
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
