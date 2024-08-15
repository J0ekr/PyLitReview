import time
import tqdm
import math
import random
import glob 
import os

import numpy as np

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from enum import Enum

class SearchWhere(Enum):
        Title = 1
        Abstract = 2
        TitleAbstract = 3 #Keywords have to be in Title OR Abstract
        Text = 4
class Library(Enum):
        IEEE = 1
        ACM = 2
        ScienceDirect = 3

globalLastLibrary = None
driver = None

DEBUG = 0

def getElement(driver, by, value, number=None, timeOut=3, maxTry=5):
    """
    Get the element from the driver in a safe way by waiting for the element to appear

    Attributes
    ----------
    driver : selenium.webdriver
        The selenium driver
    by : selenium.webdriver.common.by
        The search method
    value : str 
        The search value
    number : int, optional 
        The number of the element to return (default is None)
        If None all elements are returned as a list
    timeOut : int, optional
        The time to wait for the element to appear (default is 3)
    maxTry : int, optional
        The maximum number of tries to find the element (default is 5)

    Returns
    -------
    bool
        True if the element was found
    selenium.webdriver.element
        The element if found
        None if no element was found
    """

    i = 0
    while True:
        if (number != None):
            if len(driver.find_elements(by=by, value=value)) > number:
                try:
                    element = driver.find_elements(by=by, value=value)[number]
                    return True, element
                except:
                    if i >= maxTry:
                        print_debug(f'Error: Failed to find {value} by {by}', 0)
                        return False, None
                    else:
                        print_debug(f'Retrying to find to find {value} by {by}', 2)
                    i +=1
        else:
            try:
                driver.find_element(by=by, value=value)
                elements = driver.find_elements(by=by, value=value)
                return True, elements
            except NoSuchElementException:
                if i >= maxTry:
                    print_debug(f'Warning: Failed to find {value} by {by}', 0)
                    return False, None
                else:
                    print_debug(f'Retrying to find to find {value} by {by}', 2)
                i +=1
        time.sleep(timeOut)
    return False, None
    
    
def getFileNameOutput(infos, outputFolderBib, pagenr):
    """
    Get the output file name for the bib file
    Attributes
    ----------
    infos : dict
        The information about the search
    outputFolderBib : str
        The output folder for the bib file
    pagenr : int
        The page number
    """
    library = str(infos["Library"]).split(".")[-1].lower()
    name = ("--".join(infos["Keyword"])).replace(" ","-")
    searchWhere = str(infos["SearchWhere"]).split(".")[-1]
    return f'{outputFolderBib}{library}_{name}_{searchWhere}_page{pagenr}_{infos["YearStart"]}-{infos["YearEnd"]}.bib'

def save_screenshot(driver, infos, path = "./screenshots/"): 
    """
    Save a screenshot of the current page

    Attributes
    ----------
    driver : selenium.webdriver
        The selenium driver
    infos : dict
        The information about the search
    path : str, optional
        The path to save the screenshot (default is "./screenshots/")
    """
    library = str(infos["Library"]).split(".")[-1]
    name = "".join(infos["Keyword"])
    searchWhere = str(infos["SearchWhere"]).split(".")[-1]

    os.makedirs(path, exist_ok=True)
    driver.save_screenshot(f"{path}{library}_{name}_{searchWhere}_{int(time.time())}.png")
    
def print_debug (text, level=1):
    if DEBUG >= level:
        print(text)

