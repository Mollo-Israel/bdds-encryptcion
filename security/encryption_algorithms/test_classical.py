from security.encryption_algorithms.cipher_factory import CipherFactory

algorithms = ["CAESAR", "ATBASH", "VIGENERE", "PLAYFAIR", "HILL"]
text = "SALDO"

for alg in algorithms:
    cipher = CipherFactory.get_cipher(alg)
    encrypted = cipher.encrypt(text)
    decrypted = cipher.decrypt(encrypted)

    print(f"Algoritmo: {alg}")
    print(f"Original : {text}")
    print(f"Cifrado  : {encrypted}")
    print(f"Descifrado: {decrypted}")
    print("-" * 40)