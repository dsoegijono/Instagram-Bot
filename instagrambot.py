import praw, time, json, requests, ConfigParser
from instagram.client import InstagramAPI

def appendToFile(fileName, text):
    file = open(fileName, "a")
    file.write(text + '\n')
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
    #instagram_clientId = config.get("instagram", "clientId")
    #instagram_clientSecret = config.get("instagram", "key")
    instagram_accessToken = config.get("instagram", "token")
    
    r = praw.Reddit(user_agent=reddit_userAgent)
    r.login(reddit_username, reddit_password)
    
    instAPI = InstagramAPI(access_token=instagram_accessToken)
    
    file = open("done.txt", "r")
    alreadyDone = [line.rstrip('\n') for line in file.readlines()]
    file.close()
    
    skippedSubs = ["photoshopbattles", "bicycling", "videos"]
        
    while True:
        submissions = r.get_domain_listing("instagram.com", sort="hot", period=None, limit=25)
        for sub in submissions:
            subreddit = sub.subreddit.display_name
            if subreddit in skippedSubs: #TODO handle each sub differently?
                print ">>> sub skipped: " + subreddit + "\n"
            elif "/p/" not in sub.url and ".jpg" not in sub.url:
                print ">>> skipped: " + sub.url + " (a profile?)\n"
            elif sub.author == None:
                print ">>> post has been deleted\n"
            elif sub.id not in alreadyDone:
                subURL = sub.url
                isVideo = False
                caption = "<no caption>"
                if ".mp4" in subURL:
                    isVideo = True
                elif ".jpg" not in subURL:
                    print subURL
                    temp = requests.get("http://api.instagram.com/oembed?url=" + subURL)
                    print "RESPONSE STATUS: " + str(temp.status_code)
                    j1 = temp.json()
                    mediaID = j1['media_id']
                    media = requests.get("https://api.instagram.com/v1/media/" + mediaID + "?access_token=" + instagram_accessToken)
                    mediaJSON = media.json()
                    if j1['title']:
                        caption = j1['title']
                    if mediaJSON['data']['type'] == 'video':
                        isVideo = True
                        subURL = mediaJSON['data']['videos']['standard_resolution']['url']
                    else:
                        subURL = mediaJSON['data']['images']['standard_resolution']['url']
                
                #subURL = getImageURL(sub.url)
                print subreddit + ": " + subURL
                
                if isVideo:
                    #TODO upload video
                    print "!!! need to upload video!"
                else:
                    img = requests.post(
                        "https://api.imgur.com/3/upload.json",
                        headers = {"Authorization": "Client-ID " + imgur_clientId},
                        data = {
                            'key': imgur_key,
                            'title': caption,
                            'image': subURL
                        }
                    )
                    j = json.loads(img.text)
                
                    if j["success"]:
                        img_link = j['data']['link']
                    
                        comment = "[Imgur mirror](" + img_link +")"
                        comment += "\n\nCaption: " + caption
                        comment += "\n\n*****\n\n"
                        comment += "*This is a bot that creates imgur mirrors of instagram images (sorry, doesn't work for videos just yet). "
                        comment += "If I'm not posting the correct image, please PM me. Comments and suggestions appreciated.*\n\n"
                    
                        #print comment
                        sub.add_comment(comment)
                        alreadyDone.append(sub.id)
                        appendToFile("done.txt", sub.id)
                        
                        time.sleep(5*60)

if __name__ == "__main__":
    main()
