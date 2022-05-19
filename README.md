# PyLitReview

## Quick Guide
- Install Selenium
- Download Chromdriver with same version as current Google Chrome installation
- Put info into config_template.py and rename to config.py
- Create keywords 
- usage: crawl(keywords, Library.library, SearchWhere.searchWhere)
  - keywords must be a list of lists of strings
  - library options: 
    - IEEE 
    - ACM 
    - ScienceDirect (Not working headless)
  - searchWhere options: 
    - Title 
    - TitleAbstract (Title OR Abstract - not working for ACM) 
    - Abstract 
    - Text (All)

## ToDos
- [x] Implement title+abstractsearch 
- [x] Update Sciencedirect crawler
