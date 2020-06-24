from package import foo
from example import Simulator

def test_one():
    assert Simulator(10).allocate_qubit() == 42
    assert True
