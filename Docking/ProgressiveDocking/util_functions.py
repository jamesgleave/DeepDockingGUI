

def lerp(a, b, c):
    """
    Linearly interpolates between a and b at point c. Where lerp(a, b, 0) = a and lerp(a, b, 1) = b.
    """
    assert 0 <= c <= 1, "c must be between 0 and 1"
    return (b*c) + ((1-c) * a)


def seconds_to_datetime(seconds):
    """
    Updates the information from seconds to 00:00:00 time

    :param seconds:
    :return:
    """
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    h, m, s = int(h), int(m), int(s)

    if h < 0:
        h = m = s = 0

    if h < 10:
        h = "0" + str(h)
    else:
        h = str(h)

    if m < 10:
        m = "0" + str(m)
    else:
        m = str(m)

    if s < 10:
        s = "0" + str(s)
    else:
        s = str(s)
    return h, m, s


def datetime_string_to_seconds(dt):
    """
    Converts a datetime string like "00-04:00" into seconds.
    datetime_string_to_seconds("00-04:00") = 14400
    :param dt:
    :return:
    """
    days = int(dt[0:2])
    hours = int(dt[3:5])
    minutes = int(dt[6:8])
    seconds = 60 * minutes + 60*60 * hours + 60*60*60 * days
    return seconds
