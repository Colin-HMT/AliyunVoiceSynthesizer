import base64
import csv
import hashlib
import hmac
import time
import uuid
from urllib import parse
import requests
import threading
import nls
import tkinter as tk
from tkinter import filedialog


def encode_text(text):
    encoded_text = parse.quote_plus(text)
    return encoded_text.replace('+', '%20').replace('*', '%2A').replace('%7E', '~')


def encode_dict(dic):
    keys = dic.keys()
    dic_sorted = [(key, dic[key]) for key in sorted(keys)]
    encoded_text = parse.urlencode(dic_sorted)
    return encoded_text.replace('+', '%20').replace('*', '%2A').replace('%7E', '~')


def GetTokenFromFile(FileFullName):
    with open(FileFullName, 'r') as file:
        csv_reader = csv.reader(file)
        data = list(csv_reader)
        AccessKeyID = data[1][0]
        AccessKeySecret = data[1][1]
    parameters = {
        'AccessKeyId': AccessKeyID,
        'Action': 'CreateToken',
        'Format': 'JSON',
        'RegionId': 'cn-shanghai',
        'SignatureMethod': 'HMAC-SHA1',
        'SignatureNonce': str(uuid.uuid1()),
        'SignatureVersion': '1.0',
        'Timestamp': time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        'Version': '2019-02-28'
    }

    query_string = encode_dict(parameters)
    string_to_sign = 'GET' + '&' + encode_text('/') + '&' + encode_text(query_string)
    secreted_string = hmac.new(bytes(AccessKeySecret + '&', encoding='utf-8'),
                               bytes(string_to_sign, encoding='utf-8'),
                               hashlib.sha1).digest()
    signature = base64.b64encode(secreted_string)
    signature = encode_text(signature)
    full_url = 'http://nls-meta.cn-shanghai.aliyuncs.com/?Signature=%s&%s' % (signature, query_string)
    print('URL: %s' % full_url)
    response = requests.get(full_url)
    if response.ok:
        root_obj = response.json()
        key = 'Token'
        if key in root_obj:
            token = root_obj[key]['Id']
            return token
    return None, None


# 以下代码会根据上述TEXT文本反复进行语音合成
def test_run(tid, filefullname, appkey, test_file, text, voice, fmt):
    with open(test_file+"."+fmt, "wb") as f:
        tts = nls.NlsSpeechSynthesizer(
            url="wss://nls-gateway-cn-shanghai.aliyuncs.com/ws/v1",
            token=GetTokenFromFile(FileFullName=filefullname),
            appkey=appkey,
            on_metainfo=lambda message, *args: print("on_metainfo message=>{}".format(message)),
            on_data=lambda data, *args: f.write(data),
            on_completed=lambda message, *args: print("on_completed:args=>{} message=>{}".format(args, message)),
            on_error=lambda message, *args: print("on_error args=>{}".format(args)),
            on_close=lambda *args: print("on_close: args=>{}".format(args)),
            callback_args=[tid]
        )
        r = tts.start(
            text=text,
            voice=voice,
            aformat=fmt
        )
    f.close()

# Function to run multiple TTS threads
def multiruntest(num, filefullname, appkey, test_file, text, voice, fmt):
    threads = []
    for i in range(0, num):
        name = "thread" + str(i)
        t = threading.Thread(target=test_run, args=(name, filefullname, appkey, test_file, text, voice, fmt))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

def open_file_dialog():
    # 打开文件对话框并获取所选文件的路径
    file_path = filedialog.askopenfilename()
    if file_path:
        # 将选中的文件路径显示在文本框中
        file_path_entry.delete(0, tk.END)
        file_path_entry.insert(0, file_path)

def VoiceSyne():
    tk.messagebox.showinfo("提示", "合成的文件会保存在当前文件夹下")
    filefullname = file_path_entry.get()
    appkey = appkey_entry.get()
    test_file = output_entry.get()
    text = text_entry.get()
    voice = voice_entry.get()
    fmt = fmt_entry.get()
    multiruntest(num=1, filefullname=filefullname, appkey=appkey, test_file=test_file, text=text, voice=voice, fmt=fmt)

window = tk.Tk()

# 设置窗口标题
window.title("我的Python窗口")

# 设置窗口大小
window.geometry("400x300")

tk.messagebox.showinfo("提示", "请阅读并删除所有文本框提示文字后再输入")
tk.messagebox.showinfo("提示", "如果当前文件夹已存在同名文件，会覆盖之前的文件")

file_path_entry = tk.Entry(window)
file_path_entry.insert(0, "请选择Accesskey路径")
file_path_entry.place(x=110, y=20, width=210, height=30)

open_file_button = tk.Button(window, text="选择文件", command=open_file_dialog)
open_file_button.place(x=260, y=20, width=100, height=30)

appkey_entry = tk.Entry(window)
appkey_entry.insert(0, "请输入AppKey")
appkey_entry.place(x=110, y=60, width=210, height=30)

output_entry = tk.Entry(window)
output_entry.insert(0, "请输入不带后缀的输出文件名")
output_entry.place(x=110, y=100, width=210, height=30)

text_entry = tk.Entry(window)
text_entry.insert(0, "请输入要合成的文本")
text_entry.place(x=110, y=140, width=210, height=30)

voice_entry = tk.Entry(window)
voice_entry.insert(0, "请输入发音人名字")
voice_entry.place(x=110, y=180, width=210, height=30)

fmt_entry = tk.Entry(window)
fmt_entry.insert(0, "请输入输出文件格式,仅可以输出pcm/wav/mp3格式")
fmt_entry.place(x=110, y=220, width=210, height=30)

btn = tk.Button(window, text="开始合成", command=VoiceSyne)
btn.place(x=110, y=260, width=210, height=30)
# 启动事件循环
window.mainloop()
