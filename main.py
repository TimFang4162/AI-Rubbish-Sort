# coding=UTF-8
import cv2
from aip import AipImageClassify
import os
from PIL import Image, ImageDraw, ImageFont
import numpy
import json
import requests
print('\033[32m' + "程序启动 加载中" + '\033[0m')
session = requests.session()
execution_path = os.path.dirname(os.path.realpath(__file__))  #获取工作目录
settings = json.loads(
    open(os.path.join(execution_path, 'data//settings.json'),
         encoding='utf-8').read())
rubbish_file = json.loads(
    open(os.path.join(execution_path, 'data//garbage.json'),
         encoding='utf-8').read())
rubbish_type_list = [
    '可回收垃圾', '有害垃圾', '可回收的有害垃圾', '湿垃圾', '可回收的湿垃圾', '有害的湿垃圾', '可回收,有害的湿垃圾',
    '干垃圾', '可回收的干垃圾', '有害的干垃圾', '可回收,有害的干垃圾', '干或湿垃圾', '可回收的干或湿垃圾', '有害的干或湿垃圾',
    '可回收,有害的干或湿垃圾', '大件垃圾'
]
font = ImageFont.truetype(os.path.join(execution_path,
                                       settings["DISPLAY_FONT_PATH"]),
                          20,
                          encoding="utf-8")
client = AipImageClassify(settings["AIP_APP_ID"], settings["AIP_API_KEY"],
                          settings["AIP_SECRET_KEY"])
cap = cv2.VideoCapture(settings['CAPTURE_ID'])
displaystatus = 0


def changeview():
    global displaystatus
    global execution_path
    global client
    global session
    global frame
    global imgdes
    global rubbish_type
    if (displaystatus == 1):
        displaystatus = 0
        print('\033[32m' + "关闭识别" + '\033[0m')
    else:
        displaystatus = 1
        print('\033[32m' + "开始识别" + '\033[0m' + "\n请求中")
        cv2.imwrite(os.path.join(execution_path, 'temp//get_camera.jpg'),
                    frame)
        cv2_im = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_im = Image.fromarray(cv2_im)
        pil_im = Image.eval(pil_im, lambda x: x / 4)
        draw = ImageDraw.Draw(pil_im)
        draw.text((5, 40), "识别中", (255, 255, 255), font=font)
        frame = cv2.cvtColor(numpy.array(pil_im), cv2.COLOR_RGB2BGR)
        cv2.imshow("AI Rubbish Sort", frame)
        cv2.waitKey(1)
        with open(os.path.join(execution_path, 'temp//get_camera.jpg'),
                  'rb') as fp:
            options = {}
            options["baike_num"] = 1
            imgdes = client.advancedGeneral(fp.read(), options)
            print("识别成功,分类:" + imgdes['result'][0]['root'] + " 物体:" +
                  imgdes['result'][0]['keyword'] + " 准确率:" +
                  str(imgdes['result'][0]['score']),
                  end="")
            if ("image_url" in imgdes['result'][0]['baike_info']):
                print(" 图片:" + imgdes['result'][0]['baike_info']['image_url'])
            else:
                print(" 无图片")
        rubbish_requests = json.loads(
            session.get('https://api.66mz8.com/api/garbage.php?name=' +
                        imgdes['result'][0]["keyword"]).text)
        if (rubbish_requests['code'] == 200):
            rubbish_type = rubbish_requests['data']
            print('API 01 请求成功')
        else:
            print('API 01 请求出错,尝试 API 02')
            rubbish_requests = json.loads(
                session.get(
                    'https://sffc.sh-service.com/wx_miniprogram/sites/feiguan/trashTypes_2/Handler/Handler.ashx?a=GET_KEYWORDS&kw='
                    + imgdes['result'][0]["keyword"]).text)
            if (rubbish_requests['kw_arr'] != None):
                rubbish_type = rubbish_requests['kw_arr'][0]['TypeKey']
                print('API 02 请求成功')
            else:
                print('API 02 请求出错,尝试本地搜索')
                rubbish_type = "n"
                for eachrubbish in rubbish_file:
                    if ((eachrubbish['name'] in imgdes['result'][0]['keyword'])
                            or (imgdes['result'][0]['keyword']
                                in eachrubbish['name'])):
                        rubbish_type = rubbish_type_list[
                            eachrubbish['category'] + 1]
                if (rubbish_type == "n"):
                    print('本地搜索出错,返回 未知垃圾/非垃圾')
                    rubbish_type = '未知垃圾/非垃圾'
                else:
                    print('本地搜索请求成功')


while True:
    ret, frame = cap.read()
    shape = frame.shape
    if (displaystatus == 0):
        cv2.imshow("AI Rubbish Sort", frame)
    if (displaystatus == 1):
        frame = cv2.imread(os.path.join(execution_path,
                                        'temp//get_camera.jpg'))
        cv2_im = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_im = Image.fromarray(cv2_im)
        pil_im = Image.eval(pil_im, lambda x: x / 4)
        draw = ImageDraw.Draw(pil_im)
        draw.text((5, 20),
                  imgdes['result'][0]["root"] + " - " +
                  imgdes['result'][0]["keyword"], (255, 255, 255),
                  font=font)
        draw.text((5, 40), rubbish_type, (255, 255, 255), font=font)
        frame = cv2.cvtColor(numpy.array(pil_im), cv2.COLOR_RGB2BGR)
        cv2.imshow("AI Rubbish Sort", frame)
    if cv2.waitKey(1) & 0xff == ord(settings['KEY']):
        changeview()
