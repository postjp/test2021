import requests,time,traceback,datetime,imghdr
from PIL import Image
import os.path as ospath

from requests.adapters import HTTPAdapter

s = requests.Session()
s.mount('http://', HTTPAdapter(max_retries=3))
s.mount('https://', HTTPAdapter(max_retries=3))

def urlget(urls):
    try:
        filenameX=[]
        for url in urls:
          response = s.get(url, verify=False, timeout=60)

          t = time.time()

          filename=str(round(t * 1000000))+'_2333333333333_'
          if response.status_code == 200:
            if 'Transfer-Encoding' in response.headers:
                with open(filename, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                    f.close()
                    SUFFIxx=str(imghdr.what(filename)[0])
                    filename=filename.replace("_2333333333333_",SUFFIxx)
                    filenameX.extend(splitimg(filename,500,1000))

            elif 'Content-Length' in response.headers:
                if len(response.content) == int(response.headers['Content-Length']):
                    with open(filename, 'wb') as f:
                        for chunk in response.iter_content(1024):
                            f.write(chunk)
                        f.close()
                        SUFFIxx=str(imghdr.what(filename)[0])
                        filename=filename.replace("_2333333333333_",SUFFIxx)
                        filenameX.extend(splitimg(filename,500,1000))
      return filenameX
    except Exception as e:
        try:
            print('urlget:{0}'.format(traceback.format_exc()))
            return
        finally:
            e = None
            del e
            
            
def splitimg(xxxx,heighss,quality,output=None):
    try:
      
        outputAll=[]
        file_dir=ospath.dirname(xxxx)

        filename,extname=ospath.splitext(ospath.basename(xxxx))

        if output!=None:

            filename=output

        ## crop image

        image=Image.open(xxxx)

        W,H=image.size

        ## 计算尺寸

        LIMIT=6000000

        h=int(min(heighss,LIMIT/W-1))

        ## 截取

        begin_x,begin_y=0,0

        end_x,end_y=W,h

        count=1

        while begin_y<H:

            end_y=min(end_y,H)

            sub_image=image.crop((begin_x,begin_y,end_x,end_y))

            output=ospath.join(file_dir,filename+str(count)+extname)

            sub_image.save(output,quality)
            outputAll.append(output)
            count+=1

            begin_x,begin_y,end_x,end_y=0,end_y+1,W,end_y+1+h
        return outputAll
    except Exception as e:
        try:
            print('urlget:{0}'.format(traceback.format_exc()))
            return
        finally:
            e = None
            del e
