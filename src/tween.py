import math
import time

def interpolate(a, b, c):
    return a + (b - a) * c

def linear(x):
    return x

def quad(x):
    return x * x

def cubic(x):
    return x * x * x

def quint(x):
    return x * x * x * x

def sine(x):
    return math.sin((0.5 * math.pi) * (x))

def cosine(x):
    return math.cos((0.5 * math.pi) * (x))

style = {
    "linear" : linear,
    "quad" : quad,
    "cubic" : cubic,
    "quint" : quint,
    "sine" : sine,
    "cosine" : cosine
}

instances = list()

class Tween():
    playing = False
    ease = None
    tick = 0
    interval = 0

    initial = {}
    current = {}
    final = {}

    def __init__(self, initial = {}, final = {}, ease = "linear"):
        self.initial = initial.copy()
        self.current = initial
        self.final = final
        self.ease = ease

    def play(self, duration = 0):
        self.tick = time.monotonic()
        self.interval = duration
        self.playing = True
        instances.append(self)
    
    def stop(self):
        self.playing = False
        instances.remove(self)

    def updatez(self):
        delta = (time.monotonic() - self.tick) / self.interval
        if (delta >= 1):
            delta = 1
            self.stop()

        for key in self.final.keys():
            self.current[key] = interpolate(
                self.initial[key],
                self.final[key],
                style[self.ease](delta)
            )


