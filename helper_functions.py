
def clip(value, min, max):
    if (value > max):
        return max
    elif(value < min):
        return min
    return value