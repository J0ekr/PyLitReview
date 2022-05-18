# PyLitReview

## Quick Guide
- Install Selenium
- Download Chromdriver with same version as current Google Chrome installation
- Put info into config_template.py and rename to config.py
- Create keywords 
- usage: crawl(keywords, "Library", searchWhere)
  - Library options: 
    - "IEEE" 
    - "ACM" 
    - "ScienceDirect" (Not working headless)
  - searchWhere options: 
    - "tit" (Title only) 
    - "titAbs" (Title and Abstract) 
    - "text" (All)

## ToDos
- [x] Implement title+abstractsearch 
- [x] Update Sciencedirect crawler
