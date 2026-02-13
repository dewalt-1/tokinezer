// Token Space Colonization
// Step 1: Build organic tree with space colonization
// Step 2: Map tokens onto existing branches

// Algorithm parameters
let SegmentLength = 5;
let AttractionDistance = 50;   // Increased from 30
let KillDistance = 3;          // Decreased from 5
let MaxNodes = 4000;
let NumAttractors = 8000;      // Increased from 5000
let UseNoiseDistribution = true; // Use Perlin noise for attractor placement

// Debug mode
let showAttractors = true;  // Show the random points

// Data structures
let attractors = [];
let nodes = [];         // Space colonization nodes
let treeBuilt = false;  // Flag: is tree fully grown?

// Token overlay (populated after tree is built)
let tokenData = null;   // Tokens from backend
let branchNodes = [];   // Nodes that are branch points (have multiple children)

// Navigation state
let currentNode = null;
let selectedChildIndex = 0;

// WebSocket
let ws;
let wsConnected = false;

function setup() {
    createCanvas(windowWidth, windowHeight);
    textFont('monospace');
    textSize(10);

    // Step 1: Build the organic tree with space colonization
    initSpaceColonization();
}

function initSpaceColonization() {
    attractors = [];
    nodes = [];
    treeBuilt = false;

    // Create attractors - either with noise or random
    if (UseNoiseDistribution) {
        // Use Perlin noise for organic clustering
        let noiseScale = 0.01;
        let threshold = 0.4;  // Only place attractors where noise > threshold
        let attempts = 0;
        let maxAttempts = NumAttractors * 10;

        while (attractors.length < NumAttractors && attempts < maxAttempts) {
            let x = random(width);
            let y = random(height);
            let n = noise(x * noiseScale, y * noiseScale);

            // Place attractor if noise value is above threshold
            if (n > threshold) {
                attractors.push({
                    pos: createVector(x, y),
                    influencingNodes: []
                });
            }
            attempts++;
        }
        console.log('Created', attractors.length, 'attractors using noise distribution');
    } else {
        // Uniform random distribution
        for (let i = 0; i < NumAttractors; i++) {
            attractors.push({
                pos: createVector(random(width), random(height)),
                influencingNodes: []
            });
        }
    }

    // Single root node at center-left
    nodes.push({
        id: 0,
        pos: createVector(100, height / 2),
        parent: null,
        children: [],
        isTip: true,
        influencedBy: [],
        token: null,
        prob: null
    });
}

function draw() {
    background(0);

    if (!treeBuilt) {
        // Keep growing the tree
        let grew = updateSpaceColonization();
        if (!grew) {
            // Tree is complete - now connect to backend for tokens
            treeBuilt = true;
            console.log('Tree built with', nodes.length, 'nodes');
            identifyBranchPoints();
            connectWebSocket();
        }
    }

    // Draw the tree
    drawTree();

    // Draw status
    if (!treeBuilt) {
        fill(100);
        noStroke();
        textAlign(LEFT, TOP);
        text('Growing tree... ' + nodes.length + ' nodes', 10, 10);
    } else if (!tokenData) {
        fill(100);
        noStroke();
        textAlign(LEFT, TOP);
        text('Tree complete. Fetching tokens...', 10, 10);
    }
}

