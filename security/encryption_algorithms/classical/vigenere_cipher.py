from security.encryption_algorithms.base_cipher import BaseCipher


class VigenereCipher(BaseCipher):
    def __init__(self, key: str = "CLAVE"):
        self.key = ''.join([c.upper() for c in key if c.isalpha()])
        if not self.key:
            raise ValueError("La clave de Vigenere debe contener letras.")

    def _process(self, text: str, encrypt: bool = True) -> str:
        result = []
        key_index = 0

        for char in text:
            if char.isalpha():
                key_char = self.key[key_index % len(self.key)]
                shift = ord(key_char) - ord('A')
                if not encrypt:
                    shift = -shift

                base = ord('A') if char.isupper() else ord('a')
                new_char = chr((ord(char) - base + shift) % 26 + base)
                result.append(new_char)
                key_index += 1
            else:
                result.append(char)

        return ''.join(result)

    def encrypt(self, data: str) -> str:
        return self._process(data, encrypt=True)

    def decrypt(self, data: str) -> str:
        return self._process(data, encrypt=False)