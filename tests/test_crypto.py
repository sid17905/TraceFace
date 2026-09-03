from src.crypto.canonicalizer import canonicalize_and_hash, canonicalize_json
from src.crypto.hasher import hash_face_embedding, keccak256_bytes, sha256_bytes
from src.crypto.merkle import build_provenance_merkle_tree, verify_merkle_root


def test_sha256_and_keccak():
    data = b"TraceFace test payload"
    sha = sha256_bytes(data)
    kec = keccak256_bytes(data)

    assert len(sha) == 64
    assert kec.startswith("0x")
    assert len(kec) == 66


def test_face_embedding_hasher():
    # 512-D float vector
    vec1 = [0.1] * 512
    vec2 = [0.1] * 512
    vec3 = [0.2] * 512

    h1 = hash_face_embedding(vec1)
    h2 = hash_face_embedding(vec2)
    h3 = hash_face_embedding(vec3)

    assert h1 == h2
    assert h1 != h3
    assert h1.startswith("0x")


def test_canonical_json_ordering():
    # Unordered dicts with identical content must produce identical bytes and hashes
    dict1 = {"b": 2, "a": 1, "nested": {"z": 100, "y": 50}}
    dict2 = {"nested": {"y": 50, "z": 100}, "a": 1, "b": 2}

    canon1 = canonicalize_json(dict1)
    canon2 = canonicalize_json(dict2)

    assert canon1 == canon2
    assert canonicalize_and_hash(dict1) == canonicalize_and_hash(dict2)


def test_merkle_tree_construction_and_verification():
    leaf_img = "0x" + "1" * 64
    leaf_emb = "0x" + "2" * 64
    leaf_soc = "0x" + "3" * 64
    leaf_tgt = "0x" + "4" * 64

    tree = build_provenance_merkle_tree(leaf_img, leaf_emb, leaf_soc, leaf_tgt)
    root = tree.merkle_root

    assert root.startswith("0x")
    assert len(root) == 66

    # Verify validity
    assert verify_merkle_root(leaf_img, leaf_emb, leaf_soc, leaf_tgt, root) is True

    # Tampering test: modify 1 leaf
    tampered_soc = "0x" + "9" * 64
    assert verify_merkle_root(leaf_img, leaf_emb, tampered_soc, leaf_tgt, root) is False
