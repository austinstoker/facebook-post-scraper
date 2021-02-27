import argparse
import time
import json
import csv
import sys

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup as bs
# import Action chains  
#from selenium.webdriver.common.action_chains import ActionChains 
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.keys import Keys

with open('facebook_credentials.txt') as file:
    EMAIL = file.readline().split('"')[1]
    PASSWORD = file.readline().split('"')[1]


def _extract_post_text(item):
    actualPosts = item.find_all(attrs={"data-testid": "post_message"})
    text = ""
    if actualPosts:
        for posts in actualPosts:
            paragraphs = posts.find_all('p')
            text = ""
            for index in range(0, len(paragraphs)):
                text += paragraphs[index].text
    return text


def _extract_link(item):
    postLinks = item.find_all(class_="_6ks")
    link = ""
    for postLink in postLinks:
        link = postLink.find('a').get('href')
    return link


def _extract_post_id(item):
    postIds = item.find_all(class_="_5pcq")
    post_id = ""
    for postId in postIds:
        post_id = f"https://www.facebook.com{postId.get('href')}"
    return post_id


def _extract_image(item):
    postPictures = item.find_all(class_="scaledImageFitWidth img")
    image = ""
    for postPicture in postPictures:
        image = postPicture.get('src')
    return image


def _extract_shares(item):
    postShares = item.find_all(class_="_4vn1")
    shares = ""
    for postShare in postShares:

        x = postShare.string
        if x is not None:
            x = x.split(">", 1)
            shares = x
        else:
            shares = "0"
    return shares


def _extract_comments(item):
    postComments = item.findAll("div", {"class": "_4eek"})
    comments = dict()
    # print(postDict)
    for comment in postComments:
        if comment.find(class_="_6qw4") is None:
            continue

        commenter = comment.find(class_="_6qw4").text
        comments[commenter] = dict()

        comment_text = comment.find("span", class_="_3l3x")

        if comment_text is not None:
            comments[commenter]["text"] = comment_text.text

        comment_link = comment.find(class_="_ns_")
        if comment_link is not None:
            comments[commenter]["link"] = comment_link.get("href")

        comment_pic = comment.find(class_="_2txe")
        if comment_pic is not None:
            comments[commenter]["image"] = comment_pic.find(class_="img").get("src")

        commentList = item.find('ul', {'class': '_7791'})
        if commentList:
            comments = dict()
            comment = commentList.find_all('li')
            if comment:
                for litag in comment:
                    aria = litag.find("div", {"class": "_4eek"})
                    if aria:
                        commenter = aria.find(class_="_6qw4").text
                        comments[commenter] = dict()
                        comment_text = litag.find("span", class_="_3l3x")
                        if comment_text:
                            comments[commenter]["text"] = comment_text.text
                            # print(str(litag)+"\n")

                        comment_link = litag.find(class_="_ns_")
                        if comment_link is not None:
                            comments[commenter]["link"] = comment_link.get("href")

                        comment_pic = litag.find(class_="_2txe")
                        if comment_pic is not None:
                            comments[commenter]["image"] = comment_pic.find(class_="img").get("src")

                        repliesList = litag.find(class_="_2h2j")
                        if repliesList:
                            reply = repliesList.find_all('li')
                            if reply:
                                comments[commenter]['reply'] = dict()
                                for litag2 in reply:
                                    aria2 = litag2.find("div", {"class": "_4efk"})
                                    if aria2:
                                        replier = aria2.find(class_="_6qw4").text
                                        if replier:
                                            comments[commenter]['reply'][replier] = dict()

                                            reply_text = litag2.find("span", class_="_3l3x")
                                            if reply_text:
                                                comments[commenter]['reply'][replier][
                                                    "reply_text"] = reply_text.text

                                            r_link = litag2.find(class_="_ns_")
                                            if r_link is not None:
                                                comments[commenter]['reply']["link"] = r_link.get("href")

                                            r_pic = litag2.find(class_="_2txe")
                                            if r_pic is not None:
                                                comments[commenter]['reply']["image"] = r_pic.find(
                                                    class_="img").get("src")
    return comments


def _extract_reaction(item):
    toolBar = item.find_all(attrs={"role": "toolbar"})

    if not toolBar:  # pretty fun
        return
    reaction = dict()
    for toolBar_child in toolBar[0].children:
        str = toolBar_child['data-testid']
        reaction = str.split("UFI2TopReactions/tooltip_")[1]

        reaction[reaction] = 0

        for toolBar_child_child in toolBar_child.children:

            num = toolBar_child_child['aria-label'].split()[0]

            # fix weird ',' happening in some reaction values
            num = num.replace(',', '.')

            if 'K' in num:
                realNum = float(num[:-1]) * 1000
            else:
                realNum = float(num)

            reaction[reaction] = realNum
    return reaction


