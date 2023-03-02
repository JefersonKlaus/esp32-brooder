def scale_value(
    value: float, in_min: float, in_max: float, out_min: float, out_max: float
):
    scaled_value = (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
    return scaled_value
