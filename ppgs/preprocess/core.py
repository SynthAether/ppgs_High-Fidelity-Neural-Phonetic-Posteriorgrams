import contextlib
import multiprocessing as mp
import time

import torch

import ppgs


###############################################################################
# Preprocess
###############################################################################


@ppgs.notify.notify_on_finish('preprocessing')
def datasets(
    datasets=ppgs.DATASETS,
    representations=ppgs.ALL_REPRESENTATIONS,
    gpu=None,
    num_workers=0,
    partition=None):
    """Preprocess a dataset

    Arguments
        datasets
            The names of the dataset to preprocess
        representations
            The names of the representations to do preprocessing for
        gpu
            The gpu to use for preprocessing
        num_workers
            The number of worker threads to use
        partition
            The partition to preprocess. Default (None) uses all partitions.
    """
    for dataset in datasets:
        if dataset == 'charsiu':
            import pdb; pdb.set_trace()

        try:

            # Setup multiprocessed dataloader
            dataloader = ppgs.data.loader(
                dataset,
                partition,
                features=['wav', 'length', 'audio_file'],
                num_workers=num_workers // 2)

        except ValueError:

            # Empty partition
            continue

        output = {
            file: f'{file.parent}/{file.stem}' + '-{}.pt'
            for _, _, files in dataloader for file in files}
        from_dataloader(
            dataloader,
            representations,
            output,
            num_workers=(num_workers + 1) // 2,
            gpu=gpu)


###############################################################################
# Utilities
###############################################################################


def from_dataloader(loader, representations, output, num_workers=0, gpu=None):
    """Preprocess from a dataloader

    Arguments
        loader
            A Pytorch DataLoader yielding batches of (audio, length, filename)
        representations
            The names of the representations to do preprocessing for
        output
            A dictionary mapping audio filenames to output filenames
        num_workers
            The number of worker threads to use for async file saving
        gpu
            The gpu to use for preprocessing
    """
    device = torch.device('cpu' if gpu is None else f'cuda:{gpu}')

    # Setup multiprocessing
    if num_workers == 0:
        pool = contextlib.nullcontext()
    else:
        pool = mp.get_context('spawn').Pool(num_workers)
    with pool, torch.inference_mode():

        # Batch preprocess
        for audios, lengths, audio_files in ppgs.iterator(
            loader,
            f'Preprocessing {", ".join(representations)} '
            f'for {loader.dataset.metadata.name}',
            total=len(loader)
        ):
            # Copy to device
            audios = audios.to(device)
            lengths = lengths.to(device)

            for representation in representations:

                # Preprocess
                outputs = getattr(
                    ppgs.preprocess,
                    representation
                ).from_audios(audios, lengths, gpu=gpu).cpu()

                # Get length in frames
                if representation != 'w2v2ft':
                    frame_lengths = lengths // ppgs.HOPSIZE
                else:
                    frame_lengths = (
                        lengths +
                        ppgs.preprocess.w2v2ft.WINDOW_SIZE -
                        ppgs.preprocess.w2v2ft.HOP_SIZE)

                # Get output filenames
                filenames = []
                for file in audio_files:
                    output_file = output[file]
                    if '{}' in output_file:
                        filenames.append(output_file.format(representation))
                    else:
                        filenames.append(output_file)

                if num_workers == 0:

                    # Synchronous save
                    for latent_output, filename, new_length in zip(
                        outputs.cpu(),
                        filenames,
                        frame_lengths.cpu()
                    ):
                        save_masked(latent_output, filename, new_length)
                else:

                    # Asynchronous save
                    pool.starmap_async(
                        save_masked,
                        zip(outputs, filenames, frame_lengths.cpu()))

                    # Wait if the queue is full
                    while pool._taskqueue.qsize() > 256:
                        time.sleep(1)

    # Shutdown multiprocessing
    if num_workers > 0:
        pool.close()
        pool.join()


def from_audio(audio, sample_rate=ppgs.SAMPLE_RATE, gpu=None):
    """Preprocess audio"""
    if ppgs.REPRESENTATION == 'wav':
        return ppgs.resample(audio, sample_rate, ppgs.SAMPLE_RATE)

    # Compute representation
    with torch.autocast('cuda' if gpu is not None else 'cpu'):
        features = getattr(ppgs.preprocess, ppgs.REPRESENTATION)(
            audio,
            sample_rate=sample_rate,
            gpu=gpu)

        if features.dim() == 2:
            features = features[None]

        return features


def save_masked(tensor, file, length):
    """Save masked tensor"""
    torch.save(tensor[..., :length].clone(), file)
