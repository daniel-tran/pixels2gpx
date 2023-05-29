# Pixel Image to GPX converter

Turn your pixel-based images into GPS coordinates that vaguely resemble it

![Visual example with a diamond shape](https://github.com/daniel-tran/pixels2gpx/raw/main/images/readme/visual_example.png)

# Usage

*Note: Users should have Python 3.8 or higher installed when running these commands*

The following command installs the necessary packages for this utility:

```batch
pip install -r REQUIREMENTS.txt
```

After that, you can run this command to bring up the user interface where you can specify the input image and GPX file destination, among other things:

```batch
python pixels2gpx.py
```

# Running unit tests

You can run unit tests from this directory with the following command:

```batch
python pixels2gpx_tests.py
```

# FAQ

## Where can I view the activity results?

### Strava

After logging into Strava, you can navigate to the upload drop-down menu > Upload activity > File, and select the generated GPX file. At the time of writing this, Strava has a file limit of 25MB, so large or particularly complex images will not be viable using this method.

### GPX Studio

[GPX Studio](https://gpx.studio/) is a free online tool that lets you view tracks from a GPX file on the world map. To upload a file, click on Load GPX > Desktop, and select the generated GPX file.
Large or particularly complex images may require a bit of waiting before it shows.

## How can I improve the GPX result from a given source image?

Other than tweaking the parameters available, there are a couple of basic ways that should more or less improve the end result:

### Use a different GPX viewer

The same GPX file might look better (or worse) depending on your choice of GPX viewer. Some tracks might look good in Strava, others may look better in GPX Studio and some might look equally passable on both, thereby requiring the use of some other GPX viewer.

### Remove compression artifacts

Certain image formats such as JPEG will introduce distortions and loss of detail to achieve smaller file sizes. This adds extra noise that can make it more difficult for the utility to draw shapes, as some of these distortions may also be traversed when they are technically not part of the portrayed image.

As such, using a lossless image format such as PNG or BMP will minimise the compression artifacts present in a saved image *(note that simply changing the file extension does not remove the compression artifacts)*.

You can read more about compression artifacts [here](https://en.wikipedia.org/wiki/Compression_artifact).

### Reduce the number of colours used

Since this utility only distinguishes pixels as being black, white or coloured, all coloured pixels will always be lumped together as a single colour internally.

Therefore, the types of images that work best with this utility are those with clear divisions between coloured areas & whitespace (think of [the Steam Deck icon](https://commons.wikimedia.org/wiki/File:Steam_Deck_favicon.svg)) or images that are outlines (think of those black and white colouring pages).

In the case of the latter, you can also [generate various curve-like graphs using Wolfram Alpha](https://www.wolframalpha.com/examples/mathematics/geometry/curves-and-surfaces/popular-curves) and save the output image after pressing "Hide axes" which can then be downloaded for use with this utility.

### Minimise the number of disconnected lines

Any shapes that are separated such that there is no way to connect them using the same colour category (i.e. black, white or generally coloured) results in at least one intermediate line drawn per shape in order to traverse them all. This means that the more disconnected shapes or lines that are present in an image, the more intermediate lines are required to cover all the shapes of interest which adds visual clutter to the final image, reducing its overall appeal.

Having said that, even shapes which don't have any line disconnections (for example, the lowercase 'd' character) may still exhibit intermediate lines. So one may have to get very technical with both the parameters and the image itself to truly minimise the impact of intermediate lines.

## Why does this tool only support black, white and generally coloured pixels when indicating what's part of the track? Why not just allow users to specify an exact colour?

The short answer: This makes it a whole lot easier to use, develop, test and debug with this limitation.

The long answer: One of the guiding principles I try to adhere to in this repo is that **users should be able to configure this tool without having to open the image itself**. Why? The more things a user has to do as part of using this tool, the more complex the workflow can become. Imagine if users were required to:

1. Open the image in an editor.
2. Select the exact pixel they want to select the colour from.
3. Convert the colour value from RGB to Hexadecimal (or more broadly, do some external colour format conversion on the user's end)
4. Run this tool with a specific parameter with the calculated value in step 3.

An alternative could be to support colour ranges to eliminate the need for a precise colour selection, for example all colours greater than #00FACE but less than #F00D13. However, this could pose even more problems, as there might be a rogue pixel that happens to fall into this colour range that is in some obscure part of the image.

In that regard, abstracting the pixel colour into those categories is perhaps the easiest way forward.

## Does this replace the manual creation of Strava art?

No, for the following reasons:

1. Manual creation means you have full control over how the traversal is conducted.
You'll notice that using this tool to map complex images usually results in some intermediate lines to get from one coordinate to another far-off location, which can adversely affect the portrayed image.
2. This tool has no regard for realistically adhering to terrain and all, so it's fairly obvious when a track has been generated, especially when there are long intermediate lines.
3. Manual creation means you're at least getting *some* form of physical exercise.

# Motivation

On a lonely and rather disappointing night in May 2023, I happened to stumble across [Strava Art]( https://www.strav.art/home), which is a way of creating artworks using GPS data collected by Strava when walking, cycling or other physical activities.

It soon dawned on me that these artworks were created by painstakingly planning a very specific route, going outside and travelling said route to produce these artworks. As far as I was aware, there wasn't any open source tool or similar utility that could generalise this process of producing artworks from GPS data.

And so I set out to solve this rather unusual problem...
