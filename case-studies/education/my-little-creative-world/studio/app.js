import { outfits, outfitSvg } from './src/outfits.js';

const grid = document.querySelector('#outfit-grid');
const overlay = document.querySelector('#garment-overlay');
const status = document.querySelector('#selection-status');
const character = document.querySelector('#thiri-base');
let selected = null;

function selectOutfit(id) {
  selected = outfits.find((item) => item.id === id) ?? null;
  overlay.innerHTML = selected ? outfitSvg(selected) : '';
  document.querySelectorAll('[data-outfit]').forEach((button) => {
    const active = button.dataset.outfit === id;
    button.setAttribute('aria-pressed', String(active));
    button.classList.toggle('selected', active);
  });
  status.textContent = selected
    ? `ရွေးချယ်ထားသည် — ${selected.name} (${selected.en})`
    : 'မူလဝတ်စုံ · Base outfit restored.';
}

grid.innerHTML = outfits.map((item, index) => `
  <button class="choice" type="button" data-outfit="${item.id}" aria-pressed="false">
    <i style="--c:${item.color};--a:${item.accent}"></i>
    <span>
      <b>${String(index + 1).padStart(2, '0')} · ${item.name}</b>
      <small>${item.en}</small>
    </span>
  </button>
`).join('');

grid.addEventListener('click', (event) => {
  const button = event.target.closest('[data-outfit]');
  if (button) selectOutfit(button.dataset.outfit);
});

function downloadPng(canvas) {
  canvas.toBlob((blob) => {
    if (!blob) {
      status.textContent = 'PNG export မအောင်မြင်ပါ။';
      return;
    }
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.download = `thiri-${selected?.id.toLowerCase() ?? 'base'}.png`;
    anchor.href = url;
    anchor.click();
    window.setTimeout(() => URL.revokeObjectURL(url), 30000);
    status.textContent = 'PNG ဖိုင်ကို ထုတ်ပေးပြီးပါပြီ။';
  }, 'image/png');
}

async function exportPng() {
  try {
    await character.decode();
    const sourceWidth = character.naturalWidth;
    const sourceHeight = character.naturalHeight;
    if (!sourceWidth || !sourceHeight) {
      throw new Error('Thiri image has no intrinsic dimensions');
    }

    const canvas = document.createElement('canvas');
    canvas.width = 1024;
    canvas.height = 1536;
    const context = canvas.getContext('2d');
    if (!context) throw new Error('Canvas 2D context is unavailable');

    context.fillStyle = '#fffaf5';
    context.fillRect(0, 0, canvas.width, canvas.height);

    // Fit, never stretch: the 450×450 source remains square on the portrait page.
    const scale = Math.min(
      canvas.width / sourceWidth,
      canvas.height / sourceHeight
    );
    const drawWidth = sourceWidth * scale;
    const drawHeight = sourceHeight * scale;
    const left = (canvas.width - drawWidth) / 2;
    const top = (canvas.height - drawHeight) / 2;

    context.drawImage(character, left, top, drawWidth, drawHeight);

    if (selected) {
      const svgBlob = new Blob([outfitSvg(selected)], {
        type: 'image/svg+xml;charset=utf-8'
      });
      const svgUrl = URL.createObjectURL(svgBlob);
      try {
        const garmentLayer = new Image();
        garmentLayer.src = svgUrl;
        await garmentLayer.decode();
        context.drawImage(garmentLayer, left, top, drawWidth, drawHeight);
      } finally {
        URL.revokeObjectURL(svgUrl);
      }
    }

    downloadPng(canvas);
  } catch (error) {
    status.textContent = `PNG export မအောင်မြင်ပါ: ${error.message}`;
  }
}

document.querySelector('#reset-button').addEventListener('click', () => selectOutfit(null));
document.querySelector('#export-button').addEventListener('click', exportPng);
selectOutfit(null);
