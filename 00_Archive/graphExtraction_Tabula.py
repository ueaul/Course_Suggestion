import tabula
import pandas as pd

import camelot
import pandas as pd

def is_numeric_column(df, column_name):
    return pd.to_numeric(df[column_name], errors='coerce').notnull().all()

def get_relevant_courses(path):
    tables = tabula.read_pdf(path, pages="all", multiple_tables=True, lattice=True)

    for i in range(len(tables)):
        tables[i] = tables[i].dropna(axis=1, how="all")
        tables[i] = tables[i].iloc[:, :2]
        tables[i] = tables[i].rename(columns={tables[i].columns[0]: "Course Nr", tables[i].columns[1]: "Course"})

        pattern = "^[A-Z]{2,3} [0-9a-z]{3,4}$"
        format_correct = tables[i]["Course Nr"].str.match(pattern).all()

        if not format_correct:
            tables[i]["Course"] = tables[i]["Course Nr"]
            tables[i]["Course Nr"] = None


    courses = pd.concat(tables, axis=0)
    return courses

def get_courses(path):
    tables = tabula.read_pdf(path, pages="all", multiple_tables=True, lattice=True, columns=[62,204])

    for i in range(len(tables)):
        tables[i] = tables[i].dropna(axis=1, how="all")
        tables[i] = tables[i].fillna("")

        indices_to_drop = []
        #for j in range(1, len(tables[i])):
            #add_content = ""
            #k = 0
            #while j+k < len(tables[i]) and tables[i].at[j+k, tables[i].columns[0]] == "":
               # add_content += ("\n" + str(tables[i].at[j+k, tables[i].columns[1]]))
              #  k += 1
             #   indices_to_drop.append(j+k)
            #tables[i].at[j - 1, tables[i].columns[1]] = str(tables[i].at[j-1, tables[i].columns[1]]) + add_content


    tables[23].to_excel("Text.xlsx", index=False)

    print(tables)


#pd.set_option('display.max_rows', None)  # Alle Zeilen anzeigen
#pd.set_option('display.max_columns', None)  # Alle Spalten anzeigen
#courses = get_relevant_Courses("ressources/MK_BSc_Wifo_2020_21_Course_Overview.pdf")
#courses.to_excel("Text.xlsx", index=False)

#courses = get_courses("ressources/MK_BSc_Wifo_2020_21_Courses.pdf")

tables_raw = camelot.read_pdf("ressources/KVVZ_HWS20.pdf", pages="all", flavor="stream", columns = "95")
tables = [table.df for table in tables_raw]
print(tables)



