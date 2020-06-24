from setuptools import setup, Extension


class get_pybind_include(object):
    '''Helper class to determine the pybind11 include path

    The purpose of this class is to postpone importing pybind11
    until it is actually installed, so that the ``get_include()``
    method can be invoked. '''
    def __init__(self, user=False):
        self.user = user

    def __str__(self):
        import pybind11
        return pybind11.get_include(self.user)


setup(
    name="auto-install-test",
    ext_modules=[
        Extension(
            'example',
            sources=['example.cpp'],
            include_dirs=[
                # Path to pybind11 headers
                get_pybind_include(),
                get_pybind_include(user=True)
            ],
            language='c++')
    ],
    long_description='Testing CI upload to Pypi',
    long_description_content_type='text/x-rst',
    version="0.3.0",
    packages=setuptools.find_packages(),
)
