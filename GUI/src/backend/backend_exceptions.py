class NullProjectException(Exception):
    def __init__(self):
        pass

    def __str__(self):
        message = "No project is loaded into the backend. Load a project before starting the backend."
        return message


class NullDBError(Exception):
    def __init__(self):
        pass

    def __str__(self):
        message = "Cannot locate stored user data. Please reinstall DeepDocking."
        return message
