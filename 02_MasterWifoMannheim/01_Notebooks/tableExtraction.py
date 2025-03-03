import camelot
import numpy as np
import pandas as pd
import re

def cut_tables(tables):
    for i in range(len(tables)):
        if len(tables[i].columns) > 2:
            tables[i] = tables[i].iloc[:, :2]

#Mapping for values contained in the first column. Used to standardize the values
def mapping_first_column(text):
    if isinstance(text, str):
        if re.match("M Lodul", text) or re.match("M Codule", text):
            return "Modul"
        elif re.match("erninhalte", text):
            return "Lerninhalte"
        elif re.match(r"ECTS Modul insgesamt", text):
            return "ECTS"
        elif re.match(r"ECTS in total", text):
            return "ECTS"
        elif re.match(r"ontents:", text):
            return "Contents:"
        elif re.match("Angebotsturnus", text):
            return "Offering"
        elif re.match("Frequency", text):
            return "Offering"
        else:
            return text
    else:
        ""

#Mapping for values contained in the second column. Used to standardize the values
def mapping_second_column(text):
    if isinstance(text, str):
        if re.match(r": MAN 654", text):
            return "MAN 654 Corporate Restructuring"
        elif re.match(r"MAN 676: Ausgewählte Herausforderungen im Public Management", text):
            return "MAN 676 Ausgewählte Herausforderungen im Public Management"
        elif re.match(r"(.*[(]?(achtung|no offering|kein angebot|please note).*)", text, re.IGNORECASE):
            cut_pos = re.search(r"([(]?(achtung|no offering|kein angebot|please note))", text, re.IGNORECASE).start(1)
            return text[:cut_pos]
        elif re.match(r"Fall semester[ ]?\/[ ]?Spring semester", text, re.IGNORECASE):
            return "Continuously"
        elif re.match(r"Various seminar topics every semester, see announcements on the Internet.", text):
            return "Continuously"
        elif re.match(r"Specific seminar topics are suggested every semester, see announcements on the group website.",
                      text):
            return "Continuously"
        elif re.match(r"Various seminar topics every semester, see announcements on the Internet / Website", text):
            return "Continuously"
        elif re.match(r"Various seminar topics every semester, see announcements on the chair website.", text):
            return "Continuously"
        elif re.match(r"Every Various seminar topics every semester, see announcements on the chair website.", text):
            return "Continuously"
        elif re.match(r"Fall semester and Spring semester", text, re.IGNORECASE):
            return "Continuously"
        elif re.match(r"Spring semester[ ]?\/[ ]?Fall semester", text, re.IGNORECASE):
            return "Continuously"
        elif re.match(r"Fall semester \(July\) and spring semester \(January\)", text, re.IGNORECASE):
            return "Continuously"
        elif re.match(r"Fall semester and/or Spring semester", text, re.IGNORECASE):
            return "Continuously"
        elif re.match(r"Spring semester, Fall semester", text, re.IGNORECASE):
            return "Continuously"
        elif re.match(r"Spring semester and fall semester", text, re.IGNORECASE):
            return "Continuously"
        elif re.match(r"Herbst-[ ]?\/[ ]?Frühjahrssemester", text, re.IGNORECASE):
            return "Continuously"
        elif re.match(r"Frühjahr-[ ]?\/[ ]?Sommersemester", text, re.IGNORECASE):
            return "SSS"
        elif re.match(r"Unregelmäßig", text, re.IGNORECASE):
            return "Continuously"
        elif re.match(r"HWS[ ]?\/[ ]?FSS", text, re.IGNORECASE):
            return "Continuously"
        elif re.match(r"HWS", text, re.IGNORECASE):
            return "FWS"
        elif re.match(r"FSS", text, re.IGNORECASE):
            return "SSS"
        elif re.match(r"Spring term", text, re.IGNORECASE):
            return "SSS"
        elif re.match(r"Herbstsemester", text, re.IGNORECASE):
            return "FWS"
        elif re.match(r"Frühjahrssemester", text, re.IGNORECASE):
            return "SSS"
        elif re.match(r"Fall semester", text, re.IGNORECASE):
            return "FWS"
        elif re.match(r"Spring semester", text, re.IGNORECASE):
            return "SSS"
        elif re.match(r"Fall", text, re.IGNORECASE):
            return "FWS"
        elif re.match(r"Every semester", text, re.IGNORECASE):
            return "Continuously"
        elif re.match(r"irregular", text, re.IGNORECASE):
            return "Continuously"
        else:
            return text
    else:
        return text

def applyMapping(tables):
    for i in range(len(tables)):
        tables[i][tables[i].columns[0]] = tables[i][tables[i].columns[0]].apply(mapping_first_column)
        tables[i][tables[i].columns[1]] = tables[i][tables[i].columns[1]].apply(mapping_second_column)
        tables[i][tables[i].columns[1]] = tables[i][tables[i].columns[1]].str.lstrip()

#Reconstructs tables that were split because they span multiple pages in the PDF file
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

    tables = [table.fillna("") for table in tables]
    return tables

