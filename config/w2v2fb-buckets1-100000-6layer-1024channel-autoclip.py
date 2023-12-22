MODULE = 'ppgs'

# Configuration name
CONFIG = 'w2v2fb-buckets1-100000-6layer-1024channel-autoclip'

# Number of buckets to partition training examples to minimize padding
BUCKETS = 1

# Method to use for gradient clipping.
# One of ['autoclip', 'inf', 'l1', 'l2', 'skip'].
GRADIENT_CLIPPING_METHOD = 'autoclip'

# Gradient clipping threshold.
# For autoclip, this specifies the clipping percentile.
GRADIENT_CLIPPING_THRESHOLD = .9

# Network width
HIDDEN_CHANNELS = 1024

# Dimensionality of input representation
INPUT_CHANNELS = 768

# Maximum number of frames in a batch
MAX_TRAINING_FRAMES = 100000

# Number of hidden layers
NUM_HIDDEN_LAYERS = 6

# Input representation
REPRESENTATION = 'w2v2fb'
