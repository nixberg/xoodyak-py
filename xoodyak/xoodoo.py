class Xoodoo:
    def __init__(self):
        self._bytes = bytearray(48)

    def __getitem__(self, index):
        return self._bytes[index]

    def __setitem__(self, index, value):
        self._bytes[index] = value

    def permute(self):
        s = [0] * 12

        j = 0
        for i in range(12):
            s[i] = self._bytes[j] << 0
            j += 1
            s[i] |= self._bytes[j] << 8
            j += 1
            s[i] |= self._bytes[j] << 16
            j += 1
            s[i] |= self._bytes[j] << 24
            j += 1

        round_constants = [
            0x058,
            0x038,
            0x3C0,
            0x0D0,
            0x120,
            0x014,
            0x060,
            0x02C,
            0x380,
            0x0F0,
            0x1A0,
            0x012,
        ]

        for round_constant in round_constants:
            e = [0, 0, 0, 0]

            for i in range(4):
                r = s[i] ^ s[i + 4] ^ s[i + 8]
                e[i] = (r >> 18) | (r << 14) & 0xFFFF_FFFF
                r = e[i]
                e[i] ^= (r >> 9) | (r << 23) & 0xFFFF_FFFF

            for i in range(12):
                s[i] ^= e[(i - 1) & 3]

            s[7], s[4] = s[4], s[7]
            s[7], s[5] = s[5], s[7]
            s[7], s[6] = s[6], s[7]
            s[0] ^= round_constant

            for i in range(4):
                a = s[i]
                b = s[i + 4]
                r = s[i + 8]
                c = (r >> 21) | (r << 11) & 0xFFFF_FFFF
                r = (b & ~a) ^ c
                s[i + 8] = (r >> 24) | (r << 8) & 0xFFFF_FFFF
                r = (a & ~c) ^ b
                s[i + 4] = (r >> 31) | (r << 1) & 0xFFFF_FFFF
                s[i] ^= c & ~b

            s[8], s[10] = s[10], s[8]
            s[9], s[11] = s[11], s[9]

        j = 0
        for i in range(12):
            self._bytes[j] = (s[i] >> 0) & 0xFF
            j += 1
            self._bytes[j] = (s[i] >> 8) & 0xFF
            j += 1
            self._bytes[j] = (s[i] >> 16) & 0xFF
            j += 1
            self._bytes[j] = (s[i] >> 24) & 0xFF
            j += 1
