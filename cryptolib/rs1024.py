GENERATOR = (
    0xE0E040,
    0x1C1C080,
    0x3838100,
    0x7070200,
    0xE0E0009,
    0x1C0C2412,
    0x38086C24,
    0x3090FC48,
    0x21B1F890,
    0x3F3F120,
)


def polymod_rs1024(values: list) -> int:
    """Reed-Solomon code over GF(1024), for 10-bit blocks"""
    if len(values) < 1:
        raise ValueError("Must check values.")
    chk = 1
    for v in values:
        b = chk >> 20
        chk &= 0xFFFFF
        chk <<= 10
        chk ^= v
        for i in range(10):
            if (b >> i) & 1:
                chk ^= GENERATOR[i]
    return chk


def verify_checksum(header: bytes, data: list) -> bool:
    return polymod_rs1024(list(header) + data) == 1
