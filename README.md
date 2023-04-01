# bma-benchmark-py

Python benchmark library

<img src="https://img.shields.io/pypi/v/bma-benchmark.svg" /> <img src="https://img.shields.io/badge/license-MIT-green" /> <img src="https://img.shields.io/badge/python-3.5%20%7C%203.6%20%7C%203.7%20%7C%203.8-blue.svg" />


## Installation

```shell
pip3 install bma_benchmark
```

## Usage

```python
from bma_benchmark import Benchmark

benchmark = Benchmark()

@benchmark(base=True)
def my_function1():
    # do some job
    1 + 1

@benchmark(name='benchmark2')
def my_function2():
    # do some job
    1 * 1

benchmark.run()
# equal to
#benchmark.run(
#    number=100, precision=3, units='s', print_result=True, sort_result='desc')
```

![results](https://github.com/alttch/bma-benchmark-py/blob/main/run.png?raw=true)

### Decorator arguments

* **name** override benchmark name (default: function name)

* **base** use as the base benchmark to measure difference from (True/False)

### Benchmark.run() arguments

* **number** number of function executions

* **precision** digits after comma for numbers

* **units** min/max/avg units (s, ms, us or ns)

* **print_result** automatically print results (True/False)

* **sort_result** sort result in ascending (asc/a) or descending(desc/d) order,
  None to keep unsorted

## Calling sub-processes

The module can call sub-processes to measure difference between different
library versions in different virtual environments or between different
versions of Python interpreter.

### Primary script

```python
from bma_benchmark import Benchmark

benchmark = Benchmark()

# define some local benchmarks if required
@benchmark
def bench1():
    pass

benchmark.append_sub('./sub1.py')
benchmark.run()
```

### Secondary scripts

make sure the scripts have execution permission (chmod +x):

```python
#!/path/to/some/other/python

from bma_benchmark import Benchmark

benchmark = Benchmark()

# define benchmarks
@benchmark
def bench2():
    pass

benchmark.sub()
```

The secondary scripts can contain "base" argument in a decorator as well. The
"sub()" method outputs benchmark results to stdout in JSON format to
synchronize with the primary, so secondary benchmarks must not print anything.
