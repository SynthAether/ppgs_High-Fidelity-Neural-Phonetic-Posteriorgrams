import torch
from transformers import Wav2Vec2Model
from transformers.utils import logging

import ppgs
from ppgs.model.transformer import mask_from_lengths

logging.set_verbosity_error()

class W2V2(torch.nn.Module):

    def __init__(self):
        super().__init__()

        self.padding = 400//2 - 160//2

        # Load model
        self.w2v2: Wav2Vec2Model = Wav2Vec2Model.from_pretrained('facebook/wav2vec2-base')

        # Charsiu trick to upsample to 10ms
        self.w2v2.feature_extractor.conv_layers[-1].conv.stride = (1,)

        self.w2v2.freeze_feature_extractor()

        # Project onto space of phonemes
        assert ppgs.KERNEL_SIZE % 2 == 1
        self.output_projection = torch.nn.Conv1d(
            in_channels=768,
            out_channels=ppgs.OUTPUT_CHANNELS,
            kernel_size=ppgs.KERNEL_SIZE,
            padding=ppgs.KERNEL_SIZE // 2
        )

    def forward(self, input_tensor: torch.Tensor, lengths: torch.Tensor):
        # import pdb; pdb.set_trace()
        padded = torch.nn.functional.pad(input_tensor, (self.padding, self.padding)).squeeze(dim=1)
        mask = mask_from_lengths(lengths, self.padding).squeeze(dim=1).to(torch.long)
        w2v2_latent = self.w2v2(padded, mask).last_hidden_state
        w2v2_latent = torch.transpose(w2v2_latent, 1, 2)
        ppg = self.output_projection(w2v2_latent)
        return ppg