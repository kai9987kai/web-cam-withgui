import os
import unittest
import numpy as np
import cv2

from engine.point_cloud import PointCloudGenerator, PointCloudData


class TestPointCloudEngine(unittest.TestCase):
    """Test suite for 3D Photo Point Cloud Generator and Export."""

    def setUp(self):
        # Create synthetic test photo (640x480)
        self.frame = np.full((480, 640, 3), 100, dtype=np.uint8)
        # Add colorful foreground circle (simulating face/object)
        cv2.circle(self.frame, (320, 240), 90, (180, 150, 220), -1)
        cv2.rectangle(self.frame, (250, 180), (390, 300), (0, 200, 255), 3)

        self.generator = PointCloudGenerator()

    def test_depth_estimation(self):
        """Test continuous normalized depth map estimation."""
        depth = self.generator.estimate_depth(self.frame)
        self.assertIsNotNone(depth)
        self.assertEqual(depth.shape, (480, 640))
        self.assertTrue(np.all(depth >= 0.0) and np.all(depth <= 1.0))

    def test_point_cloud_generation(self):
        """Test 3D back-projection, normals, and colors."""
        pcd = self.generator.generate(self.frame, stride=4, depth_scale=1.5, bg_cutoff=0.9)
        self.assertIsInstance(pcd, PointCloudData)
        self.assertGreater(pcd.num_points, 5000)
        self.assertEqual(pcd.points.shape[1], 3)
        self.assertEqual(pcd.colors.shape[1], 3)
        self.assertIsNotNone(pcd.normals)
        self.assertEqual(pcd.normals.shape, pcd.points.shape)

    def test_export_ply_and_obj(self):
        """Test exporting 3D PLY and OBJ files."""
        pcd = self.generator.generate(self.frame, stride=8, depth_scale=1.0)
        os.makedirs("test_models", exist_ok=True)
        ply_path = "test_models/test_export.ply"
        obj_path = "test_models/test_export.obj"

        PointCloudGenerator.export_ply(ply_path, pcd)
        PointCloudGenerator.export_obj(obj_path, pcd)

        self.assertTrue(os.path.exists(ply_path))
        self.assertGreater(os.path.getsize(ply_path), 1000)

        self.assertTrue(os.path.exists(obj_path))
        self.assertGreater(os.path.getsize(obj_path), 1000)

        # Cleanup
        try:
            if os.path.exists(ply_path):
                os.remove(ply_path)
            if os.path.exists(obj_path):
                os.remove(obj_path)
            if os.path.exists("test_models"):
                os.rmdir("test_models")
        except Exception:
            pass


if __name__ == "__main__":
    unittest.main()
