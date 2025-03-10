import pandas as pd
import re
import networkx as nx
import sqlite3

#Construct the course name based on the first row of the DataFrame representing the course
def getCourseName(course):
    course_name = ""

    if not "Modul" in str(course.iloc[0, 0]):
        course_name += str(course.iloc[0, 0]).strip()

    if not pd.isna(course.iloc[0, 1]) and not course.iloc[0, 1] == "":
        if len(course_name) > 0:
            course_name += " " + str(course.iloc[0, 1]).strip()
        else:
            course_name += str(course.iloc[0, 1]).strip()

    return course_name

#Mapping from the course names in the graph to the course names in the database
def mapGraphToDB_courseName(course_name):
    if isinstance(course_name, pd.DataFrame):
        course_name = getCourseName(course_name)

    if course_name == "ACC 520 IFRS Accounting and Capital Markets":
        return "ACC 520 IFRS Reporting and Capital Markets"
    elif course_name == "ACC 620 Accounting for Financial Instruments and Financial Institutions":
        return "ACC 620 Accounting for Financial Instruments & Financial Institutions"
    elif course_name == "CS 710 Selected Topics in Data Science":
        return "CS 710 Seminar Selected Topics in Data Science"
    elif course_name == "CS 716 IT-Security":
        return "CS 716 Seminar IT-Security"
    elif course_name == "FIN 580 Derivatives I – Basic Strategies and Pricing":
        return "FIN 580 Derivatives I - Basic Strategies and Pricing"
    elif course_name == "IS 712 Contemporary Issues in Information Systems Research":
        return "IS 712 Seminar"
    elif course_name == "IS 722 Seminar: Context-Aware and Distributed Systems":
        return "IS 722 Seminar Trends in Distributed Systems"
    elif course_name == "MAN 655 Corporate Strategy: Managing Business Groups":
        return "MAN 655  Corporate Strategy: Managing Business Groups"
    elif course_name == "OPM 503 Transportation I – Land Transport and Shipping":
        return "OPM 503 Transportation I - Land Transport and Shipping"
    elif course_name == "OPM 504 Transportation II – Aviation":
        return "OPM 504 Transportation II: Air Transport"
    elif course_name == "OPM 544 Demand-driven adaptive supply chain planning":
        return "OPM 544 Advanced Supply Chain Planning"
    else:
        return course_name

#Mapping from the course names in the database to the course names in the graph
def mapDBtoGraph_courseName(course_name):
    if isinstance(course_name, pd.DataFrame):
        course_name = getCourseName(course_name)

    if course_name == "ACC 520 IFRS Reporting and Capital Markets":
        return "ACC 520 IFRS Accounting and Capital Markets"
    elif course_name == "ACC 620 Accounting for Financial Instruments & Financial Institutions":
        return "ACC 620 Accounting for Financial Instruments and Financial Institutions"
    elif course_name == "CS 710 Seminar Selected Topics in Data Science":
        return "CS 710 Selected Topics in Data Science"
    elif course_name == "CS 716 Seminar IT-Security":
        return "CS 716 IT-Security"
    elif course_name == "FIN 580 Derivatives I - Basic Strategies and Pricing":
        return "FIN 580 Derivatives I – Basic Strategies and Pricing"
    elif course_name == "IS 712 Seminar":
        return "IS 712 Contemporary Issues in Information Systems Research"
    elif course_name == "IS 722 Seminar Trends in Distributed Systems":
        return "IS 722 Seminar: Context-Aware and Distributed Systems"
    elif course_name == "MAN 655  Corporate Strategy: Managing Business Groups":
        return "MAN 655 Corporate Strategy: Managing Business Groups"
    elif course_name == "OPM 503 Transportation I - Land Transport and Shipping":
        return "OPM 503 Transportation I – Land Transport and Shipping"
    elif course_name == "OPM 504 Transportation II: Air Transport":
        return "OPM 504 Transportation II – Aviation"
    elif course_name == "OPM 544 Advanced Supply Chain Planning":
        return "OPM 544 Demand-driven adaptive supply chain planning"
    else:
        return course_name

#Reconstructs the full course name by matching a search string to a list of course names
def getFullCourseName(searchString, courseNames):
    for courseName in courseNames:
        if searchString in courseName:
            return courseName

    return ""

