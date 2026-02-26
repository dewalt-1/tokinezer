#!/usr/bin/env python3
"""
WebSocket server for Token Space Colonization
Wraps llama.cpp completion API for real-time token alternatives
Builds complete token tree for frontend exploration
"""

import json
import asyncio
import random
import os
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import requests
import uvicorn

# MQTT Configuration (set MQTT_BROKER to enable)
MQTT_BROKER = os.environ.get("MQTT_BROKER", "")  # e.g., "other-pi.local" or "192.168.1.100"
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_TOPIC = os.environ.get("MQTT_TOPIC", "tokens/prompt")

mqtt_client = None
if MQTT_BROKER:
    try:
        import paho.mqtt.client as mqtt
        mqtt_client = mqtt.Client()
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
        print(f"MQTT connected to {MQTT_BROKER}:{MQTT_PORT}")
    except Exception as e:
        print(f"MQTT connection failed: {e}")
        mqtt_client = None

def publish_prompt(prompt: str):
    """Publish current prompt to MQTT broker"""
    if mqtt_client:
        try:
            mqtt_client.publish(MQTT_TOPIC, prompt)
        except Exception as e:
            print(f"MQTT publish error: {e}")

app = FastAPI(title="Token Space Colonization API")

# Tree generation settings
MAX_DEPTH = 6  # How deep the tree goes
TOKENS_PER_NODE = (5, 12)  # Random range for children per node

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LLAMA_CPP_URL = "http://127.0.0.1:8080"


def check_llama_server() -> bool:
    """Check if llama.cpp server is running"""
    try:
        response = requests.get(f"{LLAMA_CPP_URL}/health", timeout=2)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def get_token_alternatives(
    prompt: str,
    n_alternatives: int = 5,
    temperature: float = 0.7
) -> List[Dict[str, Any]]:
    """
    Get alternative tokens for the next position
    Returns list of alternatives with tokens and probabilities
    """
    url = f"{LLAMA_CPP_URL}/completion"

    payload = {
        "prompt": prompt,
        "n_predict": 1,
        "temperature": temperature,
        "top_k": 40,
        "top_p": 0.9,
        "n_probs": n_alternatives,
        "stream": True,
    }

    try:
        response = requests.post(url, json=payload, stream=True, timeout=30)
        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = json.loads(line[6:])
                    if 'completion_probabilities' in data:
                        token_data = data['completion_probabilities'][0]
                        return extract_alternatives(token_data, n_alternatives)

        return []
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return []


def extract_alternatives(token_data: Dict, n_alternatives: int) -> List[Dict]:
    """Extract and format alternative tokens"""
    alternatives = []

    # Get the selected token
    selected_token = token_data.get("token", "")
    selected_logprob = token_data.get("logprob", 0.0)
    selected_prob = 2.71828 ** selected_logprob

    alternatives.append({
        "token": selected_token,
        "prob": selected_prob
    })

    # Get other alternatives
    top_logprobs = token_data.get("top_logprobs", [])
    for alt in top_logprobs[:n_alternatives]:
        alt_token = alt.get("token", "")
        alt_logprob = alt.get("logprob", 0.0)
        alt_prob = 2.71828 ** alt_logprob

        if alt_token != selected_token:
            alternatives.append({
                "token": alt_token,
                "prob": alt_prob
            })

    return alternatives[:n_alternatives]


def build_token_tree(
    prompt: str,
    max_depth: int = MAX_DEPTH,
    current_depth: int = 0,
    node_id: int = 0
) -> tuple[Dict, int]:
    """
    Recursively build the full token tree.
    Returns (tree_node, next_available_id)
    """
    if current_depth >= max_depth:
        return None, node_id

    # Get random number of alternatives for this node
    n_alts = random.randint(*TOKENS_PER_NODE)
    alternatives = get_token_alternatives(prompt, n_alternatives=n_alts)

    if not alternatives:
        return None, node_id

    # Build node with children
    children = []
    next_id = node_id + 1

    for alt in alternatives:
        child_prompt = prompt + alt["token"]
        child_node = {
            "id": next_id,
            "token": alt["token"],
            "prob": alt["prob"],
            "children": []
        }
        next_id += 1

        # Recursively build subtree
        subtree, next_id = build_token_tree(
            child_prompt,
            max_depth,
            current_depth + 1,
            next_id
        )

        if subtree and subtree.get("children"):
            child_node["children"] = subtree["children"]

        children.append(child_node)

    return {
        "id": node_id,
        "token": "[ROOT]" if current_depth == 0 else "",
        "prob": 1.0,
        "children": children
    }, next_id


