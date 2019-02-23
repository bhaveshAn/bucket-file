"""
Bucket Fill Exercise

Imagine you are working on an image editing application.
You need to implement a bucket fill tool similar to the one
in paint. The user will use the tool by selecting a color
and clicking on the canvas. The tool fills the selected
region of color with the new color.

When a pixel is filled, all of its neighbors
(above, below, left, or right) of the same color must also be filled,
as well as their neighbors, and so on, until the entire region
has been filled with the new color.

In this exercise, you must write *TWO* implementations of the tool.
Each implementation must be different. It is not
required that you invent the solutions yourself.
You are encouraged to research the problem. Please write documentation
explaining the difference of each implementation,
such as when one solution might be more appropriate than the other.
Don't forget to validate input. There is one existing test,
however, you might consider adding some more. Keep in mind
that although the given canvas is small, the solution should
be applicable for a real canvas that could have huge
resolutions.

Please use python3 to complete this assignment.
"""

import time
import unittest

timing_count = 0


def timing(f):
    """
    Simple annotation to keep track of the time spent calculating.
    It's a bit hacky due to the global
    variable but it's a simple solution for this case.
    """
    def wrap(*args):
        time1 = time.time()
        ret = f(*args)
        time2 = time.time()
        args[0].timing_count += (time2 - time1) * 1000.0
        return ret
    return wrap


class Canvas(object):
    """
    Parent canvas with some commond method and fill method definition.
    It has some tooling to keep track of the data access and validation.
    Must be extended by the concrete implementations.
    """
    class access_count_array(list):
        """
        Access counter for image matrix.
        """

        def set_parent(self, parent):
            self.parent = parent

        def __getitem__(self, index):
            self.parent.pixel_comparisons += 1
            return list.__getitem__(self, index)

    def __init__(self, pixels):
        self.pixels = Canvas.access_count_array(pixels)
        self.pixels.set_parent(self)
        self.pixel_comparisons = 0
        self.timing_count = 0

    def __str__(self):
        return '\n'.join(map(lambda row: ''.join(map(str, row)), self.pixels))

    def validate(self, x, y, color):
        """
        Common validation for the fill input

        :param x:  the x coordinate where the user clicked
        :param y: the y coordinate where the user clicked
        :param color: the specified color to change the region to
        """

        # check that the seed value are integers
        if not isinstance(x, int) or not isinstance(y, int):
            raise ValueError(
                "Invalid pixel seed format. Expecting integers {},{}".format(
                    x, y))

        # check that the seed value are within the image interval
        if x < 0 or x >= len(self.pixels) \
                or y < 0 or y >= len(self.pixels[0]):
            raise ValueError(
                "Invalid pixel seed for flood fill {},{}".format(
                    x, y))

        # check that the image has a size
        if len(self.pixels) == 0 or len(self.pixels[0]) == 0:
            raise ValueError("Image has an empty dimension")

        # check that the image has consistent sizes accross its dimensions
        len_h = len(self.pixels[0])

        if any([len_h != len(pixels) for pixels in self.pixels]):
            raise ValueError(
                "Invalid image. Rows and columns have inconsistent sizes"
            )

        # check that the new color is the same type of the pixels
        data_type = type(self.pixels[0][0])

        # This check is not always valid. numpy uses uint8 integers
        # while the user can be in int format
        # The algorithm is still able to run properly
        # check that all image pixels have the same type
        for t in self.pixels:
            for y in t:
                if type(y) is not data_type:
                    raise ValueError("Image contains inconsistent data")

    def fill(self, x, y, color):
        """
        Fills a region of color at a given location with a given color.

        :param x:  the x coordinate where the user clicked
        :param y: the y coordinate where the user clicked
        :param color: the specified color to change the region to
        """
        raise NotImplementedError


class Solution1(Canvas):
    """
    This is similar to the RecursiveSolution except it uses a queue to avoid
    recursion. The flooding type is breadth first since it tries to expand
    from the starting point out to the edges.
    """
    @timing
    def fill(self, x, y, color):
        self.validate(x, y, color)
        h = len(self.pixels[0])
        w = len(self.pixels)
        old_color = self.pixels[x][y]

        if old_color == color:
            return

        edge = [(x, y)]
        self.pixels[x][y] = color
        while edge:
            newedge = []
            for (x, y) in edge:
                for (s, t) in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= s < w and 0 <= t < h and self.pixels[s][t] == old_color:
                        self.pixels[s][t] = color
                        newedge.append((s, t))
            edge = newedge


