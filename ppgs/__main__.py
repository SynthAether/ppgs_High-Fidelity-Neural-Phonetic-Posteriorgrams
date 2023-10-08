import yapecs
from pathlib import Path

import ppgs


###############################################################################
# PPG inference command-line interface
###############################################################################


def parse_args():
    """Parse command-line arguments"""
    parser = yapecs.ArgumentParser(
        description='Phonetic posteriorgram inference')
    parser.add_argument(
        '--input_paths',
        nargs='+',
        type=Path,
        required=True,
        help='Paths to audio files and/or directories')
    parser.add_argument(
        '--output_paths',
        type=Path,
        nargs='+',
        required=True,
        help='The one-to-one corresponding output paths')
    parser.add_argument(
        '--extensions',
        nargs='+',
        help='Extensions to glob for in directories')
    parser.add_argument(
        '--checkpoint',
        default=ppgs.DEFAULT_CHECKPOINT,
        help='The checkpoint file')
    parser.add_argument(
        '--num-workers',
        type=int,
        default=8,
        help='Number of CPU threads for multiprocessing')
    parser.add_argument(
        '--gpu',
        type=int,
        help='The index of the GPU to use for inference. Defaults to CPU.')
    parser.add_argument(
        '--max-frames',
        type=int,
        default=ppgs.MAX_INFERENCE_FRAMES,
        help='Maximum number of frames in a batch')
    return parser.parse_args()


if __name__ == '__main__':
    ppgs.from_paths_to_paths(**vars(parse_args()))