@app.get("/health")
async def health():
    """Health check endpoint"""
    llama_ok = check_llama_server()
    return {
        "status": "ok",
        "llama_cpp": "connected" if llama_ok else "disconnected"
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time token requests"""
    await websocket.accept()

    try:
        while True:
            # Receive request from client
            data = await websocket.receive_text()
            request = json.loads(data)

            action = request.get("action")

            if action == "get_tokens":
                prompt = request.get("prompt", "")
                n_alternatives = request.get("n_alternatives", 5)
                temperature = request.get("temperature", 0.7)

                # Get alternatives from llama.cpp
                alternatives = await asyncio.to_thread(
                    get_token_alternatives,
                    prompt,
                    n_alternatives,
                    temperature
                )

                # Send response
                await websocket.send_json({
                    "type": "tokens",
                    "prompt": prompt,
                    "alternatives": alternatives
                })

            elif action == "build_tree":
                prompt = request.get("prompt", "Once upon a time")
                max_depth = request.get("max_depth", MAX_DEPTH)

                # Notify client we're starting
                await websocket.send_json({
                    "type": "status",
                    "message": "Building token tree..."
                })

                # Build the full tree (this takes time)
                tree, _ = await asyncio.to_thread(
                    build_token_tree,
                    prompt,
                    max_depth
                )

                # Send complete tree
                await websocket.send_json({
                    "type": "tree",
                    "prompt": prompt,
                    "tree": tree
                })

            elif action == "get_branch_tokens":
                # Old action: get tokens for pre-built branches (linear)
                prompt = request.get("prompt", "Once upon a time")
                count = request.get("count", 100)

                await websocket.send_json({
                    "type": "status",
                    "message": f"Fetching {count} tokens..."
                })

                tokens = []
                current_prompt = prompt

                for i in range(count):
                    alts = await asyncio.to_thread(
                        get_token_alternatives,
                        current_prompt,
                        n_alternatives=1
                    )
                    if alts:
                        tokens.append(alts[0])
                        current_prompt += alts[0]["token"]
                    else:
                        tokens.append({"token": "?", "prob": 0.0})

                await websocket.send_json({
                    "type": "branch_tokens",
                    "tokens": tokens
                })

            elif action == "get_branch_tokens_multi":
                # New action: get multiple alternatives at each branch point
                prompt = request.get("prompt", "Once upon a time")
                branches = request.get("branches", [])  # List of child counts per branch

                total = sum(branches)
                await websocket.send_json({
                    "type": "status",
                    "message": f"Fetching tokens for {len(branches)} branch points ({total} total)..."
                })

                # For each branch point, get that many alternatives
                all_tokens = []
                current_prompt = prompt

                for num_children in branches:
                    if num_children > 0:
                        alts = await asyncio.to_thread(
                            get_token_alternatives,
                            current_prompt,
                            n_alternatives=num_children
                        )
                        # Pad with placeholders if we didn't get enough
                        while len(alts) < num_children:
                            alts.append({"token": "?", "prob": 0.0})
                        all_tokens.extend(alts[:num_children])
                        # Advance prompt with first alternative for next branch
                        if alts:
                            current_prompt += alts[0]["token"]

                await websocket.send_json({
                    "type": "branch_tokens",
                    "tokens": all_tokens
                })

            elif action == "get_options":
                # New incremental action: get N token alternatives for current prompt
                prompt = request.get("prompt", "Once upon a time")
                count = request.get("count", 5)

                # Publish prompt to MQTT when user selects a token
                publish_prompt(prompt)

                alts = await asyncio.to_thread(
                    get_token_alternatives,
                    prompt,
                    n_alternatives=count
                )

                # Ensure we have enough options
                while len(alts) < count:
                    alts.append({"token": "?", "prob": 0.0})

                await websocket.send_json({
                    "type": "token_options",
                    "options": alts[:count]
                })

            elif action == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close()


if __name__ == "__main__":
    print("Starting Token Space Colonization Server...")
    print("Make sure llama.cpp server is running on port 8080")
    uvicorn.run(app, host="0.0.0.0", port=8000)
