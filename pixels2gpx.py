from PIL import Image
import PIL.ImageOps
import numpy as np
import datetime
import math
from gooey import Gooey, GooeyParser
from xml.sax.saxutils import escape


def convert_image_to_2d_array(file, inclusion_options, target_value):
    """
    Converts the pixel data from an image file into a 2D array of integer values

    :param file: File name of the image
    :type file: str
    :param inclusion_options: Options for standardising certain pixels
    :type inclusion_options: str
    :param target_value: Pixel value that would classify it as traversable
    :type target_value: int
    :return: 2D list of pixel values corresponding to the image
    :rtype: list
    """

    # Convert to grayscale for easier values to manage
    img_data = PIL.ImageOps.grayscale(Image.open(file))
    img_data_modified = np.asarray(img_data.getdata())  # Need to convert into a numpy array in order to utilise fancy indexing
    # Manipulate the image to make it easier to locate travserable pixels by standardising their values
    pixel_colour_black = 0
    pixel_colour_white = 255
    if 'b' in inclusion_options:
        img_data_modified[img_data_modified == pixel_colour_black] = target_value
    else:
        img_data_modified[img_data_modified == pixel_colour_black] = -1

    if 'w' in inclusion_options:
        img_data_modified[img_data_modified == pixel_colour_white] = target_value
    else:
        img_data_modified[img_data_modified == pixel_colour_white] = -1

    if 'c' in inclusion_options:
        img_data_modified[np.logical_and(img_data_modified > pixel_colour_black, img_data_modified < pixel_colour_white)] = target_value
    else:
        img_data_modified[np.logical_and(img_data_modified > pixel_colour_black, img_data_modified < pixel_colour_white)] = -1

    return img_data_modified.reshape((img_data.size[1], img_data.size[0]))


def blind_scan_on_2d_array(arr, target_value):
    """
    Returns the index coordinates of the first element in a 2D array that contains a specific value

    :param arr: 2D list of pixel values
    :type arr: list
    :param target_value: The pixel value of interest
    :type target_value: int
    :return: The X and Y coordinates of the next pixel of interest
    :rtype: tuple
    """
    results = np.nonzero(arr == target_value)
    if len(results[0]) > 0 and len(results[1]) > 0:
        # Column, Row (this is different to numpy, which orders array data in row-major format)
        return results[1][0], results[0][0]
    return 0, 0


class Trackpoint:
    def __init__(self, x, y, time_increment):
        """
        :param x: X coordinate of the trackpoint
        :type x: float
        :param y: Y coordinate of the trackpoint
        :type y: float
        :param time_increment: Number of seconds after the current time that this trackpoint was registered on
        :type time_increment: int
        """
        self.latitude = x
        self.longitude = y
        self.elevation = 0
        self.time = (datetime.datetime.utcnow() + datetime.timedelta(seconds=time_increment)).replace(microsecond=0).isoformat()  # Just missing the trailing Z
        self.extensions = {
            'cad': 35  # Not entirely sure what this does, but it's included in the exported GPX data from Strava
        }
    
    def to_gpx_string(self):
        """
        Returns a non-minified string representation of the trackpoint in the GPX format

        :return: XML string of the trackpoint
        :rtype: str
        """
        return f'''
   <trkpt lat="{self.latitude}" lon="{self.longitude}">
    <ele>{self.elevation}</ele>
    <time>{self.time}Z</time>
    <extensions>
     <gpxtpx:TrackPointExtension>
      <gpxtpx:cad>{self.extensions['cad']}</gpxtpx:cad>
     </gpxtpx:TrackPointExtension>
    </extensions>
   </trkpt>'''.lstrip()


