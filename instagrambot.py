import praw, time, json, requests, ConfigParser

def appendToFile(subId):
    file = open("done.txt", "a")
    file.write(subId + '\n')
    file.close()
    
def getImageURL(subURL):
    #TODO what if a profile is linked? (no "/p/" in path)
    if ".jpg" not in subURL and "/media/" not in subURL:
        if subURL.endswith('#'):
            subURL = subURL[:-1]
        if not subURL.endswith('/'):
            subURL += '/'
        subURL += "media/?size=l"
    return subURL

def main():
    config = ConfigParser.ConfigParser()
    config.read("config.ini")
    reddit_userAgent = config.get("reddit", "userAgent")
    reddit_username = config.get("reddit", "username")
    reddit_password = config.get("reddit", "password")
    imgur_clientId = config.get("imgur", "clientId")
    imgur_key = config.get("imgur", "key")
    
    r = praw.Reddit(user_agent=reddit_userAgent)
    r.login(reddit_username, reddit_password)
    
    file = open("done.txt", "r")
    alreadyDone = [line.rstrip('\n') for line in file.readlines()]
    file.close()
        
    while True:
        submissions = r.get_domain_listing("instagram.com", sort="hot", period=None, limit=25)
        for sub in submissions:
            if sub.id not in alreadyDone and ".mp4" not in sub.url: #TODO handle videos better!
                subURL = getImageURL(sub.url)
                
                img = requests.post(
                    "https://api.imgur.com/3/upload.json",
                    headers = {"Authorization": "Client-ID " + imgur_clientId},
                    data = {
                        'key': imgur_key,
                        'title': 'instagrambot', #TODO get original comment?
                        'image': subURL
                    }
                )
                j = json.loads(img.text)
                
                if j["success"]:
                    img_link = j['data']['link']
                    
                    comment = "[Imgur mirror](" + img_link +")"
                    comment += "\n\n*****\n\n"
                    comment += "*This is a bot that creates imgur mirrors of instagram images (sorry, doesn't work for videos just yet)."
                    comment += "If I'm not posting the correct image, please PM me. Comments and suggestions appreciated.*\n\n"
                    
                    sub.add_comment(comment)
                    alreadyDone.append(sub.id)
                    appendToFile(sub.id)
                    time.sleep(5*60)

if __name__ == "__main__":
    main()
