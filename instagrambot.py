import praw, time, json, requests, ConfigParser
from instagram.client import InstagramAPI

config = ConfigParser.ConfigParser()
config.read("config.ini")
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

# def

def main():
    r = praw.Reddit(user_agent=reddit_userAgent)
    r.login(reddit_username, reddit_password)

    # instagramAPI = InstagramAPI(access_token=instagram_accessToken)

    # file = open("done.txt", "r")
    # alreadyDone = [line.rstrip('\n') for line in file.readlines()]
    # file.close()

    already_done = []
    skipped_subs = ["photoshopbattles", "bicycling", "videos", "SquaredCircle", "tiara", "tightdresses"]

    while True:
        submissions = r.get_domain_listing("instagram.com", sort="top", period="day", limit=50)
        for sub in submissions:
            subreddit = sub.subreddit.display_name
            if subreddit in skipped_subs:
                print ">>> sub skipped: " + subreddit + "\n"
            elif "/p/" not in sub.url and ".jpg" not in sub.url:
                print ">>> skipped: " + sub.url + " (a profile?)\n"
            elif sub.author == None:
                print ">>> post has been deleted\n"
            elif sub.id not in already_done:
                subURL = sub.url
                is_video = False
                caption, username, userurl = "", "", ""
                if ".mp4" in subURL:
                    is_video = True
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
                        is_video = True
                        subURL = mediaJSON['data']['videos']['standard_resolution']['url']
                    else:
                        subURL = mediaJSON['data']['images']['standard_resolution']['url']

                print subreddit + ": " + subURL

                if is_video:
                    #TODO upload video
                    print ">>> Need to upload video"
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
                        if len(username) > 0:
                            comment += "\n\n"
                            if len(username) > 0:
                                comment += "[" + username + "](" + userurl + ")"
                            if len(caption) > 0:
                                comment += ": " + caption
                        comment += "\n\n*****\n\n"
                        comment += "*This is a bot that creates imgur mirrors of instagram images (sorry, doesn't work for videos just yet). "
                        comment += "Please PM me for any complaints, comments, or suggestions. Thank you!*\n\n"

                        #print comment
                        sub.add_comment(comment)
                        already_done.append(sub.id)
                        # appendToFile("done.txt", sub.id)

                        time.sleep(5*60)
        time.sleep(23*60*60)


if __name__ == "__main__":
    main()