#Extracts the course names that match the search string and not match the main course
def getMatchingCourses(searchString, courseNames, mainCourse):
    matchingCourses = []
    for courseName in courseNames:
        if searchString in courseName and not mainCourse in courseName:
            matchingCourses.append(courseName)

    return matchingCourses

#Extract the information for the construction of the course nodes from the DataFrames representing the courses
def getCourseNodes(courses):
    nodes = []

    for course in courses:

        #Get name of course
        course_name = getCourseName(course)

        #Get ECTS
        ECTS_row = course[course.iloc[:, 0] == "ECTS"]
        ECTS = ECTS_row.iloc[0,1]

        #Get offering cycle
        offering_cycle_row = course[course.iloc[:, 0] == "Offering"]
        offering_cycle = offering_cycle_row.iloc[0,1]

        nodes.append([course_name, ECTS, offering_cycle])

    return nodes

#Constructs the course -> skill edges of all courses of the Mannheim Master in Management based on their corresponding
#area except for the IS courses
def addBWLEdges(courses):
    additional_edges = []

    #edges = pd.read_excel(edges_path)

    for course in courses:
        course_name = getCourseName(course)
        if "ACC" in course_name or "TAX" in course_name:
            additional_edges.append([course_name, "Accounting and Taxation (AAT)"])
        elif "FIN" in course_name:
            additional_edges.append([course_name, "Banking, Finance, and Insurance (FIN)"])
        elif "MAN" in course_name:
            additional_edges.append([course_name, "Management (MAN)"])
        elif "MKT" in course_name:
            additional_edges.append([course_name, "Marketing and Sales (MKT)"])
        elif "OPM" in course_name:
            additional_edges.append([course_name, "Operations Management (OPM)"])

    return additional_edges




#Create all edges representing prerequiste relationships as well as the skill -> course edges
def complete_edges(courses, edges):
    df_bwl_edges = pd.DataFrame(addBWLEdges(courses), columns=["Outgoing", "Ingoing"])

    edges = pd.concat([edges, df_bwl_edges], ignore_index=True)

    additional_edges = addBWLEdges(courses)

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
        if row.empty:
            row = course[course.iloc[:, 0] == "Prerequisites"]

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
                        knowledge_course_names = getMatchingCourses(course_knowledge, course_names, course_name)
                        for knowledge_course_name in knowledge_course_names:
                            escaped_course_knowledge = re.escape(knowledge_course_name)
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
                        gate_created = False
                        equivalent_courses = [course.strip() for course in prerequisite_course.split("|")]
                        for equivalent_course in equivalent_courses:
                            if not equivalent_course == "":
                                matching_courses = getMatchingCourses(equivalent_course, course_names, course_name)
                                for matching_course in matching_courses:
                                    if not gate_created:
                                        helper_nodes.append(["MIN " + str(prerequisite_index), "yellow", "prerequisite", "MIN", 1])
                                        additional_edges.append(["MIN " + str(prerequisite_index), course_name, 1])
                                        gate_created = True
                                    additional_edges.append([matching_course, "MIN " + str(prerequisite_index), 1])
                        if gate_created:
                            prerequisite_index += 1
                    else:
                        prerequisite_course_names = getMatchingCourses(prerequisite_course, course_names, course_name)
                        for prerequisite_course_name in prerequisite_course_names:
                            additional_edges.append([prerequisite_course_name, course_name, 1])

        #Get rows where courses are contained that result into not beeing able to taking this course
        row = course[course.iloc[:, 0] == "Not Taken"]
        if not row.empty:
            if pd.notna(row.iloc[0, 1]):
                exclusive_courses_raw = row.iloc[0, 1]
                exclusive_courses = [course.strip() for course in exclusive_courses_raw.split(",")]

                for exclusive_course in exclusive_courses:
                    exclusive_course_names = getMatchingCourses(exclusive_course, course_names, course_name)
                    for exclusive_course_name in exclusive_course_names:
                        additional_edges.append([exclusive_course_name, course_name, -1])

        row = course[course.iloc[:, 0] == "Successor"]
        if not row.empty:
            if pd.notna(row.iloc[0, 1]):
                successor_courses_raw = row.iloc[0, 1]
                successor_courses = [course.strip() for course in successor_courses_raw.split(",")]

                for successor_course in successor_courses:
                    successor_courses_names = getMatchingCourses(successor_course, course_names, course_name)
                    for successor_courses_name in successor_courses_names:
                        additional_edges.append([course_name, successor_courses_name, 3])

    return additional_edges, helper_nodes

