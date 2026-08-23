import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys

def prikupi_podatke_od_korisnika():
    print("=== Generator ruže vetrova (Open-Meteo podaci) ===")
    
    try:
        lat = float(input("Unesite geografsku širinu (Latitude, npr. 43.27): "))
        lon = float(input("Unesite geografsku dužinu (Longitude, npr. 19.98): "))
    except ValueError:
        print("Greška: Koordinate moraju biti unete kao decimalni brojevi.")
        sys.exit(1)

    visina_unos = input("Unesite nadmorsku visinu u metrima (ostavite prazno za automatsku DEM detekciju): ")
    
    if visina_unos.strip():
        try:
            visina_param = f"&elevation={float(visina_unos)}"
        except ValueError:
            print("Greška: Nadmorska visina mora biti broj. Prekid rada.")
            sys.exit(1)
    else:
        visina_param = "" # API će koristiti svoj DEM

    # Fiksni period (može se takođe prebaciti u input po potrebi)
    start_date = "2010-01-01" 
    end_date = "2020-12-31"
    
    return lat, lon, visina_param, start_date, end_date

# --- 1. KORISNIČKI UNOS ---
LAT, LON, VISINA_PARAM, START_DATE, END_DATE = prikupi_podatke_od_korisnika()

# --- 2. PREUZIMANJE PODATAKA ---
print("\nPreuzimanje istorijskih podataka. Ovo može potrajati nekoliko sekundi...")
url = f"https://archive-api.open-meteo.com/v1/archive?latitude={LAT}&longitude={LON}{VISINA_PARAM}&start_date={START_DATE}&end_date={END_DATE}&hourly=windspeed_10m,winddirection_10m"

try:
    response = requests.get(url)
    response.raise_for_status() # Provera da li je API vratio grešku
    podaci = response.json()
except requests.exceptions.RequestException as e:
    print(f"Došlo je do greške prilikom preuzimanja podataka: {e}")
    sys.exit(1)

df = pd.DataFrame(podaci['hourly'])
df = df.dropna()

# --- 3. OBRADA PODATAKA ---
print("Obrada podataka i generisanje grafika...")
ukupno_sati = len(df)

tisine_filter = df['windspeed_10m'] < 0.1
tisine_procenat = (tisine_filter.sum() / ukupno_sati) * 100
df_vetar = df[~tisine_filter].copy()

pravci_labele = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 
                 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']

bins = np.linspace(-11.25, 371.25, 18)
df_vetar['pravac_binned'] = pd.cut(df_vetar['winddirection_10m'], bins=bins, labels=False)
df_vetar['pravac_binned'] = df_vetar['pravac_binned'].replace(16, 0) 

klasa_1 = df_vetar[(df_vetar['windspeed_10m'] >= 0.1) & (df_vetar['windspeed_10m'] <= 2.0)]
klasa_2 = df_vetar[df_vetar['windspeed_10m'] > 2.0]

def izracunaj_procente(data, ukupno):
    frekvencije = data.groupby('pravac_binned').size().reindex(range(16), fill_value=0)
    return (frekvencije / ukupno) * 100

procenti_klasa1 = izracunaj_procente(klasa_1, ukupno_sati).values
procenti_klasa2 = izracunaj_procente(klasa_2, ukupno_sati).values

procenti_klasa1 = np.append(procenti_klasa1, procenti_klasa1[0])
procenti_klasa2 = np.append(procenti_klasa2, procenti_klasa2[0])
uglovi = np.linspace(0, 2 * np.pi, 16, endpoint=False)
uglovi = np.append(uglovi, uglovi[0])

# --- 4. ISCRTAVANJE GRAFIKA ---
fig, ax = plt.subplots(figsize=(10, 8), subplot_kw=dict(polar=True))

ax.set_theta_zero_location('N')
ax.set_theta_direction(-1)

ax.set_thetagrids(np.degrees(uglovi[:-1]), pravci_labele, fontsize=11, color='#1f77b4')
ax.set_rlabel_position(0)
# Dinamičko prilagođavanje skale na osnovu maksimalnih vrednosti
max_procenat = max(np.max(procenti_klasa1), np.max(procenti_klasa2))
ax.set_ylim(0, np.ceil(max_procenat) + 1)

ax.grid(color='#a0c4e0', linestyle='-', linewidth=0.5)

ax.plot(uglovi, procenti_klasa2, linewidth=2.5, color='#1f77b4', linestyle='solid', label='> 2 m/s')
ax.plot(uglovi, procenti_klasa1, linewidth=2, color='#00bfff', linestyle='solid', label='0.1 - 2 m/s')

ax.plot(0, 0, marker='o', color='red', markersize=5)

plt.figtext(0.1, 0.1, f"Tišine:\n{tisine_procenat:.1f}%", fontsize=12, color='#1f77b4')

plt.title(f"Ruža vetrova (Lokacija: {LAT}, {LON})", y=1.08, fontweight="bold")
ax.legend(loc='lower right', title="Brzina vetra (m/s)", bbox_to_anchor=(1.2, 0))

plt.show()