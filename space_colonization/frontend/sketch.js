// Space Colonization Algorithm
// Based on Adam Runions et al, implementation by Jason Webb
// Ported to p5.js

// Algorithm parameters
let SegmentLength = 5;
let AttractionDistance = 30;
let KillDistance = 5;

// Data
let attractors = [];
let nodes = [];

function setup() {
    createCanvas(windowWidth, windowHeight);

    // Create random attractors scattered across canvas
    for (let i = 0; i < 5000; i++) {
        attractors.push({
            pos: createVector(random(width), random(height)),
            influencingNodes: []
        });
    }

    // Single root node at center-left
    nodes.push({
        pos: createVector(100, height / 2),
        parent: null,
        isTip: true,
        influencedBy: [],
        childCount: 0
    });
}

function draw() {
    background(0);

    // Run the algorithm
    update();

    // Calculate child counts for vein thickening (propagate up from tips)
    for (let node of nodes) {
        node.childCount = 0;
    }
    // Count descendants by traversing from each node up to root
    for (let node of nodes) {
        let current = node.parent;
        while (current) {
            current.childCount++;
            current = current.parent;
        }
    }

    // Draw branches with thickness based on child count
    stroke(255);
    for (let node of nodes) {
        if (node.parent) {
            // Thickness: more children = thicker (log scale, min 0.5, max 3)
            let thickness = map(Math.log(node.parent.childCount + 1), 0, Math.log(nodes.length), 0.5, 3);
            strokeWeight(thickness);
            line(node.parent.pos.x, node.parent.pos.y, node.pos.x, node.pos.y);
        }
    }
}

function update() {
    // Step 1: Clear previous associations
    for (let a of attractors) {
        a.influencingNodes = [];
    }
    for (let node of nodes) {
        node.influencedBy = [];
    }

    // Step 2: Associate attractors with nearby nodes (Open venation)
    // For each attractor, find the single closest node within attraction distance
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
                pos: newPos,
                parent: node,
                isTip: true,
                influencedBy: [],
                childCount: 0
            };

            node.isTip = false;
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
                return false; // Remove this attractor
            }
        }
        return true; // Keep this attractor
    });
}

function windowResized() {
    resizeCanvas(windowWidth, windowHeight);
}
