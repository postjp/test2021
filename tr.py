import time,datetime
from model import  OcrHandle
import tornado.web
import tornado.gen
import tornado.httpserver
import base64
from PIL import Image, ImageDraw,ImageFont
from io import BytesIO
import datetime
import json,jmespath,hashlib

from backend.tools.np_encoder import NpEncoder
from backend.tools import log
from backend.tools import imgx

import logging

logger = logging.getLogger(log.LOGGER_ROOT_NAME + '.' +__name__)

ocrhandle = OcrHandle()


request_time = {}
now_time = time.strftime("%Y-%m-%d", time.localtime(time.time()))
from config import max_post_time ,dbnet_max_size,white_ips


class TrRun(tornado.web.RequestHandler):
    '''
    使用 tr 的 run 方法
    '''

    def md5(chunk):
        
        hash_md5 = hashlib.md5()
        hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def get(self):
        self.set_status(404)
        self.write("404 : Please use POST")

    @tornado.gen.coroutine
    def post(self):
        '''
        :return:
        报错：
        400 没有请求参数
        '''
        
        start_time = time.time()
        short_size = 960
        global now_time
        global request_time
        urls = self.request.files.get('url', None)
        
        img_up = self.request.files.get('file', None)
        img_b64 = self.get_argument('img', None)
        somd5 = self.get_argument('somd5', None)
        compress_size = self.get_argument('compress', None)
        
        self.set_header('content-type', 'application/json')
        up_image_type = None
        if img_up is not None and len(img_up) > 0:
            urls=['999']
            img_up = img_up[0]
            up_image_type = img_up.content_type
            up_image_name = img_up.filename
            t = time.time()
            goxxoo=str(round(t * 1000000))+'_2333333333333_'
            with open(goxxoo,'wb') as f:
                f.write(img_up.body)
                f.close()
            if somd5 is not None:
                somd52=md5(goxxoo)
                if str(somd5) != str(somd52):
                    somd5=somd52
            imgfiles=imgx.urlget(urls,goxxoo,1)
            
        elif img_b64 is not None:
            urls=['999']
            raw_image = base64.b64decode(img_b64.encode('utf8'))
            t = time.time()
            goxxoo=str(round(t * 1000000))+'_2333333333333_'
            with open(goxxoo,'wb') as f:
                f.write(raw_image)
                f.close()
            if somd5 is not None:
                somd52=md5(goxxoo)
                if str(somd5) != str(somd52):
                    somd5=somd52
            imgfiles=imgx.urlget(urls,goxxoo,2)
            
        else:
            imgfiles=imgx.urlget(urls,0,0)

            
        
        
        
        alltxt=''
        # 判断是上传的图片还是base64

        for imgurl in imgfiles:

            up_image_type = None
            if len(imgfiles) > 0:
                img = Image.open(imgurl)
            else:
                self.set_status(400)
                logger.error(json.dumps({'code': 400, 'msg': '没有传入参数'}, cls=NpEncoder))
                self.finish(json.dumps({'code': 400, 'msg': '没有传入参数'}, cls=NpEncoder))
                return

            try:
                if hasattr(img, '_getexif') and img._getexif() is not None:
                    orientation = 274
                    exif = dict(img._getexif().items())
                    if orientation not in exif:
                        exif[orientation] = 0
                    if exif[orientation] == 3:
                        img = img.rotate(180, expand=True)
                    elif exif[orientation] == 6:
                        img = img.rotate(270, expand=True)
                    elif exif[orientation] == 8:
                        img = img.rotate(90, expand=True)
            except Exception as ex:
                error_log = json.dumps({'code': 400, 'msg': '产生了一点错误，请检查日志', 'err': str(ex)}, cls=NpEncoder)
                logger.error(error_log, exc_info=True)
                self.finish(error_log)
                return
            img = img.convert("RGB")

            time_now = time.strftime("%Y-%m-%d-%H_%M_%S",time.localtime(time.time()))
            time_day = time.strftime("%Y-%m-%d", time.localtime(time.time()))
            if time_day != now_time:
                now_time = time_day
                request_time = {}



            '''
            是否开启图片压缩
            默认为960px
            值为 0 时表示不开启压缩
            非 0 时则压缩到该值的大小
            '''
            res = []
            do_det = True



            if compress_size is not None:
                try:
                    compress_size = int(compress_size)
                except ValueError as ex:
                    # logger.error(exc_info=True)
                    res.append("短边尺寸参数类型有误，只能是int类型")
                    do_det = False
                    # self.finish(json.dumps({'code': 400, 'msg': 'compress参数类型有误，只能是int类型'}, cls=NpEncoder))
                    # return

                short_size = compress_size
                if short_size < 64:
                    res.append("短边尺寸过小，请调整短边尺寸")
                    do_det = False

                short_size = 32 * (short_size//32)


            img_w, img_h = img.size
            if max(img_w, img_h) * (short_size * 1.0 / min(img_w, img_h)) > dbnet_max_size:
                # logger.error(exc_info=True)
                res.append("图片reize后长边过长，请调整短边尺寸")
                do_det = False
                # self.finish(json.dumps({'code': 400, 'msg': '图片reize后长边过长，请调整短边尺寸'}, cls=NpEncoder))
                # return


            if do_det:

                res = ocrhandle.text_predict(img,short_size)

                img_detected = img.copy()
                img_draw = ImageDraw.Draw(img_detected)
                colors = ['red', 'green', 'blue', "purple"]


                for i, r in enumerate(res):
                    rect, txt, confidence = r
                    alltxt=alltxt+txt

            else:
                output_buffer = BytesIO()
                img.save(output_buffer, format='JPEG') 
                byte_data = output_buffer.getvalue()
                img_detected_b64 = base64.b64encode(byte_data).decode('utf8')

            log_info = {
                'ip': self.request.remote_ip,
                'return': res,
                'time': time_now
            }
        logger.info(json.dumps(log_info, cls=NpEncoder))
        self.finish(json.dumps(
            {'code': 200,'txt':alltxt,'md5':somd5},cls=NpEncoder))
        return