#Remove tabs
def clean(tables):
    for i in range(len(tables)):
        tables[i] = tables[i].replace(r"\t+", " ", regex=True)
        tables[i] = tables[i].replace(r"\s+", " ", regex=True)
    return tables

#Combine multiple rows that contain information that should be in one single row
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

##Filter the course tables to only contain courses that are relevant to the Master's Program in Business Informatics
def filter_table(tables, relevant_courses, x, y, bwl_range):
    relevant_courses_id = relevant_courses["Course Nr"].tolist()

    filtered_tables = []
    for table in tables:
        found = False
        for course_name in relevant_courses_id:
            pattern = course_name + r"(\s|\n|\r|$)"
            if re.search(pattern, table.iloc[x,y]):
                filtered_tables.append(table)
                found = True
                break
        if bwl_range and not found and re.search(r".*?([A-Z]{3} \d{3})[ :].*", table.iloc[x, y]) \
                and not "International Course" in table.iloc[x,y]:
            course = re.search(r".*?([A-Z]{3} \d{3})[ :].*", table.iloc[x, y]).group(1)
            if course[0:3] in bwl_range[0] and course[4:5] in bwl_range[1]:
                filtered_tables.append(table)
    return filtered_tables


#Get the list of courses that is relevant to the Master's Program in Business Informatics
def get_relevant_courses(path):
    tables_raw = camelot.read_pdf(path, pages="all", flavor="lattice", strip_text="\n", line_scale=50)
    tables = [table.df for table in tables_raw]

    for i in range(len(tables)):
        if (tables[i].iloc[0,0] == "Modulnr." or tables[i].iloc[0,0] == "Module no."):
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

#Extract the courses from the additional module catalogs
def get_additional_courses(relevant_courses, paths, end_cells, coordinates, bwl_range):
    tables = []
    for i in range(len(paths)):
        table_raw = (camelot.read_pdf(paths[i], pages="all", flavor="lattice", strip_text="\n", line_scale=50))
        tmp = [table.df for table in table_raw]
        tmp = clean(tmp)
        tmp = combine_splitted_tables(end_cells[i], tmp)
        tmp = filter_table(tmp, relevant_courses, coordinates[i][0], coordinates[i][1], bwl_range)
        tmp = combine_fields(tmp)

        for j in range(len(tmp)):
            # fix MAN 632
            if "MAN 632" in tmp[j].iloc[coordinates[i][0], coordinates[i][1]]:
                tmp_string = tmp[j].iloc[coordinates[i][0], coordinates[i][1]]
                content_pos = tmp_string.find("ontents: ")
                tmp[j].iloc[coordinates[i][0], coordinates[i][1]] = tmp_string[:content_pos].strip()
                content_row = pd.DataFrame({"0": [tmp_string[content_pos:].strip()]})
                tmp[j] = pd.concat([tmp[j].iloc[:1], content_row, tmp[j].iloc[1:]]).reset_index(drop=True)

            #force split for BWL courses
            if len(tmp[j].columns) == 1:
                tmp[j]["1"] = ""
            mask = tmp[j][tmp[j].columns[1]] == ""
            tmp[j].loc[mask, [tmp[j].columns[0], tmp[j].columns[1]]] = tmp[j].loc[mask, tmp[j].columns[0]].str.split(":"
                , n=1, expand=True)

            #extract ECTS BWL courses
            if tmp[j][tmp[j].columns[0]].str.contains(r".*ECTS Modul insgesamt.*|.*ECTS in total.*").any():
                idx = tmp[j].index[tmp[j][tmp[j].columns[0]].str.contains(r".*ECTS Modul insgesamt.*|.*ECTS in total.*",
                                                                          na=False)][0]
                if re.search(r"\d+", tmp[j].loc[idx, tmp[j].columns[0]]):
                    tmp[j].loc[idx, tmp[j].columns[1]] = re.search(r"(\d+)", tmp[j].loc[idx, tmp[j].columns[0]]).group(1)

        tables.extend(tmp)

    applyMapping(tables)

    return tables

#Extract the courses from the module catalog of the Master's Program in Business Informatics
def get_courses(mainFile):
    tables_raw = camelot.read_pdf(mainFile, pages = "all", strip_text="\n", line_scale=30)
    tables = [table.df for table in tables_raw]
    tables = clean(tables)

    tables = combine_splitted_tables(r"Einordnung in Fachsemester|Semester", tables)

    tables = combine_fields(tables)

    cut_tables(tables)

    # Filter
    tables_filtered = []
    for table in tables:
        if re.search(r"Einordnung in Fachsemester|Semester", table.iloc[table.shape[0] - 1, 0]) \
                and not "International Course" in table.iloc[0, 1]:
            tables_filtered.append(table)

    applyMapping(tables_filtered)

    return tables_filtered

#Apply fixes after the extraction process to avoid overwriting manual work
def post_fixes(courses):
    applyMapping(courses)
    applyMapping(courses)
    return courses

