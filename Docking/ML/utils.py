from tensorflow.python.client import device_lib


def get_available_gpus():
    local_device_protos = device_lib.list_local_devices()
    return [x.name for x in local_device_protos if x.device_type == 'GPU']


def read_tuner_config(path):
    with open(path) as config:
        values = {}
        comment = "<<"
        for line in config.readlines():
            line = line.strip(" ").strip("\n")
            if comment not in line and len(line) > 1:
                split = line.split("=")
                if len(split) > 1:
                    key = split[0]
                    value = split[1]
                else:
                    key = split[0]
                    value = ""

                try:
                    value = int(value)
                except ValueError:
                    pass
                values[key] = value
        return values
