from keras import backend as K
from keras.models import load_model
from keras.preprocessing import image
import numpy as np

from keras_loss_function.keras_ssd_loss import SSDLoss
from keras_layers.keras_layer_AnchorBoxes import AnchorBoxes
from keras_layers.keras_layer_DecodeDetections import DecodeDetections
from keras_layers.keras_layer_L2Normalization import L2Normalization

from PIL import Image


class DetectionNetwork():
    def __init__(self, net_model='full_model'):
        self.framework = "Keras"

        MODEL_FILE = 'Net/Keras/' + net_model + '.h5'

        ssd_loss = SSDLoss(neg_pos_ratio=3, n_neg_min=0, alpha=1.0)

        K.clear_session()
        try:
            self.model = load_model(MODEL_FILE, custom_objects={'AnchorBoxes': AnchorBoxes,
                                                           'L2Normalization': L2Normalization,
                                                           'DecodeDetections': DecodeDetections,
                                                           'compute_loss': ssd_loss.compute_loss})
        except:
            raise SystemExit('Incorrect or incomplete model details in YML file')

        self.classes = ['background',
                   'aeroplane', 'bicycle', 'bird', 'boat',
                   'bottle', 'bus', 'car', 'cat',
                   'chair', 'cow', 'diningtable', 'dog',
                   'horse', 'motorbike', 'person', 'pottedplant',
                   'sheep', 'sofa', 'train', 'tvmonitor']

        # the Keras network works on 300x300 images. Reference sizes:
        self.img_height = 300
        self.img_width = 300


        # Output preallocation
        self.predictions = np.asarray([])
        self.boxes = np.asarray([])
        self.scores = np.asarray([])

        dummy = np.zeros([1, self.img_height, self.img_width, 3])
        self.model.predict(dummy)


    def setCamera(self, cam):
        self.cam = cam

        self.original_height = cam.im_height
        self.original_width = cam.im_width

        # Factors to rescale the output bounding boxes
        self.height_factor = np.true_divide(self.original_height, self.img_height)
        self.width_factor = np.true_divide(self.original_width, self.img_width)


    def predict(self):
        input_image = self.cam.getImage()
        # preprocessing
        as_image = Image.fromarray(input_image)
        resized = as_image.resize((300,300), Image.NEAREST)
        np_resized = image.img_to_array(resized)

        input_col = []
        input_col.append(np_resized)
        network_input = np.array(input_col)
        # Prediction
        y_pred = self.model.predict(network_input)

        self.predictions = []
        self.scores = []
        self.boxes = []
        confidence_threshold = 0.5
        # which predictions are above the confidence threshold?
        y_pred_thresh = [y_pred[k][y_pred[k,:,1] > confidence_threshold] for k in range(y_pred.shape[0])]
        # iterate over them
        for box in y_pred_thresh[0]:
            self.predictions.append(self.classes[int(box[0])])
            self.scores.append(box[1])
            xmin = int(box[2] * self.width_factor)
            ymin = int(box[3] * self.height_factor)
            xmax = int(box[4] * self.width_factor)
            ymax = int(box[5] * self.height_factor)
            self.boxes.append([xmin, ymin, xmax, ymax])
