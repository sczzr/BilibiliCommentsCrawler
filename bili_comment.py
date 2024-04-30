import requests
import re
import time
import csv
import os

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}


def get_video_id(bv):
    url = f'https://www.bilibili.com/video/{bv}'
    html = requests.get(url, headers=headers)
    html.encoding = 'utf-8'
    content = html.text
    aid_regx = '"aid":(.*?),"bvid":"{}"'.format(bv)
    video_aid = re.findall(aid_regx, content)[0]
    return video_aid


def fetch_comment_replies(video_id, comment_id, parent_user_name, max_pages=1000):
    replies = []
    preLen = 0
    for page in range(1, max_pages + 1):
        url = f'https://api.bilibili.com/x/v2/reply/reply?oid={video_id}&type=1&root={comment_id}&ps=10&pn={page}'
        try:
            # 添加超时设置
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data and data.get('data') and 'replies' in data['data']:
                    for reply in data['data']['replies']:
                        reply_info = {
                            '用户昵称': reply['member']['uname'],
                            '评论内容': reply['content']['message'],
                            '被回复用户': parent_user_name,
                            '评论层级': '二级评论',
                            '性别': reply['member']['sex'],
                            '用户当前等级': reply['member']['level_info']['current_level'],
                            '点赞数量': reply['like'],
                            '回复时间': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(reply['ctime']))
                        }
                        replies.append(reply_info)
                    if preLen == len(replies):
                        break
                    preLen = len(replies)
                else:
                    return replies
        except requests.RequestException as e:
            print(f"请求出错: {e}")
            break
        # 控制请求频率
        time.sleep(1)
    return replies

def fetch_comment(video_id, video_name, max_pages=1000):
    last_count = 0
    for page in range(1, max_pages + 1):
        print(f"正在抓取第{page}页评论...")
        url = f'https://api.bilibili.com/x/v2/reply?pn={page}&type=1&oid={video_id}&sort=2'
        try:
            # 添加超时设置
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and 'replies' in data['data']:
                    for comment in data['data']['replies']:
                        comment_info = {
                            '用户昵称': comment['member']['uname'],
                            '评论内容': comment['content']['message'],
                            '被回复用户': '',
                            '评论层级': '一级评论',
                            '性别': comment['member']['sex'],
                            '用户当前等级': comment['member']['level_info']['current_level'],
                            '点赞数量': comment['like'],
                            '回复时间': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(comment['ctime']))
                        }
                        replies = fetch_comment_replies(video_id, comment['rpid'], comment['member']['uname'])
                        save_comment_to_csv(comment_info, video_name)
                        for reply in replies:
                            save_comment_to_csv(reply, video_name)
            else:
                break
        except requests.RequestException as e:
            print(f"请求出错: {e}")
            break
        # 控制请求频率
        time.sleep(1)


def save_comment_to_csv(comment, video_bv):
    file_path = f'./result/{video_bv}.csv'
    if not os.path.isfile(file_path):
        with open(file_path, mode='w', encoding='utf-8',newline='') as file:
            writer = csv.DictWriter(file,
                            fieldnames=['用户昵称', '性别', '评论内容', '被回复用户', '评论层级', '用户当前等级',
                                        '点赞数量', '回复时间'])
            writer.writeheader()
    else:            
        with open(file_path, mode='a', encoding='utf-8',newline='') as file:
            writer = csv.DictWriter(file,
                            fieldnames=['用户昵称', '性别', '评论内容', '被回复用户', '评论层级', '用户当前等级',
                                        '点赞数量', '回复时间'])
            writer.writerow(comment)

filename = './video_list.csv'

# 打开文件并读取数据
with open(filename, mode='r') as file:
    reader = csv.reader(file)
    next(reader)  # 跳过第一行（标题行）
    for row in reader:
        video_name = row[0]  # 视频名字
        video_bv = row[1]  # video_bv
        print(f'视频名字: {video_name}, video_bv: {video_bv}')
        aid = get_video_id(video_bv)
        video_id = aid
        fetch_comment(video_id, video_name)