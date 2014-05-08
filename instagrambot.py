import praw, time, json, requests, ConfigParser
from instagram.client import InstagramAPI

config = ConfigParser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), r"config.ini"))
reddit_userAgent = config.get("reddit", "userAgent")
reddit_username = config.get("reddit", "username")
reddit_password = config.get("reddit", "password")
imgur_clientId = config.get("imgur", "clientId")
imgur_key = config.get("imgur", "key")
instagram_accessToken = config.get("instagram", "token")

def appendToFile(fileName, text):
    file = open(fileName, "a")
    file.write(text + '\n')
    file.close()

def main():
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
                caption, username, userurl = "", "", ""
                if ".mp4" in subURL:
                    isVideo = True
                elif ".jpg" not in subURL:
                    temp = requests.get("http://api.instagram.com/oembed?url=" + subURL)
                    if temp.status_code == 404:
                        continue
                    j1 = temp.json()
                    mediaID = j1['media_id']
                    if j1['title']:
                        caption = j1['title']
                    else:
                        caption = "<no caption>"
                    username = j1['author_name']
                    userurl = j1['author_url']
                    media = requests.get("https://api.instagram.com/v1/media/" + mediaID + "?access_token=" + instagram_accessToken)
                    mediaJSON = media.json()
                    if mediaJSON['data']['type'] == 'video':
                        isVideo = True
                        subURL = mediaJSON['data']['videos']['standard_resolution']['url']
                    else:
                        subURL = mediaJSON['data']['images']['standard_resolution']['url']
                
                print subreddit + ": " + subURL
                
                if isVideo:
                    #TODO upload video
                    print "Need to upload video"
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
                        if str(username) > 0:
                            comment += "\n\n"
                            comment += "[" + username + "](" + userurl + ")"
                            if str(caption) > 0:
                                comment += ": " + caption
                        comment += "\n\n*****\n\n"
                        comment += "*This is a bot that creates imgur mirrors of instagram images (sorry, doesn't work for videos just yet). "
                        comment += "Please PM me for any complaints, comments, or suggestions. Thank you!*\n\n"
                    
                        #print comment
                        sub.add_comment(comment)
                        alreadyDone.append(sub.id)
                        appendToFile("done.txt", sub.id)
                        
                        time.sleep(5*60)

if __name__ == "__main__":
    main()
