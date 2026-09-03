import cv2
import numpy as np
import insightface
from typing import Dict, Any, List

class FaceDetector:
    """
    RetinaFace detector wrapper for finding faces and 5-point landmarks.
    """
    def __init__(self, model_name: str = 'buffalo_l', ctx_id: int = 0):
        self.app = insightface.app.FaceAnalysis(name=model_name, allowed_modules=['detection'])
        self.app.prepare(ctx_id=ctx_id, det_size=(640, 640))
        
    def detect_face(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Detects the most prominent face in the image.
        Returns a dictionary with bounding box and landmarks.
        """
        faces = self.app.get(image)
        if not faces:
            raise ValueError("ERR_NO_FACE_DETECTED")
            
        # If multiple faces, pick the largest bounding box area
        faces = sorted(faces, key=lambda f: (f.bbox[2]-f.bbox[0]) * (f.bbox[3]-f.bbox[1]), reverse=True)
        face = faces[0]
        
        bbox = face.bbox.astype(int) # [x_min, y_min, x_max, y_max]
        kps = face.kps.astype(int) # 5x2 array
        
        return {
            'bbox': bbox.tolist(),
            'landmarks': kps.tolist(),
            'confidence': float(face.det_score)
        }
