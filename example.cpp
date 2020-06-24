// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/complex.h>
#include <pybind11/stl.h>
#include <pybind11/pytypes.h>
#include <vector>
#include <complex>
#include <iostream>
#if defined(_OPENMP)
#include <omp.h>
#endif

namespace py = pybind11;

class Simulator
{
public:
    Simulator(unsigned int seed): seed_(seed) {}

    int allocate_qubit() { return 42; }
    void deallocate_qubit() { }
    
private:
    unsigned int seed_;
};

PYBIND11_MODULE(example, m) {
     m.doc() = "C++ simulator backend for ProjectQ";
     
     py::class_<Simulator>(m, "Simulator")
	  .def(py::init<unsigned>())
	  .def("allocate_qubit", &Simulator::allocate_qubit)
	  .def("deallocate_qubit", &Simulator::deallocate_qubit)
	  ;
}
