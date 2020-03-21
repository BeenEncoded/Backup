'''
Miscellaneous tests
'''
import unittest, queue

class MiscTestCase(unittest.TestCase):
    def test_queue(self) -> None:
        q = queue.Queue(0)
        for x in range(0, 100):
            q.put(x)
        print(f"Length of queue: {str(q.qsize())}")