import docx
filename = "Anwar Rohmadi_Universitas Islam Negeri Raden Mas Said Surakarta_SPATIO-TEMPORAL IMPACTS OF ENERGY TRANSITION IN INDONESIA'S NICKEL PROCESSING INDUSTRY ON SECTORAL GRDP- A GTWR AND LEONTIEF INPUT-OUTPUT APPROACH.docx"
doc = docx.Document(filename)
print(f"Total paragraphs: {len(doc.paragraphs)}")