function updateSpaceColonization() {
    // Step 1: Clear previous associations
    for (let a of attractors) {
        a.influencingNodes = [];
    }
    for (let node of nodes) {
        node.influencedBy = [];
    }

    // Step 2: Associate attractors with nearby nodes (Open venation)
    for (let a of attractors) {
        let closestNode = null;
        let closestDist = Infinity;

        for (let node of nodes) {
            let d = a.pos.dist(node.pos);
            if (d < AttractionDistance && d < closestDist) {
                closestDist = d;
                closestNode = node;
            }
        }

        if (closestNode) {
            closestNode.influencedBy.push(a);
            a.influencingNodes.push(closestNode);
        }
    }

    // Step 3: Grow - for each node influenced by attractors, create new node
    let newNodes = [];

    for (let node of nodes) {
        if (node.influencedBy.length > 0) {
            // Calculate average direction toward all influencing attractors
            let avgDir = createVector(0, 0);

            for (let a of node.influencedBy) {
                let dir = p5.Vector.sub(a.pos, node.pos);
                dir.normalize();
                avgDir.add(dir);
            }

            avgDir.normalize();
            avgDir.mult(SegmentLength);

            // Create new node
            let newPos = p5.Vector.add(node.pos, avgDir);
            let newNode = {
                id: nodes.length + newNodes.length,
                pos: newPos,
                parent: node,
                children: [],
                isTip: true,
                influencedBy: [],
                token: null,
                prob: null
            };

            node.isTip = false;
            node.children.push(newNode);
            newNodes.push(newNode);
        }
    }

    // Add new nodes
    for (let n of newNodes) {
        nodes.push(n);
    }

    // Step 4: Prune - remove attractors that have nodes within kill distance
    attractors = attractors.filter(a => {
        for (let node of nodes) {
            if (a.pos.dist(node.pos) < KillDistance) {
                return false;
            }
        }
        return true;
    });

    // Return whether we grew (if no growth or hit limit, tree is complete)
    return newNodes.length > 0 && nodes.length < MaxNodes;
}

function identifyBranchPoints() {
    // Find nodes that have branching (multiple children or are tips)
    // These are where tokens will be assigned
    branchNodes = [];

    for (let node of nodes) {
        // A branch point is where user makes a choice
        // For now, mark nodes with children as branch points
        if (node.children.length > 0) {
            branchNodes.push(node);
        }
    }

    console.log('Found', branchNodes.length, 'branch points');

    // Set initial navigation position
    currentNode = nodes[0];  // Start at root
    selectedChildIndex = 0;
}

