import random
import string


def generate_verification_code() -> str:
    return "".join(random.choices(string.digits + "ABCDEF", k=8))