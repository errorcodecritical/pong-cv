import numpy as np

class Transform2D:
    components = np.array((
        (1, 0, 0), # RightVector
        (0, 1, 0), # UpVector
        (0, 0, 1)  # Position
    ))

    def right(self):
        return np.array((self.components[0][0], self.components[0][1]))

    def up(self):
        return np.array((self.components[1][0], self.components[1][1]))

    def position(self):
        return np.array((self.components[2][0], self.components[2][1]))

    def size(self):
        return np.array((np.linalg.norm(self.right()), np.linalg.norm(self.up())))

    def __init__(self, position = (0, 0), right = (1, 0), up = (0, 1)):
        self.components = np.array((
            (right[0], right[1], 0),
            (up[0], up[1], 0),
            (position[0], position[1], 1)
        ))

    def __add__(self, other):
        result = Transform2D()
        result.components = self.components + np.array((
            (0, 0, 0), # RightVector
            (0, 0, 0), # UpVector
            (other[0], other[1], 0) # Position
        ))
        return result

    def __sub__(self, other):
        result = Transform2D()
        result.components = self.components - np.array((
            (0, 0, 0), # RightVector
            (0, 0, 0), # UpVector
            (other[0], other[1], 0) # Position
        ))
        return result

    def __mul__(self, other):
        result = Transform2D()
        result.components = np.dot(self.components, other.components)
        return result


