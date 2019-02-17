import random


def x_forwarded_for() -> str:
    return str(random.randint(0, 255)) + '.' + str(random.randint(0, 255)) + '.' + str(
        random.randint(0, 255)) + '.' + str(random.randint(0, 255))
