import requests
import time
import os
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from datetime import datetime
import io
import pyautogui
import zipfile
import logging
import shutil

storage_root = "harvests"

def get_storage_folders(title, time_string):
	day =  datetime.now().strftime("%m-%d-%Y") 
	save_path = os.path.join(storage_root, title, day, time_string)
	if not os.path.exists(save_path):
		os.makedirs(save_path)
	return save_path

def zip_paths(paths):
	"""
	Compresses directories and files to a single zip file.
	
	Returns the zip file as a data stream, None if error.
	"""
	# Check single path vs. multiple
	if isinstance(paths, str):
		paths = (paths,)

	# Filter out non-existent paths
	paths = [x for x in paths if os.path.exists(x)]

	# Make sure the zip file will actually contain something
	if not paths:
		logging.warning("No files/folders to add, not creating zip file")
		return None

	logging.debug("Creating zip file")
	zip_stream = io.BytesIO()
	try:
		zfile = zipfile.ZipFile(zip_stream, 'w', compression=zipfile.ZIP_DEFLATED)
	except EnvironmentError as e:
		logging.warning("Couldn't create zip file")
		return None

	for path in paths:
		if os.path.isdir(path):
			root_len = len(os.path.abspath(path))

			# If compressing multiple things, preserve the top-level folder names
			if len(paths) > 1:
				root_len -= len(os.path.basename(path)) + len(os.sep)

			# Walk through the directory, adding all files
			for root, dirs, files in os.walk(path):
				archive_root = os.path.abspath(root)[root_len:]
				for f in files:
					fullpath = os.path.join(root, f)
					archive_name = os.path.join(archive_root, f)
					try:
						zfile.write(fullpath, archive_name, zipfile.ZIP_DEFLATED)
					except EnvironmentError as e:
						logging.warning("Couldn't add file: %s", (str(e),))
		else:
			# Exists and not a directory, assume a file
			try:
				zfile.write(path, os.path.basename(path), zipfile.ZIP_DEFLATED)
			except EnvironmentError as e:
				logging.warning("Couldn't add file: %s", (str(e),))
	zfile.close()
	zip_stream.seek(0)
	return zip_stream

def cleanup():
	try:
		os.remove(os.path.join(download_location, "index.html"))
	except FileNotFoundError:
		pass

	try:
		os.remove(os.path.join(download_location, "index.html.html"))
	except FileNotFoundError:
		pass

	try:
		shutil.rmtree(os.path.join(download_location, "index_files"))
	except FileNotFoundError:
		pass

	try:
		shutil.rmtree(os.path.join(download_location, "index_files.html"))
	except FileNotFoundError:
		pass

def snag_page(driver, save_path):
	cleanup()
	driver.maximize_window() 
	time.sleep(2)
	pyautogui.hotkey('ctrl', 's')
	time.sleep(1)
	driver.maximize_window() 
	pyautogui.typewrite('index.html')
	time.sleep(2)
	pyautogui.hotkey('enter')
	while not os.path.exists(os.path.join(download_location, 'index.html')):
		time.sleep(1)
	my_zip_stream = zip_paths([os.path.join(download_location, "index_files"), os.path.join(download_location, 'index.html')])
	with open(os.path.join(save_path, "index.zip"), "wb") as data:
		data.write(my_zip_stream.getbuffer())
	cleanup()
	return

def full_screenshot(driver, save_path):
	save_path = os.path.join(save_path, "screenshot.png")
	# initiate value
	img_li = [] # to store image fragment
	offset = 0 # where to start
	time.sleep(3)
	# js to get height
	height = driver.execute_script('return Math.max('
	                               'document.documentElement.clientHeight, window.innerHeight);')
	# js to get the maximum scroll height
	# Ref--> https://stackoverflow.com/questions/17688595/finding-the-maximum-scroll-position-of-a-page
	max_window_height = driver.execute_script('return Math.max('
	                                          'document.body.scrollHeight, '
	                                          'document.body.offsetHeight, '
	                                          'document.documentElement.clientHeight, '
	                                          'document.documentElement.scrollHeight, '
	                                          'document.documentElement.offsetHeight);')

	# looping from top to bottom, append to img list
	# Ref--> https://gist.github.com/fabtho/13e4a2e7cfbfde671b8fa81bbe9359fb
	while offset < max_window_height:
	    # Scroll to height
	    driver.execute_script(f'window.scrollTo(0, {offset});')
	    img = Image.open(io.BytesIO((driver.get_screenshot_as_png())))
	    img_li.append(img)
	    offset += height

	# Stitch image into one
	# Set up the full screen frame
	box = (0, height - height * (max_window_height / height - max_window_height // height), img_li[-1].size[0], img_li[-1].size[1])
	img_li[-1] = img_li[-1].crop(box)
	img_frame_height = sum([img_frag.size[1] for img_frag in img_li])
	img_frame = Image.new('RGB', (img_li[0].size[0], img_frame_height))
	offset = 0
	for img_frag in img_li:
	    img_frame.paste(img_frag, (0, offset))
	    offset += img_frag.size[1]

	try:
		img_frame.save(save_path)
	except AttributeError:
		print ("Network issue - gave_up")
		# time.sleep(120)

def get_list_urls():
	with open("urls.txt") as data:
		return [x for x in data.read().split('\n') if x != ""] 

urls = get_list_urls()

def make_selenium_session(url, save_path):
	chrome_options = webdriver.ChromeOptions()
	prefs = {"profile.default_content_setting_values.notifications" : 2}
	chrome_options.add_experimental_option("prefs",prefs)
	chrome_options.add_argument('--start-maximized')
	driver = webdriver.Chrome(options=chrome_options)
	driver.get(url)
	snag_page(driver, save_path)
	full_screenshot(driver, save_path)
	driver.quit()

download_location = r"C:\Users\small_dog\Downloads"


pause_between_harvests_in_minutes = 15

while True:
	print ()
	print (datetime.now().strftime("%m-%d-%Y %H:%M:%S"))
	for url in urls:
		print (url)
		save_name = url.replace("https://", "").replace("www.", "")
		save_name = save_name.replace("/", "_").replace(".", "-")
		if not url.startswith("htt"):
			url = "https://"+url 
		time_string = datetime.now().strftime("%H-%M-%S") 
		save_path = get_storage_folders(save_name, time_string)
		make_selenium_session(url, save_path)
		
	time.sleep(60*pause_between_harvests_in_minutes)
