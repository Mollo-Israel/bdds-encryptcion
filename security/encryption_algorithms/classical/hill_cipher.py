from security.encryption_algorithms.base_cipher import BaseCipher


class HillCipher(BaseCipher):
    """
    Versión reversible para datos arbitrarios:
    1. Convierte el texto a bytes UTF-8
    2. Convierte hex -> letras A-P
    3. Aplica Hill 2x2 sobre letras A-Z
    4. Descifra y revierte A-P -> hex -> texto original
    """

    def __init__(self, key_matrix=None):
        self.mod = 26
        self.key_matrix = key_matrix or [[3, 3], [2, 5]]

        det = self._determinant(self.key_matrix) % self.mod
        if self._gcd(det, self.mod) != 1:
            raise ValueError("La matriz clave no es invertible en módulo 26.")

        self.inverse_matrix = self._matrix_mod_inverse(self.key_matrix)

    def _gcd(self, a, b):
        while b:
            a, b = b, a % b
        return a

    def _mod_inverse(self, a, m):
        a %= m
        for x in range(1, m):
            if (a * x) % m == 1:
                return x
        raise ValueError("No existe inverso modular.")

    def _determinant(self, matrix):
        return matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]

    def _matrix_mod_inverse(self, matrix):
        det = self._determinant(matrix) % self.mod
        det_inv = self._mod_inverse(det, self.mod)

        inv = [
            [matrix[1][1], -matrix[0][1]],
            [-matrix[1][0], matrix[0][0]]
        ]

        return [
            [(det_inv * inv[i][j]) % self.mod for j in range(2)]
            for i in range(2)
        ]

    def _text_to_ap(self, data: str) -> str:
        hex_text = data.encode("utf-8").hex().upper()
        return ''.join(chr(ord('A') + int(ch, 16)) for ch in hex_text)

    def _ap_to_text(self, encoded: str) -> str:
        hex_text = ''.join(format(ord(ch) - ord('A'), 'X') for ch in encoded)
        return bytes.fromhex(hex_text).decode("utf-8")

    def _text_to_numbers(self, text: str):
        return [ord(c) - ord('A') for c in text]

    def _numbers_to_text(self, numbers):
        return ''.join(chr((n % 26) + ord('A')) for n in numbers)

    def _multiply_block(self, matrix, block):
        return [
            (matrix[0][0] * block[0] + matrix[0][1] * block[1]) % self.mod,
            (matrix[1][0] * block[0] + matrix[1][1] * block[1]) % self.mod,
        ]

    def encrypt(self, data: str) -> str:
        text = self._text_to_ap(str(data))
        if len(text) % 2 != 0:
            raise ValueError("La codificación interna debe tener longitud par.")

        numbers = self._text_to_numbers(text)
        result = []

        for i in range(0, len(numbers), 2):
            block = numbers[i:i + 2]
            result.extend(self._multiply_block(self.key_matrix, block))

        return self._numbers_to_text(result)

    def decrypt(self, data: str) -> str:
        text = str(data).upper()
        if len(text) % 2 != 0:
            raise ValueError("El texto cifrado Hill debe tener longitud par.")

        numbers = self._text_to_numbers(text)
        result = []

        for i in range(0, len(numbers), 2):
            block = numbers[i:i + 2]
            result.extend(self._multiply_block(self.inverse_matrix, block))

        decoded_letters = self._numbers_to_text(result)
        return self._ap_to_text(decoded_letters)