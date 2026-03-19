from security.encryption_algorithms.base_cipher import BaseCipher


class VigenereCipher(BaseCipher):
    def __init__(self, key: str = "CLAVE"):
        self.key = ''.join([c.upper() for c in key if c.isalpha()])
        if not self.key:
            raise ValueError("La clave de Vigenere debe contener letras.")

    def _process(self, text: str, encrypt: bool = True) -> str:
        result = []
        key_index = 0

        for char in str(text):
            key_char = self.key[key_index % len(self.key)]
            alpha_shift = ord(key_char) - ord('A')
            digit_shift = alpha_shift % 10

            if char.isalpha():
                shift = alpha_shift if encrypt else -alpha_shift
                base = ord('A') if char.isupper() else ord('a')
                new_char = chr((ord(char) - base + shift) % 26 + base)
                result.append(new_char)
                key_index += 1
            elif char.isdigit():
                shift = digit_shift if encrypt else -digit_shift
                new_char = chr((ord(char) - ord('0') + shift) % 10 + ord('0'))
                result.append(new_char)
                key_index += 1
            else:
                result.append(char)

        return ''.join(result)

    def encrypt(self, data: str) -> str:
        return self._process(data, encrypt=True)

    def decrypt(self, data: str) -> str:
        return self._process(data, encrypt=False)