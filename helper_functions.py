
def clip(value, min, max):
    if (value > max):
        return max
    elif(value < min):
        return min
    return value

def wrap(value, min, max):
    range_size = max - min
    while value < min:
        value += range_size
    while value >= max:
        value -= range_size
    return value