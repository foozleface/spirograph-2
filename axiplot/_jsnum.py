"""The three JavaScript numeric behaviours this package's string output needs.

Vendored, deliberately. ``axiplot`` has to stand on its own in other programs,
and these are 60 lines against a dependency on a whole generator port. The
canonical copy is ``busy/jsnum.py`` in busy-python (which has the full set and
its own 680-check gate); the two are held together by the plot-transforms
fixture, which was captured from the JS and compares these outputs byte for
byte. If you change one, the fixture will tell you about the other.
"""

import math

INF = float("inf")


def js_round(x):
    """``Math.round``: halves go toward +Infinity, not to even.

    Python's ``round`` is banker's rounding, so ``round(0.5)`` is 0 where JS
    gives 1. The obvious replacement ``floor(x + 0.5)`` is also wrong: for
    ``x = 0.49999999999999994`` the addition rounds up to exactly 1.0 and yields
    1, while the spec (and V8) give 0. Taking the floor first and comparing the
    exact fractional part avoids that.
    """
    if x != x or x == INF or x == -INF:
        return x
    floor = math.floor(x)
    return float(floor + 1) if x - floor >= 0.5 else float(floor)


def _shortest_digits(x):
    """Return ``(digits, n)`` with ``x == 0.<digits> * 10**n`` and no trailing
    zeros in ``digits``. ``x`` must be finite and strictly positive.

    Python's repr is documented shortest-roundtrip, which is the same digit
    string ECMA-262 asks for; only the layout differs.
    """
    text = repr(float(x))
    if "e" in text:
        mantissa, _, exponent = text.partition("e")
        exponent = int(exponent)
    else:
        mantissa, exponent = text, 0
    integer, _, fraction = mantissa.partition(".")
    raw = integer + fraction
    stripped = raw.lstrip("0")
    # Leading zeros are placeholders, not significant digits: each one shifts the
    # decimal point left relative to where the integer part put it.
    n = len(integer) + exponent - (len(raw) - len(stripped))
    return stripped.rstrip("0"), n


def js_str(x):
    """``String(x)`` for a JS Number."""
    if isinstance(x, bool):                       # JS booleans are not numbers
        return "true" if x else "false"
    x = float(x)
    if x != x:
        return "NaN"
    if x == INF:
        return "Infinity"
    if x == -INF:
        return "-Infinity"
    if x == 0:                                    # covers -0.0, which JS prints as "0"
        return "0"
    sign = "-" if x < 0 else ""
    digits, n = _shortest_digits(abs(x))
    k = len(digits)

    if k <= n <= 21:                              # 1e7 -> "10000000"
        return sign + digits + "0" * (n - k)
    if 0 < n <= 21:                               # 12.75 -> "12.75"
        return sign + digits[:n] + "." + digits[n:]
    if -6 < n <= 0:                               # 1e-6 -> "0.000001"
        return sign + "0." + "0" * -n + digits
    # Exponential. The exponent is n-1 because `digits` is written as d.ddd.
    exponent = n - 1
    mantissa = digits if k == 1 else digits[0] + "." + digits[1:]
    return "%s%se%s%d" % (sign, mantissa, "+" if exponent >= 0 else "-", abs(exponent))


def js_truthy(v):
    """JS truthiness. The one that matters here is **NaN is falsy** -- Python's
    ``bool(float("nan"))`` is True, so ``h ? min(h, f) : f`` would take the wrong
    branch once ``h`` has gone NaN. ``0``, ``-0.0``, ``""``, ``None`` and
    ``False`` are the rest of the falsy set; every object, including an empty
    list or dict, is truthy.
    """
    if v is None or v is False:
        return False
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return not (v == 0 or v != v)
    if isinstance(v, str):
        return v != ""
    return True
