# whyshorts

Rendering pipeline for the "Why does…?" YouTube Shorts: each scene is a three.js + GSAP page,
captured frame by frame in headless Chrome and encoded with ffmpeg.

- `faucet-drip/` – scene 3 of "Why Does a Faucet Drip?" (realistic cutaway, 1080×1920, 30 fps)
- `render.js` – `node render.js <scene-dir> <out.mp4>` or `--stills 1.0,4.5`; `GL=cpu` for machines without a GPU
- `pod/setup.sh` – installs Chrome, Node, ffmpeg and Vulkan on a RunPod GPU pod and clones this repo

Textures and HDRI: Poly Haven (CC0).