def getURLACM(infos):
    """
    Get the URL for the ACM search
    
    Attributes
    ----------
    infos : dict
        The information about the search
    
    Returns
    -------
    str
        The URL for the search
    """

    keywords = infos["Keyword"]
    concatentation="AND"
    search = ""
    titleSearch = "doSearch?AllField="
    for i, keyword in enumerate(keywords):
        search += f"%22{keyword}%22"
        if (i < len(keywords)-1):
            search += f"+{concatentation}+"

    if infos["SearchWhere"] == SearchWhere.Title:
        print_debug("Searching ACM for title only", 0)
        titleSearch = f"doSearch?fillQuickSearch=false&expand=dl&field1=Title&text1={search}"

    elif infos["SearchWhere"] == SearchWhere.Abstract:
        print_debug("Searching ACM for abstract only", 0)
        titleSearch = f"doSearch?fillQuickSearch=false&expand=dl&field1=Abstract&text1={search}"
        
    elif infos["SearchWhere"] ==  SearchWhere.TitleAbstract:     
        titAbsDict = {SearchWhere.Title: "Title", SearchWhere.Abstract: "Abstract"}
        if (infos["SearchWhere"] == SearchWhere.TitleAbstract):
            lstWhere = [SearchWhere.Title, SearchWhere.Abstract]
            key = ''
            for i, keyword in enumerate(infos["Keyword"]):

                key = key + '['
                for j, w in enumerate(lstWhere):
                    key = f'{key}{titAbsDict[w]}:"{keyword.replace(" ", "+")}"'
                    if (len(lstWhere) - j > 1):
                        key = key + '+OR+'
                key = key + ']'
                if (len(infos["Keyword"]) - i > 1):
                    key = key + '+AND+'
            key = key + ''

        titleSearch = key.replace(":","%3A").replace("[","%28").replace("]","%29")
        
        url = f'https://dl.acm.org/action/doSearch?fillQuickSearch=false&target=advanced&expand=dl&pageSize=50'
        url += f'&AfterYear={infos["YearStart"]}&BeforeYear={infos["YearEnd"]}'
        url += f'&AllField={titleSearch}&startPage='
        return url

        
    elif infos["SearchWhere"] == SearchWhere.Text:
        print_debug("Quicksearching ACM")
        raise NotImplementedError("Can't use 'set' on an ADC!")
    else:
        print_debug("Error: Not a supproted search type", 0)


    # The url must end with the page number so we can attach the page number later
    url = f'https://dl.acm.org/action/{titleSearch}&pageSize=50'
    url = url + f'&AfterYear={infos["YearStart"]}&BeforeYear={infos["YearEnd"]}&startPage='
    return 


def loadACMBib (toOpen, driver):
    """
    Load the ACM bib file
    
    Attributes
    ----------
    toOpen : str
        The URL to open
    driver : selenium.webdriver
        The selenium driver
    
    Returns
    -------
    bool
        True if the bib file was loaded
    int
        0 if no results were found, 1 if results were found, -1 if an error occured
    """
    try:
        driver.get(toOpen)
    except:
        print_debug(f'Error: Failed to open {toOpen}', 0)
        return False, -1
    
    
    #iterate over middle navbar to see if query found paper results or only people
    successElement, navMiddle = getElement(driver, by=By.CLASS_NAME, value="search-result__nav", number=0, maxTry=2)
    found = False
    for a in navMiddle.find_elements(by=By.TAG_NAME, value="a"):
        if(a.text =="RESULTS"):
            if "active" not in a.get_attribute("class"):
                a.click()
            found = True
            break
            
    if found == False:
        return True, 0
        
    # Select "Select All" to download all entries
    successElement, element = getElement(driver, by=By.CLASS_NAME, value="item-results__checkbox", number=0)
    if (successElement):
        element.click()
    else:
        return False, -1
    
    # Seach and click the "Export Citations" button
    successElement, element = getElement(driver, by=By.CLASS_NAME, value="export-citation", number=0)
    if (successElement):
        element.click()
    else:
        return False, -1

    time.sleep(5)
    # Get the Download button from the overlay and Dowload the bib file
    successElement, elementOverlayExport = getElement(driver, by=By.CLASS_NAME, value="exportCitation__tabs", number=0)
    if (successElement):
        successElement, elementButtonDownload = getElement(elementOverlayExport, by=By.CLASS_NAME, value="download__btn", number=0)
        if (successElement):
            elementButtonDownload.click()
        else:
            False, -1
    else:
        False, -1
        
    return True, 1
        
