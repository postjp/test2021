# -*- coding: utf-8 -*-
import cv2
import torch
import numpy as np
from PIL import Image
from io import BytesIO
from crnn import LiteCrnn, CRNNHandle
from psenet import PSENet, PSENetHandel
from application import idcard, trainTicket
from crnn.keys import alphabetChinese as alphabet
from angle_class import AangleClassHandle, shufflenet_v2_x0_5


def crop_rect(img, rect, alph=0.15):
    img = np.asarray(img)
    center, size, angle = rect[0], rect[1], rect[2]
    min_size = min(size)
    if (angle > -45):
        center, size = tuple(map(int, center)), tuple(map(int, size))
        size = (int(size[0] + min_size * alph), int(size[1] + min_size * alph))
        height, width = img.shape[0], img.shape[1]
        M = cv2.getRotationMatrix2D(center, angle, 1)
        img_rot = cv2.warpAffine(img, M, (width, height))
        img_crop = cv2.getRectSubPix(img_rot, size, center)
    else:
        center = tuple(map(int, center))
        size = tuple([int(rect[1][1]), int(rect[1][0])])
        size = (int(size[0] + min_size * alph), int(size[1] + min_size * alph))
        angle -= 270
        height, width = img.shape[0], img.shape[1]
        M = cv2.getRotationMatrix2D(center, angle, 1)
        img_rot = cv2.warpAffine(img, M, (width, height))
        img_crop = cv2.getRectSubPix(img_rot, size, center)
    img_crop = Image.fromarray(img_crop)
    return img_crop


def crnnRec(im, rects_re, f=1.0):
    results = []
    im = Image.fromarray(im)
    for index, rect in enumerate(rects_re):
        degree, w, h, cx, cy = rect
        partImg = crop_rect(im, ((cx, cy), (h, w), degree))
        newW, newH = partImg.size
        partImg_array = np.uint8(partImg)
        if newH > 1.5 * newW:
            partImg_array = np.rot90(partImg_array, 1)
        angel_index = angle_handle.predict(partImg_array)
        angel_class = lable_map_dict[angel_index]
        rotate_angle = rotae_map_dict[angel_class]
        if rotate_angle != 0:
            partImg_array = np.rot90(partImg_array, rotate_angle // 90)
        partImg = Image.fromarray(partImg_array).convert("RGB")
        partImg_ = partImg.convert('L')
        try:
            if crnn_vertical_handle is not None and angel_class in ["shudao", "shuzhen"]:
                simPred = crnn_vertical_handle.predict(partImg_)
            else:
                simPred = crnn_handle.predict(partImg_)  # 识别的文本
        except:
            continue
        if simPred.strip() != u'':
            results.append({'cx': cx * f, 'cy': cy * f, 'text': simPred, 'w': newW * f, 'h': newH * f,
                            'degree': degree})
    return results


def text_predict(img):
    '''文本预测'''
    preds, boxes_list, rects_re, t = text_handle.predict(img, long_size=pse_long_size)
    result = crnnRec(np.array(img), rects_re)
    return result


# 调用CPU或GPU
gpu_id = 0
if gpu_id and isinstance(gpu_id, int) and torch.cuda.is_available():
    device = torch.device("cuda:{}".format(gpu_id))
else:
    device = torch.device("cpu")
print('device:', device)

# psenet相关
pse_scale = 1
pse_long_size = 960  # 图片长边
pse_model_type = "mobilenetv2"
pse_model_path = "models/psenet_lite_mbv2.pth"
text_detect_net = PSENet(backbone=pse_model_type, pretrained=False, result_num=6, scale=pse_scale)
text_handle = PSENetHandel(pse_model_path, text_detect_net, pse_scale, gpu_id=gpu_id)

# crnn相关
nh = 256
crnn_model_path = "models/crnn_lite_lstm_dw_v2.pth"
crnn_net = LiteCrnn(32, 1, len(alphabet) + 1, nh, n_rnn=2, leakyRelu=False, lstmFlag=True)
crnn_handle = CRNNHandle(crnn_model_path, crnn_net, gpu_id=gpu_id)
crnn_vertical_model_path = "models/crnn_dw_lstm_vertical.pth"
crnn_vertical_net = LiteCrnn(32, 1, len(alphabet) + 1, nh, n_rnn=2, leakyRelu=False, lstmFlag=True)
crnn_vertical_handle = CRNNHandle(crnn_vertical_model_path, crnn_vertical_net, gpu_id=gpu_id)

# angle_class相关
lable_map_dict = {0: "hengdao", 1: "hengzhen", 2: "shudao", 3: "shuzhen"}  # hengdao: 文本行横向倒立 其他类似
rotae_map_dict = {"hengdao": 180, "hengzhen": 0, "shudao": 180, "shuzhen": 0}  # 文本行需要旋转的角度
angle_model_path = "models/shufflenetv2_05.pth"
angle_net = shufflenet_v2_x0_5(num_classes=len(lable_map_dict), pretrained=False)
angle_handle = AangleClassHandle(angle_model_path, angle_net, gpu_id=gpu_id)

def result(img):
    back = {}
    img = Image.open(BytesIO(img)).convert('RGB')
    img = np.array(img)
    result = text_predict(img)
    back['文本'] = list(map(lambda x: x['text'], result))
    return back
