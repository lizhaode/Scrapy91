import base64


def get_url(param1: str, param2: str) -> str:
    """
    这个方法是来自于 https://github.com/techGay/v9porn/pull/105/files 这条 PR
    大体逻辑是：
            1. 首先从 html 中找到 document.write(strencode()) 的内容
            2. strencode() 中的内容一共3部分，第一部分和第三部分相同
            3. 取出来第一部分和第二部分
            4. 对第一部分做 base64 decode
            5. 然后就是本方法中的内容，可以解密出真实的地址
    :param param1:
    :param param2:
    :return:
    """
    param1 = base64.b64decode(param1).decode()
    length = len(param1)
    result = ''
    for i in range(length):
        k = i % len(param2)
        tmp = ord(param1[i]) ^ ord(param2[k])
        result += chr(tmp)

    source = base64.b64decode(result)
    url = source.decode().split('\'')[1]
    return url
