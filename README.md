# Auto-Cotrans
A Tool used to Translate folders of images by bootstrapping [Cotrans](https://github.com/VoileLabs/cotrans) through Web Scraping via Selenium.

Cotrans options are currently hardcoded, commented appropriately -- in case it has to be changed (whether by users, or by myself in a foreseeable future).

## Requirements:
 - Selenium (pip install selenium)
 - Webdriver_Manager (pip install webdriver-manager)
 - Tqdm (pip install tqdm)
 - Chromedriver Autoinstaller (pip install chromedriver-autoinstaller) for a Compatible Chromedriver (https://googlechromelabs.github.io/chrome-for-testing/)

## Execution:
  - python script.py
  - In File-Explorer, Select the Input Folder
  - Afterwards, it will output to a 'TL' folder within the Input Folder Selected
