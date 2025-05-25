import random
import string

ALPHABET = string.ascii_uppercase

def generate_substitution_key():
    shuffled = list(ALPHABET)
    random.shuffle(shuffled)
    return dict(zip(ALPHABET, shuffled))

def invert_key(key):
    return {v: k for k, v in key.items()}

def encrypt(text, key):
    return ''.join(key.get(c, c) for c in text)

def decrypt(text, key):
    inv = invert_key(key)
    return ''.join(inv.get(c, c) for c in text)
