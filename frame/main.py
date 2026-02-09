import requests
import os
import argparse


API_BASE_URL="http://localhost:8000/api/v1"
CREATE_ENDPOINT="/framily/create"


def create_framily(name: str | None = None):
    payload = {"name": name} if name else {}
    response = requests.post(API_BASE_URL + CREATE_ENDPOINT, json=payload)

    if response.status_code == 201:
        framily_code = response.json().get("framily_code")
        frame_token = response.json().get("frame_token")
        with open(f"{framily_code}.token", "w") as f:
            f.write(frame_token)
        print("Framily created successfully.")
    else:
        print(f"Failed to create framily: {response.text}")


def main(args):
    if args.command == "create":
        create_framily(args.name)
    else:
        print("No command specified. Use --help for usage information.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Framily Emulator")
    subparsers = parser.add_subparsers(dest="command")

    create_parser = subparsers.add_parser("create", help="Create a new framily")
    create_parser.add_argument("--name", type=str, help="Optional name for the framily")

    args = parser.parse_args()

    main(args)