def saveACMBib(driver, infos, outputFolderBib):
    acm_maxpage = 39
    
    keyword = [item.replace(" ", "+") for item in infos["Keyword"]]
    
    print_debug(f"Search for: {keyword}", 1)
    
    url = getURLACM(infos)
    
    print_debug(url, 1)

    driver.get(url)
    time.sleep(7)
    
    successElement, navbar = getElement(driver, by=By.CLASS_NAME, value="search-result__nav-container", number=0)
    if not successElement:
        return False, url, -1
    
    successElement, navelements = getElement(navbar, by=By.XPATH, value=".//*", number=None)
    if not successElement:
        return False, url, -1
        
    foundResults = False
    for nav_element in navelements:
        if "RESULTS" in nav_element.text: 
            foundResults = True
            
    if foundResults == False: 
        print_debug("Only people in results - next keyword", 2)
        return False, url, -1
    
    save_screenshot(driver, infos)

    successElement, searchResultCount = getElement(driver, by=By.CLASS_NAME, value="result__count", number=0)
    if not successElement:
        return False, url, -1

    searchResultCount = searchResultCount.text.split(" ")[0]
    if "," in searchResultCount:
        searchResultCount = searchResultCount.replace(",", "")
    searchResultCount = int(searchResultCount)
    
    if searchResultCount == 0:
        return True, url, searchResultCount
    
    r = np.min([math.ceil(searchResultCount / 50), acm_maxpage])

    if (r > acm_maxpage):
        print_debug(f'Warning: Too many results for ACM search: {"".join(infos["Keyword"])}, only downloading the first {acm_maxpage} pages', 0)
        return False, url, searchResultCount
    
    # Loop through all pages and save resulting bib files
    for i in tqdm.tqdm(range(r), desc="pages"):
        toOpen = url + str(i)
        
        success, count = loadACMBib(toOpen, driver)
        if success and (count > 0): 
            time.sleep(1)
            #try:
            tmpFile = ""
            while True:
                # If more than one bib element is in the file
                if os.path.isfile(f'{outputFolderBib}acm.bib'):
                    tmpFile = f'{outputFolderBib}acm.bib'
                    break

                # IF only one element is in the file
                filesAvailable = glob.glob(f'{outputFolderBib}/acm_*.*.bib')
                if (len(filesAvailable) == 1):
                    tmpFile = filesAvailable[0]
                    break
                elif (len(filesAvailable) > 2):
                    print_debug(f'Error: Too many ACM files in {outputFolderBib}', 0)
                    break

                time.sleep(1)
                print_debug(f'Wait for file ACM bib file.', 2)
            os.rename(tmpFile, getFileNameOutput(infos, outputFolderBib, i))
        else:
            return False, url, searchResultCount
            
    return True, url, searchResultCount

def getURLIEEE(infos):
    """
    Get the URL for the IEEE search

    Attributes
    ----------
    infos : dict
        The information about the search

    Returns
    -------
    str
        The URL for the search
    """
    concatentation="AND"
    URL = ""
    search = ""
    
    titAbsDict = {SearchWhere.Title: "Document%20Title", SearchWhere.Abstract: "Abstract"}
    key = ""
    if (infos["SearchWhere"] == SearchWhere.TitleAbstract):
        lstWhere = [SearchWhere.Title, SearchWhere.Abstract]
        key = '('
        for i, keyword in enumerate(infos["Keyword"]):

            key = key + '('
            for j, w in enumerate(lstWhere):
                key = f'{key}"{titAbsDict[w]}":"{keyword}"'
                if (len(lstWhere) - j > 1):
                    key = key + ' OR '
            key = key + ')'
            if (len(infos["Keyword"]) - i > 1):
                key = key + ' AND '
        key = key + ')'
    elif infos["SearchWhere"] == SearchWhere.Text:# | _:
        for i, keyword in enumerate(infos["Keyword"]):
            key += f"%22{keyword}%22"
            if (i < len(infos["Keyword"])-1):
                key += f"+{concatentation}+"
    else:
        key += "("
        for i, keyword in enumerate(infos["Keyword"]):
            key += f'"{titAbsDict[searchWhere]}":"{keyword}"'
            if (i < len(infos["Keyword"])-1):
                key += "+AND+"
            else:
                key += ")"
    search = key.replace("\"","%22").replace(" ","%20")

    # The url must end with the page number so we can attach the page number later
    url = f"https://ieeexplore.ieee.org/search/searchresult.jsp?action=search&matchBoolean=true"
    url = url + f"&queryText={search}&highlight=true&returnFacets=ALL"
    url = url + f'&returnType=SEARCH&matchPubs=true&ranges={infos["YearStart"]}_{infos["YearEnd"]}_Year'
    url = url + f"&rowsPerPage=50&pageNumber="
    return url

