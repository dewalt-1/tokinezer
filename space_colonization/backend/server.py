#!/usr/bin/env python3
"""
WebSocket server for Token Space Colonization
Wraps llama.cpp completion API for real-time token alternatives
"""

import json
import asyncio
from typing import List, Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import requests
import uvicorn

app = FastAPI(title="Token Space Colonization API")

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
