from security.encryption_algorithms.base_cipher import BaseCipher


class HillCipher(BaseCipher):
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

    def _normalize_text(self, text: str) -> str:
        text = ''.join([c.upper() for c in text if c.isalpha()])
        if len(text) % 2 != 0:
            text += 'X'
        return text

    def _text_to_numbers(self, text: str):
        return [ord(c) - ord('A') for c in text]

    def _numbers_to_text(self, numbers):
        return ''.join(chr(n % 26 + ord('A')) for n in numbers)

    def _multiply_block(self, matrix, block):
        return [
            (matrix[0][0] * block[0] + matrix[0][1] * block[1]) % self.mod,
            (matrix[1][0] * block[0] + matrix[1][1] * block[1]) % self.mod,
        ]

    def encrypt(self, data: str) -> str:
        text = self._normalize_text(data)
        numbers = self._text_to_numbers(text)
        result = []

        for i in range(0, len(numbers), 2):
            block = numbers[i:i + 2]
            result.extend(self._multiply_block(self.key_matrix, block))

        return self._numbers_to_text(result)

    def decrypt(self, data: str) -> str:
        text = self._normalize_text(data)
        numbers = self._text_to_numbers(text)
        result = []

        for i in range(0, len(numbers), 2):
            block = numbers[i:i + 2]
            result.extend(self._multiply_block(self.inverse_matrix, block))

        return self._numbers_to_text(result)