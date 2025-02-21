from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import requests
import html5lib
import json
import logging
logging.basicConfig(filename="app.log",
                    encoding='utf-8',
                    format="{asctime} - {levelname} - {message}",
                    filemode='a',
                    style="{",
                    datefmt="%Y-%m-%d %H:%M")
logger = logging.getLogger()

class ExtractPokemonStrategyData:
    def __init__(self,save_filename,html_filename,url):
        self.save_filename = save_filename
        self.html_filename = html_filename
        self.url = url
        self.data_dict = {"pokemon":"",
                          "gen":"",
                          "tier":"",
                          "attrs":{"strategy_names":[],
                                   "moves":[],
                                   "items":[],
                                   "abilities":[],
                                   "natures":[],
                                   "evs":[],
                                   "ivs":[],
                                   "tera_types":[],
                                   "strategy_descriptions":[]}}

    def load_data(self):
        logger.info("Loading HTML data from file...")
        try:
            with open(self.html_filename,'r') as h:
                soup = BeautifulSoup(h.read(),'html5lib')
        except FileNotFoundError as f:
            logger.error(f"{f} not found")
            soup = None
        except Exception as e:
            logger.error(f"{e} occured.")
            soup = None

        if not soup:
            logger.info("Using BeatifulSoup to extract data from web")
            driver = webdriver.Chrome(ChromeDriverManager().install())

            driver.get(self.url)
            soup = BeautifulSoup(driver.page_source,'html5lib')
            driver.quit()

            logger.info("Saving data into a file...")
            with open(self.html_filename,'w') as h:
                h.write(soup.prettify())

        return soup

    def extract_moves_info(self,moves_info):
        for move_info in moves_info:
            moves_data = move_info.find_all('tr',{'data-reactid':True})
            moves_list = []
            for move_data in moves_data:
                move = move_data.find_all('a',class_="MoveLink")
                if move:
                    move_str = "/".join([m.get_text().strip() for m in move])
                    moves_list.append(move_str)
            self.data_dict["attrs"]["moves"].append(moves_list)

    def extract_misc_info(self,misc_info):
        for info in misc_info:
            misc_element = info.find_all('tr',{'data-reactid':True})

            # Extract Items data from misc_element (Corresponds to index 0)
            items_element = misc_element[0].find_all('a',class_="ItemLink")
            item_str = "/".join([item.find_all('span',{'data-reactid':True})[4].get_text().strip() for item in items_element])
            self.data_dict["attrs"]["items"].append(item_str)

            # Extract Abilities data from misc_element (Corresponds to index 1)
            abilities_element = misc_element[1].find_all('a',class_="AbilityLink")
            ability_str = "/".join([ability.find_all('span',{'data-reactid':True})[0].get_text().strip() for ability in abilities_element])
            self.data_dict["attrs"]["abilities"].append(ability_str)

            # Extract Natures data from misc_element (Corresponds to index 2)
            natures_element = misc_element[2].find_all('ul',class_="NatureList")
            nature_str = "/".join([nature.find_all('abbr',{'data-reactid':True})[0].get_text().strip() for nature in natures_element])
            self.data_dict["attrs"]["natures"].append(nature_str)

            # Extract EVs data from misc_element (Corresponds to index 3)
            evs_list = []
            evs_element = misc_element[3].find_all('ul',class_="evconfig")
            for ev_element in evs_element:
                ev_str = "/".join([evs.get_text().strip() for evs in ev_element.find_all('li',{'data-reactid':True})])
                evs_list.append(ev_str)
            self.data_dict["attrs"]["evs"].append(evs_list)
            
            # Extract IVs data from misc_element (Corresponds to index 4 (if exists))
            ivs_element = misc_element[4].find_all('ul',class_="ivconfig")
            iv_str = "/".join([iv_element.get_text().strip() for iv_element in ivs_element])
            self.data_dict["attrs"]["ivs"].append(iv_str)

            # Extract Tera type data from misc_element (Corresponds to index 4/5)
            if iv_str:
                teratypes_element = misc_element[5].find_all('ul',class_="TypeList")
            else:
                teratypes_element = misc_element[4].find_all('ul',class_="TypeList")
            teratype_str ="/".join([teratype_element.get_text().strip() for teratype_element in teratypes_element[0].find_all('a')])
            self.data_dict["attrs"]["tera_types"].append(teratype_str)

    def extract_strategy_description(self,strategy_data):
        desc_list = []
        desc_sec_data = strategy_data.find_all('section',{'data-reactid':True})
        for desc_data in desc_sec_data:
            paras = desc_data.find_all('p')
            desc = " ".join([line.get_text().strip() for para in paras for line in para])
            desc_list.append(desc)
        self.data_dict['attrs']['strategy_descriptions'] = desc_list

    # Extracts Strategies section from the web page for each Pokemon
    def extract_data(self):
        soup = self.load_data()
        title_data = soup.find_all('title')[0].get_text().strip().split(" | ")

        # Extract Pokemon Name
        self.data_dict["pokemon"] = title_data[0]

        logger.info(f"Extracting data for {title_data[0]}")

        # Extract Pokemon Generation
        self.data_dict['gen'] = title_data[1]

        # Extract Strategy Tier
        self.data_dict['tier'] = soup.find_all('div',class_="PokemonPage-StrategySelector")[0].find_all('span',class_="is-selected")[0].get_text().strip()
        
        strategy_data = soup.find('div',attrs={"data-reactid":".0.1.1.2.6.0.2.0"})

        # Extract Strategy Names
        strategy_name_elements = strategy_data.find_all('h3',attrs={"data-reactid":True})
        self.data_dict["attrs"]["strategy_names"] = [element.get_text().strip() for element in strategy_name_elements if "Credits" not in element.get_text()]

        strategies = strategy_data.find_all('div',class_="MovesetInfo")
        for strategy in strategies:

            # Extract Move Data
            moves_info = strategy.find_all('div',class_="MovesetInfo-moves")
            self.extract_moves_info(moves_info)
            
            # Extract Misc Data
            misc_info = strategy.find_all('div',class_="MovesetInfo-misc")
            self.extract_misc_info(misc_info)

            # Extract Strategy Descriptions
            self.extract_strategy_description(strategy_data)

            # #Save to JSON
            self.save_data_to_json(self.save_filename)

    def save_data_to_json(self,filename):
        with open(filename,'a') as json_file:
            json.dump(self.data_dict,json_file,indent=4)

if __name__=="__main__":
    save_filename = "PokemonStrategyData.json"
    html_filename = "dragonite-ou-sv.html"
    # html_filename = r"C:\Users\shash\Downloads\Raging Bolt _ SV _ Smogon Strategy Pokedex.html"
    # html_filename = r"C:\Users\shash\Downloads\Gliscor _ SV _ Smogon Strategy Pokedex.html"

    url = "https://www.smogon.com/dex/sv/pokemon/dragonite"

    obj = ExtractPokemonStrategyData(save_filename,html_filename,url)
    obj.extract_data()