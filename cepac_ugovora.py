import docx
import re
from pathlib import Path

ugovor_fajl = Path(r"D:\Dokumenti\kolektivni_ugovor\KolektivniUgovor.docx")

def podeli_ugovor_na_clanove():
    print(f"⏳ Otvaram i analiziram Kolektivni ugovor...\n")
    doc = docx.Document(ugovor_fajl)
    
    # Skupljamo tekst
    puni_tekst = []
    for paragraf in doc.paragraphs:
        tekst = paragraf.text.strip()
        if tekst:
            puni_tekst.append(tekst)
            
    # Spajamo sve u jedan ogroman string, gde je svaki paragraf u novom redu
    ceo_dokument = "\n".join(puni_tekst)
    
    # REGEX MAGIJA:
    # \n       -> traži novi red
    # (?= ...) -> "lookahead" (iseci pre onoga što sledi)
    # [Чч][Лл][Аа][Нн] -> pokriva i "Члан" i "ЧЛАН" na ćirilici
    # \s+      -> jedan ili više razmaka
    # \d+      -> jedan ili više brojeva (npr. 1, 14, 125)
    # \.       -> tačka na kraju (npr. "Члан 14.")
    
    sablon = r"\n(?=[Чч][Лл][Аа][Нн]\s+\d+\.)"
    
    # Seci!
    delovi_ugovora = re.split(sablon, ceo_dokument)
    
    print(f"✅ Ugovor je uspešno prepoznat i podeljen na {len(delovi_ugovora)} delova (chunk-ova)!\n")
    
    # Prvi deo (indeks 0) je obično uvodni tekst pre "Član 1."
    print("--- UVODNI DEO (Pre Člana 1) ---")
    print(delovi_ugovora[0][:150] + "...\n")
    
    # Prikazujemo prva 3 stvarna člana da proverimo da li je sečenje uspelo
    # Počinjemo od indeksa 1 (jer je indeks 0 uvod)
    for i in range(1, min(4, len(delovi_ugovora))):
        print(f"--- CHUNK {i} ---")
        # Štampamo prvih 200 karaktera svakog člana
        print(delovi_ugovora[i][:200] + "...\n")
        
if __name__ == "__main__":
    podeli_ugovor_na_clanove()