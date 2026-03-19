from security.encryption_algorithms.base_cipher import BaseCipher


class PlayfairCipher(BaseCipher):
    """
    Versión reversible para datos arbitrarios usando un alfabeto interno A-P.

    Flujo:
    1. Convierte el texto a bytes UTF-8
    2. Convierte cada nibble hex (0-F) a letras A-P
    3. Aplica Playfair sobre una matriz 4x4 construida con A-P
    4. Revierte el proceso al descifrar

    Esto evita el problema de la Playfair clásica 5x5 con la letra J.
    """

    INTERNAL_ALPHABET = "ABCDEFGHIJKLMNOP"
    MATRIX_SIZE = 4

    def __init__(self, key: str = "SEGURIDAD"):
        self.key = self._normalize_key(key)
        self.matrix = self._generate_matrix()

    def _normalize_key(self, text: str) -> str:
        text = text.upper()
        seen = set()
        normalized = []

        for char in text:
            if char in self.INTERNAL_ALPHABET and char not in seen:
                seen.add(char)
                normalized.append(char)

        return "".join(normalized)

    def _generate_matrix(self):
        seen = set()
        sequence = []

        for char in self.key + self.INTERNAL_ALPHABET:
            if char in self.INTERNAL_ALPHABET and char not in seen:
                seen.add(char)
                sequence.append(char)

        return [
            sequence[i:i + self.MATRIX_SIZE]
            for i in range(0, len(sequence), self.MATRIX_SIZE)
        ]

    def _find_position(self, char: str):
        for row_idx, row in enumerate(self.matrix):
            if char in row:
                return row_idx, row.index(char)

        raise ValueError(f"Carácter no encontrado en matriz interna Playfair: {char}")

    def _process_pair(self, a: str, b: str, encrypt: bool = True):
        row1, col1 = self._find_position(a)
        row2, col2 = self._find_position(b)

        shift = 1 if encrypt else -1

        if row1 == row2:
            return (
                self.matrix[row1][(col1 + shift) % self.MATRIX_SIZE],
                self.matrix[row2][(col2 + shift) % self.MATRIX_SIZE],
            )

        if col1 == col2:
            return (
                self.matrix[(row1 + shift) % self.MATRIX_SIZE][col1],
                self.matrix[(row2 + shift) % self.MATRIX_SIZE][col2],
            )

        return (
            self.matrix[row1][col2],
            self.matrix[row2][col1],
        )

    def _text_to_ap(self, data: str) -> str:
        hex_text = data.encode("utf-8").hex().upper()
        return "".join(chr(ord("A") + int(ch, 16)) for ch in hex_text)

    def _ap_to_text(self, encoded: str) -> str:
        hex_text = "".join(format(ord(ch) - ord("A"), "X") for ch in encoded)
        return bytes.fromhex(hex_text).decode("utf-8")

    def encrypt(self, data: str) -> str:
        text = self._text_to_ap(str(data))

        if len(text) % 2 != 0:
            raise ValueError("La codificación interna debe tener longitud par.")

        result = []
        for i in range(0, len(text), 2):
            a, b = text[i], text[i + 1]
            x, y = self._process_pair(a, b, encrypt=True)
            result.extend([x, y])

        return "".join(result)

    def decrypt(self, data: str) -> str:
        text = str(data).upper()

        if len(text) % 2 != 0:
            raise ValueError("El texto cifrado Playfair debe tener longitud par.")

        result = []
        for i in range(0, len(text), 2):
            a, b = text[i], text[i + 1]
            x, y = self._process_pair(a, b, encrypt=False)
            result.extend([x, y])

        return self._ap_to_text("".join(result))