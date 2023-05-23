import numpy as np
from PIL import UnidentifiedImageError
import unittest
from pixels2gpx import *


class TestImageTo2DArray(unittest.TestCase):

    def test_basic_image_convert(self):
        result = convert_image_to_2d_array('images_test/square.png', 'b', 0)
        # Testing a small sample of pixels from one of the corners
        self.assertEqual(result[0][0], 0)
        self.assertEqual(result[0][1], 0)
        self.assertEqual(result[1][0], 0)
        self.assertEqual(result[1][1], 255)

    def test_image_convert_bw(self):
        result = convert_image_to_2d_array('images_test/square.png', 'bw', 0)
        self.assertEqual(result[0][0], 0)
        self.assertEqual(result[0][1], 0)
        self.assertEqual(result[1][0], 0)
        self.assertEqual(result[1][1], 0)

    def test_image_convert_c(self):
        result = convert_image_to_2d_array('images_test/square_coloured.png', 'c', 0)
        self.assertEqual(result[0][0], 0)
        self.assertEqual(result[0][1], 0)
        self.assertEqual(result[1][0], 0)
        self.assertEqual(result[1][1], 255)

    def test_image_convert_none(self):
        result = convert_image_to_2d_array('images_test/square.png', '', 0)
        self.assertEqual(result[0][0], 0)
        self.assertEqual(result[0][1], 0)
        self.assertEqual(result[1][0], 0)
        self.assertEqual(result[1][1], 255)

    def test_fake_image_convert(self):
        self.assertRaises(UnidentifiedImageError, convert_image_to_2d_array, 'pixels2gpx_test.py', '', 0)


class TestBlindScan(unittest.TestCase):

    def test_basic_blind_scan(self):
        array_data = np.asarray([[255, 255], [0, 255]])
        result = blind_scan_on_2d_array(array_data, 0)
        self.assertEqual((0, 1), result)

    def test_blind_scan_no_match(self):
        array_data = np.asarray([[255, 255], [0, 255]])
        result = blind_scan_on_2d_array(array_data, 1)
        self.assertEqual((0, 0), result)

    def test_blind_scan_single_column(self):
        array_data = np.asarray([[255], [0]])
        result = blind_scan_on_2d_array(array_data, 0)
        self.assertEqual((0, 1), result)

    def test_blind_scan_single_row(self):
        array_data = np.asarray([[255, 0]])
        result = blind_scan_on_2d_array(array_data, 0)
        self.assertEqual((1, 0), result)


class TestGenerateGPX(unittest.TestCase):

    def test_basic_generate_gpx(self):
        test_trackpoints = [Trackpoint(13, 37, 1), Trackpoint(13, 38, 2)]
        result = generate_gpx(test_trackpoints, 'Test Track #42')
        self.assertTrue('''
 <trk>
  <name>Test Track #42</name>
  <type>10</type>
  <trkseg>
   <trkpt lat="13" lon="37">'''.lstrip() in result)
        self.assertTrue('''
   </trkpt>
   <trkpt lat="13" lon="38">'''.lstrip() in result)

    def test_generate_gpx_no_trackpoints(self):
        test_trackpoints = []
        result = generate_gpx(test_trackpoints, 'Empty Test Track')
        self.assertEqual('', result)

    def test_generate_gpx_no_name(self):
        test_trackpoints = [Trackpoint(13, 37, 1)]
        result = generate_gpx(test_trackpoints, '')
        self.assertTrue('<name></name>' in result)


class TestTraversalVectors(unittest.TestCase):

    def test_basic_traversal_vectors(self):
        result = get_traversal_vectors(1)
        self.assertEqual([(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)], result)

    def test_traversal_vectors_size_2(self):
        result = get_traversal_vectors(2)
        self.assertEqual([(2, 0), (2, 1), (2, 2), (1, 2), (0, 2), (-1, 2), (-2, 2), (-2, 1), (-2, 0), (-2, -1), (-2, -2), (-1, -2), (0, -2), (1, -2), (2, -2), (2, -1)], result)

    def test_traversal_vectors_size_0(self):
        result = get_traversal_vectors(0)
        self.assertEqual([], result)

    def test_traversal_vectors_size_negative(self):
        result = get_traversal_vectors(-1)
        self.assertEqual([], result)


