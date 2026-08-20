import hashlib
import os
import struct
import sys

block_size = 4096

class MT19937:
    def __init__(self, seed_words):
        self.state = [0] * 624
        self.position = 624
        self.seed(seed_words)

    def seed(self, seed_words):
        self.state[0] = 19650218

        for i in range(1, 624):
            previous = self.state[i - 1]
            self.state[i] = (
                1812433253 * (previous ^ (previous >> 30)) + i
            ) & 0xFFFFFFFF

        i = 1
        key_index = 0

        for _ in range(max(624, len(seed_words))):
            previous = self.state[i - 1]
            self.state[i] = (
                (self.state[i] ^ ((previous ^ (previous >> 30)) * 1664525))
                + seed_words[key_index]
                + key_index
            ) & 0xFFFFFFFF

            i += 1
            key_index += 1

            if i == 624:
                self.state[0] = self.state[623]
                i = 1

            if key_index == len(seed_words):
                key_index = 0

        for _ in range(623):
            previous = self.state[i - 1]
            self.state[i] = (
                (self.state[i] ^ ((previous ^ (previous >> 30)) * 1566083941))
                - i
            ) & 0xFFFFFFFF

            i += 1
            if i == 624:
                self.state[0] = self.state[623]
                i = 1

        self.state[0] = 0x80000000
        self.position = 624

    def twist(self):
        for i in range(624):
            combined = (
                (self.state[i] & 0x80000000)
                | (self.state[(i + 1) % 624] & 0x7FFFFFFF)
            )

            new_value = self.state[(i + 397) % 624] ^ (combined >> 1)
            if combined & 1:
                new_value ^= 0x9908B0DF

            self.state[i] = new_value

        self.position = 0

    def next_number(self):
        if self.position == 624:
            self.twist()

        number = self.state[self.position]
        self.position += 1

        number ^= number >> 11
        number ^= (number << 7) & 0x9D2C5680
        number ^= (number << 15) & 0xEFC60000
        number ^= number >> 18

        return number & 0xFFFFFFFF


def make_block_key(filename):
    filename = os.path.basename(filename).lower()
    digest = hashlib.md5(("Rk3nwA8ZYV0yV" + filename).encode("utf-8")).digest()
    seed_words = struct.unpack("<4I", digest)
    random = MT19937(seed_words)

    key = bytearray()
    while len(key) < block_size:
        key.extend(struct.pack("<I", random.next_number()))

    return key

def process_movie(input_path, output_path):
    if os.path.abspath(input_path) == os.path.abspath(output_path):
        raise ValueError("the input and output paths must be different")

    block_key = make_block_key(input_path)

    with open(input_path, "rb") as input_file, open(output_path, "wb") as output_file:
        while True:
            data = input_file.read(block_size)
            if not data:
                break

            result = bytes(byte ^ block_key[i] for i, byte in enumerate(data))
            output_file.write(result)

if __name__ == "__main__":
    try:
        print(f"processing '{sys.argv[1]}'...")
        process_movie(sys.argv[1], sys.argv[2])
        print(f"saved to '{sys.argv[2]}'")
    except (OSError, ValueError) as error:
        print(f"errir: {error}")
        sys.exit(1)
