/**
 * Minimal Strudel sound
 */

let soundReady = false;
const scale = ['c', 'd', 'e', 'g', 'a'];

function initSound() {
    try {
        if (typeof initStrudel === 'function') {
            initStrudel();
            soundReady = true;
        }
    } catch (e) {
        console.log('Sound init failed:', e);
    }
}

function playNav() {
    if (!soundReady) return;
    try {
        note("c5").sound("sine").gain(0.1).decay(0.05).sustain(0).play();
    } catch (e) {}
}

function playSelect(prob, depth) {
    if (!soundReady) return;
    try {
        const idx = Math.floor(prob * scale.length);
        const n = scale[Math.min(idx, scale.length - 1)];
        const oct = 3 + Math.min(depth, 3);
        note(`${n}${oct}`).sound("sawtooth").gain(0.2).decay(0.2).sustain(0.1).release(0.3).lpf(1200).play();
    } catch (e) {}
}
