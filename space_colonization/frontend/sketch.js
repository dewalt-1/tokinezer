// Token Space Colonization - Incremental Growth
// Tree grows on-demand as user selects tokens

// Algorithm parameters
let SegmentLength = 4;          // Smaller steps for organic look
let AttractionDistance = 60;    // Range for attractor influence
let KillDistance = 8;
let NumAttractors = 8000;
let UseNoiseDistribution = true;
let GrowthStepsPerChoice = 8;   // Fewer steps per selection (slower)
let MinTokenOptions = 5;        // Min token choices
let MaxTokenOptions = 10;       // Max token choices
let BackgroundGrowthRate = 3;   // Frames between background growth steps

// Debug mode
let showAttractors = true;

// Data structures
let attractors;
let nodes;

// State machine
let state = 'INIT';  // INIT -> WAITING_FOR_TOKENS -> CHOOSING -> GROWING -> WAITING_FOR_TOKENS ...
let currentPrompt = 'Once upon a time';
let tokenOptions = [];      // Current token options (5-10)
let selectedOptionIndex = 0;
let growthTarget = null;    // Direction/region to grow toward
let growthStepsRemaining = 0;
let missedDirections = [];  // Directions user didn't choose
let frameCounter = 0;       // For background growth timing

// Navigation (for viewing history)
let currentNode = null;
let selectedPath = [];      // Track the path of selected nodes

// WebSocket
let ws;
let wsConnected = false;

function setup() {
    createCanvas(windowWidth, windowHeight);
    textFont('monospace');
    textSize(12);

    initAttractors();
    initTree();
    connectWebSocket();
}

function initAttractors() {
    attractors = [];

    if (UseNoiseDistribution) {
        let noiseScale = 0.01;
        let threshold = 0.4;
        let attempts = 0;
        let maxAttempts = NumAttractors * 10;

        while (attractors.length < NumAttractors && attempts < maxAttempts) {
            let x = random(width);
            let y = random(height);
            let n = noise(x * noiseScale, y * noiseScale);

            if (n > threshold) {
                attractors.push({
                    pos: createVector(x, y),
                    active: true
                });
            }
            attempts++;
        }
        console.log('Created', attractors.length, 'attractors');
    } else {
        for (let i = 0; i < NumAttractors; i++) {
            attractors.push({
                pos: createVector(random(width), random(height)),
                active: true
            });
        }
    }
}

function initTree() {
    nodes = [];
    missedTips = [];
    selectedPath = [];

    // Single root node
    let root = {
        id: 0,
        pos: createVector(100, height / 2),
        parent: null,
        children: [],
        token: null,
        prob: null,
        isSelected: true,  // Root is always on the selected path
        isMissed: false
    };
    nodes.push(root);
    selectedPath.push(root);
    currentNode = root;
}

function connectWebSocket() {
    ws = new WebSocket('ws://localhost:8000/ws');

    ws.onopen = function() {
        console.log('Connected to backend');
        wsConnected = true;
        // Request first set of tokens
        requestTokenOptions();
    };

    ws.onmessage = function(event) {
        let data = JSON.parse(event.data);

        if (data.type === 'token_options') {
            tokenOptions = data.options;
            selectedOptionIndex = 0;
            state = 'CHOOSING';
            console.log('Received', tokenOptions.length, 'token options');
        }
    };

    ws.onclose = function() {
        wsConnected = false;
        console.log('Disconnected');
    };

    ws.onerror = function(err) {
        console.error('WebSocket error:', err);
    };
}

function requestTokenOptions() {
    state = 'WAITING_FOR_TOKENS';

    // Random number of options between 5-10
    let count = floor(random(MinTokenOptions, MaxTokenOptions + 1));

    ws.send(JSON.stringify({
        action: 'get_options',
        prompt: currentPrompt,
        count: count
    }));
}

