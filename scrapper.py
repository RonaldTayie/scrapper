from genericpath import exists
import json
from pydoc import HTMLDoc
from bs4 import BeautifulSoup
import bs4
import requests
import os
import io

# url : ufseed.com
# data: all on seeds


'''
	Step 1:
	Get the links from the header by category and pull the links

	Step 2:
	visit the links and pull all the data based on the size of the set present or accessible

	Step 3:
	Store the RAW (HTML) data in an array after pulling the section that hold the data (The Row).

	Set 4:
	Go through the content and pull each item while adding to a schema or model.


	SETUP
'''

# get header links
# There are two approaches to this:
# 1. read the all section of the page
# 2. pull each link in the header section or category pull the associated or related items.

'''

	SCHEMA 

	# To be pulled from target header section
	Plant type
	{
		name: plant type name,
		description: plant type description 
	}

	#  plant
	{
		name: seedName,
		plantType: plantType # e.g [... Vegetable, Herd],
		image: seed/plant image,
		description: seed/plant description,
		link: description page link,
	}
	# plant comprehensive
	For this section I will have to pull the "Product details" section and pull the data avalilable and turn it to json as it is variable to most or every plant. The DB schema will have to be set such that it's size and collumns are set to be the same as those of the most detailed or biggest insttence of the "Product details" section.

'''

target = 'https://ufseeds.com'

BASE_DIR = os.path.join(__file__,'json')

'''
	header structure 
	{
		name: string,
		all_link: string,
		sub_headers: [
		 ...{
		 		name: string,
		 		full_link: string
			}
		]
	}
'''
headers = []
Header_items = []
final_shape = {}

def load_headers():
	page = BeautifulSoup(requests.get(target).text,'html.parser')
	raw_header = page.find_all('li',class_="nav-item")
	raw_header.pop()
	raw_header.pop()
	raw_header.pop()
	for section in raw_header:
		header = {}
		# select the first child "<a>"
		title = section.find('a',class_="nav-link")
		all_link = target + title['href']
		header['title'] =  title.string
		header['all_link'] = all_link
		#  get header section items
		raw_items_section = section.find('ul',class_="dropdown-list",role="menu")
		raw_items = raw_items_section.find_all('li',class_="dropdown-item")
		header_items = []
		for raw_item in raw_items:
			tmp_item = {}
			item = raw_item.find('a')
			tmp_item['name']= item.string
			tmp_item['full_link'] = target + item['href']
			header_items.append(tmp_item)
		header['items'] = header_items
		# get content Size
		page = BeautifulSoup( requests.get(all_link+'?start=0&sz=1').text,'html.parser')
		raw_size = page.find('div',class_='range-of-page-footer').text
		size_num_text = raw_size.split("of")[1].strip()
		
		if len(size_num_text)>3:
			s1,s2 = size_num_text.split(",")
			size = int(s1+s2)
			
		else:
			size = int(size_num_text)
		header['content_size'] = size
		headers.append(header)

def write_headers_to_file():
	with open('./json/headers.json','w') as data:
		data.write( json.dumps(headers))

#  decision was made to preserve the obtained structure of the headers but use the full link to get the data
def load_header_data():
	# Read from created Json File
	'''
	[
		"category":
	]
	'''
	DOM_Objects = []
	print("\t Reading Site Objects ...")
	print("\t Reading Header Destinations")
	for header in headers:
		category_seeds = {}
		link = header['all_link'] + '?start=0&sz='+str(header['content_size'])
		page = BeautifulSoup(requests.get(link).text,'html.parser')
		products = page.find_all('div',class_='product')
		category_seeds['title'] = header['title']
		product_maps = []
		for product in products:
			p = {}
			p['image'] = product.find('img',class_="tile-image")['src']
			product_tag = product.find('a',class_="link")
			p['link'] = product_tag['href']
			p['name'] = product_tag.text
			p['description'] = product.find('p',class_="text-muted").text.strip()
			product_maps.append(p)
		category_seeds['products'] = product_maps
		DOM_Objects.append(category_seeds)
	DOM  = {}
	DOM["DOM"] = DOM_Objects
	Header_items = DOM
	with open('./json/all_products.json','w') as data:
		data.write( json.dumps(DOM))

if exists('./json/headers.json'):
	print('\t Header file Found')
	headers = json.load(open('./json/headers.json','r'))
	print('\t Headers Ready...')
else:
	print('\t Header file NOT  Found.')
	print('\t Fetching DATA')
	load_headers()
	write_headers_to_file()
	print('\t Data fetched..')
	print('\t Header File Created.')
	print('\t Headers Ready...')

if exists('./json/all_products.json'):
	Header_items = json.load( open('./json/all_products.json','r') )
else:
	load_header_data()

# Go to each and every page in the Header_lists, pull the data

'''
{
	"Vegetables":[
	  ..{
		  	name:ProductName,
			group:productGroup,
			type: productType,
			image: productImage,
			description: productFullDescription,
			detailsMap: {
				product DetailsMAP
			}

		}
	]
}
'''

def request_item_data():
	full_products = {}
	if Header_items:
		print("\t Headers found")
		DOM = Header_items['DOM']
		print("\t Loaded into memory.\t")
		print("-"*20)
		DetailedList = []
		for group in DOM:
			group_products = group['products']
			detailed_group = {}
			detailed_group['name'] = group['title']
			detailed_group_items = []
			for product in group_products:
				page_link = target + product['link']
				page = BeautifulSoup( requests.get(page_link).text,'html.parser')
				detailed_product = {}
				detailed_product['name'] = page.find('h1',class_="product-name").text.strip()
				detailed_product['group'] = detailed_group['name']
				detailed_product['type'] = page.find('p',class_="product-category").text.strip()
				detailed_product['description'] = product['description']
				detailed_product['image'] = product['image']
				detail_section = page.find('div',id="collapsible-attributes-1")
				# there are two rows and we want the last one
				row = detail_section.contents[1]
				values = row.find_all('div',class_='attribute-values')
				valueMap = {}
				for value in values:
					valueMap[str(value.find('p').text.strip()).strip()] = value.find('strong').text.strip()
				detailed_product['deatils'] = valueMap
				detailed_group_items.append(detailed_product)
			detailed_group['items'] = detailed_group_items
			DetailedList.append(detailed_group)
		# Write the final shape by appeending all the data to the dictionalr and dumping it to a JSON file
		final_shape['data'] = DetailedList
		# FINALLY DUMP THE DATA TO A JSON FILE
		with open('./json/FINAL.json','w') as data:
			data.write( json.dumps(final_shape) )

request_item_data()