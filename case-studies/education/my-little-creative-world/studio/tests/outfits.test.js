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

test('each outfit overlay uses the original square character coordinate system', () => {
  for (const item of outfits) {
    const svg = outfitSvg(item);
    assert.ok(svg.includes('viewBox="0 0 450 450"'));
    assert.ok(svg.includes('clip-path="url(#blouse)"'));
    assert.ok(svg.includes('clip-path="url(#sash)"'));
    assert.ok(svg.includes('clip-path="url(#htamein)"'));
    assert.ok(svg.includes(item.color));
  }
});
