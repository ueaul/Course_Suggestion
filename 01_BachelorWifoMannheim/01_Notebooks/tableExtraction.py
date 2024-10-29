import camelot
import pandas as pd
import re

def cut_tables(tables):
    for i in range(len(tables)):
        if len(tables[i].columns) > 2:
            tables[i] = tables[i].iloc[:, :2]

def mapping_first_row(text):
    if isinstance(text, str):
        if re.match("M Lodul", text):
            return "Modul"
        elif re.match("erninhalte", text):
            return "Lerninhalte"
        elif re.match(r"ECTS Modul insgesamt.*", text):
            return "ECTS"
        else:
            return text
    else:
        ""

def mapping_second_row(text):
    if isinstance(text, str):
        if re.match(r"Herbst-/Frühjahrssemester", text):
            return "Continuously"
        elif re.match(r"Frühjahr-/Sommersemester", text):
            return "SSS"
        elif re.match(r"Herbst-/Wintersemester", text):
            return "FWS"
        elif re.match(r"Herbstsemester", text):
            return "FWS"
        elif re.match(r"Frühjahrssemester", text):
            return "SSS"
        elif re.match(r"Unregelmäßig", text, re.IGNORECASE):
            return "Continuously"
        elif re.match(r"HWS/FSS", text):
            return "Continuously"
        elif re.match(r"HWS", text):
            return "FWS"
        else:
            return text
    else:
        return text

def applyMapping(tables):
    for i in range(len(tables)):
        tables[i][tables[i].columns[0]] = tables[i][tables[i].columns[0]].apply(mapping_first_row)
        tables[i][tables[i].columns[1]] = tables[i][tables[i].columns[1]].apply(mapping_second_row)
        tables[i][tables[i].columns[1]] = tables[i][tables[i].columns[1]].str.lstrip()

def combine_splitted_tables (last_cell, tables):
    table_ends = []
    i=0
    while i in range(len(tables)):
        check_cell = tables[i][tables[i].columns[0]].iloc[-1]
        if re.fullmatch(last_cell, check_cell):
            if i+1 in range(len(tables)) and tables[i+1][tables[i+1].columns[0]].eq("").all():
                i += 1
            table_ends.append(i)
        i += 1

    indices_to_drop = []
    i = 0
    j = 0
    while i < len(tables):
        k = 1
        tmp = tables[i]
        while i + k <= table_ends[j]:
            tmp = pd.concat([tmp, tables[i + k]], ignore_index=True, axis=0)
            indices_to_drop.append(i + k)
            k += 1
        tables[i] = tmp
        i += k
        j += 1
        if (j >= len(table_ends)):
            break

    for i in reversed(indices_to_drop):
        del tables[i]

    return tables

def clean(tables):
    for i in range(len(tables)):
        tables[i] = tables[i].replace(r"\t+", " ", regex=True)
        tables[i] = tables[i].replace(r"\s+", " ", regex=True)
    return tables

def append_raw_knowledge_field(fields, tables):
    for i in range(len(tables)):
        raw_knowledge = tables[i].iloc[0,0] + " " + tables[i].iloc[0,1]
        for field in fields:
            if tables[i][tables[i].columns[0]].isin([field]).any():
                row = tables[i].loc[tables[i][tables[i].columns[0]] == field]
                raw_knowledge += " " + row.iloc[0,1]

        tables[i].loc[tables[i].index.max() + 1] = ["Raw Knowledge", raw_knowledge]
    return tables

def combine_fields(tables):
    for i in range(len(tables)):
        indices_to_drop = []
        for j in range(1, len(tables[i])):
            add_content = ""
            k = 0
            while j+k < len(tables[i]) and tables[i].at[j+k, tables[i].columns[0]] == "":
                add_content += (" " + str(tables[i].at[j+k, tables[i].columns[1]]))
                indices_to_drop.append(j+k)
                k += 1
            tables[i].at[j - 1, tables[i].columns[1]] = str(tables[i].at[j - 1, tables[i].columns[1]]) + add_content
        tables[i] = tables[i].drop(index=indices_to_drop)
    return tables

def filter_table(tables, relevant_courses, x, y):
    relevant_courses_names = relevant_courses["Course"].tolist()

    filtered_tables = []
    for table in tables:
        for course_name in relevant_courses_names:
            pattern = course_name + r"(\s|\n|\r|$)"
            if re.search(pattern, table.iloc[x, y]):
                filtered_tables.append(table)
                break
    return filtered_tables