def generate_gpx(trackpoint_list, track_name):
    """
    Returns the XML contents for a GPX file based on a list of track points

    :param trackpoint_list: List of Trackpoint objects that collectively compose a single track
    :type trackpoint_list: list
    :param track_name: The name of the track
    :type track_name: str
    :return: The XML string of the track
    :rtype: str
    """
    if len(trackpoint_list) <= 0:
        return ''
    trackpoint_separator = '\n   '
    return f'''
<?xml version="1.0" encoding="UTF-8"?>
<gpx creator="StravaGPX Android" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd http://www.garmin.com/xmlschemas/GpxExtensions/v3 http://www.garmin.com/xmlschemas/GpxExtensionsv3.xsd http://www.garmin.com/xmlschemas/TrackPointExtension/v1 http://www.garmin.com/xmlschemas/TrackPointExtensionv1.xsd" version="1.1" xmlns="http://www.topografix.com/GPX/1/1" xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1" xmlns:gpxx="http://www.garmin.com/xmlschemas/GpxExtensions/v3">
 <metadata>
  <time>{trackpoint_list[0].time}Z</time>
 </metadata>
 <trk>
  <name>{escape(track_name)}</name>
  <type>10</type>
  <trkseg>
   {trackpoint_separator.join([trackpoint.to_gpx_string() for trackpoint in trackpoint_list])}
  </trkseg>
 </trk>
</gpx>
'''.lstrip()


def get_traversal_vectors(magnitude):
    """
    Gets the coordinates relative to the centre that should be tested for valid traversal
    Vectors are ordered such that the first coordinate is the immediate right and then follows clockwise

    :param magnitude: The number of cells from the centre point to the rightmost cell
    :type magnitude: int
    :return: List of tuples representing the traversal vectors
    :rtype: list
    """
    vectors = []
    if magnitude > 0:
        [vectors.append((magnitude, right_to_bottom_magnitude)) for right_to_bottom_magnitude in range(0, magnitude + 1)]
        [vectors.append((right_to_left_magnitude, magnitude))   for right_to_left_magnitude   in reversed(range(-magnitude + 1, magnitude))]
        [vectors.append((-magnitude, left_to_top_magnitude))    for left_to_top_magnitude     in reversed(range(-magnitude, magnitude + 1))]
        [vectors.append((top_to_right_magnitude, -magnitude))   for top_to_right_magnitude    in range(-magnitude + 1, magnitude + 1)]
        [vectors.append((magnitude, right_to_start_magnitude))  for right_to_start_magnitude  in range(-magnitude + 1, 0)]
    return vectors


def calculate_next_traversal(arr, traversal_start, traversal_index, target_value, traversal_check_direction):
    """
    Calculates the next cell to navigate to based on a 2D array of integers

    :param arr: 2D list of pixel values
    :type arr: list
    :param traversal_start: X and Y coordinates of where the traversal starts from
    :type traversal_start: tuple
    :param traversal_index: Index corresponding to the vector being used to check traversals
    :type traversal_index: int
    :param target_value: Pixel value that would classify it as traversable
    :type target_value: int
    :param traversal_check_direction: Direction of traversal checking, which is either clockwise or counter-clockwise
    :type traversal_check_direction: int
    :return: Dictionary containing the traversal vector and the vector index for calculating the next traversal
    :rtype: dict
    """
    # The pixel may not have any immediately available neighbours, but we also want to avoid calling blind_scan_on_2d_array()
    # where possible, as that can usually result in a giant line running across the entire track to get to the next pixel.
    # Thus, only check within a certain range to minimise the potential noise produced by these intermediate lines.
    max_check_radius = math.ceil(len(arr[0]) / 2)
    for power in range(1, max_check_radius):
        traversal_vectors = get_traversal_vectors(power)
        for i in range(len(traversal_vectors)):
            # Continue moving in the same direction, only pivoting when said direction has proven to make no progress.
            # While it *may* be technically more correct to have (traversal_index * power), this seems to result in
            # slightly more noticeable intermediate lines compared to not doing this calculation. The reason this would be considered is
            # that we want the vector to scale along with the number of calculated vectors (i.e. the vector going up will remain up)
            try_index = (traversal_index + (i * traversal_check_direction)) % len(traversal_vectors)
            try_vector = (traversal_vectors[try_index][0] + traversal_start[0], traversal_vectors[try_index][1] + traversal_start[1])
            if (try_vector[0] < 0 or try_vector[0] > len(arr[0]) - 1) or (try_vector[1] < 0 or try_vector[1] > len(arr) - 1):
                # Accessing the pixel goes outside the image boundaries
                continue
            elif arr[try_vector[1]][try_vector[0]] == target_value:
                # Found an available pixel
                return {
                    'index': math.floor(
                        (
                            # Base the next vector to check from the opposite side of the current direction to account for lines that bend away from the current vector, which should slightly improve traversal results
                            # The -traversal_check_direction is to check the next unknown position, rather than re-check a location that is already known
                            (try_index - (math.ceil(len(traversal_vectors) / 2) - traversal_check_direction)) % len(traversal_vectors)
                        ) / power  # Division by power is needed to ensure the index maps as nicely as possible to the base vectors when this function is re-entered next time
                    ),
                    'vector': try_vector
                }
    # No immediate pixel to traverse to, just jump to the next pixel -- though this may need to be smarter when legitimately at the end
    print('Blindly scanning for next pixel')
    return {
        'index': 0,
        'vector': blind_scan_on_2d_array(arr, target_value)
    }


