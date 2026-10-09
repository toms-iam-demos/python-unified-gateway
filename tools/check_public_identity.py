"""Regression guard for current tracked publication content; not a history/OCR audit."""
import hashlib
import html
from pathlib import Path
import re
import struct
import subprocess
import sys
from urllib.parse import unquote

# Normalized identifying words/phrases; no original organization names in this file.
BLOCKED = frozenset(['1a6c8974c83c0847c44b5d2a3e305465b0da320e82e9889fc9ab3106608d87b9', '225aac426d4a9cc1454ba032c9345b54f7efb50263900a95332734bffefdbc32', '4a868a47694dcdf63db1a812dda31ba9ab060bb34aa800e5dbedbb432af65dbe', '4ae044f6332cf7b057bb0e43e0c9bd6ecbac2a39f870fd3cf5e9a371ab906510', '56fe43f748e258de06b4955e2b8978bbc1c28ff9ba53917387d6dca8fb920018', '5dd336c3be7b217f5b6d2daa9dd55963271c1b851bf9d6325bfbc17b109debd5', '6b59cc18e090e7f1cd324fe4b807fa2ed1de0e701f543ab826ae71148146c80d', '6c6b013cec6b38956c83da597262572ea25455fb36faffec407815a2e7a98a76', '6d0e0bcd5380342e2f8e1f90bef510e35ffc079654f191d2abe6bec769bf9382', '798f3328a6c80fc70e603f727618cd2f1e908e3d368c68ab9bbf7f706b1eccc9', '93d0f83b8dee6fd208d0804c80d0819d1b2cb39d11ddd553291627943e4d0394', '958272842345dc514f401ef3db2ea2be3010287944c62498abf312218895ee9d', '9d0a88c9308ec2d145389dcbc020146eddca2271f9add1c3eb1069c99855932c', 'a0991b78daf88069f1f89f0331423dfe365e550a4c18c8d5bf1803cd88685c0d', 'c83625086eb353b994a1eefab10731c3402aebfd714231dc79060642aec331b4', 'd6018b670d021eb2f3025f89267c75ace47e601e74d2fa849b73e075e8e54d77', 'de19c97d557a0e8a8cb2eb074915a22154e5f7606bd248aaf4ae6d24782f1409', 'dff4e9972f117960383aa5467fee70b1e2f5f2388433eca3c16a6d1ea5b17286', 'f245cccd6987e5ece6a52308e04e1166f4b00178f5c4527bec5f3c7cf33f5da3', 'f747b68c75eba02305030617998ead1f0aabd6f6f88025158e44c1febd8e4062'])


def has_identity(text, blocked=BLOCKED):
    for _ in range(3):
        text = html.unescape(unquote(text))
    words = re.findall(r"[a-z0-9]+", text.casefold())
    for index in range(len(words)):
        for size in range(1, min(3, len(words) - index) + 1):
            value = " ".join(words[index:index + size])
            if hashlib.sha256(value.encode()).hexdigest() in blocked:
                return True
    return False


def font_names(data):
    """Read SFNT name metadata; do not interpret compressed glyph bytes as text."""
    count = struct.unpack_from(">H", data, 4)[0]
    for index in range(count):
        tag, _, offset, length = struct.unpack_from(">4sIII", data, 12 + 16 * index)
        if tag != b"name":
            continue
        if offset + length > len(data):
            raise ValueError("invalid font table bounds")
        table = data[offset:offset + length]
        _, records, storage = struct.unpack_from(">HHH", table)
        values = []
        for record in range(records):
            platform, _, _, _, size, start = struct.unpack_from(">HHHHHH", table, 6 + 12 * record)
            start += storage
            if start + size > len(table):
                raise ValueError("invalid font name bounds")
            encoding = "utf-16-be" if platform in (0, 3) else "mac_roman"
            values.append(table[start:start + size].decode(encoding))
        return "\n".join(values)
    raise ValueError("font lacks a reviewable name table")


def check(root):
    names = subprocess.check_output(
        ["git", "-C", str(root), "ls-files", "-z"],
    ).decode("utf-8").split("\0")
    failures = []
    for name in filter(None, names):
        path = root / name
        if path.is_symlink() or not path.is_file():
            failures.append((name, "unsupported or missing tracked file"))
            continue
        try:
            data = path.read_bytes()
            text = font_names(data) if path.suffix == ".ttf" else data.decode("utf-8")
        except (UnicodeError, ValueError, struct.error):
            failures.append((name, "unreviewed binary or invalid metadata"))
            continue
        if has_identity(name) or has_identity(text):
            failures.append((name, "known identity reference"))
        if path.suffix == ".svg" and "<!--SRC=" in text:
            failures.append((name, "embedded diagram source metadata"))
    return failures


if __name__ == "__main__":
    result = check(Path(__file__).resolve().parents[1])
    for name, reason in result:
        print(f"{name}: {reason}")
    print(f"Publication identity check: {len(result)} failure(s)")
    sys.exit(bool(result))