def get_relevant_courses(path):
    tables_raw = camelot.read_pdf(path, pages="all", flavor="lattice")
    tables = [table.df for table in tables_raw]

    for i in range(len(tables)):
        tables[i] = tables[i].drop(index=0)
        tables[i] = tables[i].iloc[:, :2]
        tables[i] = tables[i].rename(columns={tables[i].columns[0]: "Course Nr", tables[i].columns[1]: "Course"})

        pattern = "^[A-Z]{2,3} [0-9a-z]{3,4}$"
        format_correct = tables[i]["Course Nr"].str.match(pattern).any()
        all_empty = (tables[i]["Course Nr"] == "").all()

        if not format_correct and not all_empty:
            tables[i]["Course"] = tables[i]["Course Nr"]
            tables[i]["Course Nr"] = None


    courses = pd.concat(tables, axis=0, ignore_index=True)
    return courses

def get_additional_courses(relevant_courses, paths, end_cells, coordinates):
    tables = []
    for i in range(len(paths)):
        table_raw = (camelot.read_pdf(paths[i], pages="all", flavor="lattice", strip_text="\n", line_scale=50))
        tmp = [table.df for table in table_raw]
        tmp = clean(tmp)
        tmp = combine_splitted_tables(end_cells[i], tmp)
        tmp = filter_table(tmp, relevant_courses, coordinates[i][0], coordinates[i][1])
        tmp = combine_fields(tmp)

        for j in range(len(tmp)):
            #force split for BWL courses
            mask = tmp[j][tmp[j].columns[1]] == ""
            tmp[j].loc[mask, [tmp[j].columns[0], tmp[j].columns[1]]] = tmp[j].loc[mask, tmp[j].columns[0]].str.split(":"
                , n=1, expand=True)

            #extract ECTS BWL courses
            if tmp[j][tmp[j].columns[0]].str.contains(r".*ECTS Modul insgesamt.*").any():
                idx = tmp[j].index[tmp[j][tmp[j].columns[0]].str.contains(r".*ECTS Modul insgesamt.*", na=False)][0]
                tmp[j].loc[idx, tmp[j].columns[1]] = re.search(r"(\d+)", tmp[j].loc[idx, tmp[j].columns[0]]).group(1)

        tables.extend(tmp)

    tables.extend(clean(get_VWL_courses()))

    for i in range(len(tables)):
        tables[i][tables[i].columns[0]] = tables[i][tables[i].columns[0]].apply(mapping_first_row)
        tables[i][tables[i].columns[1]] = tables[i][tables[i].columns[1]].apply(mapping_second_row)
        tables[i][tables[i].columns[1]] = tables[i][tables[i].columns[1]].str.lstrip()

    return tables

