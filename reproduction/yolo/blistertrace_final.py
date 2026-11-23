"""Reproducible blister-defect training helpers, embedded in the Kaggle notebook.

No secrets, model downloads, or training run on import. Physical target tests
and the separate Llama/ExecuTorch component remain separate deployment gates.
"""
from pathlib import Path
from collections import Counter, defaultdict
import csv
import hashlib
import json
import math
import random
import re
import shutil


def write_json(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2, default=str))


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def source_family(stem):
    """Roboflow export siblings share the filename preceding .rf.<hash>.

    This is a source-image family, NOT proof of physical-strip identity.
    """
    return re.split(r'\.rf\.', stem, maxsplit=1)[0]


def fingerprint(path):
    import numpy as np
    from PIL import Image
    with Image.open(path) as opened:
        rgb = opened.convert('RGB')
        rgb.load()
        exact = hashlib.sha256(str(rgb.size).encode() + rgb.tobytes()).hexdigest()
        gray = np.asarray(rgb.convert('L').resize((17, 16)), dtype=np.int16)
        bits = (gray[:, 1:] > gray[:, :-1]).ravel()
        perceptual = int.from_bytes(np.packbits(bits).tobytes(), 'big')
        return exact, perceptual, rgb.size


def load_boxes(path, class_count):
    rows = []
    if not Path(path).is_file():
        raise ValueError(f'Missing annotation: {path}')
    for line_no, line in enumerate(Path(path).read_text().splitlines(), 1):
        if not line.strip():
            continue
        values = [float(v) for v in line.split()]
        if len(values) != 5 or not all(math.isfinite(v) for v in values):
            raise ValueError(f'Expected five finite box values: {path}:{line_no}')
        c, x, y, w, h = values
        if not c.is_integer() or not 0 <= c < class_count:
            raise ValueError(f'Invalid class: {path}:{line_no}')
        if not (0 <= x <= 1 and 0 <= y <= 1 and 0 < w <= 1 and 0 < h <= 1):
            raise ValueError(f'Invalid box: {path}:{line_no}')
        if min(x-w/2, y-h/2) < -0.002 or max(x+w/2, y+h/2) > 1.002:
            raise ValueError(f'Out-of-bounds box: {path}:{line_no}')
        rows.append((int(c), x, y, w, h))
    return rows


def compare_duplicate_annotations(first, second, size):
    """Accept exact labels or same-class one-to-one matches within 1 px and IoU .99.

    Applied only after decoded RGB pixel hashes match. The canonical annotation
    is retained unchanged. Every rounded match includes both original labels.
    """
    if sorted(first) == sorted(second):
        return {'annotation_match':'exact', 'max_corner_delta_pixels':0., 'min_box_iou':1.}
    if len(first) != len(second):
        return None
    left = [xyxy(box,*size) for box in first]
    right = [xyxy(box,*size) for box in second]
    candidates = []
    for a in left:
        choices = []
        for j,b in enumerate(right):
            delta = max(abs(x-y) for x,y in zip(a[1:],b[1:]))
            overlap = iou(a[1:],b[1:])
            if a[0] == b[0] and delta <= 1.0+1e-9 and overlap >= .99-1e-12:
                choices.append((j,delta,overlap))
        candidates.append(choices)
    matched = {}
    def assign(index, seen):
        for j,_,_ in candidates[index]:
            if j in seen:
                continue
            seen.add(j)
            if j not in matched or assign(matched[j],seen):
                matched[j] = index
                return True
        return False
    if not all(assign(i,set()) for i in range(len(left))):
        return None
    selected = [next((delta,overlap) for k,delta,overlap in candidates[i] if k==j)
                for j,i in matched.items()]
    return {'annotation_match':'bounded_rounding',
            'max_corner_delta_pixels':max(d for d,_ in selected),
            'min_box_iou':min(o for _,o in selected)}


