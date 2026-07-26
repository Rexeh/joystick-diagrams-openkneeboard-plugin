#!/usr/bin/env python3
"""Developer CLI tool for signing plugins with Ed25519.

Usage:
    # Generate a new key pair (do this once, keep private key safe):
    python scripts/sign_plugin.py genkey --out keys/

    # Sign a plugin directory:
    python scripts/sign_plugin.py sign --plugin path/to/plugin_dir --key keys/private.key

This tool is NOT shipped with the application. Only the developer uses it
to sign plugins before distribution.
"""

import argparse
import base64
import sys
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)

# Add parent to path so we can import the signing module
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from joystick_diagrams.plugins.plugin_signing import (
    SIGNATURE_FILENAME,
    compute_plugin_digest,
)


def cmd_genkey(args):
    """Generate a new Ed25519 key pair."""
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    # Save private key (PEM format)
    private_path = out_dir / "private.key"
    private_path.write_bytes(
        private_key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())
    )
    print(f"Private key saved to: {private_path}")

    # Save public key (PEM format)
    public_path = out_dir / "public.key"
    public_path.write_bytes(
        public_key.public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)
    )
    print(f"Public key saved to: {public_path}")

    # Print the base64-encoded raw public key for embedding in plugin_signing.py
    raw_public = public_key.public_bytes(Encoding.Raw, PublicFormat.Raw)
    b64_public = base64.b64encode(raw_public).decode("ascii")
    print(f"\nBase64 public key (embed in plugin_signing.py):\n  {b64_public}")


def cmd_sign(args):
    """Sign a plugin directory."""
    plugin_path = Path(args.plugin).resolve()
    key_path = Path(args.key).resolve()

    if not plugin_path.is_dir():
        print(f"Error: Plugin directory not found: {plugin_path}")
        sys.exit(1)

    if not key_path.is_file():
        print(f"Error: Private key not found: {key_path}")
        sys.exit(1)

    # Load private key
    from cryptography.hazmat.primitives.serialization import load_pem_private_key

    private_key = load_pem_private_key(key_path.read_bytes(), password=None)
    if not isinstance(private_key, Ed25519PrivateKey):
        print("Error: Key is not an Ed25519 private key")
        sys.exit(1)

    # Compute digest and sign
    digest = compute_plugin_digest(plugin_path)
    signature = private_key.sign(digest)
    sig_b64 = base64.b64encode(signature).decode("ascii")

    # Write signature file
    sig_path = plugin_path / SIGNATURE_FILENAME
    sig_path.write_text(sig_b64, encoding="utf-8")
    print(f"Plugin signed: {sig_path}")

    # Verify
    public_key = private_key.public_key()
    try:
        public_key.verify(signature, digest)
        print("Verification: OK")
    except Exception as e:
        print(f"Verification FAILED: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Joystick Diagrams Plugin Signer")
    subparsers = parser.add_subparsers(dest="command", required=True)

    gen_parser = subparsers.add_parser("genkey", help="Generate a new Ed25519 key pair")
    gen_parser.add_argument(
        "--out", default="keys", help="Output directory for key files"
    )

    sign_parser = subparsers.add_parser("sign", help="Sign a plugin directory")
    sign_parser.add_argument("--plugin", required=True, help="Plugin directory to sign")
    sign_parser.add_argument(
        "--key", required=True, help="Path to Ed25519 private key (PEM)"
    )

    args = parser.parse_args()
    if args.command == "genkey":
        cmd_genkey(args)
    elif args.command == "sign":
        cmd_sign(args)


if __name__ == "__main__":
    main()
