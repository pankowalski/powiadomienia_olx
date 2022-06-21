# Biblioteki
import traceback
import os
# from pyvirtualdisplay import Display # Ma na celu możliwe nieużywanie na serwerze opcji --headless (minimalizacja wykrycia bota) (firefox)
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.firefox.options import Options (niestety nie obsługuje action chains)
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
# from webdriver_manager.firefox import GeckoDriverManager (niestety nie obsługuje action chains)
from time import sleep
from datetime import date, datetime, time, timedelta
import pandas as pd
from bs4 import BeautifulSoup
import re
import yagmail as yg

# os.environ['GH_TOKEN'] = '{GitHub Token}' # Używane dla firefoxa

# Dane do wysyłki maila przy użyciu yagmail
sender = 'twoj_email@gmail.com'
password = 'password' # Gmail app password. Lepiej przechowywać w innej formie niż string - do poprawy

miasto = 'warszawa' # Jeżeli takie samo wyszukiwanie chcę się wykonać dla różnych miast to można ustalić jako zmienną

# Link do przeszukania (mieszkania, wynajem, tylko ze zdjęciami, 1000 <= cena <= 2600, umeblowane, od 35mkw, 1-3 pokoje)
link = 'https://www.olx.pl/d/nieruchomosci/mieszkania/wynajem/' + miasto + '/?search%5Bphotos%5D=1&search%5Border%5D=created_at:desc&search%5Bfilter_float_price:from%5D=1000&search%5Bfilter_float_price:to%5D=2600&search%5Bfilter_enum_furniture%5D%5B0%5D=yes&search%5Bfilter_float_m:from%5D=35&search%5Bfilter_enum_rooms%5D%5B0%5D=two&search%5Bfilter_enum_rooms%5D%5B1%5D=three'

# Przygotowanie 'opakowań' do zbierania ogłoszeń - słownik i ramka danych do której każde ogłoszenie (zmienne w słowniku) będzie dopisywane
ogloszenie_zmienne = ['czas_dodania_ogloszenia',
                      'lokalizacja',
                      'tytul',
                      'powierzchnia',
                      'liczba_pokoi',
                      'cena',
                      'oplaty_dodatkowe',
                      'link']

ogloszenie_dict = {key: None for key in ogloszenie_zmienne}
wszystkie_ogloszenia = pd.DataFrame()

# Zmienne czasu
teraz = datetime.now()
teraz_str = teraz.strftime('%Y-%m-%d %H:%M:%S')
ostatnie_pol_godziny = teraz - timedelta(hours = 0, minutes = 33)
ostatnie_pol_godziny_str = ostatnie_pol_godziny.strftime('%Y-%m-%d %H:%M:%S')

# Opcje ustawień przeglądarki chrome
options = Options()
options.add_argument('--disable-notifications')
options.add_argument('--headless') # Tej opcji najlepiej nie wykorzystywać, wzrasta ryzyko wykrycia bota ale na ten moment nie mam lepszego rozwiązania
options.add_argument('--no-sandbox')
options.add_argument('--disable-blink-features=AutomationControlled')
# user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'
# options.add_argument(f'user-agent={user_agent}')



