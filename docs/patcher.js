// In-browser builder: applies the BPS patch to the player's own Super Scribblenauts ROM (.nds or .zip)
// and hands back "Fairly OddParents - Magic Words.nds". Nothing is uploaded anywhere.
const PATCH_URL = 'https://raw.githubusercontent.com/NyteRyzer/fopgame/main/patches/fop-magic-words.bps';
const OUT_NAME = 'Fairly OddParents - Magic Words.nds';

const CRC_TABLE = (() => {
  const t = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    t[n] = c >>> 0;
  }
  return t;
})();

function crc32(b) {
  let c = 0xffffffff;
  for (let i = 0; i < b.length; i++) c = CRC_TABLE[(c ^ b[i]) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}

const u32 = (b, i) => (b[i] | b[i + 1] << 8 | b[i + 2] << 16 | b[i + 3] << 24) >>> 0;
const u16 = (b, i) => b[i] | b[i + 1] << 8;

function applyBps(src, patch) {
  if (String.fromCharCode(...patch.subarray(0, 4)) !== 'BPS1') throw new Error('Not a BPS patch.');
  let i = 4;
  const num = () => {
    let data = 0, shift = 1;
    for (;;) {
      const x = patch[i++];
      data += (x & 0x7f) * shift;
      if (x & 0x80) return data;
      shift *= 128;
      data += shift;
    }
  };
  const srcSize = num(), dstSize = num(), metaSize = num();
  i += metaSize;
  const crc = crc32(src);
  if (src.length === dstSize && crc === u32(patch, patch.length - 8)) {
    throw new Error('This ROM is already Fairly OddParents: Magic Words! Just play it.');
  }
  if (src.length !== srcSize || crc !== u32(patch, patch.length - 12)) {
    throw new Error('This is not a clean Super Scribblenauts (USA) ROM (expected CRC32 69F707EA).');
  }
  const dst = new Uint8Array(dstSize);
  let out = 0, srcRel = 0, dstRel = 0;
  const end = patch.length - 12;
  while (i < end) {
    const d = num(), cmd = d & 3, n = Math.floor(d / 4) + 1;
    if (cmd === 0) {
      dst.set(src.subarray(out, out + n), out); out += n;
    } else if (cmd === 1) {
      dst.set(patch.subarray(i, i + n), out); out += n; i += n;
    } else {
      const o = num(), off = o & 1 ? -Math.floor(o / 2) : Math.floor(o / 2);
      if (cmd === 2) {
        srcRel += off; dst.set(src.subarray(srcRel, srcRel + n), out); srcRel += n; out += n;
      } else {
        dstRel += off;
        for (let k = 0; k < n; k++) dst[out++] = dst[dstRel++];
      }
    }
  }
  if (crc32(dst) !== u32(patch, patch.length - 8)) throw new Error('Patched ROM failed its checksum.');
  return dst;
}

// first .nds inside a zip (stored or deflated), via the central directory
async function ndsFromZip(b) {
  let e = b.length - 22;
  while (e >= 0 && u32(b, e) !== 0x06054b50) e--;
  if (e < 0) throw new Error('Could not read the zip file.');
  let p = u32(b, e + 16);
  for (let k = u16(b, e + 10); k > 0; k--) {
    const method = u16(b, p + 10), size = u32(b, p + 20), nlen = u16(b, p + 28);
    const name = new TextDecoder().decode(b.subarray(p + 46, p + 46 + nlen));
    const local = u32(b, p + 42);
    p += 46 + nlen + u16(b, p + 30) + u16(b, p + 32);
    if (!/\.nds$/i.test(name)) continue;
    const start = local + 30 + u16(b, local + 26) + u16(b, local + 28);
    const data = b.subarray(start, start + size);
    if (method === 0) return data;
    if (method !== 8) throw new Error('Unsupported zip compression; unzip the ROM first.');
    const stream = new Blob([data]).stream().pipeThrough(new DecompressionStream('deflate-raw'));
    return new Uint8Array(await new Response(stream).arrayBuffer());
  }
  throw new Error('No .nds file found in the zip.');
}

async function build(file, status) {
  status('Reading your ROM…');
  let rom = new Uint8Array(await file.arrayBuffer());
  if (u32(rom, 0) === 0x04034b50) rom = await ndsFromZip(rom);
  status('Downloading the patch…');
  const res = await fetch(PATCH_URL);
  if (!res.ok) throw new Error('Could not download the patch (' + res.status + ').');
  const patch = new Uint8Array(await res.arrayBuffer());
  status('Building Fairly OddParents: Magic Words…');
  await new Promise(r => setTimeout(r, 30));
  const out = applyBps(rom, patch);
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([out], { type: 'application/octet-stream' }));
  a.download = OUT_NAME;
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 60000);
  status('Done! Your download "' + OUT_NAME + '" has started.', 'ok');
}

if (typeof document !== 'undefined') {
  const input = document.getElementById('rom');
  const msg = document.getElementById('status');
  const status = (t, kind) => { msg.textContent = t; msg.dataset.kind = kind || ''; };
  document.getElementById('get-rom').addEventListener('click', () => input.click());
  input.addEventListener('change', () => {
    if (input.files[0]) build(input.files[0], status).catch(e => status(e.message, 'error'));
    input.value = '';
  });
}

if (typeof module !== 'undefined') module.exports = { applyBps, crc32, ndsFromZip };
