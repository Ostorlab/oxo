import threading

from ostorlab.cli import console as cli_console

console = cli_console.Console()

COLOR_POOL = [
    'dodger_blue2',
    'deep_sky_blue3',
    'deep_sky_blue2',
    'cyan3',
    'spring_green2',
    'spring_green2',
    'grey37',
    'chartreuse4',
    'cornflower_blue',
    'chartreuse3',
    'steel_blue1',
    'dark_red',
    'plum4',
]

def _stream_log(log_generator, name, color):
    for line in log_generator:
        console.info(f'[{color} bold]{name}:[/] {line[:-1].decode()}')

class LogStream:

    def __init__(self):
        self._threads = []
        self._color_map = {}

    def stream(self, service):
        if service.name in self._color_map:
            color = self._color_map[service.name]
        else:
            color = COLOR_POOL.pop()

        logs = service.logs(details=False, follow=True, stdout=True, stderr=True)
        t = threading.Thread(target=_stream_log, args=(logs, service.name, color), daemon=True)
        self._threads.append(t)
        t.start()


