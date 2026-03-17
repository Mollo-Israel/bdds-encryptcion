from ..base_cipher import BaseCipher


class CaesarCipher(BaseCipher):
    def __init__(self, shift: int = 3):
        self.shift = shift % 26

    def _transform(self, text: str, shift: int) -> str:
        result = []

        for char in text:
            if char.isalpha():
                base = ord('A') if char.isupper() else ord('a')
                new_char = chr((ord(char) - base + shift) % 26 + base)
                result.append(new_char)
            else:
                result.append(char)

        return ''.join(result)

    def encrypt(self, data: str) -> str:
        return self._transform(data, self.shift)

    def decrypt(self, data: str) -> str:
        return self._transform(data, -self.shift)