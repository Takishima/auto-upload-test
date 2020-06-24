import setuptools
from distutils.errors import (CompileError, LinkError, CCompilerError,
                              DistutilsExecError, DistutilsPlatformError)
from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext
import sys
import os
import subprocess
import platform


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

class BuildFailed(Exception):
    def __init__(self):
        self.cause = sys.exc_info()[1]  # work around py 2/3 different syntax

def important_msgs(*msgs):
    print('*' * 75)
    for msg in msgs:
        print(msg)
    print('*' * 75)


def status_msgs(*msgs):
    print('-' * 75)
    for msg in msgs:
        print('# INFO: ', msg)
    print('-' * 75)


def compiler_test(compiler,
                  flagname=None,
                  link=False,
                  include='',
                  body='',
                  postargs=None):
    '''
    Return a boolean indicating whether a flag name is supported on the
    specified compiler.
    '''
    import tempfile
    f = tempfile.NamedTemporaryFile('w', suffix='.cpp', delete=False)
    f.write('{}\nint main (int argc, char **argv) {{ {} return 0; }}'.format(
        include, body))
    f.close()
    ret = True

    if postargs is None:
        postargs = [flagname] if flagname is not None else None
    elif flagname is not None:
        postargs.append(flagname)

    try:
        exec_name = os.path.join(tempfile.mkdtemp(), 'test')

        if compiler.compiler_type == 'msvc':
            olderr = os.dup(sys.stderr.fileno())
            err = open('err.txt', 'w')
            os.dup2(err.fileno(), sys.stderr.fileno())

        obj_file = compiler.compile([f.name], extra_postargs=postargs)
        if not os.path.exists(obj_file[0]):
            raise RuntimeError('')
        if link:
            compiler.link_executable(obj_file,
                                     exec_name,
                                     extra_postargs=postargs)

        if compiler.compiler_type == 'msvc':
            err.close()
            os.dup2(olderr, sys.stderr.fileno())
            with open('err.txt', 'r') as err_file:
                if err_file.readlines():
                    raise RuntimeError('')
    except (CompileError, LinkError, RuntimeError):
        ret = False
    os.unlink(f.name)
    return ret

cpython = platform.python_implementation() == 'CPython'
ext_errors = (CCompilerError, DistutilsExecError, DistutilsPlatformError)
if sys.platform == 'win32':
    # 2.6's distutils.msvc9compiler can raise an IOError when failing to
    # find the compiler
    ext_errors += (IOError, )