#Extract all edges where the connected nodes have a certain value for one of their attributes
def getFilteredEdges(graph, outgoing_node_attribute, ingoing_node_attribute, outgoing_node_value, ingoing_node_value):
    filteredEdges = []

    for u, v in graph.edges():
        if (graph.nodes[u].get(outgoing_node_attribute) == outgoing_node_value and
                graph.nodes[v].get(ingoing_node_attribute) == ingoing_node_value):
            filteredEdges.append((u,v))

    return filteredEdges

#Script for weighting the course -> skill edges
def getCourseSkillWeights(graph, database, min):
    course_skill_edge_weights = []

    #Get edges relevant for the script (course -> skill and skill -> course edges)
    course_skill_edges = getFilteredEdges(graph, "type", "type", "course", "skill")
    skill_course_edges = getFilteredEdges(graph, "type", "type", "skill", "course")

    conn = sqlite3.connect(database)
    cursor = conn.cursor()

    #Create edge weight for all course -> skill edges
    for edge in course_skill_edges:
        course_providing_skill = edge[0]
        course_providing_skill_mapped = mapGraphToDB_courseName(course_providing_skill)
        skill = edge[1]

        #Get all courses that have an ingoing edge that is outgoing from the considered skill
        courses_requiring_skill = [tmp_edge[1] for tmp_edge in skill_course_edges if tmp_edge[0] == skill]

        if course_providing_skill in courses_requiring_skill:
            courses_requiring_skill.remove(course_providing_skill)

        average_grades_with_course = []
        average_grades_without_course = []

        #Compute average grades for students that passed the courses
        for course_requiring_skill in courses_requiring_skill:
            course_requiring_skill_mapped = mapGraphToDB_courseName(course_requiring_skill)

            #Get the average grade achieved in the course when students completed the considered course prior
            query = """SELECT AVG(note), COUNT(note) 
                       FROM pruefungsleistung p JOIN studium s ON p.studium_id = s.studium_id
                       WHERE ? LIKE p.bezeichnung || '%' AND s.studium_bezeichnung = 'Wirtschaftsinformatik' AND s.studium_art = 'Master' 
                       AND p.status IN ("BE", "NB") AND s.status IN ("BE", "R", "NB", "N")
                       AND EXISTS(
                           SELECT *
                           FROM pruefungsleistung p2 JOIN studium s2 ON p2.studium_id = s2.studium_id
                           WHERE ? LIKE p2.bezeichnung || '%' AND p2.semester < p.semester AND p2.status = "BE" AND p2.studium_id = p.studium_id
                        )
                        """
            cursor.execute(query, (course_requiring_skill_mapped, course_providing_skill_mapped,))
            results_with_course = cursor.fetchall()

            # Get the average grade achieved in the course when students didn't complete the considered course prior
            query = """SELECT AVG(note), COUNT(note) 
                        FROM pruefungsleistung p JOIN studium s ON p.studium_id = s.studium_id
                        WHERE ? LIKE p.bezeichnung || '%' AND s.studium_bezeichnung = 'Wirtschaftsinformatik' AND s.studium_art = 'Master'
                        AND p.status IN ("BE", "NB") AND s.status IN ("BE", "R", "NB", "N")
                        AND NOT EXISTS(
                           SELECT *
                           FROM pruefungsleistung p2 JOIN studium s2 ON p2.studium_id = s2.studium_id
                           WHERE ? LIKE p2.bezeichnung || '%' AND p2.semester < p.semester AND p2.status = "BE" AND p2.studium_id = p.studium_id
                        )
                        """
            cursor.execute(query, (course_requiring_skill_mapped, course_providing_skill_mapped,))
            results_without_course = cursor.fetchall()

            #Collect the results if exist
            if results_with_course and results_with_course[0][1] > 0:
                average_grades_with_course.append([results_with_course[0][0], results_with_course[0][1]])
            if results_without_course and results_without_course[0][1] > 0:
                average_grades_without_course.append([results_without_course[0][0], results_without_course[0][1]])

        grades_with_course = 0
        grades_without_course = 0
        count_with_course = 0
        count_without_course = 0

        #summarize average grades
        for grades in average_grades_with_course:
            grades_with_course += grades[0] * grades[1]
            count_with_course += grades[1]
        for grades in average_grades_without_course:
            grades_without_course += grades[0] * grades[1]
            count_without_course += grades[1]

        #calculate edge weight
        if count_with_course > 0 and count_without_course > 0:
            edge_weight = grades_without_course / count_without_course - grades_with_course / count_with_course
        else:
            edge_weight = min

        #Set age weight to zero if result is not representative
        if edge_weight < min:
            edge_weight = min

        course_skill_edge_weights.append([edge_weight, course_providing_skill, skill, count_with_course, count_without_course])

    conn.close()

    return course_skill_edge_weights

