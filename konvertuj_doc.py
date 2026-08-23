import os
import win32com.client
from pathlib import Path

folder_oprema = Path(r"D:\Dokumenti\oprema")

def konvertuj_doc_u_docx():
    # Pokrećemo MS Word u pozadini
    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False # Da ne iskaču prozori
    
    konvertovano = 0
    for doc_fajl in folder_oprema.rglob("*.doc"):
        # Preskačemo fajlove koji su već .docx
        if doc_fajl.suffix.lower() == '.doc':
            novi_docx = doc_fajl.with_suffix('.docx')
            
            # Ako već postoji .docx verzija (što je kod tebe slučaj), preskačemo
            if not novi_docx.exists():
                print(f"Konvertujem: {doc_fajl.name}...")
                # Otvaramo stari .doc
                dokument = word.Documents.Open(str(doc_fajl))
                # Čuvamo kao novi .docx (Format 16 je docx)
                dokument.SaveAs2(str(novi_docx), FileFormat=16)
                dokument.Close()
                konvertovano += 1
                
    word.Quit()
    print(f"✅ Konvertovano {konvertovano} novih .docx fajlova.")

if __name__ == "__main__":
    konvertuj_doc_u_docx()