def get_VWL_courses():
    tables = []
    df = pd.DataFrame(columns=["0", "1"])
    df = pd.concat([df, pd.DataFrame([{'0': 'Recht', '1': ''}])], ignore_index=True)
    df = pd.concat([df, pd.DataFrame(
        [{'0': 'Modulverantwortlicher', '1': 'Dr. jur. Gernot Wirth und Prof. Dr. Thomas Fetzer, LL.M'}])],
                   ignore_index=True)
    df = pd.concat([df, pd.DataFrame([{'0': 'ECTS', '1': '6'}])], ignore_index=True)
    df = pd.concat([df, pd.DataFrame([{'0': 'Vorausgesetzte Kenntnisse', '1': ''}])], ignore_index=True)
    df = pd.concat([df, pd.DataFrame([{'0': 'Lehrinhalte', '1': '''Ziele und Inhalte des Moduls: Die erste Hälfte der 
        Veranstaltung verschafft einen Überblick über das
        deutsche Privatrecht. Der Schwerpunkt der Vorlesung liegt im allgemeinen Privatrecht (Allgemeine Regeln,
        Vertrags- und Sachenrecht des Bürgerlichen Gesetzbuchs). Ergänzend wird auf Sonderprivatrechte wie etwa
        dem Handelsrecht als Sonderprivatrecht der Kaufleute Bezug genommen. Die zweite Hälfte der
        Veranstaltung verschafft einen ersten Einblick in das System des deutschen öffentlichen Rechts.
        Der Schwerpunkt der Vorlesung liegt im Verfassungsrecht und betrifft die Kernfragen des
        Staatsorganisationsrechts und der Grundrechtslehre sowie Grundzüge des Finanzverfassungsrechts. Darüber
        hinaus werden die Grundlagen des allgemeinen Verwaltungsrechts behandelt und ergänzend die
        Grundlagen des Verfassungs- und Verwaltungsprozesses besprochen.
        Erwartete Kompetenzen nach Abschluss des Moduls: Die Studierenden sind in der Lage, sowohl ihre
        berufliche Qualifikation als auch ihre praktischen Tätigkeiten in die rechtlichen und gesellschaftlichen
        Rahmenbedingungen des Wirtschaftslebens einordnen zu können. Durch die Vermittlung rechtlicher
        Grundlagen sowie Methoden und Arbeitsweisen sind sie darauf vorbereitet, die erworbenen
        Grundkenntnisse bei der späteren praktischen Tätigkeit einzuordnen und anzuwenden.'''}])], ignore_index=True)
    df = pd.concat([df, pd.DataFrame([{'0': 'Angebotsturnus', '1': 'Herbstsemester'}])], ignore_index=True)

    tables.append(df)

    df = pd.DataFrame(columns=["0", "1"])
    df = pd.concat([df, pd.DataFrame([{'0': 'Grundlagen der Volkswirtschaftslehre', '1': ''}])], ignore_index=True)
    df = pd.concat(
        [df, pd.DataFrame([{'0': 'Modulverantwortlicher', '1': 'Prof. Dr. Martin Peitz; Steffen Habermalz, Ph.D'}])],
        ignore_index=True)
    df = pd.concat([df, pd.DataFrame([{'0': 'ECTS', '1': '8'}])], ignore_index=True)
    df = pd.concat([df, pd.DataFrame([{'0': 'Vorausgesetzte Kenntnisse', '1': ''}])], ignore_index=True)
    df = pd.concat([df, pd.DataFrame([{'0': 'Lehrinhalte', '1': '''Ziele und Inhalte des Moduls: Die Veranstaltung vermittelt eine 
        Einführung in die Prinzipien volkswirtschaftlichen Denkens. Die Teilnehmer werden mit den grundlegenden 
        Fragestellungen in Mikround Makroökonomik vertraut gemacht, insbesondere dem Funktionieren von Märkten, der 
        Ökonomik des öffentlichen Sektors, der Arbeitsmarktökonomik und der Makroökonomik geschlossener und offener
        Volkwirtschaften. Die Inhalte der Veranstaltung umfassen:
        2
         Einführung: Einige Prinzipien volkswirtschaftlichen Denkens; Handwerkszeug der ökonomischen Analyse
         Angebot und Nachfrage I: Wie Märkte funktionieren
         Angebot und Nachfrage II: Märkte und Wohlstand
         Ökonomik des öffentlichen Sektors: Externalitäten, Kollektivgüter und die Notwendigkeit staatlicher
        Eingriffe; Ausgestaltung des Steuersystems
         Unternehmensverhalten und die Organisation von Märkten
         Arbeitsmarktökonomik
         Grenzbereiche der Mikroökonomik
         Empirische Beobachtung und Makroökonomik: Volkswirtschaftliche Gesamtrechnung
         Die langfristige ökonomische Entwicklung: Produktion und Wachstum, Sparen, Investieren und das
        Finanzsystem
         Geld und Inflation
         Makroökonomik offener Volkswirtschaften
         Kurzfristige wirtschaftliche Schwankungen
         Gesamtwirtschaftliche Politik
         Europäische Währungsunion
        Erwartete Kompetenzen nach Abschluss des Moduls: Erfolgreiche Absolventen kennen die Grundsätze
        ökonomischen Denkens. Sie können diese anwenden, um die Wirkungen verschiedener einfacher
        wirtschaftspolitischer Maßnahmen zu analysieren und zu beurteilen, welche Wirkungen gesellschaftlich
        wünschenswert sind. Sie können ihr Wissen über die in wirtschaftlichen Prozessen wirkenden Anreize
        nutzen, um Laien in mäßig komplexen wirtschaftlichen und politischen Entscheidungsproblemen fachlich
        fundiert zu beraten. Sie sind in der Lage, fachbezogene Positionen zu aktuellen gesellschaftlichen Problemen
        (wie z. B. die Wirtschafts-und Finanzkrise) zu formulieren und mögliche Lösungen mit Fachvertretern zu
        diskutieren.'''}])], ignore_index=True)
    df = pd.concat([df, pd.DataFrame([{'0': 'Angebotsturnus', '1': 'Herbstsemester'}])], ignore_index=True)

    tables.append(df)

    applyMapping(tables)
    return tables


def get_courses(mainFile):
    tables_raw = camelot.read_pdf(mainFile, pages = "all", strip_text="\n", line_scale=30)
    tables = [table.df for table in tables_raw]
    tables = clean(tables)

    tables = combine_splitted_tables(r"Einordnung in Fachsemester|Semester", tables)

    tables = combine_fields(tables)
    cut_tables(tables)
    applyMapping(tables)
    return tables

def post_fixes(courses):
    applyMapping(courses)
    applyMapping(courses)
    return courses







