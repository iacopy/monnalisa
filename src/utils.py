"""
Incremental averageing.

Calculate mean accumulatively.
https://math.stackexchange.com/questions/106700/incremental-averageing
"""


class AccumulativeMean:
    """
    Calculate mean knowing only the new incoming value,
    the current mean and the current count of data.
    """
    def __init__(self, mean=0, count=0, round_digits=4):
        self.mean = mean
        self.count = count
        self.round_digits = round_digits

    def __repr__(self):
        return 'UM[{}]({})'.format(self.count, self.mean)

    def __add__(self, new_value):
        """Useful with a `collections.Counter`."""
        self.update(new_value)
        return self

    def __lt__(self, other):
        """To be used with '<' operator (-> Counter.most_common() uses '<')
        """
        return self.mean < other.mean

    def update(self, new_value):
        """
        Update mean.

        :param new_value: new value
        :rtype: float
        """
        self.count += 1
        new_mean = self.mean + (new_value - self.mean) / self.count
        self.mean = round(new_mean, self.round_digits)
        return self.mean

    def get_current(self):
        """Return the current mean value."""
        return self.mean

    def get_count(self):
        """
        Return the current count of numbers.

        Note that the actual list of numbers is not stored.
        """
        return self.count
