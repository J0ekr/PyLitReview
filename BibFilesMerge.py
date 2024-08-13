#!/usr/bin/env python3

import os
import sys

sys.path.insert(0, './pybtex/')
from pybtex.database import parse_file
from pybtex.database import BibliographyData, Entry

import unidecode
import argparse
import csv
import html

mergedCont = 0 

#=============================================================
def mergeEntry(original, novo):
    global mergedCont
    merged = False

    yearOut = int(str(original.fields['year']))
    year2 = int(str(novo.fields['year']))
    if (year2<yearOut):
        original.fields['year'] = novo.fields['year']
        merged = True

    for novoKey in novo.fields:
        if novoKey not in original.fields:
            original.fields[novoKey] = novo.fields[novoKey]
            merged = True

    abs1 = ""
    abs2 = ""
    if "abstract" in original.fields:
        abs1 = original.fields['abstract']
    if "abstract" in novo.fields:
        abs2 = novo.fields['abstract']
    if (len(abs2)>len(abs1)):
        original.fields['abstract'] = novo.fields['abstract']
        merged = True

    if merged:
        mergedCont = mergedCont + 1

    original.fields['source'] = original.fields['source'] +";" + novo.fields['source']

    return original

#=============================================================
def getEntryDOIStr(entry):
    doi = ''
    if 'doi' in entry.fields:
        doi = str(entry.fields['doi']).replace('https://doi.org/', '')
    return doi

def getEntryAuthorStr(entry):
    author = ''
    if 'author' in entry.persons:
        author = ' and '.join([''.join(p.last()) + ', ' + ''.join(p.first()) for p in entry.persons['author']])
    return author

def getEntryYearStr(entry):
    year = ''
    if 'year' in entry.fields:
        year = int(str(entry.fields['year']))
        if year == 0:
            year = ''
    return year

def getEntryTitleStr(entry):
    title = ''
    if 'title' in entry.fields:
        title = str(entry.fields['title'])
    return title

def getEntryPublishStr(entry):
    publish = ''
    if 'journal' in entry.fields:
        publish = str(entry.fields['journal'])
    elif 'journaltitle' in entry.fields:
        publish = str(entry.fields['journaltitle'])
    elif 'booktitle' in entry.fields:
        publish = str(entry.fields['booktitle'])
    elif 'howpublished' in entry.fields:
        publish = str(entry.fields['howpublished'])
    elif 'type' in entry.fields:
        publish = str(entry.fields['type'])
    elif 'url' in entry.fields:
        publish = "URL {}".format(entry.fields['url'])
    elif 'crossref' in entry.fields:
        publish = entry.fields['crossref'].replace("_", " ")
        publish = capwords(publish)
    elif 'publisher' in entry.fields:
        publish = str(entry.fields['publisher'])
    elif 'arxivId' in entry.fields:
        publish = "arXiv"
    return publish

def getEntryAbstractStr(entry):
    abstract = ''
    if 'abstract' in entry.fields:
        # abstract = str(entry.fields['abstract'])
        abstract = entry.fields['abstract']
    if (abstract != ''):
        abstract = html.unescape(abstract).replace('\\%','%')
    return abstract

def cleanStringToCompare(xStr):
    return xStr.lower().replace(' ','').replace('.','').replace(',','').replace('-','').replace(':','').replace('/','').replace('\\','').replace("'",'').replace('`','')