function draw() {
    background(0);
    frameCounter++;

    // Draw attractors (debug)
    if (showAttractors) {
        noStroke();
        fill(30, 30, 50);
        for (let a of attractors) {
            if (a.active) {
                ellipse(a.pos.x, a.pos.y, 2, 2);
            }
        }
    }

    // Handle growth state
    if (state === 'GROWING' && growthStepsRemaining > 0) {
        growOneStep(false);  // Grow main branch (not missed)
        growthStepsRemaining--;

        if (growthStepsRemaining === 0) {
            // Done growing main branch, now start missed branches
            startMissedBranches();
            // Request next tokens
            requestTokenOptions();
        }
    }

    // Background growth: while user is choosing, missed branches keep growing
    if ((state === 'CHOOSING' || state === 'WAITING_FOR_TOKENS') && frameCounter % BackgroundGrowthRate === 0) {
        growMissedBranchesStep();
    }

    // Draw tree
    drawTree();

    // Draw token options if choosing
    if (state === 'CHOOSING') {
        drawTokenOptions();
    }

    // Draw current prompt at bottom
    drawPromptBar();

}

function growOneStep(isMissed, customTip, customTarget) {
    // Grow from current node or custom tip
    let tip = customTip || currentNode;
    let target = customTarget || growthTarget;
    if (!tip) return null;

    let margin = 40;
    let bottomMargin = 80;  // Account for prompt bar

    // Calculate edge repulsion force if near edges
    let edgeRepulsion = createVector(0, 0);
    let edgeThreshold = 60;  // Start repelling when this close to edge

    if (tip.pos.x < edgeThreshold) {
        edgeRepulsion.x += (edgeThreshold - tip.pos.x) / edgeThreshold;
    }
    if (tip.pos.x > width - edgeThreshold) {
        edgeRepulsion.x -= (tip.pos.x - (width - edgeThreshold)) / edgeThreshold;
    }
    if (tip.pos.y < edgeThreshold) {
        edgeRepulsion.y += (edgeThreshold - tip.pos.y) / edgeThreshold;
    }
    if (tip.pos.y > height - bottomMargin - edgeThreshold + 20) {
        edgeRepulsion.y -= (tip.pos.y - (height - bottomMargin - edgeThreshold + 20)) / edgeThreshold;
    }

    // Find attractors within range, biased toward target direction
    let nearbyAttractors = [];
    for (let a of attractors) {
        if (a.active) {
            let d = tip.pos.dist(a.pos);
            if (d < AttractionDistance) {
                // If we have a target, prefer attractors in that direction
                if (target) {
                    let toAttractor = p5.Vector.sub(a.pos, tip.pos).normalize();
                    let alignment = p5.Vector.dot(toAttractor, target);
                    // Only include attractors somewhat aligned with target (> -0.3)
                    if (alignment > -0.3) {
                        nearbyAttractors.push({ attractor: a, alignment: alignment });
                    }
                } else {
                    nearbyAttractors.push({ attractor: a, alignment: 1 });
                }
            }
        }
    }

    // Calculate direction
    let avgDir;
    if (nearbyAttractors.length === 0) {
        // No attractors nearby, continue in target direction with slight randomness
        if (target) {
            avgDir = target.copy();
            // Add slight randomness for organic feel
            avgDir.rotate(random(-0.2, 0.2));
        } else {
            return null;
        }
    } else {
        // Calculate weighted average direction toward attractors
        avgDir = createVector(0, 0);
        for (let item of nearbyAttractors) {
            let dir = p5.Vector.sub(item.attractor.pos, tip.pos);
            dir.normalize();
            // Weight by alignment with target
            let weight = 0.5 + item.alignment * 0.5;
            dir.mult(weight);
            avgDir.add(dir);
        }

        // Blend with target direction
        if (target) {
            avgDir.add(p5.Vector.mult(target, 0.5));
        }
    }

    // Apply edge repulsion (stronger effect when near edges)
    if (edgeRepulsion.mag() > 0) {
        avgDir.add(p5.Vector.mult(edgeRepulsion, 2));
    }

    avgDir.normalize();
    avgDir.mult(SegmentLength);

    // Create new node
    let newPos = p5.Vector.add(tip.pos, avgDir);

    // Constrain to canvas bounds (with margin)
    newPos.x = constrain(newPos.x, margin, width - margin);
    newPos.y = constrain(newPos.y, margin, height - bottomMargin);

    let newNode = {
        id: nodes.length,
        pos: newPos,
        parent: tip,
        children: [],
        token: null,
        prob: null,
        isSelected: !isMissed,
        isMissed: isMissed
    };

    tip.children.push(newNode);
    nodes.push(newNode);

    if (!isMissed) {
        currentNode = newNode;
        selectedPath.push(newNode);
    }

    // Kill nearby attractors (only for main branch, not missed)
    if (!isMissed) {
        for (let a of attractors) {
            if (a.active && a.pos.dist(newPos) < KillDistance) {
                a.active = false;
            }
        }
    }

    return newNode;
}

