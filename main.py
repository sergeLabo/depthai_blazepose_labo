
from BlazeposeDepthaiEdge import BlazeposeDepthai
from BlazeposeRenderer import BlazeposeRenderer



def get_config():
    """
    Blazepose body pose detector
    Arguments:
    - input_src:
        frame source,
            - "rgb" or None: OAK* internal color camera,
            - "rgb_laconic": same as "rgb" but without sending the frames to the
                host. Note that as we are in Edge mode, input sources coming
                from the host like a image or a video is not supported

    - pd_model:
        Blazepose detection model blob file
        (if None, takes the default value POSE_DETECTION_MODEL)

    - pd_score:
        confidence score to determine whether a detection is reliable
        (a float between 0 and 1)

    - pp_model:
        detection postprocessing model blob file
        (if None, takes the default value DETECTION_POSTPROCESSING_MODEL)

    - lm_model:
        Blazepose landmark model blob file
            - None or "full": the default blob file LANDMARK_MODEL_FULL
            - "lite": the default blob file LANDMARK_MODEL_LITE
            - "831": the full model from previous version of mediapipe (0.8.3.1)
                LANDMARK_MODEL_FULL_0831
            - a path of a blob file.

    - lm_score_thresh :
        confidence score to determine whether landmarks prediction is reliable
        (a float between 0 and 1)

    - xyz:
        boolean, when True get the (x, y, z) coords of the reference point
        (center of the hips) (if the device supports depth measures)

    - crop :
        boolean which indicates if square cropping is done or not

    - smoothing:
        boolean which indicates if smoothing filtering is applied

    - filter_window_size and filter_velocity_scale:
        The filter keeps track (on a window of specified size) of
        value changes over time, which as result gives velocity of how value
        changes over time. With higher velocity it weights new values higher.
        - higher filter_window_size adds to lag and to stability
        - lower filter_velocity_scale adds to lag and to stability

    - internal_fps :
        when using the internal color camera as input source, set its FPS to
        this value (calling setFps())

    - internal_frame_height :
        when using the internal color camera, set the frame height
        (calling setIspScale()). The width is calculated accordingly to height
        and depends on value of 'crop'

    - stats :
        boolean, when True, display some statistics when exiting.

    - trace:
        boolean, when True print some debug messages

    - force_detection:
        boolean, force person detection on every frame (never use landmarks from
        previous frame to determine ROI)

    BlazeposeRenderer
    -show_3d
        choices = [None, "image", "world", "mixed"]
        Display skeleton in 3d in a separate window. See README for description
    - output
        Path to output video file
    """

    config = {}


    # Blazepose
    config['edge'] = True
    config['input_src'] = 'rgb'
    config['pd_model'] = None
    config['pp_model'] = None
    config['lm_model'] = 'lite'
    config['pd_score_thresh'] = 0.5
    config['lm_score_thresh'] = 0.7
    config['smoothing'] = True
    config['xyz'] = True
    config['crop'] = True
    config['filter_window_size'] = 5
    config['filter_velocity_scale'] = 10
    config['internal_fps'] = None
    config['internal_frame_height'] = 640
    config['stats'] = False
    config['trace'] = False
    config['force_detection'] = False

    # Renderer
    config['show_3d'] = None
    config['output'] = None

    return config


def main():
    config = get_config()

    tracker = BlazeposeDepthai(**config)
    renderer = BlazeposeRenderer(tracker, **config)

    while True:
        # Run blazepose on next frame
        frame, body = tracker.next_frame()

        if body:
            print("Depth:", int(body.xyz[2]))

        if frame is None:
            break

        # Draw 2d skeleton
        frame = renderer.draw(frame, body)
        key = renderer.waitKey(delay=1)
        if key == 27 or key == ord('q'):
            break

    renderer.exit()
    tracker.exit()


if __name__ == "__main__":
    main()