#Script for weighting the skill -> course edges
def getSkillCourseWeights(graph, database):
    course_names_graph = list(graph.nodes())

    skill_course_edge_weights = []

    edges_to_check = []

    skill_course_edges = getFilteredEdges(graph, "type", "type", "skill", "course")

    conn = sqlite3.connect(database)
    cursor = conn.cursor()

    for edge in skill_course_edges:
        skill = edge[0]
        course_requiring_skill = edge[1]
        course_requiring_skill_mapped = mapGraphToDB_courseName(course_requiring_skill)

        query = """SELECT DISTINCT p.studium_id, p.semester
                   FROM pruefungsleistung p JOIN studium s ON p.studium_id = s.studium_id
                   WHERE s.studium_bezeichnung = 'Wirtschaftsinformatik' AND s.studium_art = 'Master' AND 
                   p.status = "BE" AND ? LIKE p.bezeichnung || '%' AND s.status IN ("BE", "R", "NB", "N")
                    """
        cursor.execute(query, (course_requiring_skill_mapped,))
        students_passed_course = cursor.fetchall()

        skill_levels_for_passing = []
        if students_passed_course:
            for student in students_passed_course:
                study_id = student[0]
                semester = student[1]

                query = """SELECT DISTINCT bezeichnung
                           FROM pruefungsleistung
                           WHERE studium_id = ? AND semester < ? AND status = "BE"
                            """
                cursor.execute(query, (study_id, semester,))
                prior_passed_courses = cursor.fetchall()

                skill_level = 0
                if prior_passed_courses:
                    for course in prior_passed_courses:
                        course_name = mapDBtoGraph_courseName(course[0])
                        course_name_full = getFullCourseName(course_name, course_names_graph)
                        if graph.has_edge(course_name_full, skill):
                            skill_level += graph[course_name_full][skill].get("weight")
                        else:
                            edges_to_check.append([course_name, course_name_full, skill])

                skill_levels_for_passing.append(skill_level)

        if skill_levels_for_passing:
            average_skill_level_for_passing = sum(skill_levels_for_passing) / len(skill_levels_for_passing)
        else:
            average_skill_level_for_passing = 0
        skill_course_edge_weights.append([average_skill_level_for_passing, skill, course_requiring_skill,
                                         len(skill_levels_for_passing)])

    return skill_course_edge_weights, edges_to_check

def createPools(graph):
    for node in graph.nodes:
        if graph.nodes[node].get("type") == "course":
            if node[0:6] in ["CS 500", "CS 530", "CS 550", "CS 560", "IE 500", "IE 560", "IS 553"]:
                graph.nodes[node]["pool"] = "Fundamentals Computer Science"
            elif node[0:3] in ["ACC", "TAX", "FIN", "MAN", "MKT", "OPM"]:
                graph.nodes[node]["pool"] = "Fundamentals Business Administration"
            elif node[0:4] in ["CS 7", "IE 7", "IS 7"]:
                graph.nodes[node]["pool"] = "Seminars"
            elif node[0:2] in ["CS", "IE", "IS"]:
                graph.nodes[node]["pool"] = "Specialization Courses"
            elif node == "SQ 500 Scientific Research":
                graph.nodes[node]["pool"] = "Scientific Research"
            elif node[0:6] == "TP 500":
                graph.nodes[node]["pool"] = "Projects"
            elif node == "MA 650 Master Thesis":
                graph.nodes[node]["pool"] = "Thesis"
    return graph