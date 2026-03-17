from security.encryption_algorithms.base_cipher import BaseCipher


class PlayfairCipher(BaseCipher):
    def __init__(self, key: str = "SEGURIDAD"):
        self.key = self._normalize_text(key)
        self.matrix = self._generate_matrix()

    def _normalize_text(self, text: str) -> str:
        text = text.upper().replace("J", "I")
        return ''.join([c for c in text if c.isalpha()])

    def _generate_matrix(self):
        alphabet = "ABCDEFGHIKLMNOPQRSTUVWXYZ"
        seen = set()
        sequence = []

        for char in self.key + alphabet:
            if char not in seen:
                seen.add(char)
                sequence.append(char)

        return [sequence[i:i + 5] for i in range(0, 25, 5)]

    def _find_position(self, char: str):
        for row_idx, row in enumerate(self.matrix):
            if char in row:
                return row_idx, row.index(char)
        raise ValueError(f"Carácter no encontrado en matriz: {char}")

    def _prepare_text(self, text: str) -> list:
        text = self._normalize_text(text)
        pairs = []
        i = 0

        while i < len(text):
            a = text[i]
            b = text[i + 1] if i + 1 < len(text) else 'X'

            if a == b:
                pairs.append((a, 'X'))
                i += 1
            else:
                pairs.append((a, b))
                i += 2

        if pairs and len(pairs[-1]) == 1:
            pairs[-1] = (pairs[-1][0], 'X')

        return pairs

    def _process_pair(self, a: str, b: str, encrypt: bool = True):
        row1, col1 = self._find_position(a)
        row2, col2 = self._find_position(b)

        if row1 == row2:
            shift = 1 if encrypt else -1
            return (
                self.matrix[row1][(col1 + shift) % 5],
                self.matrix[row2][(col2 + shift) % 5]
            )

        if col1 == col2:
            shift = 1 if encrypt else -1
            return (
                self.matrix[(row1 + shift) % 5][col1],
                self.matrix[(row2 + shift) % 5][col2]
            )

        return (
            self.matrix[row1][col2],
            self.matrix[row2][col1]
        )

    def encrypt(self, data: str) -> str:
        pairs = self._prepare_text(data)
        result = []

        for a, b in pairs:
            x, y = self._process_pair(a, b, encrypt=True)
            result.extend([x, y])

        return ''.join(result)

    def decrypt(self, data: str) -> str:
        text = self._normalize_text(data)
        if len(text) % 2 != 0:
            raise ValueError("El texto cifrado Playfair debe tener longitud par.")

        result = []
        for i in range(0, len(text), 2):
            a, b = text[i], text[i + 1]
            x, y = self._process_pair(a, b, encrypt=False)
            result.extend([x, y])

        return ''.join(result)