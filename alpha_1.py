import requests
import time
import os
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from datetime import datetime
import io
import wget

def get_list_urls():
	urls = ["www.stuff.co.nz",
			"www.rnz.co.nz",
			"www.nzherald.co.nz"]
	return urls 

urls = get_list_urls()


def full_screenshot(url, save_path):

	save_path = os.path.join("screenshots", save_path+".png")

	# print (save_path)
	# quit()
	chrome_options = webdriver.ChromeOptions()
	prefs = {"profile.default_content_setting_values.notifications" : 2}
	chrome_options.add_experimental_option("prefs",prefs)
	# chrome_options.add_argument('--headless')
	chrome_options.add_argument('--start-maximized')
	driver = webdriver.Chrome(chrome_options=chrome_options)
	driver.get(url)

	# initiate value
	img_li = [] # to store image fragment
	offset = 0 # where to start

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
	img_frame.save(save_path)
	driver.quit()

def make_warc(url, filename):

	# wget.download(url, filename, True)

	print (help(wget))

	quit()



while True:
	print ()
	print (datetime.now().strftime("%m-%d-%Y %H:%M:%S"))
	for url in urls:
		print (url)

	# 	__, fname, __ = url.split(".", 2) 
		if not url.startswith("htt"):
			url = "https://"+url 
		make_warc(url, "test.warc")

	# 	time_string = datetime.now().strftime("__%m-%d-%Y__%H-%M-%S") 

	# 	full_screenshot(url, fname+time_string)

	# 	with open(os.path.join("pages", fname+time_string+".html"), "w", encoding="utf8") as data:
	# 		data.write(requests.get(url).text)
		

	# time.sleep(60*5)
