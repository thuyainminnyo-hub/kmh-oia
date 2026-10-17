# KMH Verification Run — Anthropic NIST ECDSA Seed Reproduction

**Run date:** 2026-10-17  
**Status:** Reproduction passed for the 14 seed values listed in Anthropic's published Python snippet; independent review pending.  
**Primary source:** https://www.anthropic.com/research/ecdsa-curve-origins  
**Protocol:** https://github.com/thuyainminnyo-hub/kmh-oia/blob/main/docs/research/kmh-research-protocol-v1.0.md

## Question
Does the published timestamp-seeded `lrand48` reconstruction reproduce the published hex seed values for the 10 prime-curve entries and four binary-curve entries shown in Anthropic's code?

## Method and environment
- Executed the Python reproduction logic in the available ChatGPT Python execution environment on 2026-10-17.
- Used the published constants, timestamps, candidate indexes, and bit shifts from Anthropic's page.
- Compared each generated hexadecimal string visually/exactly with the corresponding expected value printed by the source.
- This was not run on the user's Android device and has not been independently reviewed by a second person or a separate implementation.

## Actual output
```text
prime239v1 E43BB460F0B80CC0C0B075798E948060F8321B7D
prime239v2 E8B4011604095303CA3B8099982BE09FCB9AE616
prime239v3 7D7374168FFE3471B60A857686A19475D3BFA2FF
P-192 3045AE6FC8422F64ED579528D38120EAE12196D5
prime192v3 C469684435DEB378C4B65CA9591E2A5763059A2E
prime192v2 31A92EE2029FD10D901B113E990710F0D21AC6B6
P-521 D09E8800291CB85396CC6717393284AAA0DA64BA
P-256 C49D360886E704936A6678E1139D26B7819F7E90
P-384 A335926AA319A27A1D00896A6773A4827ACDAC73
P-224 BD71344799D5C7FCDC45B59FA3B9AB8F6A948BC5
B-233 74D59FF07F6B413D0EA14B344B20A2DB049B50C3
B-283 77E2B07370EB0F832A6DD5B62DFC88CD06BB84BE
B-409 4099B5A457F9D69F79213D094C4BCD4D4262210B
B-571 2AA058F73A0E33AB486B0F610410C53A7F132310
```

## Result
- **Expected vs actual:** All 14 generated strings match the output published on Anthropic's page.
- **Reproduction result:** PASS for this narrow computational check.
- **Independent verification:** PENDING.
- **Overall security conclusion:** Not established by this run. This does not prove every NIST curve or cryptographic system is free of weaknesses, and does not resolve B-163 or all base-point origins.

## QA notes
This confirms that the published reconstruction snippet reproduces the published seed strings in this execution environment. It does not independently validate every historical interpretation or the original curve-selection process. Keep source claims, computational reproduction, and broader security conclusions separate.

## Next actions
- [ ] Have a second reviewer run the snippet independently.
- [ ] Optionally rerun on a separate Python runtime/device and record version.
- [ ] Keep B-163, unexplained base points, and skipped candidate-selection criteria as open questions.
