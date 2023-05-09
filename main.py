import os
import re
import io
import hashlib
from pathlib import Path

import smtplib
from email.encoders import encode_base64
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests
from requests.utils import default_headers
from dotenv import load_dotenv
from PyPDF2 import PdfReader, PdfWriter
from bs4 import BeautifulSoup
from apscheduler.schedulers.blocking import BlockingScheduler

load_dotenv()

regex = re.compile("[\s\n\r:,]")

def compute_hash(blob: bytes) -> str:
    stream = io.BytesIO()
    stream.write(blob)

    text = ""
    reader = PdfReader(stream)
    for page in reader.pages:
        text += page.extract_text()
    hasher = hashlib.sha256()
    hasher.update(regex.sub("",text).lower().encode("utf-8"))
    
    return hasher.hexdigest()

def save_file(blob: bytes) -> None:
    stream = io.BytesIO()
    stream.write(blob)

    reader = PdfReader(stream)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    with open("report.pdf", "wb") as file:
        writer.write(file)

def send_email(file_content: bytes) -> None:
    s = smtplib.SMTP()
    s.connect("smtp.polymtl.ca", 587)
    s.ehlo()

    message = MIMEMultipart()
    message["Subject"] = "[POLYMTL] Changements sur le bulletin"
    message["From"] = os.environ["DOSSIER_SENDER_EMAIL"]
    message["To"] = os.environ["DOSSIER_TO_EMAIL"]

    body = """
    
    Des changements ont été détectés dans le bulletin. Vous pouvez le consutler, il est attaché dans ce courriel.

    """

    message.attach(MIMEText(body, "plain"))

    part = MIMEBase("application", "octet-stream")
    part.set_payload(file_content)

    encode_base64(part)

    part.add_header(
        "Content-Disposition",
        "attachment; filename = report.pdf"
    )
    message.attach(part)
    text = message.as_string()

    s.sendmail(os.environ["DOSSIER_SENDER_EMAIL"], os.environ["DOSSIER_TO_EMAIL"], text)
    

def main() -> None:
    data = {
        "code": os.environ["DOSSIER_USERNAME"],
        "nip": os.environ["DOSSIER_PASSWORD"],
        "naissance": os.environ["DOSSIER_DOB"]
    }
    headers = default_headers()
    headers.update({
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36"
    })

    s = requests.Session()

    rlogin = s.post("https://dossieretudiant.polymtl.ca/WebEtudiant7/ValidationServlet", data=data, headers=headers)
    loginPage = ""

    if rlogin.status_code != 200:
        print(f"Invalid response: {rlogin.status_code}")
    
    print("Connected to dossieretudiant")
    loginPage = rlogin.text

    soup = BeautifulSoup(loginPage, "html.parser")
    pdfRequest = {}

    for element in soup.form.find_all("input", attrs={"type":"hidden"}):
        pdfRequest[element.attrs["name"]] = element.attrs["value"]

    rreport = s.post("https://dossieretudiant.polymtl.ca/WebEtudiant7/AfficheBulletinServlet", data=pdfRequest, headers=headers)

    if rreport.status_code != 200:
        print("Invalid response code PDF")
        return
    
    report = rreport.content
    print("Report card fetched from dossier etudiant.")

    current_file = Path("report.pdf")

    rdigest = compute_hash(report)

    if current_file.is_file():
        # File was already saved, compare the received data with the current file
        with open("report.pdf", "rb") as file:
            current_digest = compute_hash(file.read())
            
        if rdigest == current_digest:
            print("No new changes detected")
        else:
            # Save the new file to disk
            save_file(report)
            print("Detected new changes, sending email with attachment")
            send_email(report)
    else:
        # File doesn't exist, save it. Comparison will be done on the next run
        print("First time seeing the report.pdf, saving...")
        save_file(report)
        

if __name__ == "__main__":
    scheduler = BlockingScheduler()
    scheduler.add_job(main, 'interval', minutes=10)
    scheduler.start()