class BuildExt(build_ext):
    '''A custom build extension for adding compiler-specific options.'''
    c_opts = {
        'msvc': ['/EHsc'],
        'unix': [],
    }

    def run(self):
        try:
            build_ext.run(self)
        except DistutilsPlatformError:
            raise BuildFailed()

    def build_extensions(self):
        self._configure_compiler()
        for ext in self.extensions:
            ext.extra_compile_args = self.opts
            ext.extra_link_args = self.link_opts
        try:
            build_ext.build_extensions(self)
        except ext_errors:
            raise BuildFailed()
        except ValueError:
            # this can happen on Windows 64 bit, see Python issue 7511
            if "'path'" in str(sys.exc_info()[1]):  # works with both py 2/3
                raise BuildFailed()
            raise

    def _configure_compiler(self):
        ct = self.compiler.compiler_type
        self.opts = self.c_opts.get(ct, [])
        self.link_opts = []

        if not compiler_test(self.compiler):
            important_msgs(
                'ERROR: something is wrong with your C++ compiler.\n'
                'Failed to compile a simple test program!')
            raise BuildFailed()

        # ------------------------------

        status_msgs('Configuring OpenMP')
        self._configure_openmp()
        status_msgs('Configuring compiler intrinsics')
        self._configure_intrinsics()
        status_msgs('Configuring C++ standard')
        self._configure_cxx_standard()

        # ------------------------------
        # Other compiler tests

        status_msgs('Other compiler tests')
        if ct == 'unix':
            if compiler_test(self.compiler, '-fvisibility=hidden'):
                self.opts.append('-fvisibility=hidden')
            self.opts.append("-DVERSION_INFO=\"{}\"".format(
                self.distribution.get_version()))
        elif ct == 'msvc':
            self.opts.append("/DVERSION_INFO=\\'{}\\'".format(
                self.distribution.get_version()))

        status_msgs('Finished configuring compiler!')

    def _configure_openmp(self):
        if self.compiler.compiler_type == 'msvc':
            return

        kwargs = {
            'link': True,
            'include': '#include <omp.h>',
            'body': 'int a = omp_get_num_threads(); ++a;'
        }

        for flag in ['-openmp', '-fopenmp', '-qopenmp', '/Qopenmp']:
            if compiler_test(self.compiler, flag, **kwargs):
                self.opts.append(flag)
                self.link_opts.append(flag)
                return

        flag = '-fopenmp'
        if (sys.platform == 'darwin' and compiler_test(self.compiler, flag)):
            try:
                llvm_root = subprocess.check_output(
                    ['brew', '--prefix', 'llvm']).decode('utf-8')[:-1]
                compiler_root = subprocess.check_output(
                    ['which', self.compiler.compiler[0]]).decode('utf-8')[:-1]

                # Only add the flag if the compiler we are using is the one
                # from HomeBrew
                if llvm_root in compiler_root:
                    l_arg = '-L{}/lib'.format(llvm_root)
                    if compiler_test(self.compiler,
                                     flag,
                                     postargs=[l_arg],
                                     **kwargs):
                        self.opts.append(flag)
                        self.link_opts.extend((l_arg, flag))
                        return
            except subprocess.CalledProcessError:
                pass

            try:
                # Only relevant for MacPorts users with clang-3.7
                port_path = subprocess.check_output(['which', 'port'
                                                     ]).decode('utf-8')[:-1]
                macports_root = os.path.dirname(os.path.dirname(port_path))
                compiler_root = subprocess.check_output(
                    ['which', self.compiler.compiler[0]]).decode('utf-8')[:-1]

                # Only add the flag if the compiler we are using is the one
                # from MacPorts
                if macports_root in compiler_root:
                    c_arg = '-I{}/include/libomp'.format(macports_root)
                    l_arg = '-L{}/lib/libomp'.format(macports_root)

                    if compiler_test(self.compiler,
                                     flag,
                                     postargs=[c_arg, l_arg],
                                     **kwargs):
                        self.opts.extend((c_arg, flag))
                        self.link_opts.extend((l_arg, flag))
                        return
            except subprocess.CalledProcessError:
                pass

        important_msgs('WARNING: compiler does not support OpenMP!')

    def _configure_intrinsics(self):
        for flag in [
                '-march=native', '-mavx2', '/arch:AVX2', '/arch:CORE-AVX2',
                '/arch:AVX'
        ]:
            if compiler_test(
                    self.compiler,
                    flagname=flag,
                    link=False,
                    include='#include <immintrin.h>',
                    body='__m256d neg = _mm256_set1_pd(1.0); (void)neg;'):

                if sys.platform == 'win32':
                    self.opts.extend(('/DINTRIN', flag))
                else:
                    self.opts.extend(('-DINTRIN', flag))
                break

        for flag in ['-ffast-math', '-fast', '/fast', '/fp:precise']:
            if compiler_test(self.compiler, flagname=flag):
                self.opts.append(flag)
                break

    def _configure_cxx_standard(self):
        if self.compiler.compiler_type == 'msvc':
            return

        cxx_standards = [17, 14, 11]
        if sys.version_info[0] < 3:
            cxx_standards = [year for year in cxx_standards if year < 17]

        if sys.platform == 'darwin':
            _, minor_version, _ = [
                int(i) for i in platform.mac_ver()[0].split('.')
            ]
            if minor_version < 14:
                cxx_standards = [year for year in cxx_standards if year < 17]

        for year in cxx_standards:
            flag = '-std=c++{}'.format(year)
            if compiler_test(self.compiler, flag):
                self.opts.append(flag)
                return
            flag = '/Qstd=c++{}'.format(year)
            if compiler_test(self.compiler, flag):
                self.opts.append(flag)
                return

        important_msgs('ERROR: compiler needs to have at least C++11 support!')
        raise BuildFailed()


setup(
    name="auto-install-test",
    ext_modules=[
        Extension(
            'package.example',
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
    cmdclass={'build_ext': BuildExt},
    packages=find_packages(),
)
