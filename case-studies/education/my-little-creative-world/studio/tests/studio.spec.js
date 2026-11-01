import { test, expect } from '@playwright/test';
import { readFile } from 'node:fs/promises';

test('studio loads Thiri and ten outfit choices', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Thiri’s Outfit Studio' })).toBeVisible();
  await expect(page.locator('#thiri-base')).toBeVisible();
  await expect(page.locator('[data-outfit]')).toHaveCount(10);
});

test('immutable Thiri source fully decodes and retains its original lower pixel', async ({ page }) => {
  await page.goto('/');
  const image = page.locator('#thiri-base');
  const sample = await image.evaluate(async (img) => {
    await img.decode();
    if (img.naturalWidth !== 450 || img.naturalHeight !== 450) {
      throw new Error(`Unexpected Thiri dimensions: ${img.naturalWidth}x${img.naturalHeight}`);
    }
    const canvas = document.createElement('canvas');
    canvas.width = img.naturalWidth;
    canvas.height = img.naturalHeight;
    const context = canvas.getContext('2d');
    if (!context) throw new Error('Canvas 2D context unavailable');
    context.drawImage(img, 0, 0);
    const pixel = context.getImageData(220, 400, 1, 1).data;
    return { red: pixel[0], green: pixel[1], blue: pixel[2] };
  });
  // This point is in the lower purple htamein on the original reference.
  // It detects a partially decoded image that paints a grey block below the fold.
  expect(sample.red).toBeGreaterThan(80);
  expect(sample.green).toBeLessThan(90);
  expect(sample.blue).toBeGreaterThan(70);
});

test('neutral body-base overlay hides the original purple htamein without editing the source', async ({ page }) => {
  await page.goto('/');
  const result = await page.evaluate(async () => {
    const original = document.querySelector('#thiri-base');
    await original.decode();
    const svg = document.querySelector('#garment-overlay svg');
    if (!svg) throw new Error('Neutral base SVG was not rendered');
    const markup = new XMLSerializer().serializeToString(svg);
    const url = URL.createObjectURL(new Blob([markup], { type: 'image/svg+xml' }));
    try {
      const overlay = new Image();
      overlay.src = url;
      await overlay.decode();
      const canvas = document.createElement('canvas');
      canvas.width = 450;
      canvas.height = 450;
      const context = canvas.getContext('2d');
      if (!context) throw new Error('Canvas 2D context unavailable');
      context.drawImage(original, 0, 0);
      context.drawImage(overlay, 0, 0);
      const pixel = context.getImageData(220, 400, 1, 1).data;
      return { red: pixel[0], green: pixel[1], blue: pixel[2] };
    } finally {
      URL.revokeObjectURL(url);
    }
  });
  expect(result.red).toBeGreaterThan(220);
  expect(result.green).toBeGreaterThan(200);
  expect(result.blue).toBeGreaterThan(180);
  await expect(page.locator('#garment-overlay [data-layer="BODY_BASE_TOP"]')).toBeVisible();
  await expect(page.locator('#garment-overlay [data-layer="BODY_BASE_LOWER"]')).toBeVisible();
});

test('selection and reset work', async ({ page }) => {
  await page.goto('/');
  const first = page.locator('[data-outfit="MLCW-OUTFIT-001"]');
  await first.click();
  await expect(first).toHaveAttribute('aria-pressed', 'true');
  await expect(page.locator('#garment-overlay svg')).toBeVisible();
  await expect(page.locator('#garment-overlay [data-layer="BLOUSE"]')).toBeVisible();
  await expect(page.locator('#garment-overlay [data-layer="SASH"]')).toBeVisible();
  await expect(page.locator('#garment-overlay [data-layer="HTAMEIN"]')).toBeVisible();
  await expect(page.locator('#garment-overlay [data-layer="DETAILS"]')).toBeVisible();
  await page.getByRole('button', { name: /Reset/ }).click();
  await expect(first).toHaveAttribute('aria-pressed', 'false');
  await expect(page.locator('#garment-overlay [data-layer="BODY_BASE_LOWER"]')).toBeVisible();
  await expect(page.locator('#garment-overlay [data-layer="MLCW-OUTFIT-001"]')).toHaveCount(0);
});

test('keyboard activation works', async ({ page }) => {
  await page.goto('/');
  const first = page.locator('[data-outfit="MLCW-OUTFIT-001"]');
  await first.focus();
  await page.keyboard.press('Enter');
  await expect(first).toHaveAttribute('aria-pressed', 'true');
});

test('export downloads a PNG with 1024 by 1536 dimensions', async ({ page }) => {
  await page.goto('/');
  await page.waitForFunction(() => {
    const img = document.querySelector('#thiri-base');
    return Boolean(img && img.complete && img.naturalWidth > 0);
  }, { timeout: 10000 });
  await page.locator('[data-outfit="MLCW-OUTFIT-001"]').click();
  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('button', { name: /Export PNG/ }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toMatch(/\.png$/i);
  const png = await readFile(await download.path());
  expect(png.subarray(0, 8)).toEqual(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]));
  expect(png.readUInt32BE(16)).toBe(1024);
  expect(png.readUInt32BE(20)).toBe(1536);

  const margins = await page.evaluate(async (encoded) => {
    const image = new Image();
    image.src = `data:image/png;base64,${encoded}`;
    await image.decode();
    const canvas = document.createElement('canvas');
    canvas.width = image.naturalWidth;
    canvas.height = image.naturalHeight;
    const context = canvas.getContext('2d');
    if (!context) throw new Error('Canvas 2D context unavailable');
    context.drawImage(image, 0, 0);
    return {
      top: [...context.getImageData(512, 100, 1, 1).data],
      bottom: [...context.getImageData(512, 1400, 1, 1).data]
    };
  }, png.toString('base64'));
  // A centered square character on a portrait page leaves both vertical margins intact.
  expect(margins.top).toEqual([255, 250, 245, 255]);
  expect(margins.bottom).toEqual([255, 250, 245, 255]);
});