def loadIEEEBib (toOpen, driver, outputFolderBib):
    """
    Load the IEEE bib file
    
    Attributes
    ----------
    toOpen : str
        The URL to open
    driver : selenium.webdriver
        The selenium driver
    outputFolderBib : str
        The output folder for the bib file

    Returns
    -------
    bool
        True if the bib file was loaded
    str
        The path to the downloaded bib file
        Empy if the file was not downloaded
    """
    driver.get(toOpen)

    ## Check if login is needed - might not be needed
    # lstLogin = driver.find_elements(by=By.TAG_NAME, value="xpl-personal-signin-custom")
    # if len(lstLogin) > 0:
    #     print_debug("Performing Login")
    #     login = lstLogin[0]

    #     for elementInput in login.find_elements(by=By.TAG_NAME, value="input"):
    #         if "email" in elementInput.get_attribute("aria-label"):
    #             elementInput.send_keys(ieeeLoginEmail);
    #     #         print_debug("email")
    #         elif "password" in elementInput.get_attribute("aria-label"):
    #             elementInput.send_keys(ieeeLoginPassword);
    #     #         print_debug("password")
    #     for elementButton in login.find_elements(by=By.TAG_NAME, value="button"):
    #         if elementButton.text == "Sign In":
    #             elementButton.click()
    time.sleep(random.uniform(5,20))
    
    #Click SELECT ALL to export all papers
    found = False
    for e in driver.find_elements(by=By.CLASS_NAME, value="results-actions-selectall"):
        if e.text == 'Select All on Page':
            found = True
            e.click()
    if not found:
        print_debug("Warning: element not found 'Select All on Page'", 2)
        return False, ""
    time.sleep(5)

    # Find EXPORT and open the overlay
    found = False
    for e in driver.find_elements(by=By.CLASS_NAME, value="xpl-toggle-btn"):
        if e.text == "Export":
            found = True
            e.click()
            break
    if not found:
        print_debug("Warning: element not found 'Select All on Page'", 2)
        return False, ""
    time.sleep(random.uniform(2,7))


    # Press "Cistion" in the Overlay
    elementOverlay = driver.find_elements(by=By.CLASS_NAME, value="modal-content")
    if (len(elementOverlay) != 1):
        print_debug("Warning: element not found Citation Overlay", 2)
        return False, ""
    else: 
        elementOverlay = elementOverlay[0]

    found = False
    for e in elementOverlay.find_elements(by=By.CLASS_NAME, value="nav-item"):
        if e.text == "Citations":
            found = True
            e.click()
            break
    if not found:
        print_debug("Warning: element not found 'Citations'", 2)
        return False, ""
    time.sleep(random.uniform(2,5))

    
    found = False
    for e in elementOverlay.find_elements(by=By.TAG_NAME, value="label"):
        if e.get_attribute("for") == "download-bibtex":
            found = True

            elementRadio = e.find_elements(by=By.TAG_NAME, value="input")
            if len(elementRadio) != 1:
                print_debug("Warning: element not found Dowload Bibtex", 2)
                return False, ""
            else:
                elementRadio = elementRadio[0]
                elementRadio.click()
            break
    if not found:
        print_debug("Warning: element not found 'BibTeX'", 2)
        return False, ""
    time.sleep(random.uniform(2,3))
    
    found = False
    for e in elementOverlay.find_elements(by=By.TAG_NAME, value="label"):
        if e.get_attribute("for") == "citation-abstract":
            found = True

            elementRadio = e.find_elements(by=By.TAG_NAME, value="input")
            if len(elementRadio) != 1:
                print_debug("Warning: element not found Citation Format", 2)
                return False, ""
            else:
                elementRadio = elementRadio[0]
                elementRadio.click()
            break
    if not found:
        print_debug("Warning: element not found 'Citation and Abstract'", 2)
        return False, ""
    time.sleep(random.uniform(2,3))

    # Press Downloadbutton
    found = False
    for e in elementOverlay.find_elements(by=By.TAG_NAME, value="button"):
        if e.text == "Download":
            found = True
            e.click()
            break
    if not found:
        print_debug("Warning: element not found 'Download'", 2)
        return False, ""
    time.sleep(random.uniform(3,7))

    ## test to get the file name from the download manager
    # if(len(driver.window_handles) == 1):
    #     driver.execute_script("window.open('');")
    #     driver.switch_to.window(driver.window_handles[1])
    #     time.sleep(1)
    #     driver.get("chrome://downloads/")
    # else:
    #     driver.switch_to.window(driver.window_handles[1])
    # time.sleep(1)

    # # https://stackoverflow.com/questions/61067252/navigating-chrome-downloads-page-using-python-selenium
    # file_name = driver.execute_script("""
    #                 var file_name = document.querySelector('downloads-manager')
    #                     .shadowRoot.getElementById('frb0')
    #                     .shadowRoot.getElementById('file-link').textContent;
    #                 return file_name;
    #                 """)

    # driver.switch_to.window(driver.window_handles[0])
    # pathToDownloadedFile = f'{outputFolderBib}{file_name}'

    lstFiles = glob.glob(f'{outputFolderBib}/IEEE Xplore Citation BibTeX Download*.bib')
    if len(lstFiles) != 1:
        print_debug("Error: Too many IEEE Explore files in the Download folder, remove old ones before proceeding.", 1)
        return False, ""
    
    pathToDownloadedFile = lstFiles[0]
        
    return True, pathToDownloadedFile