def generate_trackpoints(image, reference_coordinate, pixel_start, traversal_index, target_value, traversal_check_direction):
    """
    Returns a list of coordinates corresponding to the pixels from a given image object

    :param image: 2D list of pixel values
    :type image: list
    :param reference_coordinate: Longitude and latitude of where the track occurs
    :type reference_coordinate: tuple
    :param pixel_start: X and Y coordinate on the image where the track begins from
    :type pixel_start: tuple
    :param traversal_index: Index corresponding to the vector being used to check traversals
    :type traversal_index: int
    :param target_value: Pixel value that would classify it as traversable
    :type target_value: int
    :param traversal_check_direction: Direction of traversal checking, which is either clockwise or counter-clockwise
    :type traversal_check_direction: int
    :return: List of Trackpoint objects
    :rtype: list
    """
    output_trackpoints = []
    pixel_ignore_value = -1
    pixel_target_count = np.count_nonzero(image == target_value)

    # You can modify the pixel_target_count to get only the coordinates from index 0 to N rather than the full list
    for pixel_traversed_count in range(0, pixel_target_count):
        print(f'Traversing to ({pixel_start[0]}, {pixel_start[1]})')
        # The initial reference coordinate is ordered as latitude, longitude.
        # The pixel data from numpy is ordered as longitude, latitude
        output_trackpoints.append(Trackpoint(reference_coordinate[0] - (pixel_start[1] * 0.00001), reference_coordinate[1] + (pixel_start[0] * 0.00001), pixel_traversed_count))

        image[pixel_start[1]][pixel_start[0]] = pixel_ignore_value  # Remember that numpy arrays are in row-major order
        pixel_ignore_value -= 1  # Decrement the value only for debug purposes to see the traversal path
        pixel_next_traversal = calculate_next_traversal(image, pixel_start, traversal_index, target_value, traversal_check_direction)
        pixel_start = pixel_next_traversal['vector']
        traversal_index = pixel_next_traversal['index']
    return output_trackpoints

    
def calculate_starting_pixel(image, start, traversal_index, target_value, traversal_check_direction):
    """
    Returns the pixel coordinates of an image where the track begins from

    :param image: 2D list of pixel values
    :type image: list
    :param start: X and Y coordinate on the image where the track begins from
    :type start: tuple
    :param traversal_index: Index corresponding to the vector being used to check traversals
    :type traversal_index: int
    :param target_value: Pixel value that would classify it as traversable
    :type target_value: int
    :param traversal_check_direction: Direction of traversal checking, which is either clockwise or counter-clockwise
    :type traversal_check_direction: int
    :return: X and Y coordinate on the image where a valid traversal can begin from
    :rtype: tuple
    """
    if start[0] >= 0 and start[1] >= 0:
        # Ensure the specified coordinates are within the image boundaries
        start_x_normalised = min(max(0, start[0]), len(image[0]) - 1)
        start_y_normalised = min(max(0, start[1]), len(image) - 1)
        start_coordinate_normalised = (start_x_normalised, start_y_normalised)

        if not image[start_y_normalised][start_x_normalised] == target_value:
            # Need to find the next valid coordinate, otherwise a line will be drawn from the starting point
            coordinate_correction = calculate_next_traversal(image, start_coordinate_normalised, traversal_index, target_value, traversal_check_direction)
            return coordinate_correction['vector'][0], coordinate_correction['vector'][1]
        return start_coordinate_normalised
    else:
        return blind_scan_on_2d_array(image, target_value)


