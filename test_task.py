from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
from selenium.webdriver.common.keys import Keys


class CourseInfo:
    name: str
    description: str
    has_flex: bool
    has_fulltime: bool
    duration: str

    def get_type_text(self):
        if self.has_flex and self.has_fulltime:
            return "Full-time or Flex"
        elif self.has_flex:
            return "Flex"
        else:
            return "Full-time"

def hide_elements(driver: webdriver.Chrome, selector: By, selectorText: str):
    for i in range(5):
        # Find elements that need to be hidden
        # and hide them with display: none style
        elements = driver.find_elements(selector, selectorText)
        for element in elements:
            driver.execute_script("arguments[0].style.display = 'none';", element)
        if (len(elements) > 0):
            break
        else:
            time.sleep(1)

def hide_bottom_banner(driver: webdriver.Chrome):
    hide_elements(driver, By.CSS_SELECTOR, "[class*='PromoBanner_container']")

def hide_react_modal(driver: webdriver.Chrome):
    hide_elements(driver, By.CLASS_NAME, "ReactModalPortal")


# Init driver, open the site
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options)

URL = "https://mate.academy" 
driver.get(URL)

# Hide bottom banner
# because it prevents selenium from 
# reading the course description
hide_bottom_banner(driver)

# Find courses
courses = driver.find_elements(By.CLASS_NAME, "ProfessionCard_cardWrapper__BCg0O")
actions = webdriver.ActionChains(driver, 2000)

courseInfos: list[CourseInfo] = []

for course in courses:
    driver.switch_to.window(driver.window_handles[0]) # Switch to main tab

    courseInfo = CourseInfo()
    courseInfos.append(courseInfo)
    courseInfo.name = course.find_element(By.CLASS_NAME, "ProfessionCard_title__m7uno").text
    courseInfo.duration = course.find_element(By.CLASS_NAME, "ProfessionCard_duration__13PwX").text

    # Move to course content and read description
    actions.scroll_to_element(course).perform() 
    actions.move_to_element(course).perform()
    driver.execute_script("arguments[0].style.display = 'block';", course)
    time.sleep(1)
    # After some interaction the modal appears
    # which needs to be hidden
    hide_react_modal(driver)
    courseInfo.description = course.find_element(By.CLASS_NAME, "ProfessionCard_description__K8weo").text

    # Open course page in a new tab
    course.send_keys(Keys.CONTROL + Keys.RETURN)  # Use Keys.COMMAND + Keys.RETURN on Mac
    driver.switch_to.window(driver.window_handles[1]) 
    time.sleep(2)
    hide_bottom_banner(driver)

    # Find if the source if FLEX or FULLTIME or Both
    types = driver.find_elements(By.CLASS_NAME, "LandingTables_columnHeaderWhite__577Bn")
    for type_el in types:
        type_text = type_el.text
        if type_text == 'У вільний час':
            courseInfo.has_flex = True
        elif (type_text == 'Будні з 9 до 18'):
            courseInfo.has_fulltime = True

    # Close current tab
    driver.close()
    time.sleep(1)

# Save results as csv
data = []
for courseInfo in courseInfos:
    data.append({
            "Name": courseInfo.name,
            "Description": courseInfo.description,
            "Duration": courseInfo.duration,
            "Type": courseInfo.get_type_text(),
        })

df = pd.DataFrame(data)
df.to_csv("mate_courses.csv", index=False)
print(df)

driver.quit()

