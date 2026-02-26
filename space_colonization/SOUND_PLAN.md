# Sound Integration Plan

## Overview

Integrate Strudel for generative audio that responds to the token tree visualization. The sound design should complement the organic, exploratory nature of the space colonization algorithm.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     sketch.js (p5.js)                       │
│                                                             │
│   ┌───────────────┐   ┌───────────────┐   ┌──────────────┐ │
│   │ keyPressed()  │──▶│ sound.js API  │──▶│   Strudel    │ │
│   │ selectToken() │   │               │   │   Engine     │ │
│   │ growOneStep() │   └───────────────┘   └──────────────┘ │
│   └───────────────┘                                         │
└─────────────────────────────────────────────────────────────┘
```

## Sound Events

| Event | Trigger Point | Sound Character |
|-------|--------------|-----------------|
| **Navigation** | Arrow key pressed | Subtle tick/blip, pitch varies by position in list |
| **Selection** | Space/Right arrow | Harmonic chord, intensity based on probability |
| **Branch Growth** | Each growth step | Soft percussive click, panning follows branch position |
| **Background Growth** | Missed branches growing | Very quiet, ambient texture, like distant whispers |
| **Ambient Drone** | Continuous | Low evolving pad, pitch/texture changes with tree depth |

## Parameter Mappings

### Probability → Pitch
```
prob = 0.0 (unlikely)  → Lower notes (C3, D3, E3)
prob = 1.0 (certain)   → Higher notes (C5, E5, G5)
```

### Tree Depth → Octave/Timbre
```
depth = 0 (root)       → Bass register, warm timbre
depth = 5+             → Higher register, brighter timbre
```

### Position → Stereo Pan
```
x = 0 (left edge)      → Pan -1.0 (left speaker)
x = width (right edge) → Pan +1.0 (right speaker)
```

### Node Count → Harmonic Density
```
few nodes              → Simple intervals (octaves, fifths)
many nodes             → Richer chords (7ths, 9ths, clusters)
```

## Strudel Patterns

### Navigation Sound
```javascript
// Quick sine blip, pitch based on list position
note(`c${4 + positionOffset}`)
  .sound("sine")
  .gain(0.1)
  .decay(0.05)
  .sustain(0)
  .play();
```

### Selection Sound
```javascript
// Chord based on probability and depth
const baseNote = scaleNote(probability);
const octave = 3 + Math.min(depth, 3);

note(`<${baseNote}${octave} ${baseNote}${octave+1}>`)
  .sound("sawtooth")
  .gain(0.2 * probability)
  .attack(0.01)
  .decay(0.3)
  .sustain(0.1)
  .release(0.5)
  .lpf(800 + probability * 2000)
  .play();
```

### Branch Growth Sound
```javascript
// Soft click, panned by x position
note("c6")
  .sound("triangle")
  .gain(0.05)
  .decay(0.02)
  .sustain(0)
  .pan(mapToPan(branchX))
  .play();
```

### Ambient Drone
```javascript
// Evolving pad based on tree state
// Run continuously, parameters updated periodically
note(`<c${droneOctave} e${droneOctave} g${droneOctave}>`)
  .sound("sine")
  .gain(0.08)
  .lpf(400 + treeDepth * 100)
  .room(0.8)
  .slow(8)
  .play();
```

## Implementation Steps

### Step 1: Update index.html
- Add Strudel library CDN
- Load sound.js before sketch.js
- Add click handler for audio context initialization (browser requirement)

### Step 2: Expand sound.js
- Add all sound event functions
- Implement parameter mapping utilities
- Add ambient drone management
- Add mute toggle

### Step 3: Integrate into sketch.js
- Call `initSound()` in setup or on first user interaction
- Call `playNav()` in `keyPressed()` for UP/DOWN
- Call `playSelect(prob, depth)` in `selectToken()`
- Call `playGrowth(x)` in `growOneStep()`
- Call `playMissedGrowth()` in `growMissedBranchesStep()`
- Update drone in `draw()` based on tree state

### Step 4: Add Controls
- 'M' key to mute/unmute all sound
- Volume control (optional slider in UI)

## File Changes Summary

### index.html
```html
<!-- Add before </head> -->
<script src="https://unpkg.com/@strudel/web@1.0.3"></script>

<!-- Add after sketch.js -->
<script src="sound.js"></script>

<!-- Audio init overlay -->
<div id="audio-init" onclick="startAudio()">
  Click to enable sound
</div>
```

### sound.js (expanded)
```javascript
let soundEnabled = false;
let muted = false;

function startAudio() {
    initStrudel();
    soundEnabled = true;
    document.getElementById('audio-init').style.display = 'none';
}

function playNav(index, total) { ... }
function playSelect(prob, depth, x) { ... }
function playGrowth(x, isMissed) { ... }
function updateDrone(depth, nodeCount) { ... }
function toggleMute() { ... }
```

### sketch.js
```javascript
// In keyPressed()
if (keyCode === UP_ARROW) {
    selectedOptionIndex = ...;
    playNav(selectedOptionIndex, tokenOptions.length);
}

// In selectToken()
let depth = selectedPath.length;
playSelect(selected.prob, depth, currentNode.pos.x / width);

// In growOneStep()
if (!isMissed) {
    playGrowth(newPos.x / width, false);
}

// In draw() (throttled)
if (frameCount % 60 === 0) {
    updateDrone(selectedPath.length, nodes.length);
}

// Add to keyPressed()
if (key === 'm' || key === 'M') {
    toggleMute();
}
```

## Scale/Harmony Reference

Using pentatonic scale for pleasant, non-clashing tones:
```javascript
const scale = ['c', 'd', 'e', 'g', 'a'];  // C major pentatonic
```

For more tension as tree grows deeper:
```javascript
const scales = {
    0: ['c', 'd', 'e', 'g', 'a'],           // Pentatonic (calm)
    3: ['c', 'd', 'e', 'f', 'g', 'a', 'b'], // Major (neutral)
    6: ['c', 'd', 'eb', 'f', 'g', 'ab', 'bb'] // Natural minor (tense)
};
```

## Browser Audio Requirements

Modern browsers require user interaction before playing audio. The implementation handles this with:
1. Initial overlay prompting user to click
2. `initStrudel()` called on first click
3. All subsequent sounds work without further interaction

## Testing Checklist

- [ ] Sound plays on navigation (UP/DOWN keys)
- [ ] Sound plays on token selection
- [ ] Sound pans correctly left-to-right as tree grows
- [ ] Probability affects pitch/intensity
- [ ] Tree depth affects timbre
- [ ] Mute toggle works
- [ ] No audio glitches/pops
- [ ] Ambient drone evolves smoothly
- [ ] Sound doesn't overwhelm visuals
- [ ] Works after page refresh (click to init)
