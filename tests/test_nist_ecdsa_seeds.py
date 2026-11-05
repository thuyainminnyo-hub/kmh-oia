
from datetime import datetime, timezone
import unittest


def unix(when):
    return int(
        datetime.fromisoformat(when)
        .replace(tzinfo=timezone.utc)
        .timestamp()
    )


def candidate(t, n, per, shift, width):
    x = (t << 16) | 0x330E
    out = ""

    for i in range(per * n):
        x = (0x5DEECE66D * x + 0xB) % 2**48
        if i >= per * (n - 1):
            out += "%0*X" % (width, x >> shift)

    return out


PRIME = {
    "prime239v1": ("1997-05-15 15:49:03", 2185),
    "prime239v2": ("1997-05-15 15:49:03", 2320),
    "prime239v3": ("1997-05-15 15:49:03", 3048),
    "P-192": ("1997-05-18 14:45:34", 139),
    "prime192v3": ("1997-05-18 14:45:34", 5228),
    "prime192v2": ("1997-05-18 14:45:34", 6013),
    "P-521": ("1997-08-08 01:12:04", 1136),
    "P-256": ("1997-08-16 01:52:34", 1842),
    "P-384": ("1997-08-30 14:50:08", 2688),
    "P-224": ("1998-04-03 12:52:07", 7026),
}

BINARY = {
    "B-233": ("1998-04-17 15:24:18", 155),
    "B-283": ("1998-04-17 15:27:44", 32),
    "B-409": ("1998-04-17 15:30:18", 60),
    "B-571": ("1998-04-17 15:32:08", 73),
}

EXPECTED = {
    "prime239v1": "E43BB460F0B80CC0C0B075798E948060F8321B7D",
    "prime239v2": "E8B4011604095303CA3B8099982BE09FCB9AE616",
    "prime239v3": "7D7374168FFE3471B60A857686A19475D3BFA2FF",
    "P-192": "3045AE6FC8422F64ED579528D38120EAE12196D5",
    "prime192v3": "C469684435DEB378C4B65CA9591E2A5763059A2E",
    "prime192v2": "31A92EE2029FD10D901B113E990710F0D21AC6B6",
    "P-521": "D09E8800291CB85396CC6717393284AAA0DA64BA",
    "P-256": "C49D360886E704936A6678E1139D26B7819F7E90",
    "P-384": "A335926AA319A27A1D00896A6773A4827ACDAC73",
    "P-224": "BD71344799D5C7FCDC45B59FA3B9AB8F6A948BC5",
    "B-233": "74D59FF07F6B413D0EA14B344B20A2DB049B50C3",
    "B-283": "77E2B07370EB0F832A6DD5B62DFC88CD06BB84BE",
    "B-409": "4099B5A457F9D69F79213D094C4BCD4D4262210B",
    "B-571": "2AA058F73A0E33AB486B0F610410C53A7F132310",
}


class TestNISTECDSASeeds(unittest.TestCase):

    def test_all_14_published_seeds(self):
        actual = {}

        for name, (when, n) in PRIME.items():
            actual[name] = candidate(
                unix(when), n, 20, 40, 2
            )

        for name, (when, n) in BINARY.items():
            actual[name] = candidate(
                unix(when) // 2, n, 5, 17, 8
            )

        self.assertEqual(set(actual), set(EXPECTED))

        for name, expected in EXPECTED.items():
            with self.subTest(curve=name):
                self.assertEqual(actual[name], expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