def saveIEEEBib(driver, infos, outputFolderBib):
    ieee_maxpage = math.inf
    
    print_debug(f'Search for: {infos["Keyword"]}', 1)
    
    url = getURLIEEE(infos)
    
        

    print_debug(url)
    
    driver.get(url)
    time.sleep(7)

    save_screenshot(driver, infos)

    
    searchResultCount = -1
    successElement, element = getElement(driver, by=By.CLASS_NAME, value="Dashboard-header", number=0)
    if (successElement):
        successElement, element = getElement(element, by=By.TAG_NAME, value="span", number=0)
        if (successElement):
            if (element.text == "No results found"):
                searchResultCount = 0
            else:
                successElement, element = getElement(element, by=By.TAG_NAME, value="span", number=1)
                if successElement:
                    searchResultCount = int(element.text)
                else:
                    return False, url, searchResultCount
        else:
            return False, url, searchResultCount
    else:
        return False, url, searchResultCount
            
    if searchResultCount == 0:
        return True, url, searchResultCount
    
    r = int(np.min([math.ceil(searchResultCount / 50), ieee_maxpage]))

    return True, url, searchResultCount

    for i in tqdm.tqdm(range(r), desc="pages"):
        toOpen = url + str(i+1)

        success, pathToDownloadedFile = loadIEEEBib(toOpen, driver, outputFolderBib)
        
        if success:
            os.rename(pathToDownloadedFile, getFileNameOutput(infos, outputFolderBib, i))
        else:
            return False, url, searchResultCount

        time.sleep(2)
        
    return True, url, searchResultCount

def getURLScienceDirect(infos):
    """
    Get the URL for the ScienceDirect search

    Attributes
    ----------
    infos : dict
        The information about the search
    """
    concatentation="AND"
    
    search = ""
   
    
    titleSearch = "tak="
    if infos["SearchWhere"] == SearchWhere.Title:
        titleSearch = "title="
    elif infos["SearchWhere"] == SearchWhere.TitleAbstract:
        titleSearch = "tak="
        
    for i, keyword in enumerate(infos["Keyword"]):
        search += f"%22{keyword}%22"
        if (i < len(infos["Keyword"])-1):
            search += f"%20{concatentation}%20" 
            
    url = f'https://www.sciencedirect.com/search?date={infos["YearStart"]}-{infos["YearEnd"]}&'
    url = url+ f'{titleSearch}{search}&show=50&offset='
    return url


def loginScienceDirect(driver, username, password):
    Login_URL = "https://www.sciencedirect.com/"
    driver.get(Login_URL)
    time.sleep(5)
    
    if DEBUG > 1:
        driver.save_screenshot("./screenshots/init.png")
        
    driver.find_element(by=By.LINK_TEXT, value="Sign in").click()
    time.sleep(10)
    mail = driver.find_element(by=By.ID, value="bdd-email")
    mail.send_keys(username)
    time.sleep(1)
    mail.send_keys(Keys.ENTER)
    time.sleep(1)
    
    if DEBUG > 1:
        driver.save_screenshot("./screenshots/login.png")
        
    time.sleep(1)
    driver.find_element(by=By.ID, value="bdd-elsPrimaryBtn").click()
    time.sleep(1)
    driver.find_element(by=By.ID, value="username").send_keys(username)
    time.sleep(1)
    pwd = driver.find_element(by=By.ID, value="password")
    pwd.send_keys(password)
    time.sleep(1)
    pwd.send_keys(Keys.ENTER)
    time.sleep(2)
    
    try:
        driver.find_element(by=By.ID, value="institution-button").click()
    except:
        print_debug("Error: intitution button apparently no accessable", 0)
        driver.save_screenshot("./screenshots/StaleElement.png")
        driver.find_element(by=By.ID, value="institution-button").click()
    time.sleep(2)
    return driver

