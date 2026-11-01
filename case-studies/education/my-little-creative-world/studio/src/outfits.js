export const outfits = [
  { id: 'MLCW-OUTFIT-001', name: 'ပန်းရောင်လှိုင်း', en: 'Pink wave motif', color: '#d96b91', accent: '#f4c4d4', pattern: 'wave' },
  { id: 'MLCW-OUTFIT-002', name: 'စိမ်းပြာနှင့် ကောင်းကင်ပြာ', en: 'Teal & sky blue', color: '#318f91', accent: '#9edce0', pattern: 'stripe' },
  { id: 'MLCW-OUTFIT-003', name: 'ရွှေနှင့် ကြက်သွေးရောင်', en: 'Gold & maroon', color: '#8f3048', accent: '#e6bd65', pattern: 'diamond' },
  { id: 'MLCW-OUTFIT-004', name: 'လာဗင်ဒါ', en: 'Lavender', color: '#9276bd', accent: '#d8c8ef', pattern: 'flower' },
  { id: 'MLCW-OUTFIT-005', name: 'မဲနယ်နှင့် ရွှေ', en: 'Indigo & gold', color: '#344477', accent: '#e5c36b', pattern: 'diamond' },
  { id: 'MLCW-OUTFIT-006', name: 'သစ်တောစိမ်း', en: 'Forest green', color: '#477a55', accent: '#c7d7a0', pattern: 'leaf' },
  { id: 'MLCW-OUTFIT-007', name: 'သန္တာနှင့် အညို', en: 'Coral & brown', color: '#c96c58', accent: '#e8b18c', pattern: 'dot' },
  { id: 'MLCW-OUTFIT-008', name: 'နို့နှစ်နှင့် မဲနယ်', en: 'Cream & indigo', color: '#d8c99e', accent: '#596a9b', pattern: 'stripe' },
  { id: 'MLCW-OUTFIT-009', name: 'ပွဲတော်ပန်းရောင်', en: 'Festival pink', color: '#d64d89', accent: '#f5d16f', pattern: 'flower' },
  { id: 'MLCW-OUTFIT-010', name: 'တော်ဝင်နို့နှစ်နှင့် ရွှေ', en: 'Royal cream & gold', color: '#e4d5ad', accent: '#b98a32', pattern: 'diamond' }
];

export function outfitSvg(item) {
  const motifs = {
    wave: '<path d="M0 12 Q12 0 24 12 T48 12"/>',
    stripe: '<path d="M8 0V48 M24 0V48 M40 0V48"/>',
    diamond: '<path d="M12 0L24 12L12 24L0 12Z M36 24L48 36L36 48L24 36Z"/>',
    flower: '<circle cx="24" cy="24" r="5"/><circle cx="24" cy="15" r="4"/><circle cx="33" cy="24" r="4"/><circle cx="24" cy="33" r="4"/><circle cx="15" cy="24" r="4"/>',
    leaf: '<path d="M4 25Q8 4 27 4Q25 22 4 25ZM25 45Q29 26 46 26Q44 43 25 45Z"/>',
    dot: '<circle cx="12" cy="12" r="3"/><circle cx="36" cy="36" r="3"/><circle cx="36" cy="12" r="3"/>'
  };

  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 450 450" preserveAspectRatio="none" role="img" aria-label="${item.en} garment overlay">
    <defs>
      <pattern id="motif" width="48" height="48" patternUnits="userSpaceOnUse">
        <g fill="none" stroke="${item.accent}" stroke-width="1.8" opacity=".85">${motifs[item.pattern]}</g>
      </pattern>
      <clipPath id="blouse">
        <path d="M180 239 C174 226 180 211 194 205 C207 198 221 196 237 197 L272 199 C288 200 299 211 300 225 L282 269 C274 285 263 298 248 302 L215 289 C198 282 184 266 180 239Z"/>
      </clipPath>
      <clipPath id="sash">
        <path d="M256 205 C270 198 284 202 292 212 L270 301 L242 299Z"/>
      </clipPath>
      <clipPath id="htamein">
        <path d="M184 297 C205 304 245 304 268 296 C276 329 277 382 268 426 C240 432 209 430 183 425 C176 385 176 331 184 297Z"/>
      </clipPath>
    </defs>
    <path d="M180 239 C174 226 180 211 194 205 C207 198 221 196 237 197 L272 199 C288 200 299 211 300 225 L282 269 C274 285 263 298 248 302 L215 289 C198 282 184 266 180 239Z"
      fill="${item.color}" opacity=".72" clip-path="url(#blouse)"/>
    <rect x="175" y="194" width="132" height="112" fill="url(#motif)" clip-path="url(#blouse)"/>
    <path d="M256 205 C270 198 284 202 292 212 L270 301 L242 299Z"
      fill="${item.color}" opacity=".88" clip-path="url(#sash)"/>
    <rect x="238" y="198" width="62" height="108" fill="url(#motif)" clip-path="url(#sash)"/>
    <path d="M184 297 C205 304 245 304 268 296 C276 329 277 382 268 426 C240 432 209 430 183 425 C176 385 176 331 184 297Z"
      fill="${item.color}" opacity=".76" clip-path="url(#htamein)"/>
    <rect x="176" y="292" width="100" height="140" fill="url(#motif)" clip-path="url(#htamein)"/>
  </svg>`;
}