function startMissedBranches() {
    // Start branches for the directions not chosen
    if (missedDirections.length === 0) return;

    // Find the branch point (where we started this growth cycle)
    let branchPoint = selectedPath[selectedPath.length - GrowthStepsPerChoice - 1];
    if (!branchPoint) branchPoint = selectedPath[0];

    for (let dir of missedDirections) {
        // Create initial seed node in missed direction
        // These will then grow via space colonization in growMissedBranchesStep
        growOneStep(true, branchPoint, dir);
    }

    missedDirections = [];
}

function growMissedBranchesStep() {
    // TRUE space colonization algorithm with BRANCHING:
    // 1. For each attractor, find the closest node among ALL missed nodes
    // 2. If closest node is a tip (no children), it gets influenced
    // 3. Group attractors by angular direction - if spread is wide, CREATE MULTIPLE BRANCHES
    // 4. Kill attractors that are too close to any missed node

    // Get ALL missed nodes (for distance checking)
    let allMissedNodes = [];
    for (let node of nodes) {
        if (node.isMissed) {
            allMissedNodes.push(node);
        }
    }

    if (allMissedNodes.length === 0) return;

    // Get tip nodes only (nodes that can grow)
    let tipNodes = [];
    for (let node of allMissedNodes) {
        if (node.children.length === 0) {
            tipNodes.push(node);
        }
    }

    if (tipNodes.length === 0) return;

    // Map: tip node -> list of influencing attractors
    let tipInfluences = new Map();
    for (let tip of tipNodes) {
        tipInfluences.set(tip, []);
    }

    // For each active attractor, find the closest missed node (any, not just tips)
    // But only add influence if the closest node is a tip
    for (let a of attractors) {
        if (!a.active) continue;

        let closestNode = null;
        let closestDist = AttractionDistance;

        // Check ALL missed nodes for closest
        for (let node of allMissedNodes) {
            let d = node.pos.dist(a.pos);
            if (d < closestDist) {
                closestDist = d;
                closestNode = node;
            }
        }

        // Only influence if the closest node is a tip (can grow)
        if (closestNode && closestNode.children.length === 0) {
            tipInfluences.get(closestNode).push(a);
        }
    }

    // Grow tips that have influencing attractors
    let grownCount = 0;
    let maxGrowPerStep = 20;

    for (let [tip, influencers] of tipInfluences) {
        if (influencers.length === 0) continue;
        if (grownCount >= maxGrowPerStep) break;

        // Calculate angles of all influencing attractors relative to tip
        let attractorAngles = [];
        for (let a of influencers) {
            let dir = p5.Vector.sub(a.pos, tip.pos);
            let angle = atan2(dir.y, dir.x);
            attractorAngles.push({ attractor: a, angle: angle, dir: dir.normalize() });
        }

        // Sort by angle
        attractorAngles.sort((a, b) => a.angle - b.angle);

        // Find clusters of attractors (detect gaps > threshold to split into branches)
        let clusters = [];
        let currentCluster = [attractorAngles[0]];
        let branchAngleThreshold = PI / 4;  // 45 degrees gap = new branch

        for (let i = 1; i < attractorAngles.length; i++) {
            let angleDiff = attractorAngles[i].angle - attractorAngles[i-1].angle;
            if (angleDiff > branchAngleThreshold) {
                // Gap detected, start new cluster
                clusters.push(currentCluster);
                currentCluster = [attractorAngles[i]];
            } else {
                currentCluster.push(attractorAngles[i]);
            }
        }
        clusters.push(currentCluster);

        // Also check wrap-around gap (from last to first)
        if (clusters.length > 1) {
            let wrapGap = (attractorAngles[0].angle + TWO_PI) - attractorAngles[attractorAngles.length-1].angle;
            if (wrapGap <= branchAngleThreshold) {
                // Merge first and last clusters
                let lastCluster = clusters.pop();
                clusters[0] = lastCluster.concat(clusters[0]);
            }
        }

        // Create a branch for each cluster
        for (let cluster of clusters) {
            if (grownCount >= maxGrowPerStep) break;

            // Average direction for this cluster
            let avgDir = createVector(0, 0);
            for (let item of cluster) {
                avgDir.add(item.dir);
            }
            avgDir.normalize();
            avgDir.mult(SegmentLength);

            // Create new node
            let newPos = p5.Vector.add(tip.pos, avgDir);

            // Constrain to canvas
            let margin = 20;
            let bottomMargin = 70;
            newPos.x = constrain(newPos.x, margin, width - margin);
            newPos.y = constrain(newPos.y, margin, height - bottomMargin);

            let newNode = {
                id: nodes.length,
                pos: newPos,
                parent: tip,
                children: [],
                token: null,
                prob: null,
                isSelected: false,
                isMissed: true
            };

            tip.children.push(newNode);
            nodes.push(newNode);
            grownCount++;
        }
    }

    // Kill attractors that are too close to ANY missed node (including newly created)
    for (let a of attractors) {
        if (!a.active) continue;

        for (let node of nodes) {
            if (node.isMissed && a.pos.dist(node.pos) < KillDistance) {
                a.active = false;
                break;
            }
        }
    }
}

