import json
from typing import Any, Dict, Optional, Tuple

from .crypto import b64d, b64e, mac_tag, xor_stream


class SecureChannel:

    def __init__(self, enc_key: bytes, mac_key: Optional[bytes], use_mac: bool = True):
        self.enc_key = enc_key
        self.mac_key = mac_key
        self.use_mac = use_mac
        if self.use_mac and not self.mac_key:
            raise ValueError("MAC enabled but mac_key is missing")

    def seal(self, inner_obj: Dict[str, Any]) -> Tuple[str, Optional[str]]:
        plaintext = json.dumps(inner_obj, separators=(",", ":")).encode("utf-8")
        ciphertext = xor_stream(plaintext, self.enc_key)
        tag_b64: Optional[str] = None
        if self.use_mac:
            tag = mac_tag(self.mac_key, ciphertext)
            tag_b64 = b64e(tag)
        return b64e(ciphertext), tag_b64

    def open(self, ciphertext_b64: str, mac_b64: Optional[str]) -> Dict[str, Any]:
        ciphertext = b64d(ciphertext_b64)
        if self.use_mac:
            if mac_b64 is None:
                raise ValueError("missing mac")
            expected = mac_tag(self.mac_key, ciphertext)
            provided = b64d(mac_b64)
            import hmac

            if not hmac.compare_digest(expected, provided):
                raise ValueError("bad mac")
        plaintext = xor_stream(ciphertext, self.enc_key)
        return json.loads(plaintext.decode("utf-8"))
