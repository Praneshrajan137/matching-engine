"""Setup configuration for order-gateway package"""

from setuptools import setup, find_packages

setup(
    name="order-gateway",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.11",
)