function drawTree() {
    // Draw missed branches first (white, thin)
    for (let node of nodes) {
        if (node.parent && node.isMissed) {
            stroke(255);
            strokeWeight(0.5);
            line(node.parent.pos.x, node.parent.pos.y, node.pos.x, node.pos.y);
        }
    }

    // Draw selected path branches (white, thick)
    for (let node of nodes) {
        if (node.parent && node.isSelected) {
            stroke(255);
            strokeWeight(2.5);
            line(node.parent.pos.x, node.parent.pos.y, node.pos.x, node.pos.y);
        }
    }

    // Draw tokens on selected path
    textAlign(LEFT, CENTER);
    textSize(9);
    for (let node of nodes) {
        if (node.isSelected && node.token) {
            // Position label slightly offset from node
            let labelX = node.pos.x + 5;
            let labelY = node.pos.y - 8;

            // Format token for display
            let displayToken = node.token.replace(/\n/g, '↵');
            if (displayToken.length > 8) {
                displayToken = displayToken.substring(0, 7) + '…';
            }

            // Draw with slight background for readability
            fill(0, 0, 0, 150);
            noStroke();
            rect(labelX - 2, labelY - 6, textWidth(displayToken) + 4, 12, 2);

            fill(200, 200, 255);
            text(displayToken, labelX, labelY);
        }
    }

    // Draw current position marker
    if (currentNode) {
        fill(255, 200, 0);
        noStroke();
        ellipse(currentNode.pos.x, currentNode.pos.y, 10, 10);
    }
}

