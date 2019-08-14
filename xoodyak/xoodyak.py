from enum import IntEnum
from xoodyak.xoodoo import Xoodoo


class Flag(IntEnum):
    ZERO = 0x00
    ABSORB_KEY = 0x02
    ABSORB = 0x03
    RATCHET = 0x10
    SQUEEZE_KEY = 0x20
    SQUEEZE = 0x40
    CRYPT = 0x80


class Mode(IntEnum):
    HASH = 0
    KEYED = 1


class Rates:
    HASH = 16
    INPUT = 44
    OUTPUT = 24
    RATCHET = 16

    def __init__(self, absorb, squeeze):
        self.absorb = absorb
        self.squeeze = squeeze

    @staticmethod
    def hash():
        return Rates(Rates.HASH, Rates.HASH)

    @staticmethod
    def keyed():
        return Rates(Rates.INPUT, Rates.OUTPUT)


class Phase(IntEnum):
    UP = 0
    DOWN = 1


class Xoodyak:
    def __init__(self):
        self.mode = Mode.HASH
        self.rates = Rates.hash()
        self.phase = Phase.UP
        self.xoodoo = Xoodoo()

    @staticmethod
    def keyed(key, id=None, counter=None):
        key = memoryview(key)
        assert key.itemsize == 1

        if id:
            id = memoryview(id)
        else:
            id = memoryview(bytes(0))
        assert id.itemsize == 1

        if counter:
            counter = memoryview(counter)
        else:
            counter = memoryview(bytes(0))
        assert counter.itemsize == 1

        self = Xoodyak()
        self.mode = Mode.KEYED
        self.rates = Rates.keyed()

        buffer = memoryview(bytes([*key, *id, len(id) & 0xFF]))
        assert len(buffer) <= Rates.INPUT
        self._absorb_any(buffer, self.rates.absorb, Flag.ABSORB_KEY)

        if len(counter) > 0:
            self._absorb_any(counter, 1, Flag.ZERO)

        return self

    def _absorb_any(self, input, rate, down_flag):
        while True:
            if self.phase != Phase.UP:
                self._up(None, 0, Flag.ZERO)

            block_len = min(len(input), rate)
            self._down(input, block_len, down_flag)
            input = input[block_len:]
            down_flag = Flag.ZERO

            if not len(input) > 0:
                break

    def _crypt(self, input, output, decrypt):
        flag = Flag.CRYPT
        while True:
            block_size = min(len(input), Rates.OUTPUT)

            self._up(None, 0, flag)
            flag = Flag.ZERO

            for i in range(len(input)):
                output[i] = input[i] ^ self.xoodoo[i]

            if decrypt:
                self._down(output, block_size, Flag.ZERO)
            else:
                self._down(input, block_size, Flag.ZERO)

            input = input[block_size:]
            output = output[block_size:]

            if not len(input) > 0:
                break

    def _squeeze_any(self, output, up_flag):
        block_len = min(len(output), self.rates.squeeze)
        self._up(output, block_len, up_flag)
        output = output[block_len:]

        while len(output) > 0:
            block_len = min(len(output), self.rates.squeeze)
            self._down(None, 0, Flag.ZERO)
            self._up(output, block_len, Flag.ZERO)
            output = output[block_len:]

    def _down(self, block, count, flag):
        self.phase = Phase.DOWN
        for i in range(count):
            self.xoodoo[i] ^= block[i]
        self.xoodoo[count] ^= 0x01
        if self.mode == Mode.HASH:
            self.xoodoo[47] ^= flag & 0x01
        else:
            self.xoodoo[47] ^= flag

    def _up(self, block, count, flag):
        self.phase = Phase.UP
        if self.mode != Mode.HASH:
            self.xoodoo[47] ^= flag
        self.xoodoo.permute()
        for i in range(count):
            block[i] = self.xoodoo[i]

    def absorb(self, input):
        input = memoryview(input)
        assert input.itemsize == 1

        self._absorb_any(input, self.rates.absorb, Flag.ABSORB)

    def encrypt(self, plaintext, ciphertext):
        plaintext = memoryview(plaintext)
        assert plaintext.itemsize == 1

        ciphertext = memoryview(ciphertext)
        assert ciphertext.itemsize == 1
        assert ciphertext.readonly == False

        assert len(plaintext) == len(ciphertext)

        self._crypt(plaintext, ciphertext, False)

    def decrypt(self, ciphertext, plaintext):
        ciphertext = memoryview(ciphertext)
        assert ciphertext.itemsize == 1

        plaintext = memoryview(plaintext)
        assert plaintext.itemsize == 1
        assert plaintext.readonly == False

        assert len(ciphertext) == len(plaintext)

        assert self.mode == Mode.KEYED
        self._crypt(ciphertext, plaintext, True)

    def squeeze(self, output):
        output = memoryview(output)
        assert output.itemsize == 1
        assert output.readonly == False

        self._squeeze_any(output, Flag.SQUEEZE)

    def squeeze_key(self, output):
        output = memoryview(output)
        assert output.readonly == False

        assert self.mode == Mode.KEYED
        self._squeeze_any(output, Flag.SQUEEZE_KEY)

    def ratchet(self):
        assert self.mode == Mode.KEYED
        buffer = memoryview(bytearray(Rates.RATCHET))
        self._squeeze_any(buffer, Flag.RATCHET)
        self._absorb_any(buffer, Rates.RATCHET, Flag.ZERO)