def _extract_html(bs_data):

    #Add to check
    with open('./bs.html',"w", encoding="utf-8") as file:
        file.write(str(bs_data.prettify()))

    k = bs_data.find_all(class_="_5pcr userContentWrapper")
    postBigDict = list()

    for item in k:
        postDict = dict()
        postDict['Post'] = _extract_post_text(item)
        postDict['Link'] = _extract_link(item)
        postDict['PostId'] = _extract_post_id(item)
        postDict['Image'] = _extract_image(item)
        postDict['Shares'] = _extract_shares(item)
        postDict['Comments'] = _extract_comments(item)
        # postDict['Reaction'] = _extract_reaction(item)

        #Add to check
        postBigDict.append(postDict)
        with open('./postBigDict.json','w', encoding='utf-8') as file:
            file.write(json.dumps(postBigDict, ensure_ascii=False).encode('utf-8').decode())

    return postBigDict


def _login(browser, email, password):
    browser.get("http://facebook.com")
    #browser.maximize_window()
    browser.find_element_by_name("email").send_keys(email)
    browser.find_element_by_name("pass").send_keys(password)
    browser.find_element_by_name('login').click()

def attemptClickByXpath(browser, desc, xpath):
  keepTrying = True
  while (keepTrying):
    try:
      print("searching for ",desc)
      matches = browser.find_elements_by_xpath(xpath)
      if not matches:
        print("no match for ", desc)
        return False
      print("match found ", desc)
      #browser.execute_script("return arguments[0].scrollIntoView(true);", matches[0])
      matches[0].click()
      time.sleep(1) #Todo do better here.
      return True
    except StaleElementReferenceException:
      print("StaleElementReferenceException")
    except NoSuchElementException:
      print("NoSuchElementException")
      return False
    except:
      print("Unhandled Exception")
      e = sys.exc_info()[0]
      print(e)


def clickViewPreviousComments(browser):
  return attemptClickByXpath(browser,"View previous comments", "//*[contains(text(), 'View previous comments')]")

def expandComments(browser):
  return attemptClickByXpath(browser,"See more","//*[contains(text(), 'See More')]")

def getNewCommentText(browser):
  keepTrying = True
  while (keepTrying):
    try:
      print("searching for Comments")
      matches = browser.find_elements_by_xpath("//*[starts-with(@aria-label, 'Comment by')]")
      if not matches:
        print("no match for ")
        return False
      print("matches found ")
      for m in matches:
        print (m)
        print(match.find_element_by_xpath(".//div[contains(@style,'text-align: start;')]").text)
      return True
    except StaleElementReferenceException:
      print("StaleElementReferenceException")
    except NoSuchElementException:
      print("NoSuchElementException")
      return False
    except:
      print("Unhandled Exception")
      e = sys.exc_info()[0]
      print(e)

def extract(page):
    option = Options()
    option.add_argument("--disable-infobars")
    #option.add_argument("start-maximized")
    option.add_argument("--disable-extensions")

    # Pass the argument 1 to allow and 2 to block
    option.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 1
    })

    # chromedriver should be in the same folder as file
    browser = webdriver.Chrome(executable_path="./chromedriver", options=option)
    _login(browser, EMAIL, PASSWORD)
    time.sleep(5)
    browser.get(page)
    
    time.sleep(5)
    howManyCommentPages = 0
    howManyCommentsExpanded = 0
    
    getNewCommentText(browser)
    while(clickViewPreviousComments(browser)):
      howManyCommentPages += 1
      while(expandComments(browser)):
        howManyCommentsExpanded+=1
        getNewCommentText(browser)

      browser.find_element_by_tag_name('body').send_keys(Keys.CONTROL + Keys.HOME)


    print ("Pages of comments:")
    print (howManyCommentPages)
    print ("Comments expanded:")
    print (howManyCommentsExpanded)
    time.sleep(90)

    # Now that the page is fully scrolled, grab the source code.
    source_data = browser.page_source

    # Throw your source into BeautifulSoup and start parsing!
    bs_data = bs(source_data, 'html.parser')

    postBigDict = _extract_html(bs_data)
    browser.close()

    return postBigDict


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Facebook Page Scraper")
    required_parser = parser.add_argument_group("required arguments")
    required_parser.add_argument('-page', '-p', help="The Facebook Public Page you want to scrape", required=True)
    args = parser.parse_args()
    postBigDict = extract(page=args.page)

    print("Finished")
