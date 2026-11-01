import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('studio has no critical or serious automated WCAG 2.1 A/AA violations', async ({ page }, testInfo) => {
  await page.goto('/');
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
    .analyze();
  await testInfo.attach('axe-accessibility-results', {
    body: JSON.stringify(results, null, 2),
    contentType: 'application/json'
  });
  const blocking = results.violations.filter((item) =>
    item.impact === 'critical' || item.impact === 'serious'
  );
  expect(blocking, JSON.stringify(blocking, null, 2)).toEqual([]);
});
