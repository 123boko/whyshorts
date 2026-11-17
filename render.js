// Render a scene page to MP4 (or stills) with headless Chrome.
//   node render.js <scene-dir> <out.mp4>                 full video
//   node render.js <scene-dir> --stills 1.0,4.5          JPEG stills
//   node render.js --gpuinfo                             print the WebGL renderer in use
// Env: CHROME (browser path), GL=gpu|cpu (default gpu), QUERY (extra ?query for the page)
const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const puppeteer = require('puppeteer-core');

const log = (...a) => process.stderr.write(a.join(' ') + '\n');
const ROOT = __dirname;
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.glb': 'model/gltf-binary',
  '.json': 'application/json', '.jpg': 'image/jpeg', '.png': 'image/png', '.hdr': 'application/octet-stream' };

const GL_FLAGS = {
  gpu: ['--use-gl=angle', '--use-angle=gl-egl', '--disable-features=Vulkan', '--ignore-gpu-blocklist'],
  cpu: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'],
};

function serve() {
  return new Promise((resolve) => {
    const srv = http.createServer((req, res) => {
      const p = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
      if (!p.startsWith(ROOT) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); return res.end(); }
      res.writeHead(200, { 'Content-Type': TYPES[path.extname(p)] || 'application/octet-stream' });
      fs.createReadStream(p).pipe(res);
    });
    srv.listen(0, '127.0.0.1', () => resolve(srv));
  });
}

async function launch() {
  const mode = process.env.GL || 'gpu';
  return puppeteer.launch({
    executablePath: process.env.CHROME || '/usr/bin/google-chrome', headless: true,
    args: ['--no-sandbox', '--no-proxy-server', '--disable-dev-shm-usage', '--font-render-hinting=none', ...GL_FLAGS[mode]],
  });
}

(async () => {
  const args = process.argv.slice(2);
  const srv = await serve();
  const browser = await launch();
  const page = await browser.newPage();
  page.on('console', (m) => { const t = m.text(); if (!t.includes('GPU stall')) log('[page]', t); });
  page.on('pageerror', (e) => log('[pageerror]', e.message));
  await page.setViewport({ width: 1080, height: 1920, deviceScaleFactor: 1 });
  const base = `http://127.0.0.1:${srv.address().port}`;

  if (args[0] === '--gpuinfo') {
    await page.goto(base + '/package.json');
    const info = await page.evaluate(() => {
      const gl = document.createElement('canvas').getContext('webgl2');
      if (!gl) return 'no webgl2';
      const ext = gl.getExtension('WEBGL_debug_renderer_info');
      return ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER);
    });
    log('WebGL renderer:', info);
    await browser.close(); srv.close(); return;
  }

  const scene = args[0];
  const query = process.env.QUERY ? '?' + process.env.QUERY : '';
  await page.goto(`${base}/${scene}/index.html${query}`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  const ok = await page.evaluate(() => window.ready);
  if (!ok) throw new Error('scene failed to load');

  const si = args.indexOf('--stills');
  if (si >= 0) {
    for (const t of args[si + 1].split(',').map(Number)) {
      const t0 = Date.now();
      await page.evaluate((t) => window.renderAt(t), t);
      const out = path.join(scene, `still_${t.toFixed(2)}.jpg`);
      await page.screenshot({ path: out, type: 'jpeg', quality: 92 });
      log(`still ${out} ${Date.now() - t0} ms`);
    }
  } else {
    const out = args[1] || path.join(scene, 'out.mp4');
    const { FPS, DURATION } = await page.evaluate(() => window.meta);
    const frames = Math.round(FPS * DURATION);
    const tmp = out.replace(/\.mp4$/, '.part.mp4');
    const ff = spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
      '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', tmp],
      { stdio: ['pipe', 'inherit', 'inherit'] });
    const t0 = Date.now();
    for (let i = 0; i < frames; i++) {
      await page.evaluate((t) => window.renderAt(t), i / FPS);
      const buf = await page.screenshot({ type: 'jpeg', quality: 92 });
      if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
      if (i % 30 === 0) log(`frame ${i}/${frames}  ${((Date.now() - t0) / (i + 1)).toFixed(0)} ms/frame`);
    }
    ff.stdin.end();
    const code = await new Promise((r) => ff.on('close', r));
    if (code !== 0) throw new Error('ffmpeg exited ' + code);
    fs.renameSync(tmp, out);
    log(`done ${frames} frames in ${((Date.now() - t0) / 1000).toFixed(1)} s -> ${out}`);
  }
  await browser.close(); srv.close();
})().catch((e) => { log(String(e && e.stack || e)); process.exit(1); });
