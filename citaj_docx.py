import docx
from pathlib import Path

ugovor_fajl = Path(r"D:\Dokumenti\kolektivni_ugovor\KolektivniUgovor.docx")

def probaj_citanje_ugovora():
    if not ugovor_fajl.exists():
        print("Fajl nije pronađen.")
        return

    print(f"⏳ Čitam: {ugovor_fajl.name}\n")
    doc = docx.Document(ugovor_fajl)
    
    # Skupljamo sav tekst u jednu listu
    puni_tekst = []
    for paragraf in doc.paragraphs:
        if paragraf.text.strip(): # Ignorišemo prazne redove
            puni_tekst.append(paragraf.text)
            
    # Spajamo ga i prikazujemo prvih 1000 karaktera
    ceo_dokument = "\n".join(puni_tekst)
    print("--- POČETAK UGOVORA ---")
    print(ceo_dokument[:1000])
    print("\n✅ Ugovor uspešno učitan.")

if __name__ == "__main__":
    probaj_citanje_ugovora()