if __name__ == '__main__':
    @Gooey(image_dir='images/gooey', default_size=(700, 480))
    def convert_pixels_to_gpx():
        parser = GooeyParser(
            description='Conversion tool to generate a GPX file based on an image, with each pixel of interest connected as a single track.'
        )
        parser.add_argument('-i', dest='image_file', metavar='Source Image', required=True, widget='FileChooser', help='Input file location')
        parser.add_argument('-o', dest='output_file', metavar='Output File', required=True, default='./output.gpx', widget='FileSaver', help='Output file location')
        parser.add_argument('-n', dest='track_name', metavar='Track Name', default='My Walk', help='Name of the track')
        parser.add_argument('-col', dest='colour_zones', metavar='Colour Zones', default='b', help='\n'.join(['Colour categories to consider as part of traversal which can be combined together, e.g. bw. Possible options are:', 'b = black pixels (default)', 'w = white pixels', 'c = non-black and non-white pixels']))
        parser.add_argument('-cx', dest='centre_x', metavar='Longitude', default=32.3451, type=float, help='X coordinate of where the trackpoints will be based around')
        parser.add_argument('-cy', dest='centre_y', metavar='Latitude', default=-106.5614, type=float, help='Y coordinate of where the trackpoints will be based around')
        parser.add_argument('-px', dest='start_x', metavar='Initial X Coordinate', default=-1, type=int, help='X pixel coordinate (zero-based) of where the track will start on the image.\nThis has no effect when set to less than 0 or specified without the initial Y coordinate argument, and might be automatically adjusted to the nearest pixel of interest.')
        parser.add_argument('-py', dest='start_y', metavar='Initial Y Coordinate', default=-1, type=int, help='Y pixel coordinate (zero-based) of where the track will start on the image.\nThis has no effect when set to less than 0 or specified without the initial X coordinate argument, and might be automatically adjusted to the nearest pixel of interest.')
        parser.add_argument('-pd', dest='pixel_traversal_index', metavar='Initial Traversal Direction', default=0, type=int, choices=range(0, 8), help='\n'.join(['Initial traversal direction from the starting pixel coordinate. Each possible value corresponds to:', '0 = Right (default)', '1 = Right-down', '2 = Down', '3 = Left-down', '4 = Left', '5 = Left-up', '6 = Up', '7 = Right-up']))
        parser.add_argument('-d', dest='direction', metavar='Traversal Check Direction', default=1, type=int, choices=[1, -1], help='\n'.join(['Direction of traversal checks.', '1 = Clockwise (default)', '-1 = Counter-clockwise']))
        args = parser.parse_args()

        # For the time being, only consider black pixels to be travserable - allowing this to be configurable could get very technical, especially since this is a grayscale value
        pixel_target_value = 0
        image_data = convert_image_to_2d_array(args.image_file, args.colour_zones.lower(), pixel_target_value)
        start_coordinate = calculate_starting_pixel(image_data, (args.start_x, args.start_y), args.pixel_traversal_index, pixel_target_value, args.direction)
        trackpoints = generate_trackpoints(image_data, (args.centre_x, args.centre_y), start_coordinate, args.pixel_traversal_index, pixel_target_value, args.direction)
        print(f'Completed GPX conversion of "{args.image_file}"')

        with open(args.output_file, 'w', newline='', encoding='utf-8') as f:
            f.write(generate_gpx(trackpoints, args.track_name))
            print(f'Success! The GPX file can be located at "{args.output_file}"')
    convert_pixels_to_gpx()
