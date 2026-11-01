import { bodyBaseLayers } from './body-base.js';

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

const blousePath = 'M176 239 C171 222 179 207 194 200 C209 193 231 195 251 198 C266 200 271 210 268 225 L249 303 C232 305 211 295 197 285 C182 273 177 257 176 239Z';
const sashPath = 'M246 199 C257 196 267 203 268 214 L249 302 L231 297 L247 217Z';
const htameinPath = 'M177 290 C205 300 246 300 271 290 C279 329 280 383 269 428 C240 433 206 431 179 428 C172 382 171 330 177 290Z';

export function outfitSvg(item = null) {
  const base = bodyBaseLayers();
  if (!item) {
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 450 450" role="img" aria-label="Thiri neutral modest base costume">${base}</svg>`;
  }

  const motifs = {
    wave: '<path d="M0 12 Q12 0 24 12 T48 12"/>',
    stripe: '<path d="M8 0V48 M24 0V48 M40 0V48"/>',
    diamond: '<path d="M12 0L24 12L12 24L0 12Z M36 24L48 36L36 48L24 36Z"/>',
    flower: '<circle cx="24" cy="24" r="5"/><circle cx="24" cy="15" r="4"/><circle cx="33" cy="24" r="4"/><circle cx="24" cy="33" r="4"/><circle cx="15" cy="24" r="4"/>',
    leaf: '<path d="M4 25Q8 4 27 4Q25 22 4 25ZM25 45Q29 26 46 26Q44 43 25 45Z"/>',
    dot: '<circle cx="12" cy="12" r="3"/><circle cx="36" cy="36" r="3"/><circle cx="36" cy="12" r="3"/>'
  };

  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 450 450" role="img" aria-label="${item.en} garment overlay">
    <defs>
      <pattern id="motif" width="48" height="48" patternUnits="userSpaceOnUse">
        <g fill="none" stroke="${item.accent}" stroke-width="1.8" opacity=".9">${motifs[item.pattern]}</g>
      </pattern>
      <clipPath id="blouse"><path d="${blousePath}"/></clipPath>
      <clipPath id="sash"><path d="${sashPath}"/></clipPath>
      <clipPath id="htamein"><path d="${htameinPath}"/></clipPath>
    </defs>
    ${base}
    <g data-layer="${item.id}">
      <g data-layer="BLOUSE">
        <path d="${blousePath}" fill="${item.color}" stroke="#6d4d58" stroke-width="1.1" stroke-linejoin="round"/>
        <rect x="172" y="190" width="102" height="116" fill="url(#motif)" clip-path="url(#blouse)"/>
      </g>
      <g data-layer="SASH">
        <path d="${sashPath}" fill="${item.accent}" stroke="${item.color}" stroke-width="1.2" stroke-linejoin="round"/>
        <rect x="228" y="190" width="48" height="118" fill="url(#motif)" clip-path="url(#sash)"/>
      </g>
      <g data-layer="HTAMEIN">
        <path d="${htameinPath}" fill="${item.color}" stroke="#6d4d58" stroke-width="1.1" stroke-linejoin="round"/>
        <rect x="170" y="288" width="108" height="146" fill="url(#motif)" clip-path="url(#htamein)"/>
      </g>
      <g data-layer="DETAILS" fill="none" stroke="${item.accent}" stroke-width="2">
        <path d="M181 406 Q223 413 268 406"/>
        <path d="M184 412 Q224 419 267 412"/>
      </g>
    </g>
  </svg>`;
}