def loadScienceDirectBib(toOpen, driver):
    driver.get(toOpen)
    time.sleep(5)
    if DEBUG > 1: driver.save_screenshot("./screenshots/sciencedirect.png")
    driver.find_element(by=By.ID, value="select-all-results").click()
    time.sleep(1)
    if DEBUG > 1: driver.save_screenshot("./screenshots/sciencedirect_clickall.png")
    driver.find_element(by=By.CLASS_NAME, value="button-link.export-all-link-button.button-link-primary").click()
    time.sleep(5)
    driver.find_elements(by=By.CLASS_NAME, value="button-link.button-link-primary.export-option.u-display-block")[2].click()
    time.sleep(10)
    return True

def saveScienceDirectBib(driver, infos, outputFolderBib): #keywords_list, outputFolderBib, titleOnly):
    sd_maxpage = 19
    #driver = setupCrawler(outputFolderBib, Library.ScienceDirect)
    url = getURLScienceDirect(infos)
    driver.get("https://www.sciencedirect.com/")
    
    save_screenshot(driver, infos)
        
    try:
        driver = loginScienceDirect(driver)
    except NoSuchElementException:
        print_debug("Already logged in or wrong credentials", 1) 
        
    # loginScienceDirect(driver)
    
    save_screenshot(driver, infos)

#     for keywords in keywords_list:
    print_debug(f'Search for: {infos["Keyword"]}', 1)
    url = getURLScienceDirect(infos)
    driver.get(url)
    time.sleep(3)
    try:
        searchResultCount = driver.find_element(by=By.CLASS_NAME, value="search-body-results-text")
        searchResultCount = searchResultCount.text.split(" ")[0]
        if "," in searchResultCount:
            searchResultCount = searchResultCount.replace(",", "")
        searchResultCount = int(searchResultCount)
    except NoSuchElementException:
        searchResultCount = 0

    r = np.min([math.ceil(searchResultCount / 50), sd_maxpage])


    if (r > sd_maxpage):
        print_debug(f'Warning: Too many results for ScienceDirect search: {"".join(infos["Keyword"])}, only downloading the first {sd_maxpage} pages', 0)
        return False, url, searchResultCount
    
    for i in tqdm.tqdm(range(r), desc="pages"):
        # driver = setupCrawler(dl_folder)
        toOpen = url + str(i*50)
        success = loadScienceDirectBib(toOpen, driver)
        if not success:
            return False, url, searchResultCount

    return True, url, searchResultCount


def setupCrawler(targetLibrary, outputFolderBib):
    """
    Setup the crawler for the target library and return the scelenium driver object

    Attributes
    ----------
    targetLibrary : Library Emum
        The target library to crawl
    outputFolderBib : str
        The output folder for the bib files
    """
    options = webdriver.ChromeOptions()
    options.add_argument('window-size=1920,1080')
    
    if targetLibrary == Library.ACM:
        options.add_argument('headless')
        options.add_argument("disable-gpu")
    elif targetLibrary == Library.IEEE:
        options.add_argument('headless')
        options.add_argument("disable-gpu")
    elif targetLibrary == Library.ScienceDirect:
        None
    p = {"download.default_directory": outputFolderBib}
    options.add_experimental_option("prefs", p)
    #ser = Service("./chromedriver.exe")
    op = webdriver.ChromeOptions()
    driver = webdriver.Chrome(options=options) #
    print_debug("Driver setup complete.", 1)
    return driver

def crawl(infos, outputFolderBib):
    """
    Crawl the target library and save the bib file

    Attributes
    ----------
    infos : dict
        The information about the search
    outputFolderBib : str
        The output folder for the bib file
    """
    global globalLastLibrary
    global driver
    
    if (globalLastLibrary != infos["Library"]):
        driver = setupCrawler(infos["Library"], outputFolderBib)
        globalLastLibrary = infos["Library"]
        print_debug(f'Setup Crwaler for {infos["Library"]}', 1)
    
    print_debug(f'Start crawling {infos["Library"]}', 1)
        
    if infos["Library"] == Library.ACM:
        success, url, searchResultCount = saveACMBib(driver, infos, outputFolderBib)
    elif infos["Library"] == Library.IEEE:
        success, url, searchResultCount = saveIEEEBib(driver, infos, outputFolderBib)
    elif infos["Library"] == Library.ScienceDirect:
        keyword = [item.replace(" ", "%20") for item in keyword]
        success, url, searchResultCount = saveScienceDirectBib(driver, infos, outputFolderBib)
    else:
        print_debug(f'Error: Library {infos["Library"]} not yet supported', 0)
        
    return success, url, searchResultCount