class TestTrackpoint(unittest.TestCase):

    def test_gpx_string_from_trackpoint(self):
        tp = Trackpoint(13, 37, 1)
        self.assertTrue('<trkpt lat="13" lon="37">' in tp.to_gpx_string())


class TestNextTraversal(unittest.TestCase):

    def test_basic_next_traversal(self):
        array_data = np.asarray([[255, 0, 255, 255],
                                 [255, 255, 255, 255],
                                 [255, 255, 255, 255],
                                 [255, 255, 255, 255]])
        result = calculate_next_traversal(array_data, (0, 0), 0, 0, 1)
        self.assertEqual(5, result['index'])
        self.assertEqual((1, 0), result['vector'])

    def test_next_traversal_adjacent(self):
        array_data = np.asarray([[255, 255, 255, 255],
                                 [0, 255, 255, 255],
                                 [255, 255, 255, 255],
                                 [255, 255, 255, 255]])
        result = calculate_next_traversal(array_data, (0, 0), 0, 0, 1)
        self.assertEqual(7, result['index'])
        self.assertEqual((0, 1), result['vector'])

    def test_next_traversal_with_extended_reach(self):
        array_data = np.asarray([[255, 255, 255, 255, 255],
                                 [255, 255, 0, 255, 255],
                                 [255, 255, 255, 255, 255],
                                 [255, 255, 255, 255, 255]])
        result = calculate_next_traversal(array_data, (0, 0), 0, 0, 1)
        self.assertEqual(5, result['index'])
        self.assertEqual((2, 1), result['vector'])

    def test_final_traversal(self):
        array_data = np.asarray([[255, 255], [255, 255], [255, 255]])
        result = calculate_next_traversal(array_data, (0, 0), 0, 0, 1)
        self.assertEqual(0, result['index'])
        self.assertEqual((0, 0), result['vector'])

    def test_next_traversal_reverse_direction(self):
        array_data = np.asarray([[255, 255, 255, 255],
                                 [0, 0, 255, 255],
                                 [255, 255, 255, 255],
                                 [255, 255, 255, 255]])
        result = calculate_next_traversal(array_data, (0, 0), 0, 0, -1)
        self.assertEqual(5, result['index'])
        self.assertEqual((0, 1), result['vector'])


class TestStartPixel(unittest.TestCase):

    def test_basic_start_pixel(self):
        array_data = np.asarray([[255, 0, 255, 255],
                                 [255, 255, 255, 255],
                                 [255, 255, 255, 255],
                                 [255, 255, 255, 255]])
        result = calculate_starting_pixel(array_data, (1, 0), 0, 0, 1)
        self.assertEqual((1, 0), result)

    def test_start_pixel_default(self):
        array_data = np.asarray([[255, 255, 255, 255],
                                 [255, 255, 255, 255],
                                 [255, 255, 255, 0],
                                 [255, 255, 255, 255]])
        result = calculate_starting_pixel(array_data, (-1, -1), 0, 0, 1)
        self.assertEqual((3, 2), result)

    def test_start_pixel_with_close_by_valid_candidate(self):
        array_data = np.asarray([[0, 0, 0, 255],
                                 [255, 255, 255, 255],
                                 [255, 255, 255, 255],
                                 [255, 255, 255, 255]])
        result = calculate_starting_pixel(array_data, (2, 1), 0, 0, 1)
        self.assertEqual((1, 0), result)

    def test_start_pixel_non_zero_vector_index(self):
        array_data = np.asarray([[0, 0, 0, 255],
                                 [255, 255, 255, 255],
                                 [255, 255, 255, 255],
                                 [255, 255, 255, 255]])
        result = calculate_starting_pixel(array_data, (2, 1), 6, 0, 1)
        self.assertEqual((2, 0), result)

    def test_start_pixel_reverse_direction(self):
        array_data = np.asarray([[0, 255, 0, 255],
                                 [255, 255, 255, 255],
                                 [255, 255, 255, 255],
                                 [255, 255, 255, 255]])
        result = calculate_starting_pixel(array_data, (1, 0), 6, 0, -1)
        self.assertEqual((0, 0), result)


if __name__ == '__main__':
    unittest.main()
