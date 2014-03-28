import praw
import time
import json
import requests

r = praw.Reddit(user_agent='instagrambot')
r.login('', '') # user login

already_done = []

while True:
    submissions = r.get_domain_listing("instagram.com", sort="hot", period=None, limit=25)
    for sub in submissions:
        if sub.id not in already_done:
            sub_url = sub.url
            if ".jpg" not in sub_url and "/media/" not in sub_url:
                if sub_url.endswith('#'):
                    sub_url = sub_url[:-1]
                if not sub_url.endswith('/'):
                    sub_url += '/'
                sub_url += "media/?size=l"
        
            img = requests.post(
                "https://api.imgur.com/3/upload.json",
                headers = {"Authorization": "Client-ID <client-id>"},
                data = {
                    'key': "<key>",
                    'title': 'instagrambot',
                    'image': sub_url
                }
            )
            j = json.loads(img.text)
        
            if j['success']:
                img_link = j['data']['link']
        
                comment = "[Imgur mirror](" + img_link +")"
                comment += "\n\n*****\n\n"
                comment += "*This is a bot that creates imgur mirrors of instagram posts. If I'm not posting the correct image, please PM me. Comments and suggestions appreciated.*"
            
                sub.add_comment(comment)
                already_done.append(sub.id)
                time.sleep(5*60)
