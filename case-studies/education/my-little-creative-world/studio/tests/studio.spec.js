import { test, expect } from '@playwright/test';
import { readFile } from 'node:fs/promises';

test('studio loads Thiri and ten outfit choices', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Thiri’s Outfit Studio' })).toBeVisible();
  await expect(page.locator('#thiri-base')).toBeVisible();
  await expect(page.locator('[data-outfit]')).toHaveCount(10);
});

test('Thiri image fully decodes and retains the lower purple outfit', async ({ page }) => {
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

test('selection and reset work', async ({ page }) => {
  await page.goto('/');
  const first = page.locator('[data-outfit="MLCW-OUTFIT-001"]');
  await first.click();
  await expect(first).toHaveAttribute('aria-pressed', 'true');
  await expect(page.locator('#garment-overlay svg')).toBeVisible();
  await page.getByRole('button', { name: /Reset/ }).click();
  await expect(first).toHaveAttribute('aria-pressed', 'false');
  await expect(page.locator('#garment-overlay')).toBeEmpty();
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
});
