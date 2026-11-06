import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..');
const manifest = JSON.parse(await readFile(path.join(root, 'artwork/layer-manifest.json'), 'utf8'));

function gitBlobSha1(buffer) {
  const header = Buffer.from('blob ' + buffer.length + String.fromCharCode(0), 'utf8');
  return createHash('sha1').update(header).update(buffer).digest('hex');
}

function jpegDimensions(buffer) {
  assert.equal(buffer.subarray(0, 2).toString('hex'), 'ffd8', 'source must begin with JPEG SOI');
  const sofMarkers = new Set([0xc0, 0xc1, 0xc2, 0xc3, 0xc5, 0xc6, 0xc7, 0xc9, 0xca, 0xcb, 0xcd, 0xce, 0xcf]);
  let offset = 2;
  while (offset + 8 < buffer.length) {
    if (buffer[offset] !== 0xff) { offset += 1; continue; }
    const marker = buffer[offset + 1];
    offset += 2;
    if (marker === 0xd8 || marker === 0xd9 || marker === 0x01 || (marker >= 0xd0 && marker <= 0xd7)) continue;
    const segmentLength = buffer.readUInt16BE(offset);
    if (sofMarkers.has(marker)) {
      return {
        height: buffer.readUInt16BE(offset + 3),
        width: buffer.readUInt16BE(offset + 5),
        components: buffer[offset + 7]
      };
    }
    offset += segmentLength;
  }
  throw new Error('JPEG frame dimensions not found');
}

test('layer manifest defines the expected character and artwork coordinate system', () => {
  assert.equal(manifest.project_id, 'MLCW-MYANMAR-001');
  assert.equal(manifest.character_id, 'MLCW-CHAR-001');
  assert.deepEqual(manifest.canvas, {
    width: 450,
    height: 450,
    coordinate_system: 'source-pixel',
    color_mode: 'RGB'
  });
  assert.equal(manifest.layer_stack.filter(layer => layer.type === 'outfit-group').length, 10);
  for (const layer of manifest.layer_stack.filter(layer => layer.type === 'outfit-group')) {
    assert.deepEqual(layer.layers, ['BLOUSE', 'SASH', 'HTAMEIN', 'DETAILS']);
  }
});

test('repository Thiri source is byte-identical to the immutable original reference', async () => {
  const sourcePath = path.join(root, manifest.source_reference.path);
  const bytes = await readFile(sourcePath);
  const sha256 = createHash('sha256').update(bytes).digest('hex');
  const gitSha = gitBlobSha1(bytes);
  const dimensions = jpegDimensions(bytes);

  assert.equal(bytes.length, manifest.source_reference.bytes,
    `Source byte count mismatch: found ${bytes.length}, expected ${manifest.source_reference.bytes}`);
  assert.equal(sha256, manifest.source_reference.sha256,
    `Source SHA-256 mismatch: found ${sha256}`);
  assert.equal(gitSha, manifest.source_reference.git_blob_sha1,
    `Git blob SHA mismatch: found ${gitSha}`);
  assert.deepEqual(dimensions, { width: 450, height: 450, components: 3 });
});
