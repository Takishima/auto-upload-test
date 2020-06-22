from setuptools import setup, Extension

setup(
    name="auto-install-test",
    ext_modules=[Extension('example', sources=['example.cpp'])],
    version="0.1.0",
)
