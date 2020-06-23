from setuptools import setup, Extension

setup(
    name="auto-install-test",
    ext_modules=[Extension('example', sources=['example.cpp'])],
    long_description='Testing CI upload to Pypi',
    long_description_content_type='text/x-rst',
    version="0.2.0",
)