function drawTokenOptions() {
    if (tokenOptions.length === 0) return;

    let tip = currentNode;
    if (!tip) return;

    // Find attractors and cluster them into directions
    let directions = getDirectionClusters(tip, tokenOptions.length);

    // Draw token options as a list near the current tip
    let listX = tip.pos.x + 40;
    let listY = tip.pos.y - (tokenOptions.length * 20) / 2;

    // Clamp to screen bounds
    listX = min(listX, width - 320);
    listY = max(listY, 30);
    listY = min(listY, height - tokenOptions.length * 20 - 60);

    // Background for readability
    fill(0, 0, 0, 200);
    noStroke();
    rect(listX - 10, listY - 14, 310, tokenOptions.length * 20 + 12, 5);

    // Find max probability for normalization
    let maxProb = 0;
    for (let token of tokenOptions) {
        if (token.prob > maxProb) maxProb = token.prob;
    }

    let barLength = 10;  // Total characters in the bar

    for (let i = 0; i < tokenOptions.length; i++) {
        let token = tokenOptions[i];
        let y = listY + i * 20;

        // Normalize probability (0-1 relative to max)
        let normalizedProb = maxProb > 0 ? token.prob / maxProb : 0;

        // Build text-based probability bar
        let filledCount = round(normalizedProb * barLength);
        let emptyCount = barLength - filledCount;
        let probBar = '█'.repeat(filledCount) + '░'.repeat(emptyCount);

        // Format token display
        let displayToken = token.token.replace(/\n/g, '↵');
        // Truncate long tokens
        if (displayToken.length > 12) {
            displayToken = displayToken.substring(0, 11) + '…';
        }
        // Pad token to fixed width for alignment
        displayToken = displayToken.padEnd(12, ' ');

        // Build the full line
        let line = probBar + ' ' + displayToken;

        // Draw selection indicator and text
        textAlign(LEFT, CENTER);
        if (i === selectedOptionIndex) {
            fill(100, 200, 255);
            textSize(13);
            text('▶ ' + line, listX, y);
        } else {
            fill(150);
            textSize(12);
            text('  ' + line, listX, y);
        }
    }

    // Store directions for selection
    currentDirections = directions;
}

let currentDirections = [];