function connectWebSocket() {
    ws = new WebSocket('ws://localhost:8000/ws');

    ws.onopen = function() {
        console.log('Connected to backend');
        wsConnected = true;
        // Request tokens for the branch points
        requestTokensForBranches();
    };

    ws.onmessage = function(event) {
        var data = JSON.parse(event.data);
        console.log('Received:', data.type);

        if (data.type === 'branch_tokens') {
            applyTokensToBranches(data.tokens);
        } else if (data.type === 'status') {
            console.log('Status:', data.message);
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

function requestTokensForBranches() {
    // Build a list of how many children each branch point has
    let branchInfo = [];
    for (let node of branchNodes) {
        branchInfo.push(node.children.length);
    }

    ws.send(JSON.stringify({
        action: 'get_branch_tokens_multi',
        prompt: 'Once upon a time',
        branches: branchInfo
    }));
}

function applyTokensToBranches(tokens) {
    // Assign tokens to the children of each branch point
    tokenData = tokens;
    let tokenIndex = 0;

    for (let node of branchNodes) {
        for (let child of node.children) {
            if (tokenIndex < tokens.length) {
                child.token = tokens[tokenIndex].token;
                child.prob = tokens[tokenIndex].prob;
                tokenIndex++;
            }
        }
    }

    console.log('Applied', tokenIndex, 'tokens to branches');

    // Debug: check if root has children with tokens
    if (nodes[0] && nodes[0].children) {
        console.log('Root has', nodes[0].children.length, 'children');
        for (let i = 0; i < Math.min(3, nodes[0].children.length); i++) {
            console.log('Child', i, 'token:', nodes[0].children[i].token);
        }
    }
}

function drawTree() {
    // Debug: draw attractors
    if (showAttractors && attractors.length > 0) {
        noStroke();
        fill(40, 40, 60);
        for (let a of attractors) {
            ellipse(a.pos.x, a.pos.y, 2, 2);
        }
    }

    // Get current path for highlighting
    let currentPath = [];
    if (currentNode) {
        let n = currentNode;
        while (n) {
            currentPath.push(n);
            n = n.parent;
        }
    }

    // Draw all branches
    for (let node of nodes) {
        if (node.parent) {
            let isOnPath = currentPath.includes(node);
            let isSelected = currentNode &&
                             currentNode.children &&
                             currentNode.children[selectedChildIndex] === node;

            if (isOnPath) {
                stroke(255);
                strokeWeight(1.5);
            } else if (isSelected) {
                stroke(100, 200, 255);
                strokeWeight(1.5);
            } else {
                stroke(60);
                strokeWeight(0.5);
            }

            line(node.parent.pos.x, node.parent.pos.y, node.pos.x, node.pos.y);
        }
    }

    // Draw token labels on: current path, selected child, AND all children of current node
    if (tokenData) {
        noStroke();
        textAlign(LEFT, CENTER);

        // Get all children of current node for display
        let currentChildren = (currentNode && currentNode.children) ? currentNode.children : [];

        for (let node of nodes) {
            if (node.token && node.parent) {
                let isOnPath = currentPath.includes(node);
                let isSelected = currentChildren[selectedChildIndex] === node;
                let isChildOfCurrent = currentChildren.includes(node);

                // Show text for: path nodes, selected child, or any child of current node
                if (!isOnPath && !isChildOfCurrent) continue;

                let midX = (node.pos.x + node.parent.pos.x) / 2;
                let midY = (node.pos.y + node.parent.pos.y) / 2;

                if (isOnPath) {
                    fill(255);
                } else if (isSelected) {
                    fill(100, 200, 255);  // Bright blue for selected
                } else {
                    fill(100);  // Dim for other children
                }

                let displayToken = node.token.replace(/\n/g, '\\n');
                text(displayToken, midX + 3, midY);
            }
        }
    }

    // Draw current position marker
    if (currentNode && treeBuilt) {
        fill(255, 200, 0);
        noStroke();
        ellipse(currentNode.pos.x, currentNode.pos.y, 8, 8);
    }

    // Draw text output at bottom
    if (treeBuilt) {
        drawTextOutput(currentPath);
    }
}

function drawTextOutput(path) {
    // Build text from path (reversed since we built it from current to root)
    let textOutput = '';
    for (let i = path.length - 1; i >= 0; i--) {
        if (path[i].token) {
            textOutput += path[i].token;
        }
    }

    // Draw background bar
    fill(20);
    noStroke();
    rect(0, height - 40, width, 40);

    // Draw text
    fill(255);
    textAlign(LEFT, CENTER);
    textSize(12);
    text('Output: ' + textOutput, 20, height - 20);
    textSize(10);
}

function keyPressed() {
    if (!currentNode || !treeBuilt) return;

    if (keyCode === UP_ARROW) {
        if (currentNode.children && currentNode.children.length > 0) {
            selectedChildIndex = (selectedChildIndex - 1 + currentNode.children.length) % currentNode.children.length;
        }
    } else if (keyCode === DOWN_ARROW) {
        if (currentNode.children && currentNode.children.length > 0) {
            selectedChildIndex = (selectedChildIndex + 1) % currentNode.children.length;
        }
    } else if (keyCode === RIGHT_ARROW) {
        if (currentNode.children && currentNode.children.length > 0) {
            currentNode = currentNode.children[selectedChildIndex];
            selectedChildIndex = 0;
        }
    } else if (keyCode === LEFT_ARROW) {
        if (currentNode.parent) {
            let parent = currentNode.parent;
            selectedChildIndex = parent.children.indexOf(currentNode);
            if (selectedChildIndex < 0) selectedChildIndex = 0;
            currentNode = parent;
        }
    }

    return false;
}

function windowResized() {
    resizeCanvas(windowWidth, windowHeight);
}
