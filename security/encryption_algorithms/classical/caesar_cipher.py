from ..base_cipher import BaseCipher


class CaesarCipher(BaseCipher):
    def __init__(self, shift: int = 3):
        self.shift = shift % 26
        self.digit_shift = shift % 10

    def encrypt(self, data: str) -> str:
        return "".join(self._shift_char(ch, encrypt=True) for ch in str(data))

    def decrypt(self, data: str) -> str:
        return "".join(self._shift_char(ch, encrypt=False) for ch in str(data))

    def _shift_char(self, ch: str, encrypt: bool) -> str:
        if ch.islower():
            base = ord("a")
            offset = ord(ch) - base
            step = self.shift if encrypt else -self.shift
            return chr(base + ((offset + step) % 26))

        if ch.isupper():
            base = ord("A")
            offset = ord(ch) - base
            step = self.shift if encrypt else -self.shift
            return chr(base + ((offset + step) % 26))

        if ch.isdigit():
            base = ord("0")
            offset = ord(ch) - base
            step = self.digit_shift if encrypt else -self.digit_shift
            return chr(base + ((offset + step) % 10))

        return ch