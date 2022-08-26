from scraper.Scraper import Scraper

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.wait import WebDriverWait
import time
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import uuid 
import pandas as pd
from pandas import json_normalize

class JlScraper(Scraper):
        

    def _get_product_id(self, xpath:str = '//jl-store-stock')->str:
        name = self._find_element(xpath)
        product_id = name.get_attribute('skuid')
        return product_id
    
    # FIXME: only certain categories of products are fine
    def _get_product_name(self,xpath:str = '//div[@class="xs-up"]//*[@class="ProductTitle_title__JiefQ"]')->str:
        productName=self._find_element(xpath)
        return productName.text


    def _get_product_rating(self, xpath:str ='//span[@data-test="rating"]')->str:    
        # get rating - some products' rating is not availabe so try is used.
        
        rating = ''
        try:
            productRating=WebDriverWait(self.driver,self.delay).until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
            rating=productRating[1].text
        
        except TimeoutException: 
            rating='no rating available'
        
        return rating

    # FIXME: only certain categories of products are fine
    # different size has different availability and price so the below is created in one method
    def _get_product_size_availability_price_list(self,xpath:str ='//button[@data-cy="size-selector-item"]')->list: 
        
        
        size_list = WebDriverWait(self.driver,self.delay).until(EC.presence_of_all_elements_located((By.XPATH, xpath)))

        size_availability_price=[]

        for size in size_list:
            temp_list=[]
            
            try:
                size.click()
                time.sleep(0.5)
                
            except Exception as e: 
                print(f'cannot click {size_list.index(size)}')
                print(e.args)
            
            # the attribute 'aria-label' of size is in the format like '4. This size is selected' if available or ' 8. This size is selected but unavailable'
            # split is used to get separated information of size and whether it is available
            size.get_attribute('aria-label').split('.')[0]
            temp_list.append(size.get_attribute('aria-label').split('.')[0])

            if 'unavailable' in size.get_attribute('aria-label').split('.')[1]:
                temp_list.append('unavailable')
            else: 
                temp_list.append('available')
            
            temp_list.append(self._get_product_price_history())


            size_availability_price.append(temp_list)

        return size_availability_price
   
    def _get_product_src(self,xpath:str='//*[@class="ImageMagnifier_image-wrapper__GhoSr"]')->list: 
        # get src of the images of the product 
        src_elements = WebDriverWait(self.driver,self.delay).until(EC.presence_of_all_elements_located((By.XPATH, xpath)))

        product_src_list=[]
        for i in src_elements:
            src = i.find_element(By.CSS_SELECTOR,'img')
            product_src_list.append(src.get_attribute('src'))
        
        return product_src_list
    
    # # FIXME: only certain categories of products are fine

    def _get_product_price_history(self,xpath:str='//span[@class="ProductPrice_prices-list__jbkRS"]')->str:
        
        price_elements =self.driver.find_elements(By.XPATH,xpath)
        return price_elements[1].text

    def create_prodcut_dic(self,url:str)->dict:

        """this method is to create a python dictionary to save the id, name, rating, size and price, src links of a product"""

        self._get_driver(url)

        product_info_dic = {'uuid':str(uuid.uuid4()), 'product id': '', 'product name': '', 'product rating': '', 'available size and price':[], 'src links':[]}
        
        product_info_dic['product id']=self._get_product_id()
        product_info_dic['product name']=self._get_product_name()
        product_info_dic['product rating'] = self._get_product_rating()
        product_info_dic['available size and price']=self._get_product_size_availability_price_list()
        product_info_dic['src links'] = self._get_product_src()

        return product_info_dic

    def save_product_info(self,product_info_dic:dict):

        """this method is to save the production information and pictures in a local folder"""

        raw_data_folder_path= self._create_folder('raw data', '/Users/shubosun/Desktop/Data_Collection')
        product_folder_path = self._create_folder(product_info_dic['product id'],raw_data_folder_path)
        
        for src_link in product_info_dic['src links']:
            # need to find the local path to save image but currently downloading is fine
            name=product_info_dic['product id']+'_'+str(product_info_dic['src links'].index(src_link))
            self._download_image_locally(src_link, name ,product_folder_path)
        
        self._save_dic_in_json(product_info_dic, product_info_dic['product id'],product_folder_path)
        # df=pd.DataFrame.from_dict(product_info_dic, orient='index')
        # df=json_normalize(product_info_dic)
        