#=============================================================
def run(folderPath, fileList, fileNameOut, logProcess):
    global mergedCont

    if logProcess:
        fRemoved = open(os.path.join(folderPath, 'BibFilesMerge_removed.csv'),'w', encoding='utf-8')
        csvRemoved = csv.writer(fRemoved, delimiter=';', quotechar='"')
        csvRemoved.writerow(['cause','source','key','doi','author','year','title','publish'])
        fFinal = open(os.path.join(folderPath, 'BibFilesMerge_final.csv'),'w', encoding='utf-8')
        csvFinal = csv.writer(fFinal, delimiter=';', quotechar='"')
        csvFinal.writerow(['key','source','doi','author','year','title','publish','abstract'])

    fileNamePathOut = os.path.join(folderPath, fileNameOut)

    bibDataOut = BibliographyData()

    total = 0
    mergedCont = 0 
    withoutAuthor = 0
    withoutYear = 0 
    withoutJornal = 0
    duplicates = 0

    print()
    print()

    for bibFileName in fileList:
       

        bibData = parse_file(os.path.join(folderPath,bibFileName))

        print(bibFileName + ':',len(bibData.entries.values()),"                                             ")    

        for entry in bibData.entries.values():
            total = total + 1
            doi = getEntryDOIStr(entry)
            author = getEntryAuthorStr(entry)
            year = getEntryYearStr(entry)
            title = getEntryTitleStr(entry)
            publish = getEntryPublishStr(entry)

            if author == '':
                withoutAuthor = withoutAuthor + 1
                if logProcess:
                    #cause;source;key;doi;author;year;title;publish
                    csvRemoved.writerow(['no author', bibFileName, entry.key, doi, author, year, title, publish])
                
            elif year == '':
                withoutYear = withoutYear + 1
                if logProcess:
                    #cause;source;key;doi;author;year;title;publish
                    csvRemoved.writerow(['no year', bibFileName, entry.key, doi, author, year, title, publish])
                
            elif publish == '':
                withoutJornal = withoutJornal + 1
                if logProcess:
                    #cause;source;key;doi;author;year;title;publish
                    csvRemoved.writerow(['no journal', bibFileName, entry.key, doi, author, year, title, publish])

            else:
                key =  entry.key.lower()
                print("Key "+key+"               \r", end="", flush=True)

                entry.fields['source'] = bibFileName
                oldEntry = None
                cleanTitle = cleanStringToCompare(title)

                for entryOut in bibDataOut.entries.values():
                    if (doi != ''):
                        doiOut = getEntryDOIStr(entryOut)
                        if (doiOut != '' and doi == doiOut):
                            oldEntry = entryOut
                            break
                    
                    cleanOutTitle = cleanStringToCompare(entryOut.fields['title'])
                    if (cleanTitle == cleanOutTitle):
                        year = int(str(entry.fields['year']))
                        yearOut = int(str(entryOut.fields['year']))
                        diff = abs(year-yearOut)
                        if (diff==0):
                            oldEntry = entryOut
                        elif (diff==1 or diff==2):
                            try:
                                lastname = unidecode.unidecode(entry.persons['author'][0].last_names[0]).lower()
                            except :
                                lastname = ""
                                
                            try:
                                lastNameOut = unidecode.unidecode(entryOut.persons['author'][0].last_names[0]).lower()
                            except :
                                lastNameOut = ""
                                
                            try:
                                firstName = unidecode.unidecode(entry.persons['author'][0].firstNames[0]).lower()
                            except :
                                firstName = ""
                                
                            try:
                                firstNameOut = unidecode.unidecode(entryOut.persons['author'][0].firstNames[0]).lower()
                            except :
                                firstNameOut = ""

                            if (lastname==lastNameOut or lastname==firstNameOut or lastNameOut==firstName):
                                oldEntry = entryOut
                                break


  
                if (oldEntry != None):
                    duplicates = duplicates + 1

                    if logProcess:
                        #cause;source;key;doi;author;year;title;publish
                        csvRemoved.writerow(['duplicate of next', bibFileName, entry.key, doi, author, year, title, publish])

                        doi = getEntryDOIStr(oldEntry)
                        author = getEntryAuthorStr(oldEntry)
                        year = getEntryYearStr(oldEntry)
                        title = getEntryTitleStr(oldEntry)
                        publish = getEntryPublishStr(oldEntry)
                        csvRemoved.writerow(['duplicate of prev', oldEntry.fields['source'], oldEntry.key, doi, author, year, title, publish])

                    bibDataOut.entries[oldEntry.key] = mergeEntry(oldEntry, entry)

                else:
                    while (key in bibDataOut.entries.keys()):
                        key = key +"_a"
                    bibDataOut.entries[key] = entry

    print("                                                     ")
    print("Total:\t\t", total)

    print("No Author:\t", withoutAuthor)
    print("No Year:\t", withoutYear)
    print("No Publisher:\t", withoutJornal)

    print("Duplicates:", duplicates, "| Merged:",mergedCont)
    print("Final:\t\t", len(bibDataOut.entries))


    withoutAbstractList = {i: 0 for i in fileList}
    withoutAbstract = 0 
    for entry in bibDataOut.entries.values():
        if logProcess:
            doi = getEntryDOIStr(entry)
            author = getEntryAuthorStr(entry)
            year = getEntryYearStr(entry)
            title = getEntryTitleStr(entry)
            publish = getEntryPublishStr(entry)
            abstract = getEntryAbstractStr(entry)

            #key;source;doi;author;year;title;publish;abstract
            csvFinal.writerow([entry.key, entry.fields['source'], doi, author, year, title, publish, abstract])

    #     if not 'abstract' in entry.fields:
    #         withoutAbstract = withoutAbstract + 1
    #         withoutAbstractList[entry.fields['source']] = withoutAbstractList[entry.fields['source']] + 1

    # print("without Abstract ", withoutAbstract, withoutAbstractList)

    bibDataOut.to_file(fileNamePathOut)

    if logProcess:
        fRemoved.close()
        fFinal.close()


#=============================================================================
# construct the argument parser and parse the arguments
# ap = argparse.ArgumentParser()
# ap.add_argument("-p", "--folderPath", required=True, help="Bib files folder path")
# ap.add_argument("-f", "--fileList", nargs='*', required=False, help='bib file name list, e.g. -files IEEE.bib ACM.bib science.bib Springer.bib')
# ap.add_argument("-o", "--fileNameOut", required=False, help="File name of merged file")
# ap.add_argument("-l", "--logProcess", required=False, help="Log processing to csv files", action='store_true')

# args = vars(ap.parse_args())

# print("--folderPath\t",args["folderPath"])
# print("--fileNameOut\t",args["fileNameOut"])
# print("--fileList\t",args["fileList"])
# print("--logProcess\t",args["logProcess"])

# run(args["folderPath"], args["fileList"], args["fileNameOut"], args["logProcess"])

#python BibFilesMerge.py -p "Revisao\resultados pesquisas" -o "MyFile.bib" -f IEEE.bib ACM.bib science.bib Springer.bib
    
#python BibFilesMerge.py -p "Revisao\resultados pesquisas" -f IEEE.bib ACM.bib science.bib Springer.bib -o "MyFile.bib" 

