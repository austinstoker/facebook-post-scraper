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
from selenium.common.exceptions import ElementNotInteractableException
from selenium.webdriver.common.keys import Keys

with open('facebook_credentials.txt') as file:
    EMAIL = file.readline().split('"')[1]
    PASSWORD = file.readline().split('"')[1]

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
    except ElementNotInteractableException:
      print("ElementNotInteractableException")
      return False
    except:
      print("Unhandled Exception")
      e = sys.exc_info()[0]
      print(e)


def clickViewPreviousComments(browser):
  prev = attemptClickByXpath(browser,"View previous comments", "//*[contains(text(), 'View previous comments')]")
  more = attemptClickByXpath(browser,"More comments", "//*[contains(text(), 'more comments')]")
  return prev or more

def expandComments(browser):
  return attemptClickByXpath(browser,"See more","//*[contains(text(), 'See More')]")

def expandReplies(browser):
  return attemptClickByXpath(browser,"Replies","//*[(contains(text(), 'Replies') or contains(text(), 'more replies') or contains(text(), 'more reply')) and not(contains(text(), 'Hide'))]")

def expandCommentsAndReplies(browser):
  comments = expandComments(browser) 
  replies = expandReplies(browser)
  return comments or replies

def getNewCommentText(browser, setOfKnownComments, listOfComments):
  # try:
    print("searching for Comments")
    matches = browser.find_elements_by_xpath("//*[starts-with(@aria-label, 'Comment by') or starts-with(@aria-label, 'Reply by')]")
    if not matches:
      print("no match for ")
      return False
    print(len(matches), "matches found ")
    for m in matches:
      try:
        #val = m.text
        # print (m.text)
        val = m.find_element_by_xpath(".//div[contains(@style,'text-align: start;')]").text
        #print(val)
        if val not in setOfKnownComments:
          setOfKnownComments.add(val)
          listOfComments.append(val)
      except:
        print("Unhandled Exception")
        e = sys.exc_info()[0]
        print(e)
    return True
  # except StaleElementReferenceException:
  #   print("StaleElementReferenceException")
  # except NoSuchElementException:
  #   print("NoSuchElementException")
  #   return False
  # except:
  #   print("Unhandled Exception")
  #   e = sys.exc_info()[0]
  #   print(e)

def saveResultsResults(path, browser, listOfComments):
    with open(path, mode='wt', encoding='utf-8') as myfile:
      for c in listOfComments:
        myfile.write(c)
        myfile.write('\n')
      myfile.flush()
    source_data = browser.page_source
    # Throw your source into BeautifulSoup and start parsing!
    bs_data = bs(source_data, 'html.parser')
    with open('./pagePartialSnapshot.html',"w", encoding="utf-8") as file:
        file.write(str(bs_data.prettify()))

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
    setOfKnownComments = set()
    listOfComments = list()

    while(expandCommentsAndReplies(browser)):
        howManyCommentsExpanded+=1
    browser.find_element_by_tag_name('body').send_keys(Keys.CONTROL + Keys.HOME)
    getNewCommentText(browser, setOfKnownComments, listOfComments)

    while(clickViewPreviousComments(browser)):
      howManyCommentPages += 1
      while(expandCommentsAndReplies(browser)):
        howManyCommentsExpanded+=1
      browser.find_element_by_tag_name('body').send_keys(Keys.CONTROL + Keys.HOME)
      getNewCommentText(browser, setOfKnownComments, listOfComments)
      saveResultsResults("partialResults.txt", browser, listOfComments)
      print("length of list of comments: ", len(listOfComments))


    print ("Pages of comments:")
    print (howManyCommentPages)
    print ("Comments expanded:")
    print (howManyCommentsExpanded)
    saveResultsResults("finalResults.txt", browser, listOfComments)

    browser.close()

    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Facebook Page Scraper")
    required_parser = parser.add_argument_group("required arguments")
    required_parser.add_argument('-page', '-p', help="The Facebook Public Page you want to scrape", required=True)
    args = parser.parse_args()
    extract(page=args.page)

    print("Finished")