def scan_export(root, names):
    root = Path(root)
    images = sorted(p for p in root.rglob('*')
                    if p.suffix.lower() in {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
                    and p.parent.name == 'images')
    if not images:
        raise ValueError('No images found in split/images folders.')
    records, exact_seen, duplicates = [], {}, []
    for image in images:
        label = image.parent.parent / 'labels' / (image.stem + '.txt')
        boxes = load_boxes(label, len(names))
        exact, dhash, size = fingerprint(image)
        if exact in exact_seen:
            previous = exact_seen[exact]
            comparison = compare_duplicate_annotations(previous['boxes'],boxes,size)
            if comparison is None:
                raise ValueError(
                    'Identical image pixels have conflicting labels; review source. '
                    f'First image: {previous["image"]}; label: {previous["label"]}; '
                    f'other image: {image}; label: {label}. '
                    'Compare annotations before resolving; do not select a copy arbitrarily.')
            duplicate = {'removed':str(image), 'kept':previous['image'], **comparison}
            if comparison['annotation_match']=='bounded_rounding':
                duplicate.update({'kept_boxes':previous['boxes'], 'removed_boxes':boxes,
                                  'image_size':size,
                                  'policy':'same class/count, one-to-one, <=1 pixel per corner and IoU >=0.99; canonical labels unchanged'})
            duplicates.append(duplicate)
            continue
        record = {'image': str(image), 'label': str(label),
                  'source_split': image.parent.parent.name,
                  'family': source_family(image.stem), 'sha256_pixels': exact,
                  'dhash': dhash, 'size': size, 'boxes': boxes}
        exact_seen[exact] = record
        records.append(record)
    return records, duplicates


def curate_export(root, names):
    """Audit the whole export; exclude unresolved source families before splitting.

    All copies of conflicting pixel groups and their source-family siblings are
    excluded, including aliases in other pixel groups. Source files are read only.
    No label merging, majority voting, or class relabeling occurs.
    """
    root=Path(root)
    images=sorted(p for p in root.rglob('*') if p.parent.name=='images'
                  and p.suffix.lower() in {'.jpg','.jpeg','.png','.bmp','.webp'})
    if not images:
        raise ValueError('No images found in split/images folders.')
    pixels=defaultdict(list)
    invalid=[]
    bad_families=set()
    bad_hashes=set()
    for image in images:
        label=image.parent.parent/'labels'/(image.stem+'.txt')
        family=source_family(image.stem)
        try:
            exact,dhash,size=fingerprint(image)
        except Exception as error:
            invalid.append({'image':str(image),'label':str(label),'family':family,
                            'reason':'unreadable_image','detail':str(error)})
            bad_families.add(family)
            continue
        try:
            boxes=load_boxes(label,len(names))
        except (ValueError,OSError,UnicodeError) as error:
            invalid.append({'image':str(image),'label':str(label),'family':family,
                            'sha256_pixels':exact,'reason':'invalid_or_missing_annotation',
                            'detail':str(error)})
            bad_families.add(family)
            bad_hashes.add(exact)
            continue
        pixels[exact].append({'image':str(image),'label':str(label),
            'source_split':image.parent.parent.name,'family':family,
            'sha256_pixels':exact,'dhash':dhash,'size':size,'boxes':boxes})
    conflicts=[]
    for exact,copies in pixels.items():
        # Pairwise comparison prevents a chain of small shifts exceeding the bound.
        incompatible=any(compare_duplicate_annotations(a['boxes'],b['boxes'],a['size']) is None
                         for i,a in enumerate(copies) for b in copies[:i])
        if incompatible:
            conflicts.append({'sha256_pixels':exact,
                'reason':'annotation_difference_exceeds_bounded_rounding_or_class_count_mismatch',
                'copies':copies})
            bad_hashes.add(exact)
            bad_families.update(r['family'] for r in copies)
    # Transitively exclude every alias of a bad pixel group/source family.
    changed=True
    while changed:
        changed=False
        for exact,copies in pixels.items():
            if exact in bad_hashes or any(r['family'] in bad_families for r in copies):
                before=(len(bad_families),len(bad_hashes))
                bad_hashes.add(exact)
                bad_families.update(r['family'] for r in copies)
                changed=changed or before!=(len(bad_families),len(bad_hashes))
    records,duplicates,excluded=[],[],list(invalid)
    for exact,copies in pixels.items():
        if exact in bad_hashes:
            excluded.extend(dict(r,reason='excluded_source_family_or_pixel_alias') for r in copies)
            continue
        canonical=dict(copies[0],families=sorted({r['family'] for r in copies}))
        records.append(canonical)
        for row in copies[1:]:
            comparison=compare_duplicate_annotations(canonical['boxes'],row['boxes'],canonical['size'])
            duplicates.append({'removed':row['image'],'kept':canonical['image'],**comparison,
                'kept_boxes':canonical['boxes'],'removed_boxes':row['boxes'],'image_size':canonical['size']})
    report={'policy_version':'curated-v2',
        'policy':'Exclude all unresolved pixel-group copies and source-family aliases before splitting; preserve source files and canonical labels.',
        'rounding_policy':{'max_corner_delta_pixels':1.,'minimum_iou':.99,
                           'same_class_and_count':True,'matching':'pairwise one-to-one'},
        'source_images':len(images),'retained_unique_images':len(records),
        'duplicate_copies_excluded':len(duplicates),'excluded_images':len(excluded),
        'excluded_fraction':len(excluded)/len(images),'excluded_families':sorted(bad_families),
        'invalid_files':invalid,'conflicting_pixel_groups':conflicts,
        'excluded':excluded,'duplicates':duplicates,
        'evaluation_scope':'Curated public subset; exclusions may change difficulty and class distribution. Local camera evaluation remains required.'}
    return records,report


def group_records(records, dhash_distance=6, physical_groups=None):
    """Conservatively connect source siblings and near-duplicate image hashes.

    A provided physical_groups mapping is authoritative but may be merged further
    by similarity. Missing physical IDs are rejected, never invented.
    """
    parent = list(range(len(records)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    def union(i, j):
        parent[find(j)] = find(i)
    families = {}
    physical = {}
    for i, row in enumerate(records):
        aliases=row.get('families',[row['family']])
        for family in aliases:
            if family in families:
                union(i, families[family])
            families[family] = i
        if physical_groups is not None:
            for key in aliases:
                if key not in physical_groups or not physical_groups[key]:
                    raise ValueError(f'Missing physical specimen identity for {key}')
                specimen = physical_groups[key]
                if specimen in physical:
                    union(i, physical[specimen])
                physical[specimen] = i
    for i, first in enumerate(records):
        for j in range(i):
            second = records[j]
            if (first['dhash'] ^ second['dhash']).bit_count() <= dhash_distance:
                union(i, j)
    grouped = defaultdict(list)
    for i, row in enumerate(records):
        grouped[find(i)].append(row)
    return list(grouped.values())


def split_groups(groups, class_count, seed=42, attempts=500):
    """Find a reproducible 60/20/20 group assignment with each class present.

    If similarity collapses the data to too few independent groups, stop rather
    than splitting those groups to manufacture a good-looking test result.
    """
    if len(groups) < 6:
        raise ValueError('Fewer than 6 independent image groups: need more data or group review.')
    coverage={c:sum(any(b[0]==c for r in g for b in r['boxes']) for g in groups)
              for c in range(class_count)}
    if any(n<3 for n in coverage.values()):
        raise ValueError(f'Each class needs at least 3 independent groups for train/val/test. Group coverage: {coverage}')
    best, best_score = None, float('inf')
    total_images = sum(map(len, groups))
    totals = Counter(b[0] for g in groups for r in g for b in r['boxes'])
    rng = random.Random(seed)
    for _ in range(attempts):
        order = list(range(len(groups)))
        rng.shuffle(order)
        ntrain = max(1, int(len(order)*0.6))
        nval = max(1, int(len(order)*0.2))
        parts = {'train': order[:ntrain], 'val': order[ntrain:ntrain+nval],
                 'test': order[ntrain+nval:]}
        if not all(parts.values()):
            continue
        score, valid = 0., True
        for split, indexes in parts.items():
            target = 0.6 if split == 'train' else 0.2
            rows = [r for index in indexes for r in groups[index]]
            counts = Counter(b[0] for r in rows for b in r['boxes'])
            if any(counts[c] == 0 for c in range(class_count)):
                valid = False
                break
            score += abs(len(rows)/total_images-target)
            score += sum(abs(counts[c]/totals[c]-target) for c in range(class_count)) / class_count
        if valid and score < best_score:
            best, best_score = parts, score
    if best is None:
        raise ValueError('Cannot create group-disjoint splits containing every class. Collect/review groups.')
    result = {}
    for split, indexes in best.items():
        result[split] = []
        for index in indexes:
            for row in groups[index]:
                result[split].append(dict(row, group_id=f'group-{index:05d}'))
    return result


def materialize(splits, destination, names):
    import yaml
    destination = Path(destination)
    if destination.exists():
        raise ValueError('Prepared dataset already exists. Use a new experiment directory.')
    manifest, summary = [], {}
    for split, rows in splits.items():
        images = destination / 'images' / split
        labels = destination / 'labels' / split
        images.mkdir(parents=True)
        labels.mkdir(parents=True)
        counts = Counter()
        for index, row in enumerate(rows):
            stem = f'{index:06d}_{row["sha256_pixels"][:12]}'
            image = images / (stem + Path(row['image']).suffix.lower())
            label = labels / (stem + '.txt')
            shutil.copy2(row['image'], image)
            shutil.copy2(row['label'], label)
            counts.update(b[0] for b in row['boxes'])
            manifest.append({'image': str(image.relative_to(destination)),
                             'source_image': str(row['image']), 'split': split,
                             'group_id': row['group_id'], 'family': row['family'],
                             'source_family_aliases':json.dumps(row.get('families',[row['family']])),
                             'sha256_pixels': row['sha256_pixels']})
        summary[split] = {'images': len(rows), 'boxes': {names[c]: counts[c] for c in names},
                          'groups': len({r['group_id'] for r in rows}),
                          'negative_images': sum(not r['boxes'] for r in rows)}
    with (destination/'split_manifest.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(manifest[0]))
        writer.writeheader()
        writer.writerows(manifest)
    config = {'path': str(destination.resolve()), 'train': 'images/train',
              'val': 'images/val', 'test': 'images/test', 'nc': len(names), 'names': names}
    (destination/'data.yaml').write_text(yaml.safe_dump(config, sort_keys=False))
    write_json(destination/'audit.json', summary)
    return destination/'data.yaml', summary


def preview(root, split, names, output, limit=8):
    from PIL import Image
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    files = sorted((Path(root)/'images'/split).iterdir())
    random.Random(42).shuffle(files)
    columns = 4
    fig, axes = plt.subplots(math.ceil(limit/columns), columns, figsize=(18, 9), squeeze=False)
    for ax in axes.flat:
        ax.axis('off')
    for ax, path in zip(axes.flat, files[:limit]):
        with Image.open(path) as im:
            rgb = im.convert('RGB')
            width, height = rgb.size
            ax.imshow(rgb)
        boxes = load_boxes(Path(root)/'labels'/split/(path.stem+'.txt'), len(names))
        for c,x,y,w,h in boxes:
            color = 'cyan' if names[c] == 'strip' else 'red'
            left, top = (x-w/2)*width, (y-h/2)*height
            ax.add_patch(Rectangle((left, top), w*width, h*height, fill=False, ec=color, lw=2))
            ax.text(left, top, names[c], fontsize=8, color='white', backgroundcolor=color)
        ax.set_title(path.name[:20])
    fig.suptitle(f'Ground truth: {split}; cyan=context, red=defect')
    fig.tight_layout()
    fig.savefig(output, dpi=130)
    return fig


def xyxy(box, width, height):
    c,x,y,w,h = box
    return [int(c), (x-w/2)*width, (y-h/2)*height,
            (x+w/2)*width, (y+h/2)*height]


def iou(first, second):
    area = max(0, min(first[2], second[2])-max(first[0], second[0])) * max(
        0, min(first[3], second[3])-max(first[1], second[1]))
    union = max(0, first[2]-first[0])*max(0, first[3]-first[1]) + max(
        0, second[2]-second[0])*max(0, second[3]-second[1])-area
    return area/union if union else 0.


def operating_metrics(samples, class_id, threshold, minimum_iou=0.5):
    tp=fp=fn=0
    for sample in samples:
        gt = [b[1:] for b in sample['truth'] if int(b[0]) == class_id]
        predictions = sorted((b for b in sample['predictions']
                              if int(b[0]) == class_id and b[1] >= threshold),
                             key=lambda b: -b[1])
        matched = set()
        for prediction in predictions:
            choices = [(iou(prediction[2:], box), j) for j,box in enumerate(gt) if j not in matched]
            overlap,index = max(choices, default=(0., -1))
            if index >= 0 and overlap >= minimum_iou:
                tp += 1
                matched.add(index)
            else:
                fp += 1
        fn += len(gt)-len(matched)
    precision = tp/(tp+fp) if tp+fp else 0.
    recall = tp/(tp+fn) if tp+fn else 0.
    f2 = 5*precision*recall/(4*precision+recall) if precision+recall else 0.
    return {'tp':tp, 'fp':fp, 'fn':fn, 'support':tp+fn,
            'precision':precision, 'recall':recall, 'f2':f2}


def tune_thresholds(samples, names, target_recall=0.95):
    selected = {}
    for c,name in names.items():
        rows = []
        for k in range(1, 100):
            threshold = k/100
            rows.append(dict(operating_metrics(samples, c, threshold), threshold=threshold))
        feasible = [r for r in rows if r['support'] > 0 and r['recall'] >= target_recall]
        if feasible:
            best = max(feasible, key=lambda r: (r['precision'], r['f2'], r['threshold']))
        else:
            best = max(rows, key=lambda r: (r['f2'], r['recall'], r['threshold']))
        selected[name] = dict(best, class_id=c, target_recall_met=bool(feasible),
                              role='context' if name == 'strip' else 'defect')
    return selected


def collect_predictions(model, root, split, names, imgsz=640, device=0, batch_size=8):
    """Collect CPU records with explicitly bounded image-list batches."""
    from PIL import Image
    if not isinstance(batch_size, int) or batch_size < 1:
        raise ValueError('batch_size must be a positive integer')
    files = sorted(p for p in (Path(root)/'images'/split).iterdir() if p.is_file())
    samples = []
    for start in range(0, len(files), batch_size):
        chunk = files[start:start + batch_size]
        for result in model.predict(source=[str(p) for p in chunk], stream=True,
                                    batch=batch_size, imgsz=imgsz, device=device,
                                    conf=0.001, iou=0.7, max_det=300, verbose=False):
            image = Path(result.path)
            with Image.open(image) as im:
                width, height = im.size
            truth = load_boxes(Path(root)/'labels'/split/(image.stem+'.txt'), len(names))
            predictions = []
            for box in result.boxes.data.cpu().tolist():
                x1, y1, x2, y2, confidence, c = box
                predictions.append([int(c), confidence, x1, y1, x2, y2])
            samples.append({'image': str(image),
                            'truth': [xyxy(b, width, height) for b in truth],
                            'predictions': predictions})
        print(f'{split}: collected {len(samples)}/{len(files)} images', flush=True)
    if len(samples) != len(files):
        raise RuntimeError('Prediction count differs from input image count')
    return samples


def evaluate_frozen(samples, names, thresholds):
    per_class = {name:operating_metrics(samples,c,thresholds[name]['threshold'])
                 for c,name in names.items()}
    defects = {c for c,name in names.items() if name != 'strip'}
    false_pass=false_hold=defective=good=0
    for sample in samples:
        actual = any(b[0] in defects for b in sample['truth'])
        predicted = any(b[0] in defects and b[1] >= thresholds[names[b[0]]]['threshold']
                        for b in sample['predictions'])
        defective += actual
        good += not actual
        false_pass += actual and not predicted
        false_hold += not actual and predicted
    return {'per_class':per_class,
            'image_level': {'defective_images':defective,'negative_images':good,
                            'false_pass_images':false_pass,'false_hold_images':false_hold,
                            'false_pass_rate':false_pass/defective if defective else None,
                            'false_hold_rate':false_hold/good if good else None},
            'unit_note':'Image-level metrics, not per-strip production measurements.'}


def prepare_calibration(root, output, count=512):
    source=Path(root)/'images'/'train'
    files=sorted(source.iterdir())
    random.Random(42).shuffle(files)
    selected=files[:count]
    Path(output).mkdir(parents=True, exist_ok=True)
    manifest=[]
    for p in selected:
        shutil.copy2(p, Path(output)/p.name)
        manifest.append({'file':p.name,'sha256':file_hash(p),'origin':'train_only'})
    write_json(Path(output)/'calibration_manifest.json',manifest)
    return len(selected)


def export_onnx(checkpoint, output, samples, imgsz=640):
    """Legacy static exporter is explicit for PyTorch 2.11, opset 11 for Hailo recipe.

    Validates raw prediction parity; final Hailo parse/NMS/quantized evaluation
    still require the vendor compiler and actual device.
    """
    import copy
    import numpy as np
    import torch
    import onnx
    import onnxruntime as ort
    from ultralytics import YOLO
    from ultralytics.data.augment import LetterBox
    import cv2
    predictor = YOLO(str(checkpoint))
    model = copy.deepcopy(predictor.model).cpu().float().eval()
    model.fuse()
    for module in model.modules():
        if hasattr(module,'export'):
            module.export=True
            module.format='onnx'
            module.dynamic=False
    example=torch.zeros(1,3,imgsz,imgsz)
    with torch.inference_mode():
        expected=model(example)
    if isinstance(expected,(tuple,list)):
        raise ValueError('Expected one raw detection tensor; inspect the export wrapper.')
    output=Path(output)
    torch.onnx.export(model, example, str(output), input_names=['images'],
                      output_names=['predictions'], opset_version=11,
                      dynamic_axes=None, dynamo=False)
    graph=onnx.load(str(output))
    onnx.checker.check_model(graph)
    session=ort.InferenceSession(str(output),providers=['CPUExecutionProvider'])
    differences=[]
    for file in samples:
        image=cv2.imread(str(file))
        if image is None:
            raise ValueError(f'Unreadable export validation image: {file}')
        letterbox=LetterBox(new_shape=(imgsz,imgsz), auto=False, stride=32)
        image=letterbox(image=image)
        array=np.ascontiguousarray(image[:,:,::-1].transpose(2,0,1))[None].astype(np.float32)/255.
        with torch.inference_mode():
            reference=model(torch.from_numpy(array)).numpy()
        actual=session.run(None,{'images':array})[0]
        np.testing.assert_allclose(actual,reference,rtol=1e-3,atol=1e-2)
        differences.append({'image':Path(file).name,'max_abs':float(np.abs(actual-reference).max())})
    inventory = [{'name':node.name,'op':node.op_type,'outputs':list(node.output)}
                 for node in graph.graph.node]
    write_json(output.with_suffix('.nodes.json'),inventory)
    return {'status':'fp32_raw_tensor_parity_passed','path':str(output),
            'validation_images':differences,'shape':[int(v) for v in expected.shape],
            'opset':11,'hailo_compatibility':'unverified'}
