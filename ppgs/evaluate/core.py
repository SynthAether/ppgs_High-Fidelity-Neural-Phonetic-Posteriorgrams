"""core.py - model evaluation"""

import json
import time
from contextlib import ExitStack
from pathlib import Path
from matplotlib.figure import Figure

import numpy as np
import torch
import tqdm

import ppgs
from ppgs.notify import notify_on_finish

###############################################################################
# Evaluate
###############################################################################

@notify_on_finish('evaluate')
def datasets(datasets, model_source: Path=None, gpu=None, partition=None):
    """Perform evaluation"""

    model_source = Path(model_source)
    if not model_source.exists():
        raise FileNotFoundError(f'model source \'{model_source}\' does not exist')
    if model_source.is_dir():
        # Get the config file and configure with yapecs
        configs = list(model_source.glob('*.py'))
        assert len(configs) == 1, 'there must be exactly one python file in a run directory'
        config = configs[0]


        checkpoints = list(model_source.glob('*.pt'))
        steps = [int(checkpoint.stem) for checkpoint in checkpoints]
        checkpoint = checkpoints[np.argmax(steps)]
        import pdb; pdb.set_trace()
    else:
        checkpoint = model_source

    with ExitStack() as stack:
    
        # Start benchmarking
        ppgs.BENCHMARK = True
        #TODO restore functionality
        # ppgs.TIMER.reset()
        start = time.time()

        # Containers for results
        overall, granular = {}, {}

        # Per-file metrics
        file_metrics = ppgs.evaluate.Metrics('per-file')

        # Per-dataset metrics
        dataset_metrics = ppgs.evaluate.Metrics('per-dataset')

        # Aggregate metrics over all datasets
        aggregate_metrics = ppgs.evaluate.Metrics('aggregate', include_figures=True)

        device = torch.device('cpu' if gpu is None else f'cuda:{gpu}')

        # Evaluate each dataset
        for dataset in datasets:

            # Reset dataset metrics
            dataset_metrics.reset()

            # Setup test dataset
            dataloader = ppgs.data.loader.loader(dataset, partition, features=[ppgs.REPRESENTATION, 'length', 'phonemes', 'stem'])
            iterator = tqdm.tqdm(
                dataloader,
                f'Evaluating {ppgs.CONFIG} on {dataset}',
                len(dataloader),
                dynamic_ncols=True
            )

            # Iterate over test set
            for input_ppgs, lengths, indices, stems in iterator:

                # Reset file metrics
                file_metrics.reset()

                input_ppgs = input_ppgs.to(device)
                lengths = lengths.to(device)
                indices = indices.to(device)
                logits = ppgs.from_features(input_ppgs, lengths, checkpoint=checkpoint, gpu=gpu, softmax=False)

                # Update metrics
                file_metrics.update(logits, indices)
                dataset_metrics.update(logits, indices)
                aggregate_metrics.update(logits, indices)

                # Copy results
                stem = stems[0]
                granular[f'{dataset}/{stem}'] = file_metrics()
            overall[dataset] = dataset_metrics()
        overall['aggregate'] = aggregate_metrics()

        # Make output directory
        directory = ppgs.EVAL_DIR / ppgs.CONFIG
        print(directory)
        directory.mkdir(exist_ok=True, parents=True)

        # Write to json files
        # with open(directory / f'overall-{partition}.json', 'w') as file:
        #     json.dump(overall, file, indent=4)
        save(overall, f'overall-{partition}', directory)
        with open(directory / f'granular-{partition}.json', 'w') as file:
            json.dump(granular, file, indent=4)

        # Turn off benchmarking
        ppgs.BENCHMARK = False

        # Get benchmarking information
        # benchmark = ppgs.TIMER()
        benchmark = {}
        benchmark['elapsed'] = time.time() - start

        # Get total number of frames, samples, and seconds in test data
        #TODO make better way of accessing loss
        frames = aggregate_metrics.metrics[2].count
        #TODO check this
        # samples = ppgs.convert.frames_to_samples(frames)
        samples = int(frames * ppgs.HOPSIZE)
        # TODO check this
        # seconds = ppgs.convert.frames_to_seconds(frames)
        seconds = float(samples / ppgs.SAMPLE_RATE)

        # Format benchmarking results
        results = {
            key: {
                'real-time-factor': seconds / value,
                'samples': samples,
                'samples-per-second': samples / value,
                'total': value
            } for key, value in benchmark.items()}

        # Write benchmarking information
        with open(directory / f'time-{partition}.json', 'w') as file:
            json.dump(results, file, indent=4)


def save(metrics_dict, name, directory, save_json=True):
    """Save metrics and maybe figures"""
    fig_dir = directory / name
    fig_dir.mkdir(exist_ok=True, parents=True)
    for metric, value in list(metrics_dict.items()):
        if isinstance(value, dict):
            save(value, name, directory, save_json=False)
        elif isinstance(value, Figure):
            value.savefig(fig_dir / f'{metric.replace("/", "-")}.jpg', bbox_inches='tight', pad_inches=0)
            value.savefig(fig_dir / f'{metric.replace("/", "-")}.pdf', bbox_inches='tight', pad_inches=0)
            del metrics_dict[metric]
        elif isinstance(value, torch.Tensor) and value.dim() >= 1:
            torch.save(value, fig_dir / f'{metric.replace("/", "-")}.pt')
            del metrics_dict[metric]
    if save_json:
        with open(directory / f'{name}.json', 'w') as file:
            json.dump(metrics_dict, file, indent=4)