class Solution2(Canvas):
    """
    This bucket fill solution address the problem using recursion.
    At each iteration all the current neighbours are added to the
    recursion stack, if the current point
    needs to be filled.
    """

    def _fill(self, x, y, color, old_color):
        """
        Support recursive method.
        """
        h = len(self.pixels[0])
        w = len(self.pixels)

        if self.pixels[x][y] == old_color:
            self.pixels[x][y] = color

            if x > 0:
                self._fill(x - 1, y, color, old_color)  # left
            if x < w - 1:
                self._fill(x + 1, y, color, old_color)  # right
            if y > 0:
                self._fill(x, y - 1, color, old_color)  # up
            if y < h - 1:
                self._fill(x, y + 1, color, old_color)  # down

    @timing
    def fill(self, x, y, color):
        self.validate(x, y, color)
        old_color = self.pixels[x][y]

        if old_color == color:
            pass
        try:
            self._fill(x, y, color, old_color)
        except RuntimeError:
            print("Overflow reached")


class TestBase():
    """
    This test suit is made to test the floodfill functionalities
    and it keeps track of timing and loop count.
    """
    def setUp(self):
        global timing_count
        timing_count = 0
        self.canvas = None

    def tearDown(self):
        """
        Save run information
        """
        method_name = self.id().split('.')[-1]
        timing_results[self.impl][method_name] = {
            'array_access': self.canvas.pixel_comparisons,
            'timing': self.canvas.timing_count}

    def test_big_image(self):
        """
        Test the behavior on big images
        """
        img = [['O'] * 100] * 100

        self.canvas = self.impl(img)
        self.canvas.fill(0, 1, '*')
        self.assertTrue(all([all(pixel == '*' for pixel in line)
                        for line in self.canvas.pixels]))

    def test_fill_same_color(self):
        """
        Test that it only support 4-way connection as specified in the test
        """
        self.canvas = self.impl([['O', 'X', 'O'],
                                 ['X', 'O', 'O'],
                                 ['X', 'X', 'X']])

        self.canvas.fill(1, 0, 'X')
        self.assertTrue(str(self.canvas) == 'OXO\nXOO\nXXX')

    def test_basic_solution(self):
        """
        Test the correct behavior of the method
        """
        self.canvas = self.impl([['O', 'X']])
        self.canvas.fill(0, 1, 'O')
        self.canvas.fill(0, 0, 'O')
        self.assertTrue(str(self.canvas) == 'OO')

    def test_basic_solution_as_array(self):
        """
        Test the correct behavior of the method
        """
        self.canvas = self.impl([['O', 'X', 'O', 'X', 'X', 'X']])
        self.canvas.fill(0, 1, 'O')
        self.assertTrue(str(self.canvas) == 'OOOXXX')

    def test_solution(self):
        """
        Test the correct behavior of the method
        """
        self.canvas = self.impl([
            ['O', 'X', 'X', 'X', 'X'],
            ['X', 'O', 'O', 'O', 'X'],
            ['X', 'O', '#', 'O', 'X'],
            ['X', 'O', 'O', 'O', 'X'],
            ['X', 'X', 'X', 'X', 'X'],
            ['X', 'X', 'X', '#', '#'],
            ['X', 'X', 'X', 'X', 'X'],
            ])
        self.canvas.fill(0, 1, '*')
        self.canvas.fill(5, 4, 'O')
        self.canvas.fill(2, 2, '@')
        self.assertTrue(
           str(self.canvas),
           'O****\n*OOO*\n*O@O*\n*OOO*\n*****\n***OO\n*****'
        )

    def test_inconsistent_dims_input(self):
        """
        Test corner cases
        """
        with self.assertRaises(ValueError):
            self.canvas = self.impl([[0, 0], [1]])
            self.canvas.fill(0, 0, 'a')


timing_results = {Solution1: {},
                  Solution2: {}
                  }


class TestEdgeSolution(TestBase, unittest.TestCase):
    """
    Test suite for EdgeSolution
    """
    impl = Solution1


class TestRecursive(TestBase, unittest.TestCase):
    """
    Test suite for Recursive solution
    """
    impl = Solution2


if __name__ == '__main__':
    unittest.main()
