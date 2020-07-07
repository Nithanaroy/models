#!/usr/bin/env python
# coding: utf-8

get_ipython().system('pip install -U --pre tensorflow=="2.*"')


get_ipython().system('pip install pycocotools')


import os
import pathlib


if "models" in pathlib.Path.cwd().parts:
  while "models" in pathlib.Path.cwd().parts:
    os.chdir('..')
elif not pathlib.Path('models').exists():
  get_ipython().system('git clone --depth 1 https://github.com/tensorflow/models')


get_ipython().run_cell_magic('bash', '', 'cd models/research/\nprotoc object_detection/protos/*.proto --python_out=.')


get_ipython().run_cell_magic('bash', '', 'cd models/research\npip install .')


import numpy as np
import os
import six.moves.urllib as urllib
import sys
import tarfile
import tensorflow as tf
import zipfile

from collections import defaultdict
from io import StringIO
from matplotlib import pyplot as plt
from PIL import Image
from IPython.display import display

# tf.enable_eager_execution()

tf.__version__


import sys

models_research_dir = "models/research"
if models_research_dir not in sys.path:
    sys.path.append(models_research_dir)


from object_detection.utils import ops as utils_ops
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as vis_util


# patch tf1 into `utils.ops`
utils_ops.tf = tf.compat.v1

# Patch the location of gfile
tf.gfile = tf.io.gfile


def load_model_local(model_path):
    model_dir = pathlib.Path(model_path)/"saved_model"
#     model = tf.saved_model.load_v2(str(model_dir))
    model = tf.saved_model.load(str(model_dir))
    model = model.signatures['serving_default']
    return model


def load_model(model_name):
  base_url = 'http://download.tensorflow.org/models/object_detection/'
  model_file = model_name + '.tar.gz'
  model_dir = tf.keras.utils.get_file(
    fname=model_name, 
    origin=base_url + model_file,
    untar=True)


# List of the strings that is used to add correct label for each box.
PATH_TO_LABELS = "models/annotations/label_map.pbtxt" # 'models/research/object_detection/data/mscoco_label_map.pbtxt'
category_index = label_map_util.create_category_index_from_labelmap(PATH_TO_LABELS, use_display_name=True)


# If you want to test the code with your images, just add path to the images to the TEST_IMAGE_PATHS.
PATH_TO_TEST_IMAGES_DIR = pathlib.Path("models/images/") # pathlib.Path('models/research/object_detection/test_images')
TEST_IMAGE_PATHS = list(PATH_TO_TEST_IMAGES_DIR.glob("*.jpeg"))[:2]
TEST_IMAGE_PATHS


model_name = 'ssd_mobilenet_v1_coco_2017_11_17'
model_path = 'models/fine_tuned_model/'
detection_model = load_model_local(model_path) # load_model(model_name)


print(detection_model.inputs)


detection_model.output_dtypes


detection_model.output_shapes


def run_inference_for_single_image(model, image):
  image = np.asarray(image)
  # The input needs to be a tensor, convert it using `tf.convert_to_tensor`.
  input_tensor = tf.convert_to_tensor(image)
  # The model expects a batch of images, so add an axis with `tf.newaxis`.
  input_tensor = input_tensor[tf.newaxis,...]

  # Run inference
  output_dict = model(input_tensor)

  # All outputs are batches tensors.
  # Convert to numpy arrays, and take index [0] to remove the batch dimension.
  # We're only interested in the first num_detections.
  num_detections = int(output_dict.pop('num_detections'))
  output_dict = {key:value[0, :num_detections].numpy() 
                 for key,value in output_dict.items()}
  output_dict['num_detections'] = num_detections

  # detection_classes should be ints.
  output_dict['detection_classes'] = output_dict['detection_classes'].astype(np.int64)
   
  # Handle models with masks:
  if 'detection_masks' in output_dict:
    # Reframe the the bbox mask to the image size.
    detection_masks_reframed = utils_ops.reframe_box_masks_to_image_masks(
              output_dict['detection_masks'], output_dict['detection_boxes'],
               image.shape[0], image.shape[1])      
    detection_masks_reframed = tf.cast(detection_masks_reframed > 0.5,
                                       tf.uint8)
    output_dict['detection_masks_reframed'] = detection_masks_reframed.numpy()
    
  return output_dict


def show_inference(model, image_path):
  # the array based representation of the image will be used later in order to prepare the
  # result image with boxes and labels on it.
  image_np = np.array(Image.open(image_path))
  # Actual detection.
  output_dict = run_inference_for_single_image(model, image_np)
  # Visualization of the results of a detection.
  vis_util.visualize_boxes_and_labels_on_image_array(
      image_np,
      output_dict['detection_boxes'],
      output_dict['detection_classes'],
      output_dict['detection_scores'],
      category_index,
      instance_masks=output_dict.get('detection_masks_reframed', None),
      use_normalized_coordinates=True,
      line_thickness=8)

  display(Image.fromarray(image_np))


for image_path in TEST_IMAGE_PATHS:
  show_inference(detection_model, image_path)


model_name = "mask_rcnn_inception_resnet_v2_atrous_coco_2018_01_28"
masking_model = load_model(model_name)


masking_model.output_shapes


for image_path in TEST_IMAGE_PATHS:
  show_inference(masking_model, image_path)




