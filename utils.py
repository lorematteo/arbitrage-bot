import pytz
import datetime

def get_time():
    # Définir la timezone française
    tz_france = pytz.timezone('Europe/Paris')

    # Obtenir la date et l'heure actuelles dans la timezone française
    now = datetime.datetime.now(tz_france)

    # Formater la date et l'heure dans le format souhaité
    date_heure_format = now.strftime("[%d/%m/%Y  %H:%M:%S]")

    # Retourner la date et l'heure formatées
    return date_heure_format

def moy(list):
    sum=0
    for value in list:
        sum+=value
    return sum/len(list)