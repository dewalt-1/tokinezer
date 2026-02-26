#!/usr/bin/env python3
"""
MQTT Receiver for Token Visualization
Runs on Pi 2 - receives prompts and writes to text file

Usage:
    python mqtt_receiver.py [--broker BROKER] [--output FILE]

Example:
    python mqtt_receiver.py --broker 192.168.1.50 --output /home/pi/prompt.txt
"""

import argparse
import paho.mqtt.client as mqtt

# Default settings
DEFAULT_BROKER = "localhost"
DEFAULT_PORT = 1883
DEFAULT_TOPIC = "tokens/prompt"
DEFAULT_OUTPUT = "prompt.txt"


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"Connected to MQTT broker")
        client.subscribe(userdata["topic"])
        print(f"Subscribed to: {userdata['topic']}")
    else:
        print(f"Connection failed with code {rc}")


def on_message(client, userdata, msg):
    prompt = msg.payload.decode("utf-8")
    output_file = userdata["output"]

    # Write prompt to file
    with open(output_file, "w") as f:
        f.write(prompt)

    # Also print to console (truncated)
    display = prompt if len(prompt) < 60 else prompt[:57] + "..."
    print(f"Updated: {display}")


def main():
    parser = argparse.ArgumentParser(description="MQTT receiver for token prompts")
    parser.add_argument("--broker", "-b", default=DEFAULT_BROKER,
                        help=f"MQTT broker address (default: {DEFAULT_BROKER})")
    parser.add_argument("--port", "-p", type=int, default=DEFAULT_PORT,
                        help=f"MQTT broker port (default: {DEFAULT_PORT})")
    parser.add_argument("--topic", "-t", default=DEFAULT_TOPIC,
                        help=f"MQTT topic (default: {DEFAULT_TOPIC})")
    parser.add_argument("--output", "-o", default=DEFAULT_OUTPUT,
                        help=f"Output file path (default: {DEFAULT_OUTPUT})")

    args = parser.parse_args()

    print(f"MQTT Receiver")
    print(f"  Broker: {args.broker}:{args.port}")
    print(f"  Topic:  {args.topic}")
    print(f"  Output: {args.output}")
    print()

    # Pass settings to callbacks via userdata
    userdata = {
        "topic": args.topic,
        "output": args.output
    }

    client = mqtt.Client(userdata=userdata)
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(args.broker, args.port, 60)
        print("Waiting for messages... (Ctrl+C to stop)")
        client.loop_forever()
    except KeyboardInterrupt:
        print("\nStopped")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
