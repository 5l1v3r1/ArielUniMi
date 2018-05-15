#!/usr/bin/python3
import sys
import Config
import logging
import smtplib
import requests
from datetime import datetime
from bs4 import BeautifulSoup

headerdesktop = {"User-Agent": "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)",
                 "Accept-Language": "it"}
timeoutconnection = 10

# Inizializzo i LOG
logging.basicConfig(filename="arielunimi.log",
                    format="%(asctime)s - %(funcName)10s():%(lineno)s - %(levelname)s - %(message)s",
                    level=logging.INFO)

# Lista di tutte le pubblicazioni gia analizzate
pubblicazioniList = []


def load_pubblicazioni_analizzate():
    try:
        f = open("pubblicazioni_analizzate.txt", "r", errors="ignore")

        for line in f:
            if line:
                line = line.rstrip()
                pubblicazioniList.append(line)

        f.close()

    except IOError as e:
        logging.error(e, exc_info=True)
        sys.exit()
    except Exception as e:
        logging.error(e, exc_info=True)
        raise


def save_pubblicazioni_analizzate(title):
    try:
        f = open("pubblicazioni_analizzate.txt", "a")
        f.write(title + "\n")
        f.close()
    except IOError as e:
        logging.error(e, exc_info=True)
        sys.exit()
    except Exception as e:
        logging.error(e, exc_info=True)
        raise


def send_email(title):
    try:
        toaddrs = Config.smtp_to
        fromaddr = Config.smtp_from
        username = Config.smtp_mail
        password = Config.smtp_psw
        smtpserver = smtplib.SMTP(Config.smtp_server, 587)
        smtpserver.ehlo()
        smtpserver.starttls()
        # smtpserver.ehlo() # extra characters to permit edit
        smtpserver.login(username, password)

        header = "From: " + fromaddr + "\r\n"
        header += "To: " + ", ".join(toaddrs) + "\r\n"
        header += "Subject: Ariel UniMi Scanner: " + title + "\r\n"
        header += "Date: " + datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S -0000") + "\r\n\r\n"

        msg = header + "Rilevata Pubblicazione: \n"
        msg = msg + title + "\n"
        msg = msg + "\n\n"

        smtpserver.sendmail(fromaddr, toaddrs, msg)

        smtpserver.quit()
    except Exception as e:
        logging.error(e, exc_info=True)
        pass


def main():
    # Carico la lista delle pubblicazioni gia analizzate
    load_pubblicazioni_analizzate()

    # Effettuo il login ad Ariel e ne ricavo i Cookie di sessione
    try:
        urllogin = "https://elearning.unimi.it/authentication/skin/portaleariel/login.aspx?url=https://ariel.unimi.it/?reset=true"
        data = {"ddlType": "", "hdnSilent": "true", "tbLogin": Config.emailunimi, "tbPassword": Config.passwunimi}

        session = requests.Session()
        session.post(urllogin, data=data, headers=headerdesktop, timeout=timeoutconnection)

        cookie = session.cookies.get_dict()
    except Exception as e:
        logging.error("Errore nell'autenticazione: %s" % e)
        sys.exit(1)

    # Visualizzo la pagina del docente per estrarne le pubblicazioni
    try:
        if cookie:
            page = requests.get(Config.urlportaledocente, cookies=cookie, headers=headerdesktop,
                                timeout=timeoutconnection)
            soupdesktop = BeautifulSoup(page.text, "html.parser")

            for h2 in soupdesktop.find_all("h2", attrs={"class": "arielTitle"}):

                if h2.text.strip() not in pubblicazioniList:
                    send_email(h2.text.strip())
                    logging.info("Nuova pubblicazione rilevata: %s" % h2.text.strip())
                    save_pubblicazioni_analizzate(h2.text.strip())
    except Exception as e:
        logging.error("Errore nell'acquisizione delle pubblicazioni: %s" % e)
        pass


if __name__ == "__main__":
    main()
