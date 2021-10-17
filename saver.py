import os
import sys
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup, Comment
import cssutils
import logging
import time
import datetime

def saveFileInTag(soup, pagefolder, url, session, tag2find='img', inner='src'):
    """saves on specified `pagefolder` all tag2find objects"""
    if not os.path.exists(pagefolder):
        os.mkdir(pagefolder)
    for res in soup.findAll(tag2find):   # images, css, etc..
        try:
            if not res.has_attr(inner):  # check if inner tag (file object) exists
                continue  # may or may not exist
            print("===================")
            print(f"res: {res}")
            inner_attribute = res[inner]
            print(f"inner_attribute: {inner_attribute}")
            filename = os.path.basename(inner_attribute)
            print(f"basename: {filename}")
            filename = filename.split('?')[0]
            print(f"filename:　{filename}")
            fileurl = urljoin(url, res.get(inner))
            filepath = os.path.join(pagefolder, filename)
            # rename html ref so can move html and folder of files anywhere
            res[inner] = os.path.join(os.path.basename(pagefolder), filename)
            if not os.path.isfile(filepath):  # was not downloaded
                with open(filepath, 'wb') as file:
                    filebin = session.get(fileurl)
                    file.write(filebin.content)
        except Exception as exc:
            print("soupfindnSave(): filename: ", filename, "has error:", exc, file=sys.stderr)
    return soup

def updateLink(soup, url, session):
    """
    update all relative url path in <a> tag in the html to absolute url path
    
    Example:
    change href="/codegame/index.html" to href="https://www.w3schools.com/codegame/index.html"
    """
    for res in soup.findAll('a'):
        try:
            if not res.has_attr('href'):
                continue 
            # print("===================")
            # res['href'] = url[:-1]+res['href']
            res['href'] = updateSingleLink(url,res['href'])
            # print(f"{res['href']}")
        except Exception as exc:
            print("updateLink(): ", exc, file=sys.stderr)
    return soup

def updateSingleLink(hosturl,relativeUrl):
    """
    update a single url path to absolute url path
    """
    if relativeUrl.startswith('/'):
        relativeUrl = urljoin(hosturl[:-1], relativeUrl)
    return relativeUrl

    

def saveFileInStyle(soup, pagefolder, url, session):
    """
    Save the file in embedded css code

    Example:
    <style>
        #bgcodeimg {
            background: #282A35 url("/about/w3codes.png") no-repeat fixed center;
        }
    </style>

    This func will download the png file and change css url to "page_files/w3codes.png"
    
    """
    def replacer(relativeUrl):
        relativeUrl = updateSingleLink(url,relativeUrl)
        return relativeUrl
    cssutils.log.setLevel(logging.CRITICAL)
    for styles in soup.findAll('style'):
        try:
            sheet = cssutils.parseString(styles.encode_contents())
            cssutils.replaceUrls(sheet,replacer)
            styles.string.replace_with(sheet.cssText.decode("utf-8"))
            for fileurl in cssutils.getUrls(sheet):
                filename = os.path.basename(fileurl)
                filename = filename.split('?')[0]
                filepath = os.path.join(pagefolder, filename)
                if not os.path.isfile(filepath):  # was not downloaded
                    with open(filepath, 'wb') as file:
                        filebin = session.get(fileurl)
                        file.write(filebin.content)
            def replacer2(url):
                url = os.path.join(os.path.basename(pagefolder), filename)
                return url
            sheet = cssutils.parseString(styles.encode_contents())
            cssutils.replaceUrls(sheet,replacer2)
            styles.string.replace_with(sheet.cssText.decode("utf-8"))
        except Exception as exc:
            print("saveFileInStyle(): ", exc, file=sys.stderr)

    return soup

def addAnnotation(soup, url):
    comment = Comment(f" \nsaved from url = {url}\ncurrent time = {datetime.datetime.now()}\n")
    soup.html.insert_before(comment)
    return soup

def savePage(url, pagefilename='page'):
    session = requests.Session()
    response = session.get(url)
    # soup = BeautifulSoup(response.text, features="lxml")
    soup = BeautifulSoup(response.text, features="html.parser")
    if not os.path.exists(pagefilename):
        os.mkdir(pagefilename)
    pagefolder = pagefilename+'/'+pagefilename+'_files' 
    soup = saveFileInTag(soup, pagefolder, url, session, tag2find='img', inner='src')
    soup = saveFileInTag(soup, pagefolder, url, session, tag2find='link', inner='href')
    soup = saveFileInTag(soup, pagefolder, url, session, tag2find='script', inner='src')
    soup = saveFileInStyle(soup, pagefolder, url, session)
    soup = updateLink(soup, url, session)
    soup = addAnnotation(soup, url)
    with open(pagefilename+'/'+pagefilename+'.html', 'wb') as file:
        file.write(soup.prettify('utf-8'))
    print("===================")
    print(f"savePage({url}) finish.")
    return soup


# soup = savePage('https://github.com/rajatomar788/pywebcopy', 'pywebcopy')
# soup = savePage('https://en.wikipedia.org/wiki/Main_Page', 'wiki')
soup = savePage('https://www.w3schools.com/', 'w3schools')
