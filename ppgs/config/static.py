"""Config parameters whose values depend on other config parameters"""
import ppgs


###############################################################################
# Directories
###############################################################################


# Location to save dataset partitions
PARTITION_DIR = ppgs.ASSETS_DIR / 'partitions'

# Default checkpoint for generation
DEFAULT_CHECKPOINT = ppgs.ASSETS_DIR / 'checkpoints' / 'default.pt'

# Weighting file for class balancing
CLASS_WEIGHT_FILE = ppgs.ASSETS_DIR / 'phoneme_weights.pt'


###############################################################################
# Data parameters
###############################################################################


# Maximum number of frames on the GPU during inference
MAX_INFERENCE_FRAMES = min(ppgs.MAX_FRAMES, ppgs.MAX_PREPROCESS_FRAMES)
