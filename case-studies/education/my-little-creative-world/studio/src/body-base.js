export const BODY_BASE_COLOR = '#f4eadb';

// Opaque, modest vector cover layers aligned to the immutable 450×450 source.
// The original JPEG remains untouched underneath this application overlay.
export function bodyBaseLayers() {
  return `
    <g data-layer="BODY_BASE_TOP">
      <path d="M176 239 C171 222 179 207 194 200 C209 193 231 195 251 198 C266 200 271 210 268 225 L249 303 C232 305 211 295 197 285 C182 273 177 257 176 239Z"
        fill="${BODY_BASE_COLOR}" stroke="#d9c7ae" stroke-width="1.6" stroke-linejoin="round"/>
      <path d="M199 201 Q212 232 234 207" fill="none" stroke="#d9c7ae" stroke-width="1.8"/>
    </g>
    <g data-layer="BODY_BASE_LOWER">
      <path d="M177 290 C205 300 246 300 271 290 C279 329 280 383 269 428 C240 433 206 431 179 428 C172 382 171 330 177 290Z"
        fill="${BODY_BASE_COLOR}" stroke="#d9c7ae" stroke-width="1.8" stroke-linejoin="round"/>
      <path d="M183 414 Q225 420 268 414" fill="none" stroke="#e1d3c0" stroke-width="1.8"/>
    </g>
    <g data-layer="BASE_NECKLACE" fill="none" stroke="#d2a23f" stroke-width="2.2" stroke-linecap="round">
      <path d="M198 198 Q211 232 232 207"/>
      <circle cx="219" cy="233" r="4" fill="#c84f68" stroke="#d2a23f"/>
    </g>`;
}
