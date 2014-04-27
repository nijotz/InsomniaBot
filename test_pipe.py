import re
from socketproxy import Pipe, PlumbingServer, main
import os
import time


class TestProxy(PlumbingServer):
    def __init__(self, *args, **kwargs):
        PlumbingServer.__init__(self, *args, **kwargs)
        self.pipes.append(RateLimitPipe())
        self.pipes.append(AudioPipe('horn', open('airhorn.mp3')))
        self.pipes.append(AudioPipe('trumpet', open('trumpet.mp3')))


class AudioPipe(Pipe):
    
    def __init__(self, name, mp3):
        self.mp3 = mp3.read()
        self.name = name
        self.buff = ''

    def to_client(self, data):

        # Add mp3 to buffer
        if (os.path.isfile(self.name)):
            os.remove(self.name)
            self.buff += self.mp3

        if self.buff:
            if len(self.buff) >= len(data):
               data = self.buff[:len(data)]
               self.buff = self.buff[len(data):]
            else:
                data = self.buff + data[:-len(self.buff)]
                self.buff = ''

        return data


class RateLimitPipe(Pipe):

    def __init__(self):
        self.bitrate = 0
        self.time_of_next_send = 0

    def to_client(self, data):

        sleep_time = self.time_of_next_send - time.time()
        if sleep_time > 0:
            time.sleep(sleep_time)

        if data.find('icy-br') != -1:
            regex = re.compile('icy-br:(?P<bitrate>[0-9]*)')
            match = regex.search(data)
            if match:
                bitrate = int(match.groupdict()['bitrate'])
                self.bitrate = bitrate

        if self.bitrate:
            bits = len(data) * 8
            secs_til_next_send = float(bits) / (self.bitrate * 1024)
            self.time_of_next_send = time.time() + secs_til_next_send

        return data


if __name__ == '__main__':
    main(TestProxy)
