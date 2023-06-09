#!/usr/bin/env python3

__version__ = '0.0.6'

import time
import json
import os
import subprocess

from collections import OrderedDict
from pathlib import Path


def _get_multiplier(units):
    if units == 's':
        return 1
    elif units == 'ms':
        return 1_000
    elif units == 'us':
        return 1_000_000
    elif units == 'ns':
        return 1_000_000_000


class Target:

    def __init__(self, func, kind='func', name=None):
        self.func = func
        self.name = name or func.__name__
        self.kind = kind


class Benchmark:

    def __init__(self):
        self.targets = []
        self.base = None

    def run(self,
            number=100,
            precision=3,
            units='s',
            sort_result='desc',
            print_result=True,
            _full=True):
        """
        Run the benchmark

        Optional:
            number: number of function executions
            precision: digits after comma for numbers
            units: min/max/avg units (s, ms, us or ns)
            print_result: automatically print results (True/False)
            sort_result: sort result (a/asc, d/desc or None)

        Returns:
            dict of benchmark results

        Raises:
            RuntimeError: on sub-script execution failures
        """
        multiplier = _get_multiplier(units)
        if print_result:
            from rapidtables import format_table, FORMAT_GENERATOR_COLS
            from neotermcolor import colored, cprint
        result = []
        base_elapsed = None
        for target in self.targets:
            if print_result and target.kind in ['func', 'sub']:
                spacer = '-' * 4
                cprint(f'{spacer} {target.kind} {target.name} {spacer}',
                       color='grey')
            if target.kind == 'func':
                op_start = time.perf_counter()
                call_elapsed_min = None
                call_elapsed_max = None
                for _ in range(number):
                    call_start = time.perf_counter()
                    target.func()
                    call_elapsed = time.perf_counter() - call_start
                    if call_elapsed_min is None:
                        call_elapsed_min = call_elapsed
                    elif call_elapsed_min > call_elapsed:
                        call_elapsed_min = call_elapsed
                    if call_elapsed_max is None:
                        call_elapsed_max = call_elapsed
                    elif call_elapsed_max < call_elapsed:
                        call_elapsed_max = call_elapsed
                elapsed = time.perf_counter() - op_start
                row = OrderedDict()
                row['name'] = target.name
                row['sec'] = elapsed
                row['min'] = call_elapsed_min
                row['max'] = call_elapsed_max
                if _full:
                    row['iters/s'] = f'{round(number / elapsed):_}'
                    row['avg'] = elapsed / number
                if self.base == target.name:
                    base_elapsed = elapsed
                result.append(row)
            elif target.kind == 'sub':
                env = os.environ.copy()
                env['BMA_BENCHMARK_NUMBER'] = str(number)
                p = subprocess.run(target.func, env=env, capture_output=True)
                out = p.stdout.decode()
                err = p.stderr.decode()
                if p.returncode:
                    raise RuntimeError(
                        f'process exit code: {p.returncode}\n{err}')
                if out:
                    sub_result = json.loads(out)
                    if sub_result['base'] is not None and self.base is None:
                        self.base = sub_result['base']
                    for sub_row in sub_result['result']:
                        row = OrderedDict()
                        row['name'] = sub_row['name']
                        row['min'] = sub_row['min']
                        row['max'] = sub_row['max']
                        row['avg'] = sub_row['sec'] / number
                        row['sec'] = sub_row['sec']
                        row['iters/s'] = f'{round(number / row["sec"]):_}'
                        result.append(row)
                        if self.base == sub_row['name']:
                            base_elapsed = sub_row['sec']
            elif target.kind == 'file':
                p = Path(target.name)
                with open(p) as fh:
                    sub_result = json.load(fh)
                    sub_number = sub_result['number']
                    for sub_row in sub_result['result']:
                        row = OrderedDict()
                        row['name'] = f'{p.stem}.{sub_row["name"]}'
                        row['min'] = sub_row['min']
                        row['max'] = sub_row['max']
                        row['avg'] = sub_row['sec'] / sub_number
                        row['sec'] = sub_row['sec']
                        if self.base == row['name']:
                            base_elapsed = row['sec']
                        row['iters/s'] = f'{round(sub_number / row["sec"]):_}'
                        result.append(row)
        fout = os.getenv('OUT')
        if fout:
            with open(fout, 'w') as fh:
                json.dump(dict(result=result, number=number), fh)
        for row in result:
            if _full and base_elapsed:
                if row['name'] == self.base:
                    row['diff'] = ''
                    row['diff_col'] = None
                else:
                    if base_elapsed < row['sec']:
                        diff = 100 - base_elapsed / row['sec'] * 100
                        row['diff'] = f'-{diff:_.2f}%'
                        row['diff_col'] = 'red'
                    elif base_elapsed > row['sec']:
                        diff = base_elapsed / row['sec'] * 100 - 100
                        row['diff'] = f'+{diff:_.2f}%'
                        row['diff_col'] = 'green'
                    else:
                        row['diff'] = '0%'
                        row['diff_col'] = None
            if print_result:
                fmt = f'{{:_.{precision}f}}'
                for col in ['min', 'max', 'avg']:
                    row[f'{col} {units}'] = fmt.format(row[col] * multiplier)
                    del row[col]
                row.move_to_end('sec')
                row.move_to_end('iters/s')
                try:
                    row.move_to_end('diff')
                except KeyError:
                    pass
        if sort_result == 'asc' or sort_result == 'a':
            result = sorted(result, key=lambda k: k['sec'], reverse=True)
        elif sort_result == 'desc' or sort_result == 'd':
            result = sorted(result, key=lambda k: k['sec'])
        if base_elapsed and print_result:
            diff_col = [row.pop('diff_col') for row in result]
        if print_result:
            for row in result:
                row['sec'] = fmt.format(row['sec'])
        if print_result and result:
            header, rows = format_table(result, fmt=FORMAT_GENERATOR_COLS)
            spacer = '  '
            print(colored(spacer.join(header), color='blue'))
            print(
                colored('-' * sum([(len(x) + 2) for x in header]),
                        color='grey'))
            for (i, r) in enumerate(rows):
                print(r[0] + spacer, end='')
                print(colored(r[1], color='green'), end=spacer)
                print(colored(r[2], color='cyan'), end=spacer)
                print(colored(r[3], color='white'), end=spacer)
                print(colored(r[4], color='blue'), end=spacer)
                if len(r) == 7:
                    print(colored(r[5], color='yellow'), end=spacer)
                    print(colored(r[6], color=diff_col[i]))
                else:
                    print(colored(r[5], color='yellow'))
        if fout:
            print()
            print(f'The result has been saved into',
                  colored(fout, color='cyan', attrs='bold'))
        return result

    def __call__(self, f=None, **kwargs):

        def inner(f):
            self.append(f, **kwargs)

            def bm_func(f):
                f()

            return bm_func

        if f:
            self.append(f, **kwargs)
        return inner

    def append(self, func, name=None, base=False):
        """
        Manually append a target function

        Args:
            func: function to execute

        Optional:
            name: override the name
            base: define the base benchmark
        """
        target = Target(func, name=name)
        self.targets.append(target)
        if base:
            self.base = target.name

    def append_sub(self, path):
        """
        Append sub-script

        Args:
            path: command path
        """
        target = Target(path, kind='sub', name=path)
        self.targets.append(target)

    def append_file(self, path):
        """
        Append results from a file

        Args:
            path: file path
        """
        target = Target(path, kind='file', name=path)
        self.targets.append(target)

    def sub(self):
        """
        Must be called method in sub-scripts
        """
        print(
            json.dumps(
                dict(result=self.run(number=int(
                    os.getenv('BMA_BENCHMARK_NUMBER')),
                                     print_result=False,
                                     sort_result=None,
                                     _full=False),
                     base=self.base)))


benchmark = Benchmark()
