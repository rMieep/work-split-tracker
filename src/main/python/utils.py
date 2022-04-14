from fbs_runtime.application_context.PyQt5 import ApplicationContext


class ResourceProvider:
    def __init__(self, context: ApplicationContext):
        self._context = context

    def image(self, file_name: str):
        return self._context.get_resource(f"img/{file_name}")

    def sound(self, file_name):
        return self._context.get_resource(f"sound/{file_name}")


resource_provider: ResourceProvider


def convert_seconds_to_time_string(seconds: int):
    prefix = ''

    if seconds < 0:
        prefix = '-'

    minutes, seconds = divmod(abs(seconds), 60)
    return '{}{:02d}:{:02d}'.format(prefix, minutes, seconds)

