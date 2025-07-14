import os
import time
import smtplib
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def checkIfPreviousExists(filePath):
    exists = os.path.isfile(filePath)
    print(f"[INFO] Checking if previous file exists at {filePath}: {exists}")
    return exists


def getPreviousNumberOfApartments(fileName):
    print(f"[INFO] Reading previous number of apartments from {fileName}")
    with open(fileName, "r") as file:
        numberOfApartments = file.read()
    print(f"[INFO] Previous number of apartments: {numberOfApartments}")
    return numberOfApartments


def getUpdatedNumberOfApartments():
    url = "https://www.sssb.se/en/"
    print(f"[INFO] Launching headless browser to fetch updated number of apartments from {url}")

    chromeOptions = Options()
    # Try running in non-headless mode if still failing
    # chromeOptions.add_argument("--headless=new")
    chromeOptions.add_argument("--disable-gpu")
    chromeOptions.add_argument("--no-sandbox")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chromeOptions)

    try:
        driver.get(url)

        wait = WebDriverWait(driver, 20)
        # Look for the apartment count inside a tag with "Lediga bostäder" text
        elem = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//span[@data-widget='objektsummering@lagenheter']")
        ))

        fetchedNumber = elem.text.strip()
        print(f"[INFO] Fetched updated number of apartments: {fetchedNumber}")

    except Exception as e:
        print(f"[ERROR] Failed to get object number: {type(e).__name__}: {e}")
        with open("debug.html", "w") as f:
            f.write(driver.page_source)
        fetchedNumber = "99999"

    finally:
        driver.quit()

    return fetchedNumber



def sendMail(prevNumber, updatedNumber):
    print("[INFO] Sending email notification about apartment number update via SSL port 465...")
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)  # Use SSL SMTP on port 465
        server.login(os.environ["GMAIL_USER"], os.environ["GMAIL_PASSWORD"])

        subject = "SSSB - Updated number of apartments"
        bodyText = (
            "SSSB has changed the number of apartments \n\n"
            f"SSSB has updated number of apartments from {prevNumber} to {updatedNumber}.\n"
            "Check them out: https://www.sssb.se/soka-bostad/sok-ledigt/lediga-bostader/ \n\n"
            "/SSSB-notifier"
        )
        bodyHTML = (
            "<html><body>"
            "<h1>SSSB has changed the number of apartments</h1>"
            f"<p>SSSB has updated number of apartments from <b>{prevNumber}</b> to <b>{updatedNumber}</b></p>"
            "<p>Check them out: "
            "<a href='https://www.sssb.se/soka-bostad/sok-ledigt/lediga-bostader/'>"
            "https://www.sssb.se/soka-bostad/sok-ledigt/lediga-bostader/</a></p>"
            "<p>/SSSB-notifier</p>"
            "</body></html>"
        )

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = os.environ["GMAIL_USER"]
        message["To"] = os.environ["RECEIVING_USER"]

        part1 = MIMEText(bodyText, "plain")
        part2 = MIMEText(bodyHTML, "html")

        message.attach(part1)
        message.attach(part2)

        server.sendmail(
            os.environ["GMAIL_USER"],
            os.environ["RECEIVING_USER"],
            message.as_string()
        )
        server.quit()
        print("[INFO] Email sent successfully.")
        return True

    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")
        return False



def updateLocal(absFilePath, updatedNumber):
    print(f"[INFO] Updating local file {absFilePath} with new number: {updatedNumber}")
    with open(absFilePath, "w") as file:
        file.write(str(updatedNumber))



def checkIfUpdated():
    print("[INFO] Starting update check...")
    scriptDirectoryPath = os.path.dirname(__file__)
    fileName = "previous-number.txt"
    absFilePath = os.path.join(scriptDirectoryPath, fileName)

    prevExists = checkIfPreviousExists(absFilePath)

    if prevExists:
        previousNumberOfApartments = getPreviousNumberOfApartments(absFilePath)
        updatedNumberOfApartments = getUpdatedNumberOfApartments()

        if previousNumberOfApartments != updatedNumberOfApartments:
            print(f"[INFO] Number changed from {previousNumberOfApartments} to {updatedNumberOfApartments}")
            sendMail(previousNumberOfApartments, updatedNumberOfApartments)
            updateLocal(absFilePath, updatedNumberOfApartments)
        else:
            print("[INFO] No change in the number of apartments.")
    else:
        print("[INFO] No previous data found, saving the current number.")
        updatedNumberOfApartments = getUpdatedNumberOfApartments()
        updateLocal(absFilePath, updatedNumberOfApartments)


def main():
    print("[INFO] Starting the SSSB apartment update checker.")

    # print("[INFO] Sending test email on startup...")
    # if sendMail("Test previous number", "Test updated number"):
    #     print("[INFO] Test email sent successfully.")
    # else:
    #     print("[ERROR] Test email failed to send.")

    updateFrequencyInSeconds = 3600
    while True:
        checkIfUpdated()
        print(f"[INFO] Sleeping for {updateFrequencyInSeconds} seconds...\n")
        time.sleep(updateFrequencyInSeconds)



if __name__ == "__main__":
    main()
