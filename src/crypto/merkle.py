from dataclasses import dataclass

from src.crypto.hasher import keccak256_bytes


@dataclass
class ProvenanceMerkleResult:
    leaf_source_image: str
    leaf_face_embedding: str
    leaf_social_post: str
    leaf_target_media: str
    intermediate_left: str
    intermediate_right: str
    merkle_root: str

    def to_dict(self) -> dict[str, str]:
        return {
            "leaf_source_image": self.leaf_source_image,
            "leaf_face_embedding": self.leaf_face_embedding,
            "leaf_social_post": self.leaf_social_post,
            "leaf_target_media": self.leaf_target_media,
            "intermediate_left": self.intermediate_left,
            "intermediate_right": self.intermediate_right,
            "merkle_root": self.merkle_root,
        }


def _combine_nodes(left_hex: str, right_hex: str) -> str:
    l_bytes = bytes.fromhex(left_hex.removeprefix("0x"))
    r_bytes = bytes.fromhex(right_hex.removeprefix("0x"))
    return keccak256_bytes(l_bytes + r_bytes)


def build_provenance_merkle_tree(
    source_image_hash: str,
    face_embedding_hash: str,
    social_post_hash: str,
    target_media_hash: str
) -> ProvenanceMerkleResult:
    """
    Constructs a deterministic 4-leaf Merkle Tree anchoring forensic provenance.
    """
    l0 = source_image_hash if source_image_hash.startswith("0x") else "0x" + source_image_hash
    l1 = face_embedding_hash if face_embedding_hash.startswith("0x") else "0x" + face_embedding_hash
    l2 = social_post_hash if social_post_hash.startswith("0x") else "0x" + social_post_hash
    l3 = target_media_hash if target_media_hash.startswith("0x") else "0x" + target_media_hash

    # Level 1 combination
    node_left = _combine_nodes(l0, l1)
    node_right = _combine_nodes(l2, l3)

    # Root
    root = _combine_nodes(node_left, node_right)

    return ProvenanceMerkleResult(
        leaf_source_image=l0,
        leaf_face_embedding=l1,
        leaf_social_post=l2,
        leaf_target_media=l3,
        intermediate_left=node_left,
        intermediate_right=node_right,
        merkle_root=root,
    )


def verify_merkle_root(
    source_image_hash: str,
    face_embedding_hash: str,
    social_post_hash: str,
    target_media_hash: str,
    expected_root: str
) -> bool:
    tree = build_provenance_merkle_tree(
        source_image_hash,
        face_embedding_hash,
        social_post_hash,
        target_media_hash
    )
    return tree.merkle_root.lower() == expected_root.lower()