function getDirectionClusters(tip, numClusters) {
    // Calculate edge bias - avoid directions toward nearby edges
    let edgeThreshold = 80;
    let bottomMargin = 80;

    // Find all active attractors within range, but filter out those toward edges
    let nearby = [];
    for (let a of attractors) {
        if (a.active) {
            let d = tip.pos.dist(a.pos);
            if (d < AttractionDistance * 2) {
                // Skip attractors that would lead us toward a nearby edge
                let towardEdge = false;

                if (tip.pos.x < edgeThreshold && a.pos.x < tip.pos.x) towardEdge = true;
                if (tip.pos.x > width - edgeThreshold && a.pos.x > tip.pos.x) towardEdge = true;
                if (tip.pos.y < edgeThreshold && a.pos.y < tip.pos.y) towardEdge = true;
                if (tip.pos.y > height - bottomMargin - edgeThreshold && a.pos.y > tip.pos.y) towardEdge = true;

                if (!towardEdge) {
                    let dir = p5.Vector.sub(a.pos, tip.pos);
                    let angle = atan2(dir.y, dir.x);
                    nearby.push({ pos: a.pos, angle: angle, dir: dir.normalize() });
                }
            }
        }
    }

    if (nearby.length === 0) {
        // No attractors (or all filtered), create noise-based directions away from edges
        let dirs = [];
        for (let i = 0; i < numClusters; i++) {
            // Use noise based on tip position and index for natural-looking but consistent directions
            let noiseVal = noise(tip.pos.x * 0.01, tip.pos.y * 0.01, i * 10);
            let angle = (noiseVal - 0.5) * PI * 1.2;  // Range roughly -108 to +108 degrees

            // Bias angle away from nearby edges
            if (tip.pos.x < edgeThreshold) angle = constrain(angle, -PI/2, PI/2);  // Prefer rightward
            if (tip.pos.x > width - edgeThreshold) angle = constrain(angle, PI/2, PI) + (angle < 0 ? -PI : 0);  // Prefer leftward
            if (tip.pos.y < edgeThreshold && angle < 0) angle = -angle;  // Prefer downward
            if (tip.pos.y > height - bottomMargin - edgeThreshold && angle > 0) angle = -angle;  // Prefer upward

            dirs.push(createVector(cos(angle), sin(angle)));
        }
        return dirs;
    }

    // Sort by angle
    nearby.sort((a, b) => a.angle - b.angle);

    // Divide into clusters
    let clusterSize = ceil(nearby.length / numClusters);
    let directions = [];

    for (let i = 0; i < numClusters; i++) {
        let start = i * clusterSize;
        let end = min(start + clusterSize, nearby.length);

        if (start < nearby.length) {
            // Average direction for this cluster
            let avgDir = createVector(0, 0);
            for (let j = start; j < end; j++) {
                avgDir.add(nearby[j].dir);
            }
            avgDir.normalize();
            directions.push(avgDir);
        } else {
            // Not enough attractors, use noise-based direction
            let noiseVal = noise(tip.pos.x * 0.01, tip.pos.y * 0.01, i * 10);
            let angle = (noiseVal - 0.5) * PI * 1.2;
            directions.push(createVector(cos(angle), sin(angle)));
        }
    }

    // Shuffle directions using noise so token order doesn't map to angle order
    // Use tip position as seed for consistent but natural-looking shuffle
    let shuffled = [];
    let indices = [];
    for (let i = 0; i < directions.length; i++) {
        // Generate noise-based sort key for each direction
        let sortKey = noise(tip.pos.x * 0.02 + i * 7, tip.pos.y * 0.02 + i * 13, frameCount * 0.001);
        indices.push({ idx: i, key: sortKey });
    }
    indices.sort((a, b) => a.key - b.key);

    for (let item of indices) {
        shuffled.push(directions[item.idx]);
    }

    return shuffled;
}

function drawPromptBar() {
    // Background
    fill(20);
    noStroke();
    rect(0, height - 50, width, 50);

    // Prompt text
    fill(255);
    textAlign(LEFT, CENTER);
    textSize(12);
    text(currentPrompt, 20, height - 25);
}

function keyPressed() {
    if (state !== 'CHOOSING') return;

    if (keyCode === UP_ARROW) {
        selectedOptionIndex = (selectedOptionIndex - 1 + tokenOptions.length) % tokenOptions.length;
    } else if (keyCode === DOWN_ARROW) {
        selectedOptionIndex = (selectedOptionIndex + 1) % tokenOptions.length;
    } else if (keyCode === RIGHT_ARROW || key === ' ') {
        selectToken();
    }

    return false;
}

function selectToken() {
    if (tokenOptions.length === 0) return;

    let selected = tokenOptions[selectedOptionIndex];

    // Update prompt
    currentPrompt += selected.token;
    console.log('Selected:', selected.token, 'Direction index:', selectedOptionIndex);

    // Mark the current tip with this token
    currentNode.token = selected.token;
    currentNode.prob = selected.prob;

    // Store missed directions (directions not chosen)
    missedDirections = [];
    for (let i = 0; i < currentDirections.length; i++) {
        if (i !== selectedOptionIndex && currentDirections[i]) {
            missedDirections.push(currentDirections[i].copy());
        }
    }

    // Set growth target direction
    if (currentDirections.length > selectedOptionIndex) {
        growthTarget = currentDirections[selectedOptionIndex].copy();
        console.log('Growth target:', growthTarget.x, growthTarget.y);
    } else {
        // Fallback: grow to the right
        growthTarget = createVector(1, 0);
    }

    // Start growing
    state = 'GROWING';
    growthStepsRemaining = GrowthStepsPerChoice;
    tokenOptions = [];
}

function windowResized() {
    resizeCanvas(windowWidth, windowHeight);
}
