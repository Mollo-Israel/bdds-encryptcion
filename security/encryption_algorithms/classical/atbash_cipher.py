from security.encryption_algorithms.base_cipher import BaseCipher


class AtbashCipher(BaseCipher):
    def _transform(self, text: str) -> str:
        result = []

        for char in str(text):
            if char.isupper():
                result.append(chr(ord('Z') - (ord(char) - ord('A'))))
            elif char.islower():
                result.append(chr(ord('z') - (ord(char) - ord('a'))))
            elif char.isdigit():
                result.append(chr(ord('9') - (ord(char) - ord('0'))))
            else:
                result.append(char)

        return ''.join(result)

    def encrypt(self, data: str) -> str:
        return self._transform(data)

    def decrypt(self, data: str) -> str:
        return self._transform(data)