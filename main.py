import requests
import json
from bs4 import BeautifulSoup
import speech_recognition as sr
import pyttsx3
import pyaudio
import re
import threading
import time

API_KEY = 'tx_PZMCtUmbo'
PROJECT_TOKEN = 't7t1S9QR45Vi'
RUN_TOKEN = 't4b6sZTWfmpT'

response = requests.get(f'https://www.parsehub.com/api/v2/projects/{PROJECT_TOKEN}/last_ready_run/data',
                        params={"api_key": API_KEY})
data = json.loads(response.text)


class Data:
    def __init__(self, api_key, project_token):
        self.api_key = api_key
        self.project_token = project_token
        self.params = {
            "api_key": self.api_key
        }
        self.data = self.get_data()

    def get_data(self):
        response = requests.get(f'https://www.parsehub.com/api/v2/projects/{PROJECT_TOKEN}/last_ready_run/data',
                                params={"api_key": API_KEY})
        self.data = json.loads(response.text)
        return data

    def get_total_cases(self):
        data = self.data['Total']

        for content in data:
            if content['name'] == 'Coronavirus Cases:':
                return content['value']

    def get_total_deaths(self):
        data = self.data['Total']

        for content in data:
            if content['name'] == 'Deaths:':
                return content['value']

    def get_total_recovered(self):
        data = self.data['Total']

        for content in data:
            if content['name'] == 'Recovered:':
                return content['value']
        return "0"

    def get_country_data(self, country):
        data = self.data['Country']

        for content in data:
            if content['name'].lower() == country.lower():
                return content
        return "0"

    def get_list_of_countries(self):
        countries = []
        for country in self.data['Country']:
            countries.append(country['name'])

    def update_data(self):
        response = requests.post(f"https://www.parsehub.com/api/v2/projects/{self.project_token}/run",
                                 params=self.params)

        def poll():
            time.sleep(0.1)
            old_data = self.data
            while True:
                new_data = self.get_data()
                if new_data != old_data:
                    self.data = new_data
                    print("Data updated")
                    break
                time.sleep(5)

        t = threading.Thread(target=poll)
        t.start()


def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()


def get_audio():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        audio = r.listen(source)
        said = ""

        try:
            said = r.recognize_google(audio)
        except Exception as e:
            print("Exception:", str(e))

    return said.lower()


def main():
    data = Data(API_KEY, PROJECT_TOKEN)
    END_PHRASE = "Stop"
    country_list = list(data.get_list_of_countries())

    START_PHRASE = "Jeeves"

    TOTAL_PATTERNS = {
        re.compile("[\w\s]+ total [\w\s]+ cases"): data.get_total_cases,
        re.compile("[\w\s]+ total cases"): data.get_total_cases,
        re.compile("[\w\s]+ total [\w\s]+ deaths"): data.get_total_deaths,
        re.compile("[\w\s]+ total deaths"): data.get_total_deaths

    }

    COUNTRY_PATTERNS = {
        re.compile("[\w\s]+ cases [\w\s]+"): lambda country: data.get_country_data(country)['total_cases'],
        re.compile("[\w\s]+ deaths [\w\s]+"): lambda country: data.get_country_data(country)['total_deaths']
    }

    UPDATE_COMMAND = "update"

    while True:
        print("Listening...")
        text = get_audio()
        print(text)
        result = None

        for pattern, func in COUNTRY_PATTERNS.items():
            if pattern.match(text):
                words = set(text.split(" "))
                for country in country_list:
                    if country in words:
                        result = func(country)
                        break

        for pattern, func in TOTAL_PATTERNS.items():
            if pattern.match(text):
                result = func()
                break

        if text == UPDATE_COMMAND:
            result = "Data is being updated. This may take a moment"
            data.update_data()

        if result:
            speak(result)

        if text.find(END_PHRASE) != -1:
            speak("Goodbye Master Duntoye")
            break

        if text == START_PHRASE:
            speak("Yes Master Duntoye")


main()

data = Data(API_KEY, PROJECT_TOKEN)

# print(data.get_country_data("canada"))
