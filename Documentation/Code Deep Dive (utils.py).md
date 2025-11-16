# Code Deep Dive: `utils.py`

First, the necessary module, `math`, is imported.
```Python
import math
```

The function `lerp(a, b, t)` is defined. This is used for *linear interpolation*, or the calculation of a point along the straight line between two values, `a` and `b`, based on a parameter `t`. How this works is that `a` and `b` define the begining and end of a straight line, while the parameter `t` defines how far along the line to place the new point in terms of percent. The formula, `a + (b - a) * t`, calculates exact value you land on after traveling that specific proportion `t` of the total distance.
```Python
def lerp(a, b, t):
    return a + (b - a) * t
```

The function `lerp_angle(a, b, t)` is similar to `lerp`, but it handles angles in radians instead of linear distance. It calculates a point between two angles, `a` and `b`, taking the shortest path around a circle. Let's say we have a circle, with possible angle values from zero to 2&#960;. The vaues `a` and `b`are the starting and ending angle, respectively. The parameter `t` is the proportion of the circle we want to travel in the form of a percent. The value `diff` is the difference between `b` and `a`, modulo 2&#960;. If `diff` is greater than 2&#960;, it means we've gone past the end of the circle, so we subtract 2&#960; from `diff` to get the correct value. It then returns the *linear interpolation* of `a` and `b` based on `t`; our point along the circle.
```Python
def lerp_angle(a, b, t):
    diff = (b - a) % (2 * math.pi)
    if diff > math.pi:
        diff -= 2 * math.pi
    return a + diff * t
```

The function `smoothstep(edge0, edge1, x)` creates a smooth transition between two values instead of changing at a constant speed. The values `edge0` and `edge1` define the start and end of the range, and `x` is the input to be mapped into that range. The function first returns `0.0` if `edge0` and `edge1` are the same, to avoid dividing by zero. It then maps `x` into a `t` value between 0 and 1 and clamps it so it cannot go outside that range. Finally, it applies the formula `t * t * (3.0 - 2.0 * t)` to ease in and out, giving a smooth value between 0 and 1 that can be used for blending or animations.
```Python
def smoothstep(edge0, edge1, x):
    if edge0 == edge1:
        return 0.0
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)
```

The function `small_hash_to_phase_amp(s)` turns a short string `s` into two numbers: a `phase` (an angle in radians) and an `amp` (an amplitude or strength). This lets you take something like a name and always get the same “random‑looking” phase and amplitude from it. The function builds an integer hash `h` by combining the characters in the string. It then uses that hash to create a `phase` between `0` and `2π` and an `amp` in a range centered a bit above 1. The returned `(phase, amp)` pair can be used to give different players, objects, or effects unique but repeatable variations.
```Python
def small_hash_to_phase_amp(s):
    h = 0
    for ch in s:
        h = (h * 31 + ord(ch)) & 0xffffffff
    phase = float((h % 1000)) / 1000.0 * math.pi * 2.0
    amp = 0.7 + ((h >> 10) % 50) / 100.0
    return phase, amp
```