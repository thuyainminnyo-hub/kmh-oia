import test from 'node:test';
import assert from 'node:assert/strict';
import { outfits, outfitSvg } from '../src/outfits.js';

test('ten uniquely identified bilingual outfit concepts', () => {
  assert.equal(outfits.length, 10);
  assert.equal(new Set(outfits.map((item) => item.id)).size, 10);
  for (const item of outfits) {
    assert.ok(/^MLCW-OUTFIT-[0-9]{3}$/.test(item.id));
    assert.ok(item.name && item.en && item.color && item.accent);
  }
});

test('each outfit produces clipped SVG garment layers', () => {
  for (const item of outfits) {
    const svg = outfitSvg(item);
    assert.ok(svg.includes('viewBox="0 0 1024 1536"'));
    assert.ok(svg.includes('clip-path="url(#blouse)"'));
    assert.ok(svg.includes('clip-path="url(#skirt)"'));
    assert.ok(svg.includes(item.color));
  }
});
