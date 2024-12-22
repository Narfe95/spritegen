import math
import os
from typing import Tuple

import ffmpeg


VIDEO_FORMATS = ["mp4", "webm"]


class SpriteGen:

    def __init__(self, video_file: str):
        self.video_file = video_file

    def _get_framecount(self) -> Tuple[int, float]:
        """
        Get the total number of frames in the video using ffmpeg.probe.

        Returns:
            int: Total number of frames in the video.
        """
        probe = ffmpeg.probe(os.path.join("input", self.video_file))
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        if not video_stream or 'nb_frames' not in video_stream:
            raise ValueError("Could not retrieve frame count from video.")
        return int(video_stream.get("nb_frames")), float(probe.get("format").get("duration"))

    def generate_spritesheet(self) -> None:
        """
        Generate a sprite sheet from a video using FFmpeg.

        Returns:
            None
        """
        try:
            total_frames, duration = self._get_framecount()
        except Exception as e:
            print(f"Error getting video information: {e}")
            return

        # Determine quality level and grid size
        frames, frame_size = calculate_quality(total_frames)

        # Calculate grid dimensions
        cols = int(math.sqrt(frames))
        rows = math.ceil(frames / cols)
        new_frame_rate = round(frames / duration)

        output_name = os.path.join("output", self._output_name(framerate=new_frame_rate, rows=rows, cols=cols))

        # Generate sprite sheet
        try:
            (ffmpeg.input(os.path.join("input", self.video_file)).
             filter("fps", fps=f"{new_frame_rate}").
             filter("scale", frame_size, frame_size).
             filter("tile", f"{cols}x{rows}").
             output(output_name, vframes=1).run())
            print(f"Sprite sheet saved to {output_name}")
        except ffmpeg.Error as e:
            print(f"Error generating sprite sheet: {str(e)}")

    def _output_name(self, framerate: float, rows: int, cols: int) -> str:
        basename = self.video_file.rsplit(".")[0]
        framesize = rows * cols
        return f"{basename}_{framerate}fps_{framesize}.png"


def calculate_quality(total_frames):
    """
    Determine the best quality level for the sprite sheet based on total video frames.
    """
    quality_map = {
        "Quality": (10, 4, 512),
        "Balance": (50, 16, 256),
        "Fluidity": (float('inf'), 64, 128)
    }

    for quality, (threshold, frames, frame_size) in quality_map.items():
        if total_frames <= threshold:
            return frames, frame_size


# Example usage
if __name__ == "__main__":
    if not os.path.exists("output"):
        os.mkdir("output")

    if not os.path.exists("input"):
        raise Exception("Input directory does not exist.")

    for file in os.listdir("input"):
        if file.rsplit(".")[1] not in VIDEO_FORMATS:
            continue
        try:
            SpriteGen(video_file=file).generate_spritesheet()
        except ValueError as value_error:
            print(str(value_error))
