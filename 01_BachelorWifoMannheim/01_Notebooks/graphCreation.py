import re

import pandas as pd

def getCourseName(course):
    course_name = ""

    if not "Modul" in str(course.iloc[0, 0]):
        course_name += str(course.iloc[0, 0])

    if not pd.isna(course.iloc[0, 1]) and not course.iloc[0, 1] == "":
        if len(course_name) > 0:
            course_name += " " + str(course.iloc[0, 1])
        else:
            course_name += str(course.iloc[0, 1])

    return course_name

def getCourseNodes(courses):
    nodes = []

    for course in courses:

        #Get name of course
        course_name = getCourseName(course)

        #Get ECTS
        ECTS_row = course[course.iloc[:, 0] == "ECTS"]
        ECTS = ECTS_row.iloc[0,1]

        #Get offering cycle
        offering_cycle_row = course[course.iloc[:, 0] == "Angebotsturnus"]
        offering_cycle = offering_cycle_row.iloc[0,1]

        nodes.append([course_name, ECTS, offering_cycle])

    return nodes

def getFullCourseName(searchString, CourseNames):
    for courseName in CourseNames:
        if searchString in courseName:
            return courseName

    return ""


def complete_edges(courses, edges):
    additional_edges = []

    prerequisite_index = 0

    helper_nodes = []

    course_names = []
    for course in courses:
        course_names.append(getCourseName(course))

    knowledge_areas = pd.read_excel("../04_Graph/knowledgeAreas.xlsx").values.tolist()

    for course in courses:

        #Get name of course
        course_name = getCourseName(course)

        #Get row where courses containing required knowledge are contained
        row = course[course.iloc[:, 0] == "Vorausgesetzte Kenntnisse"]
        if row.empty:
            row = course[course.iloc[:, 0] == "Voraussetzungen"]

        #Get name of courses with required knowledge
        if not row.empty:
            if pd.notna(row.iloc[0,1]) and not str(row.iloc[0,1]) == "" and not str(row.iloc[0,1]) == "-":
                required_course_knowledge_raw = row.iloc[0,1]
                required_course_knowledge = [course.strip() for course in required_course_knowledge_raw.split(",")]

                #Create new edges
                for course_knowledge in required_course_knowledge:
                    #Skill is directly contained
                    if [course_knowledge] in knowledge_areas:
                        if not [course_knowledge, course_name] in additional_edges:
                            additional_edges.append([course_knowledge, course_name])
                    #Course is contained, add all skills associated with that course
                    else:
                        escaped_course_knowledge = re.escape(course_knowledge)
                        indices = edges[edges['Outgoing'].str.contains(escaped_course_knowledge, na=False)].index.tolist()
                        for idx in indices:
                            knowledge = edges.iloc[idx,1]
                            if not [knowledge, course_name] in additional_edges:
                                additional_edges.append([knowledge, course_name])

        #Get rows where prerequisite courses are contained
        row = course[course.iloc[:, 0] == "Benötigte Kurse"]

        if not row.empty:
            if pd.notna(row.iloc[0,1]):
                prerequisite_courses_raw = row.iloc[0,1]
                prerequisite_courses = [course.strip() for course in prerequisite_courses_raw.split(",")]

                for prerequisite_course in prerequisite_courses:
                    if "|" in prerequisite_course:
                        equivalent_courses = [course.strip() for course in prerequisite_course.split("|")]
                        helper_nodes.append(["OR " + str(prerequisite_index), "white", "course", "prerequiste_equivalence"])
                        additional_edges.append(["OR " + str(prerequisite_index), course_name, 2])
                        for equivalent_course in equivalent_courses:
                            equivalent_course_name = getFullCourseName(equivalent_course, course_names)
                            additional_edges.append([equivalent_course_name, "OR " + str(prerequisite_index), 2])

                        prerequisite_index +=1
                    else:
                        prerequisite_course_name = getFullCourseName(prerequisite_course, course_names)
                        additional_edges.append([prerequisite_course_name, course_name, 2])

        #Get rows where courses are contained that result into not beeing able to taking this course
        row = course[course.iloc[:, 0] == "Not Taken"]
        if not row.empty:
            if pd.notna(row.iloc[0, 1]):
                exclusive_courses_raw = row.iloc[0, 1]
                exclusive_courses = [course.strip() for course in exclusive_courses_raw.split(",")]

                for exclusive_course in exclusive_courses:
                    exclusive_course_name = getFullCourseName(exclusive_course, course_names)
                    additional_edges.append([exclusive_course_name, course_name, -2])

    return additional_edges, helper_nodes