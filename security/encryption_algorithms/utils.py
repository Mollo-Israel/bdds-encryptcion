import base64


def pad_pkcs7(data: bytes, block_size: int) -> bytes:
    pad_len = block_size - (len(data) % block_size)
    return data + bytes([pad_len] * pad_len)


def unpad_pkcs7(data: bytes) -> bytes:
    if not data:
        raise ValueError("Datos vacíos.")

    pad_len = data[-1]

    if pad_len < 1 or pad_len > len(data):
        raise ValueError("Padding inválido.")

    if data[-pad_len:] != bytes([pad_len] * pad_len):
        raise ValueError("Padding corrupto.")

    return data[:-pad_len]


def b64encode_bytes(data: bytes) -> str:
    return base64.b64encode(data).decode("utf-8")


def b64decode_str(data: str) -> bytes:
    return base64.b64decode(data.encode("utf-8"))