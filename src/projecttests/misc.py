'''
Miscellaneous tests
'''
import unittest, time, threading
from threads import CoroutineThread

barrier = threading.Barrier(3, timeout=5)

class MiscTestCase(unittest.TestCase):
    
    @unittest.skip("skipping")
    def test_coroutine(self) -> None:
        with CoroutineThread(test_function, 100, 10, 20, '-') as op1, \
            CoroutineThread(test_function, 200, 5, 30, '+') as op2, \
            CoroutineThread(test_function, 300, int(10 / 3), 40, '_') as op3:
            radd1, compl1 = op1.getReturnValue()
            print(f"radd1: {repr(radd1)}  compl1: {repr(compl1)}")
            radd2, compl2 = op2.getReturnValue()
            print(f"radd2: {repr(radd2)}  compl2: {repr(compl2)}")
            radd3, compl3 = op3.getReturnValue()
            print(f"radd3: {repr(radd3)}  compl3: {repr(compl3)}")
            print("FINISHED:")

def test_function(arg1, arg2, arg3, c) -> int:
    barrier.wait()
    print(f"Arg1: {arg1}  Arg2: {arg2}  Arg3: {arg3}")
    y = 0
    for x in range(0, (arg1 * arg2)):
        y += x
        if y % 10 == 0: print(c, end='')
        time.sleep(1 / 1000)

    return (arg1 + arg2 + arg3), y