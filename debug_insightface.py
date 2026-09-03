import cv2
import numpy as np
import insightface

app = insightface.app.FaceAnalysis(name='buffalo_l', allowed_modules=['detection', 'recognition'])
app.prepare(ctx_id=0, det_size=(640, 640))

img = cv2.imread('data/sample_inputs/sample_target.jpg')
faces = app.get(img)
face = faces[0]

print("Real Face attributes:")
print(dir(face))

class MockFace:
    def __init__(self, bbox, kps):
        self.bbox = np.array(bbox)
        self.kps = np.array(kps)

mock_face = MockFace(face.bbox, face.kps)
app.models['recognition'].get(img, mock_face)

print("\nMock Face attributes after get:")
print(dir(mock_face))

