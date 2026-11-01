import { test, expect } from '@playwright/test';

test('studio loads Thiri and ten outfit choices', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Thiri’s Outfit Studio' })).toBeVisible();
  await expect(page.locator('#thiri-base')).toBeVisible();
  await expect(page.locator('[data-outfit]')).toHaveCount(10);
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
  await page.locator('#thiri-base').evaluate((img) => {
    if (!img.complete || !img.naturalWidth) throw new Error('Thiri base image did not load');
  });
  await page.locator('[data-outfit="MLCW-OUTFIT-001"]').click();
  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('button', { name: /Export PNG/ }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toMatch(/\.png$/i);
  const stream = await download.createReadStream();
  const chunks = [];
  for await (const chunk of stream) chunks.push(chunk);
  const png = Buffer.concat(chunks);
  expect(png.subarray(0, 8)).toEqual(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]));
  expect(png.readUInt32BE(16)).toBe(1024);
  expect(png.readUInt32BE(20)).toBe(1536);
});
