from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time

# Filepaths
import os
import glob
import tkinter as tk
from tkinter import filedialog

# Loading Bar
from tqdm import tqdm



# Function to rename translated files
def rename_file(ctr):
    # Rename
    dl_filepath = os.path.join(download_dir, "translation-[object Object].png")
    dl_newname = os.path.join(download_dir, f"{ctr}.png")
    # If the path already exists, find a 'ctr' such that it doesn't exist.
    while os.path.exists(dl_newname):
        ctr += 1
        dl_newname = os.path.join(download_dir, f"{ctr}.png")
    os.rename(dl_filepath, dl_newname)
    return (ctr)

# Function to Select Translation Folder: returns its path
def select_folder():
    root = tk.Tk()
    root.withdraw()
    
    folder_path = filedialog.askdirectory(title="Select a folder")
    return folder_path

# Function to get a list of all images
def get_image_files(folder_path):
    # Change directory to the specified folder
    os.chdir(folder_path)
    
    # Get a sorted list (alphanumeric) of all image files within the folder
    image_files = sorted(glob.glob("*.jpg") + glob.glob("*.jpeg") + glob.glob("*.png"))

    # Join with the folder path to get image file paths
    image_paths = [os.path.normpath(os.path.join(folder_path, image_file)) for image_file in image_files]

    return image_paths

# Function to create a 'TL' folder if it doesn't exist, in the input filepath
def dl_filepath(folder_path):
    dl_filepath = os.path.normpath(os.path.join(folder_path, "TL"))
    if not os.path.exists(dl_filepath):
        os.mkdir(dl_filepath)
    return(dl_filepath)

# Function to wait until a downloaded file appears before continuing
def wait_for_file_download(download_dir, timeout=60):
    start_time = time.time()
    filename = "translation-[object Object].png"
    while True:
        if filename in os.listdir(download_dir):
            return
        if time.time() - start_time > timeout:
            raise TimeoutError("Download Timed Out")
        time.sleep(1)

fname = 0

print("Selecting Input Path...")
folder_path = select_folder()
print(folder_path)

# Change this absolute path if you want to change the directory it downloads to
#print("Selecting Output Path...")
download_dir = dl_filepath(folder_path)

# Get image files from the specified folder
image_files = get_image_files(folder_path)
num_files = len(image_files)

# Configure Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless") 
#chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument(f"--download.default_directory={download_dir}")  # Set the download director

# Get the current directory's file-path and join it with chromedriver.exe to get its filepath
script_dir = os.path.dirname(os.path.realpath(__file__))
chromedr_path = os.path.join(script_dir, "chromedriver.exe")
service = Service(executable_path=chromedr_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

# Downloading through --headless Chromium
# Src: https://github.com/TheBrainFamily/chimpy/issues/108
driver.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
params = {'cmd': 'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': download_dir}}
command_result = driver.execute("send_command", params)

# Bootstrapping Online Web Translator through Selenium Scraping
# Src: https://github.com/VoileLabs/cotrans
driver.get('https://cotrans.touhou.ai//')
driver.implicitly_wait(10)

with tqdm(total=num_files, desc="Translating Files...") as lbar:
    # Iterate through all the images
    for ctr in range (0, len(image_files)):
        # Upload Image
        upload_file = driver.find_element(By.XPATH, '//*[@id="__nuxt"]/div[2]/div/div/label/input')
        upload_file.send_keys(image_files[ctr])

        # Cotrans saves the last utilized settings, so this only needs to be done once.
        # Currently, no method to change from what's implemented but can be done easily.
        if (ctr == 0):
            # ----------------------------- Language Selection ---------------------------------
            # Open Language Options
            options_lang = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="headlessui-listbox-button-1"]')))
            options_lang.click()
            time.sleep(0.2)
            # Wait for the options to be displayed
            options_container = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, 'headlessui-listbox-options-2')))
            # Select English
            # Find and Select the English option within the container
            english_option = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, './/li[.//span[text()="English"]]')))
            english_option.click()
            time.sleep(0.3)
            # ----------------------------------------------------------------------------------
            # ----------------------------- Detection Resolution -------------------------------
            # Open Language Options
            options_dres = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="headlessui-listbox-button-3"]')))
            options_dres.click()
            time.sleep(0.2)
            # Wait for the options to be displayed
            options_container = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, 'headlessui-listbox-options-4')))
            # Select English
            # Find and Select the English option within the container
            res_option = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, './/li[.//span[text()="2560px"]]')))
            res_option.click()
            time.sleep(0.3)
            # ----------------------------------------------------------------------------------
            # ----------------------------- Detector Selection ---------------------------------
            # Open Detector Settings
            options_detr = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="headlessui-listbox-button-5"]')))
            options_detr.click()
            time.sleep(0.2)
            # Wait for the options to be displayed
            options_container = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, 'headlessui-listbox-options-6')))
            # Go either Default Detector or Comic Detector (add a condition) --> Currently Comic Detector Only
            if True == False: 
                detr_option = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, './/li[.//span[text()="Default"]]')))
                detr_option.click()
            else:
                detr_option = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, './/li[.//span[text()="Comic Text Detector"]]')))
                detr_option.click()
            time.sleep(0.3)
            # ----------------------------------------------------------------------------------
            # ----------------------------- Direction Selection --------------------------------
            # Open Text Direction Settings
            options_dirn = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="headlessui-listbox-button-7"]')))
            options_dirn.click()
            time.sleep(0.2)
            # Wait for the options to be displayed
            options_container = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, 'headlessui-listbox-options-8')))
            # Follow either Language or Image (add a condition) --> currently Follow Image Only
            if True == False: 
                dir_option = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, './/li[.//span[text()="Follow language"]]')))
                dir_option.click()
            else:
                dir_option = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, './/li[.//span[text()="Follow image"]]')))
                dir_option.click()
            time.sleep(0.3)
            # ----------------------------------------------------------------------------------
            # ----------------------------- Translator Selection -------------------------------
            # Open Text Direction Settings
            options_tl = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="headlessui-listbox-button-9"]')))
            options_tl.click()
            time.sleep(0.2)
            # Wait for the options to be displayed
            options_container = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, 'headlessui-listbox-options-10')))
            # Go either GPT-3.5 or DeepL (add a condition) --> Currently GPT-3.5 Only
            if True: 
                tl_option = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, './/li[.//span[text()="GPT-3.5"]]')))
                #tl_option = options_container.find_element(By.XPATH, './/li[.//span[text()="GPT-3.5"]]')
                tl_option.click()
            else:
                tl_option = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, './/li[.//span[text()="DeepL"]]')))
                #tl_option = options_container.find_element(By.XPATH, './/li[.//span[text()="DeepL"]]')
                tl_option.click()
            # ----------------------------------------------------------------------------------
        time.sleep(0.3)
        # Translate
        #print("Translate Clicked")
        translate_file = driver.find_element(By.XPATH, '//*[@id="__nuxt"]/div[2]/div/div/label/div/div/div[2]/button')
        translate_file.click()

        # Download
        #print("Download Clicked")
        dl_file = WebDriverWait(driver, 360).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="__nuxt"]/div[2]/div/div/label/div/div/div/button[1]')))
        dl_file.click()

        # Wait for Download to Finish
        wait_for_file_download(download_dir)
        # Rename the File
        fname = rename_file(fname)
        
        # Update Loading Bar
        lbar.update(1)

        # Return back to main page to translate the next image
        #print("Next Clicked")
        Next = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="__nuxt"]/div[2]/div/div/label/div/div/div/button[2]')))
        Next.click()
        time.sleep(0.2)