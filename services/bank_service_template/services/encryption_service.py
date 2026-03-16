from abc import ABC, abstractmethod


class BaseEncryptionService(ABC):
    """
    Interfaz base de cifrado.
    Cada banco implementa su propio servicio heredando de esta clase.
    """

    @abstractmethod
    def encrypt(self, plaintext: str) -> str:
        """Cifra un texto plano y devuelve el texto cifrado."""

    @abstractmethod
    def decrypt(self, ciphertext: str) -> str:
        """Descifra un texto cifrado y devuelve el texto plano."""


class NoOpEncryptionService(BaseEncryptionService):
    """
    Implementación de placeholder (sin cifrado).
    Usada solo en la plantilla base; cada banco la reemplaza.
    """

    def encrypt(self, plaintext: str) -> str:
        return plaintext

    def decrypt(self, ciphertext: str) -> str:
        return ciphertext


# Instancia usada por defecto en la plantilla
encryption_service: BaseEncryptionService = NoOpEncryptionService()
