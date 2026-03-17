from .cipher_factory import CipherFactory

algorithms = ["TWOFISH", "RSA", "ELGAMAL", "ECC"]
text = "saldo_usd:12345.67"

for alg in algorithms:
    cipher = CipherFactory.get_cipher(alg)
    encrypted = cipher.encrypt(text)
    decrypted = cipher.decrypt(encrypted)

    print("=" * 50)
    print(f"Algoritmo : {alg}")
    print(f"Original  : {text}")
    print(f"Cifrado   : {encrypted}")
    print(f"Descifrado: {decrypted}")

    if decrypted == text:
        print("✅ Prueba correcta")
    else:
        print("❌ Error en descifrado")