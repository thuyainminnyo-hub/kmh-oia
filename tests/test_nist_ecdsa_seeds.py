"""Reproduce the 14 ECDSA seed strings published by Anthropic.

Source: https://www.anthropic.com/research/ecdsa-curve-origins
This is a narrow reproduction test, not a cryptographic security audit.
"""
from datetime import datetime, timezone


def unix(when: str) -> int:
    return int(datetime.fromisoformat(when).replace(tzinfo=timezone.utc).timestamp())


def candidate(t: int, n: int, per: int, shift: int, width: int) -> str:
    x, out = (t << 16) | 0x330E, ""
    for i in range(per * n):
        x = (0x5DEECE66D * x + 0xB) % 2**48
        if i >= per * (n - 1):
            out += "%0*X" % (width, x >> shift)
    return out


PRIME = {
    "prime239v1": ("1997-05-15 15:49:03", 2185, "E43BB460F0B80CC0C0B075798E948060F8321B7D"),
    "prime239v2": ("1997-05-15 15:49:03", 2320, "E8B4011604095303CA3B8099982BE09FCB9AE616"),
    "prime239v3": ("1997-05-15 15:49:03", 3048, "7D7374168FFE3471B60A857686A19475D3BFA2FF"),
    "P-192": ("1997-05-18 14:45:34", 139, "3045AE6FC8422F64ED579528D38120EAE12196D5"),
    "prime192v3": ("1997-05-18 14:45:34", 5228, "C469684435DEB378C4B65CA9591E2A5763059A2E"),
    "prime192v2": ("1997-05-18 14:45:34", 6013, "31A92EE2029FD10D901B113E990710F0D21AC6B6"),
    "P-521": ("1997-08-08 01:12:04", 1136, "D09E8800291CB85396CC6717393284AAA0DA64BA"),
    "P-256": ("1997-08-16 01:52:34", 1842, "C49D360886E704936A6678E1139D26B7819F7E90"),
    "P-384": ("1997-08-30 14:50:08", 2688, "A335926AA319A27A1D00896A6773A4827ACDAC73"),
    "P-224": ("1998-04-03 12:52:07", 7026, "BD71344799D5C7FCDC45B59FA3B9AB8F6A948BC5"),
}
BINARY = {
    "B-233": ("1998-04-17 15:24:18", 155, "74D59FF07F6B413D0EA14B344B20A2DB049B50C3"),
    "B-283": ("1998-04-17 15:27:44", 32, "77E2B07370EB0F832A6DD5B62DFC88CD06BB84BE"),
    "B-409": ("1998-04-17 15:30:18", 60, "4099B5A457F9D69F79213D094C4BCD4D4262210B"),
    "B-571": ("1998-04-17 15:32:08", 73, "2AA058F73A0E33AB486B0F610410C53A7F132310"),
}


def test_published_prime_curve_seed_values() -> None:
    for name, (when, index, expected) in PRIME.items():
        actual = candidate(unix(when), index, 20, 40, 2)
        assert actual == expected, f"{name}: expected {expected}, got {actual}"


def test_published_binary_curve_seed_values() -> None:
    for name, (when, index, expected) in BINARY.items():
        actual = candidate(unix(when) // 2, index, 5, 17, 8)
        assert actual == expected, f"{name}: expected {expected}, got {actual}"


if __name__ == "__main__":
    # Keep the workflow's direct-script invocation dependency-free and explicit.
    test_published_prime_curve_seed_values()
    test_published_binary_curve_seed_values()
    print("PASS: all 14 published seed strings reproduced exactly")
