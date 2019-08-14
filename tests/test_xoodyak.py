import json

from xoodyak import __version__
from xoodyak import Xoodyak


def test_version():
    assert __version__ == "0.1.0"


def test_hash():
    with open("tests/kats/hash.json") as f:
        data = f.read()
    kats = json.loads(data)

    for kat in kats:
        msg = bytes.fromhex(kat["msg"])
        md = bytes.fromhex(kat["md"])
        new_md = bytearray(len(md))

        xoodyak = Xoodyak()
        xoodyak.absorb(msg)
        xoodyak.squeeze(new_md)

        assert len(md) == len(new_md)
        assert md == new_md


def test_aead():
    with open("tests/kats/aead.json") as f:
        data = f.read()
    kats = json.loads(data)

    for kat in kats:
        key = bytes.fromhex(kat["key"])
        nonce = bytes.fromhex(kat["nonce"])
        pt = bytes.fromhex(kat["pt"])
        ad = bytes.fromhex(kat["ad"])
        ct = bytes.fromhex(kat["ct"])
        ct_only = ct[: len(pt)]
        tag = ct[len(pt) :]

        new_ct_only = bytearray(len(ct_only))
        new_tag = bytearray(len(tag))

        xoodyak = Xoodyak.keyed(key)
        xoodyak.absorb(nonce)
        xoodyak.absorb(ad)
        xoodyak.encrypt(pt, new_ct_only)
        xoodyak.squeeze(new_tag)

        assert ct_only == new_ct_only
        assert tag == new_tag

        new_pt = bytearray(len(pt))

        xoodyak = Xoodyak.keyed(key)
        xoodyak.absorb(nonce)
        xoodyak.absorb(ad)
        xoodyak.decrypt(ct_only, new_pt)
        xoodyak.squeeze(new_tag)

        assert pt == new_pt
        assert tag == new_tag