# display = Display(visible = 0, size = (1920, 1080))
# display.start()
try:
    # driver = webdriver.Firefox(executable_path = GeckoDriverManager().install(), options = options)
    driver = webdriver.Chrome(ChromeDriverManager().install(), options = options)
    # driver.maximize_window()

    driver.get(link) # Otwórz link
    
    try:
        cookies = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//button[@id="onetrust-accept-btn-handler"]'))).click() #Akceptuj ciasteczka
    except:
        pass

    sleep(5)

    ogloszenia = driver.find_elements(By.CLASS_NAME, 'css-19ucd76') # Znajdź wszystkie ogłoszenia
    sleep(3)

    counter = 1
    counter_stare_ogloszenia = 0
    counter_otodom = 0
    for ogloszenie in ogloszenia:
        ogloszenie_dict_temp = ogloszenie_dict
        try:
            lokalizacja_i_data = ogloszenie.find_element(By.CLASS_NAME, 'css-p6wsjo-Text.eu5v0x0').text.strip()
            r = re.split(' - ', lokalizacja_i_data)
            lokalizacja = r[0]
            data = r[1]
            sleep(2)

            ogloszenie_dict_temp['czas_dodania_ogloszenia'] = data
            ogloszenie_dict_temp['lokalizacja'] = lokalizacja
        
            if data.find('Dzisiaj') != -1: # Proceduj tylko dla dzisiejszych ogłoszeń. Skrócić jeszcze proces tylko dla ogłoszeń z ostatnich x minut/godzin -> przyspieszenie algorytmu
                counter_stare_ogloszenia = 0
                try:
                    tytul = ogloszenie.find_element(By.CLASS_NAME, 'css-v3vynn-Text.eu5v0x0').text.strip()
                    ogloszenie_dict_temp['tytul'] = tytul
                except:
                    print('tytul_error')
                    error_message = traceback.format_exc()
                    print(error_message)
    #             try:
    #                 cena = ogloszenie.find_element(By.CLASS_NAME, 'css-wpfvmn-Text.eu5v0x0').text.strip() # Nie wiem dlaczego ale przy opcji --headless, algorytm nie scrapuje ceny. Work-around, to scrapowanie ceny z otwartego ogłoszenia (dalej w kodzie)
    #                 ogloszenie_dict_temp['cena'] = cena
    #             except:
    #                 pass
                try:
                    powierzchnia = ogloszenie.find_element(By.CLASS_NAME, 'css-1bhbxl1-Text.eu5v0x0').text.strip()
                    ogloszenie_dict_temp['powierzchnia'] = powierzchnia
                except:
                    print('powierzchnia_error')
                    error_message = traceback.format_exc()
                    print(error_message)
                
                try:
                    klik = ogloszenie.find_element(By.CLASS_NAME, 'css-1bbgabe')
                    ActionChains(driver).key_down(Keys.CONTROL).click(klik).key_up(Keys.CONTROL).perform()
                    sleep(3)
                    driver.switch_to.window(driver.window_handles[1])
                    sleep(5)
                
                    link = driver.current_url
                    ogloszenie_dict_temp['link'] = link
                    
                    czy_olx = driver.title
                except:
                    print('klik_error')
                    error_message = traceback.format_exc()
                    print(error_message)                    
                    czy_olx = '' # Jeżeli kliknięcie nie wyjdzie, to załóż czy_olx = '', czyli kolejny if idzie od razu do else

                if re.search("olx", czy_olx, re.IGNORECASE):
                    try:
                        szczegolowe_informacje_lista = []
                        for i in driver.find_elements(By.CLASS_NAME, 'css-xl6fe0-Text.eu5v0x0'):
                            szczegolowa_informacja = i.text.strip()
                            szczegolowe_informacje_lista.append(szczegolowa_informacja)                

                        r = re.compile('liczba pokoi', re.IGNORECASE)
                        liczba_pokoi = list(filter(r.search, szczegolowe_informacje_lista))[0]
                        ogloszenie_dict_temp['liczba_pokoi'] = liczba_pokoi

                        r = re.compile('czynsz', re.IGNORECASE)
                        oplaty_dodatkowe = list(filter(r.search, szczegolowe_informacje_lista))[0]
                        ogloszenie_dict_temp['oplaty_dodatkowe'] = oplaty_dodatkowe
                        
                        cena = driver.find_element(By.CLASS_NAME, 'css-okktvh-Text.eu5v0x0').text.strip() # Scrap ceny z ogłoszenia jako work-around, jak wspomniane wcześniej
                        ogloszenie_dict_temp['cena'] = cena
                    except:
                        print('elementy_ogloszenia_olx_error')
                        error_message = traceback.format_exc()
                        print(error_message)    
                    
                    wszystkie_ogloszenia = wszystkie_ogloszenia.append(ogloszenie_dict_temp, ignore_index=True)
                    print('Ogloszenie ' + str(counter) + ' dodano do listy')

                    driver.close()
                    sleep(3)
                    driver.switch_to.window(driver.window_handles[0])
                    sleep(3)

                elif re.search("otodom", czy_olx, re.IGNORECASE):
                    counter_otodom += 1
                    if counter_otodom == 1:
                        try:
                            cookies = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//button[@id="onetrust-accept-btn-handler"]'))).click()
                        except:
                            pass
                    else:
                        pass

                    soup = BeautifulSoup(driver.page_source, "html.parser") # Dla nauki, w tym przypadku skorzystałem z BeatifulSoup
                    try:
                        for i in soup.find_all("div", class_ = "css-1ccovha estckra9"):
                            element_text = i.find("div", class_ = "css-1h52dri estckra7").text.strip()
                            if re.search('liczba pokoi', element_text, re.IGNORECASE):
                                    element_value = i.find("div", class_ = "css-1wi2w6s estckra5").text.strip()
                                    ogloszenie_dict_temp['liczba_pokoi'] = element_value
                            elif re.search('czynsz', element_text, re.IGNORECASE):
                                    element_value = i.find("div", class_ = "css-1wi2w6s estckra5").text.strip()
                                    ogloszenie_dict_temp['oplaty_dodatkowe'] = element_value
                            else:
                                pass
                        cena = soup.find("strong", class_ = "css-8qi9av eu6swcv19").text.strip() # Scrap ceny z ogłoszenia jako work-around, jak wspomniane wcześniej
                        ogloszenie_dict_temp['cena'] = cena
                    except:
                        print('elementy_ogloszenia_otodom_error')
                        error_message = traceback.format_exc()
                        print(error_message) 

                    wszystkie_ogloszenia = wszystkie_ogloszenia.append(ogloszenie_dict_temp, ignore_index=True)
                    print('Ogloszenie ' + str(counter) + ' dodano do listy')

                    driver.close()
                    sleep(3)
                    driver.switch_to.window(driver.window_handles[0])
                    sleep(3)
                
                else:
                    wszystkie_ogloszenia = wszystkie_ogloszenia.append(ogloszenie_dict_temp, ignore_index=True)
                    print('Ogloszenie ' + str(counter) + ' dodano do listy')
                    
                    driver.switch_to.window(driver.window_handles[0])
                    sleep(3)
                
            else:
                print('Ogloszenie ' + str(counter) + ' nie jest z dzisiaj')
                counter_stare_ogloszenia += 1 
                
        except:
            print('Brak podstawowych informacji dla obiektu ' + str(counter))
            error_message = traceback.format_exc()
            print(error_message)
            sleep(3)
            driver.switch_to.window(driver.window_handles[0])
            sleep(3)
            try:
                driver.switch_to.window(driver.window_handles[1])
                sleep(3)
                driver.close()
                sleep(3)
                driver.switch_to.window(driver.window_handles[0])
                sleep(3)
            except:
                pass
        
        counter += 1
    #    if counter == 10:
    #        break
        if counter_stare_ogloszenia == 11: # 11 starych ogłoszeń pod rząd zatrzymuje pętlę - z dotychczasowych obserwacji tyle wystarczy, żeby założyć brak świeżych ogłoszeń
            break
        else:
            pass

    driver.quit()
    # display.stop()

    # Czyszczenie danych jeżeli pojawią się ogłoszenia świeższe niż X (W tym przypadku ostatnie pół godziny, a dokładnie 33 minuty bo biorę poprawkę na start algorytmu)
    wszystkie_ogloszenia[['oplaty_dodatkowe', 'cena']] = wszystkie_ogloszenia[['oplaty_dodatkowe', 'cena']].fillna(value='0')
    wszystkie_ogloszenia = wszystkie_ogloszenia.fillna(value='')

    wszystkie_ogloszenia['data'] = wszystkie_ogloszenia['czas_dodania_ogloszenia'].map(lambda x: date.today() if 'Dzisiaj' in x else '')
    wszystkie_ogloszenia['godzina'] = wszystkie_ogloszenia['czas_dodania_ogloszenia'].map(lambda x: x[-5:])
    wszystkie_ogloszenia['data'] = wszystkie_ogloszenia['data'].astype('str')
    wszystkie_ogloszenia['datestamp'] = wszystkie_ogloszenia['data'] + ' ' + wszystkie_ogloszenia['godzina'] + ':00'
    wszystkie_ogloszenia['datestamp'] = pd.to_datetime(wszystkie_ogloszenia['datestamp'])
    wszystkie_ogloszenia = wszystkie_ogloszenia.drop(columns = ['czas_dodania_ogloszenia', 'data', 'godzina'])

    wszystkie_ogloszenia = wszystkie_ogloszenia[wszystkie_ogloszenia['datestamp'] >= ostatnie_pol_godziny_str]

    if len(wszystkie_ogloszenia.index) != 0:
        wszystkie_ogloszenia['powierzchnia'] = wszystkie_ogloszenia['powierzchnia'].map(lambda x: x.strip('Powierzchnia:').strip('m²').strip())
        wszystkie_ogloszenia['liczba_pokoi'] = wszystkie_ogloszenia['liczba_pokoi'].map(lambda x: x.strip('Liczba pokoi:').strip('pokoje').strip())
        wszystkie_ogloszenia['cena'] = wszystkie_ogloszenia['cena'].map(lambda x: x.strip('\ndonegocjacji ').strip('zł').strip().replace(' ', '').replace(',', '.'))
        wszystkie_ogloszenia['cena'] = wszystkie_ogloszenia['cena'].astype(float)
        wszystkie_ogloszenia['cena'] = wszystkie_ogloszenia['cena'].astype(int)
        wszystkie_ogloszenia['oplaty_dodatkowe'] = wszystkie_ogloszenia['oplaty_dodatkowe'].map(lambda x: x.strip('Czynsz (dodatkowo):').strip('/miesiąc').strip('zł').strip().replace(' ', '').replace(',', '.'))
        wszystkie_ogloszenia['oplaty_dodatkowe'] = wszystkie_ogloszenia['oplaty_dodatkowe'].astype(float)
        wszystkie_ogloszenia['oplaty_dodatkowe'] = wszystkie_ogloszenia['oplaty_dodatkowe'].astype(int)
        wszystkie_ogloszenia['suma_kosztow'] = wszystkie_ogloszenia['cena'] + wszystkie_ogloszenia['oplaty_dodatkowe']
        wszystkie_ogloszenia = wszystkie_ogloszenia[[
            'datestamp',
            'tytul',
            'lokalizacja',
            'powierzchnia',
            'liczba_pokoi',
            'cena',
            'oplaty_dodatkowe',
            'suma_kosztow',
            'link'
        ]]
        wszystkie_ogloszenia = wszystkie_ogloszenia.rename(columns = {'datestamp': 'data_ogloszenia'})
        # wszystkie_ogloszenia = wszystkie_ogloszenia[(wszystkie_ogloszenia['suma_kosztow'] >= 1100) & (wszystkie_ogloszenia['suma_kosztow'] <= 2600)]
        wszystkie_ogloszenia = wszystkie_ogloszenia.sort_values(by='data_ogloszenia', ascending = False)
        
        print('Wykonano operacje na ramce danych')
        
    # Wysyłka maila z powiadomieniem o nowych ogłoszeniach
        body_mail = wszystkie_ogloszenia
        body_mail = body_mail.to_html(render_links = True)
        subject = 'Nowe oferty - ' + miasto + ' - wynajem'
        mail = yg.SMTP(user = sender, password = password)
        mail.send(to = sender, subject = subject, contents = body_mail)
        print('Mail wysłany')
        
    else:
        print('Brak nowych ogłoszeń')
        subject = 'Brak nowych ogłoszeń'
        mail = yg.SMTP(user = sender, password = password)
        mail.send(to = sender, subject = subject)
        print('Mail wysłany')
except:
    error_message = traceback.format_exc()
    body_mail = error_message
    subject = 'powiadomienia_olx_failed'
    mail = yg.SMTP(user = sender, password = password)
    mail.send(to = sender, subject = subject, contents = body_mail)
    print('Mail wysłany')
