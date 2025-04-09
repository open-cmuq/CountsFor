# pylint: disable=all

import pandas as pd
import json
from typing import *
from pandas.io.excel._openpyxl import OpenpyxlReader
from pandas._typing import Scalar


def formatCourseNumber (n: int) -> str:
    """
    Adds a trailing zero and dash after department code to format
    course numbers.

    Args:
        n (e.g. 2251)

    Returns:
        the formatted course number as a string (e.g. "02-251")
    """

    n = str(n)
    if len(n) == 4:
        n = "0" + n
    code = n[:2]
    num = n[2:]
    return code + "-" + num

# A mapping of department codes to names
# Source: https://www.cmu.edu/hub/registrar/student-records/transcripts/legend.html
dept_map = {
    "02": "Computational Biology",
    "03": "Biological Sciences",
    "05": "Human-Computer Interaction",
    "07": "School of Computer Science",
    "09": "Chemistry",
    "10": "Machine Learning",
    "11": "Language Technologies Institute",
    "14": "Information Networking Institute",
    "15": "Computer Science Department",
    "16": "Robotics",
    "17": "Software Engineering",
    "18": "Electrical & Computer Engineering",
    "19": "Engineering & Public Policy",
    "21": "Mathematical Sciences",
    "36": "Statistics",
    "42": "Biomedical Engineering",
    "45": "Tepper School of Business",
    "60": "Art",
    "64": "Center for the Arts in Society",
    "65": "General Dietrich College",
    "66": "Dietrich College Interdisciplinary",
    "67": "Dietrich College Information Systems",
    "70": "Business Administration",
    "73": "Economics",
    "76": "English",
    "79": "History",
    "80": "Philosophy",
    "82": "Modern Languages",
    "85": "Psychology",
    "88": "Social & Decision Sciences",
    "99": "Carnegie Mellon University-Wide Studies",
}

# A map of the long counts_for string to something more readable.
# This doesn't cover everything, but we'll handle others manually.
countsfor_map = {
    # CS Electives
    "BS in Computer Science---Computer Science---Logics & Languages Elective": "Logics & Languages Elective",
    "BS in Computer Science---Computer Science---Software Systems Elective": "Software Systems Elective",
    "BS in Computer Science---Computer Science---Domains Elective": "Domains Elective",
    "BS in Computer Science---Computer Science---Artificial Intelligence Elective": "Artificial Intelligence Elective",
    "BS in Computer Science---2 SCS Electives": "2 SCS Electives",
    # Math
    "BS in Computer Science---Mathematics and Probability---Calculus": "Mathematics and Probability",
    "BS in Computer Science---Mathematics and Probability---Mathematical Foundations for CS": "Mathematics and Probability",
    "BS in Computer Science---Mathematics and Probability---Matrix/Linear Algebra": "Mathematics and Probability",
    "BS in Computer Science---Mathematics and Probability---Calculus---3d Calculus": "Mathematics and Probability",
    "BS in Computer Science---Mathematics and Probability---Probability":"Mathematics and Probability",
    # CS Core
    "BS in Computer Science---Computer Science---xx-213 Introduction to Computer Systems": "Computer Science Core",
    "BS in Computer Science---First-year Immigration Course": "Computer Science Core",
    "BS in Computer Science---Computer Science": "Computer Science Core",
    # Core Other
    "EY2023 Qatar CS - General Education---First Year Writing": "Writing",
    "GenEd---First Year Writing": "Writing",
    "BS in Computer Science---Technical Communication": "Writing",
    "BS in Computer Science---Computing @ Carnegie Mellon": "Core@CMU",
    # Humanities Electives
    "EY2023 Qatar CS - General Education---Humanities/Arts Electives": "Humanities/Arts Electives",
    "EY2023 Qatar CS - General Education---Category 1---Category 1: Cognition, Choice, and Behavior (CS, CB, & HCI)": "Cognition, Choice, and Behavior",
    "EY2023 Qatar CS - General Education---Category 2: Economic, Political, and Social Institutions": "Economic, Political, and Social Institutions",
    "EY2023 Qatar CS - General Education---Category 3: Cultural Analysis": "Cultural Analysis",
    "GenEd---Humanities/Arts Electives": "Humanities/Arts Electives",
    "GenEd---Category 1---Category 1: Cognition, Choice, and Behavior (CS, CB, & HCI)": "Cognition, Choice, and Behavior",
    "GenEd---Category 2: Economic, Political, and Social Institutions": "Economic, Political, and Social Institutions",
    "GenEd---Category 3: Cultural Analysis": "Cultural Analysis",
    #"Humanities and Arts": "Humanities and Arts",
    # Science
    "EY2023 Qatar CS - General Education---Science and Engineering---Science and Engineering (CS, AI, & HCI)---Science/Engineering, Same Department (2 courses)---Option 2---Biology Course": "Science and Engineering",
    "EY2023 Qatar CS - General Education---Science and Engineering---Science and Engineering (CS, AI, & HCI)---Science/Engineering, Any Department (4 courses)": "Science and Engineering",
    "EY2023 Qatar CS - General Education---Science and Engineering---Science and Engineering (CS, AI, & HCI)---Science/Engineering, Same Department (2 courses)---Option 1": "Science and Engineering",
    "EY2023 Qatar CS - General Education---Science and Engineering---Science and Engineering (CS, AI, & HCI)---Science/Engineering, Same Department (2 courses)---Option 2": "Science and Engineering",
    "EY2023 Qatar CS - General Education---Science and Engineering---Science and Engineering (CS, AI, & HCI)---Lab Requirement": "Lab Requirement",
    "GenEd---Science and Engineering---Science and Engineering (CS, AI, & HCI)---Science/Engineering, Same Department (2 courses)---Option 2---Biology Course": "Science and Engineering",
    "GenEd---Science and Engineering---Science and Engineering (CS, AI, & HCI)---Science/Engineering, Any Department (4 courses)": "Science and Engineering",
    "GenEd---Science and Engineering---Science and Engineering (CS, AI, & HCI)---Science/Engineering, Same Department (2 courses)---Option 1": "Science and Engineering",
    "GenEd---Science and Engineering---Science and Engineering (CS, AI, & HCI)---Science/Engineering, Same Department (2 courses)---Option 2": "Science and Engineering",
    "GenEd---Science and Engineering---Science and Engineering (CS, AI, & HCI)---Lab Requirement": "Lab Requirement",
}

# Requirements to kill from the list because they aren't relevant to the CS major
countsfor_kill = {
    "EY2023 Qatar CS - General Education---Science and Engineering---Science and Engineering (CB)---Science/Engineering, Any Department (4 courses)---Modern Biology",
    "EY2023 Qatar CS - General Education---Science and Engineering---Science and Engineering (CB)---Science/Engineering, Same Department (2 courses)---Modern Biology",
    "EY2023 Qatar CS - General Education---Science and Engineering---Science and Engineering (CB)---Science/Engineering, Same Department (2 courses)---Molecular Biology",
    "EY2023 Qatar CS - General Education---Science and Engineering---Science and Engineering (CB)---Lab Requirement",
    "EY2023 Qatar CS - General Education---Science and Engineering---Science and Engineering (CB)---Science/Engineering, Any Department (4 courses)---Molecular Biology",
    "EY2023 Qatar CS - General Education---Science and Engineering---Science and Engineering (CB)---Science/Engineering, Any Department (4 courses)---Chemistry",
    "EY2023 Qatar CS - General Education---Science and Engineering---Science and Engineering (CB)---Science/Engineering, Any Department (4 courses)---Physics",
    "EY2023 Qatar CS - General Education---Category 1---Category 1A: Cognitive Studies (AI)",
    "GenEd---Science and Engineering---Science and Engineering (CB)---Science/Engineering, Any Department (4 courses)---Modern Biology",
    "GenEd---Science and Engineering---Science and Engineering (CB)---Science/Engineering, Same Department (2 courses)---Modern Biology",
    "GenEd---Science and Engineering---Science and Engineering (CB)---Science/Engineering, Same Department (2 courses)---Molecular Biology",
    "GenEd---Science and Engineering---Science and Engineering (CB)---Lab Requirement",
    "GenEd---Science and Engineering---Science and Engineering (CB)---Science/Engineering, Any Department (4 courses)---Molecular Biology",
    "GenEd---Science and Engineering---Science and Engineering (CB)---Science/Engineering, Any Department (4 courses)---Chemistry",
    "GenEd---Science and Engineering---Science and Engineering (CB)---Science/Engineering, Any Department (4 courses)---Physics",
    "GenEd---Category 1---Category 1A: Cognitive Studies (AI)",
}

def countsFor (course_number: str, audit: pd.DataFrame) -> Set[str]:
    """
    Given a course number and an audit, returns a set of
    sub-requirements the course counts for in the audit.

    Args:
        course_number: e.g. "15-150"
        audit: a DataFrame with the following columns:
               - Course or code
               - Requirement (e.g. "Humanities and Arts")
               - Inclusion/Exclusion
               - Type

    Returns:
        a set of the requirements the course fulfills
    """

    # Requirements that include the course explicitly.
    matched = audit[(audit["Type"] == "Course") &
                    (audit["Course or code"] == course_number) &
                    (audit["Inclusion/Exclusion"] == "Inclusion")]
    include_course = set(matched["Requirement"].values)

    # Requirements that include the course because of its code
    matched_code = audit[(audit["Type"] == "Code") &
                         (audit["Course or code"] == course_number[0:2]) &
                         (audit["Inclusion/Exclusion"] == "Inclusion")]
    include_code = set(matched_code["Requirement"].values)

    # Requirements that exclude the course explicitly
    excluded = audit[(audit["Type"] == "Course") &
                     (audit["Course or code"] == course_number) &
                     (audit["Inclusion/Exclusion"] == "Exclusion")]
    exclude_course = set(excluded["Requirement"].values)

    # Course cannot be included and excluded for the same requirement
    assert(include_course.intersection(exclude_course) == set())

    counts_for = (include_course | include_code) - exclude_course

    return counts_for

def countsForCS (course_number: str, audit: pd.DataFrame) -> Set[str]:
    """
    Given a course number and an audit, returns a set of
    sub-requirements the course counts for in the audit.

    Args:
        course_number: e.g. "15-150"
        audit: a DataFrame with the following columns:
               - Course or code
               - Requirement (e.g. "Humanities and Arts")
               - Inclusion/Exclusion
               - Type

    Returns:
        a set of the requirements the course fulfills, in which the
        CS requirements are simplified.
    """
    counts_for = countsFor(course_number, audit)
    #print(course_number, counts_for)

    # Filter the categories through the translation map above.
    new_set = set()
    for item in counts_for:
        if item in countsfor_kill:
            continue;

        if item in countsfor_map:
            new_set.add(countsfor_map[item])
        else:
            new_set.add(item)
            print("Warning: Unknown requirement: ", course_number, item)

    return new_set

def getCourseTitle(course_number: str) -> str:
    """
    Given a course number, return the course title.
    The json files used to get this information are obtained from
    Stellic using a script written by Prof. Ryan Riley.
    """

    if len(course_number) == 2: # Code, not a course
        return dept_map.get(course_number, "Unknown department")

    try:
        file = open('data/course-details/' + course_number + '.json')
    except FileNotFoundError:
        # print("No file for course: " + course_number)
        return "<No file>"
    else:
        data = json.load(file)
        if data["success"]:
            return data["name"]
        else:
            return "Invalid course"

def getCourseUnits(course_number: str) -> str:
    """
    Given a course number, return the number of units
    The json files used to get this information are obtained from
    Stellic using a script written by Prof. Ryan Riley.
    """

    if len(course_number) == 2: # Code, not a course
        return ""

    try:
        file = open('data/course-details/' + course_number + '.json')
    except FileNotFoundError:
        # print("No file for course: " + course_number)
        return "<No file>"
    else:
        data = json.load(file)
        if data["success"]:
            return data["units"]
        else:
            return "0"

def getPreReqs(course_number: str) -> str:
    """
    Given a course number, return the pre-requisites as listed in
    Stellic.
    The json files used to get this information are obtained from
    Stellic using a script written by Prof. Ryan Riley.

    To do: If the pre-reqs were listed in a more structured way, we
    could make a dependency graph of courses.
    """

    if len(course_number) < 5: #probably a course code, not a course
        return ""

    try:
        file = open('data/course-details/' + course_number + '.json')
    except FileNotFoundError:
        # print("No file for course: " + course_number)
        return "<No file>"
    else:
        data = json.load(file)
        if data["success"]:
            prereqs = data['prereqs']['text']
            #if data['prereqs']['raw_pre_req'] != '':
            #    print(data['prereqs']['raw_pre_req'])
            return prereqs
        else:
            return ""

def cmpSemester(s1: str, s2: str) -> int:
    """
    Function to pass to sorted for sorting semesters.
    Usage: sorted(s, key=functools.cmp_to_key(cmpSemester))
    where s is a list of strings in the format {S,M,F}XX.

    Returns:
        negative int if s1 is before      s2
        zero         if s1 is the same as s2
        positive int if s1 is after       s2
    """

    if s1[1:] < s2[1:]:
        return -1
    elif s1[1:] > s2[1:]:
        return 1
    else:
        # S < M < F
        d = {'S': 0, 'M': 1, 'F': 2}
        s1 = d[s1[0]]
        s2 = d[s2[0]]
        return s1 - s2

class CustomReader(OpenpyxlReader):
    """
    A custom class to read from a spreadsheet, but skip rows that are strikethrough.

    This just simplifies working with Jarrin's excel files.

    Idea for code from https://stackoverflow.com/questions/59525171/pandas-read-excel-and-skip-cells-with-strikethrough

    get_sheet_data code copied from <Python base directory>/lib/python3.10/site-packages/pandas/io/excel/_openpyxl.py from pandas 2.1.0
    """
    def get_sheet_data(
        self, sheet, file_rows_needed = None
    ) -> list[list[Scalar]]:
        if self.book.read_only:
            sheet.reset_dimensions()

        data: list[list[Scalar]] = []
        last_row_with_data = -1
        for row_number, row in enumerate(sheet.rows):
            #########################################################
            # Custom code to not read row if row[1] item is strikethrough
            if len(row) > 1:
                first = row[1]
                if first.font == None or first.font.strike:
                    continue
            #########################################################

            converted_row = [self._convert_cell(cell) for cell in row]
            while converted_row and converted_row[-1] == "":
                # trim trailing empty elements
                converted_row.pop()
            if converted_row:
                last_row_with_data = row_number
            data.append(converted_row)
            if file_rows_needed is not None and len(data) >= file_rows_needed:
                break

        # Trim trailing empty rows
        data = data[: last_row_with_data + 1]

        if len(data) > 0:
            # extend rows to max width
            max_width = max(len(data_row) for data_row in data)
            if min(len(data_row) for data_row in data) < max_width:
                empty_cell: list[Scalar] = [""]
                data = [
                    data_row + (max_width - len(data_row)) * empty_cell
                    for data_row in data
                ]

        return data

class CustomExcelFile(pd.ExcelFile):
    _engines = {"openpyxl": CustomReader,}


def read_old_format(filename: str):
    """
    Read in the schedule if it is in the "old" (pre-Fall 2024) format.
    An example is: data/schedules/2023b-fall.xlsx
    """

    # Read in the excel file, but exclude strikethrow rows
    # This code is potentially brittle and tied to a specific pandas version.
    # If it stops working, replace these next two lines with
    # schedule = pd.read_excel('data/schedules/2024a-spring.xlsx')
    schedule = CustomExcelFile(filename, engine="openpyxl")
    schedule = schedule.parse()

    # Transforms 3121 into "03-121"
    schedule["COURSE"] = schedule["COURSE"].map(formatCourseNumber)

    # Selects only relevant columns
    schedule = schedule[
        [
            "COURSE",
            "SECTION",
            "COURSE TITLE",
            "UNITS",
            "MINI",
            "DAY",
            "BEGIN TIME",
            "END TIME",
            "INSTRUCTORS",
        ]
    ]

    # Adds column with pre-reqs
    schedule["Pre-reqs"] = schedule.apply(
        lambda row: getPreReqs(row["COURSE"]), axis=1
    )

    # Figure out what it counts for
    audit = pd.read_excel(
        "data/audits-xlsx/cs-audit.xlsx", dtype={"Course or code": str}
    )
    schedule["counts-for"] = schedule.apply(
        lambda row: countsForCS(row["COURSE"], audit), axis=1
    )

    schedule.sample(n=5)
    return schedule, audit


def read_infosilem_format(filename: str):
    """
    Read in the schedule that is in the "new" (Fall 2024) format that is output by infosilem.

    Example: data/schedules/2024b-fall-trial-mar18.xlsx
    """
    schedule = CustomExcelFile(filename, engine="openpyxl")
    schedule = schedule.parse()

    # schedule["COURSE"] = schedule["Course - ID"].map(lambda s: s.split()[0])
    # Transforms 3121 into "03-121"
    schedule["COURSE"] = schedule["Course - ID"].map(formatCourseNumber)

    schedule["SECTION"] = schedule["Component - ID"]

    # Some of these cells contain single times, others contain a multiline string of times.  Who does that?  Seriously.
    from datetime import datetime

    def map_time(s):
        if type(s) == str:
            return datetime.strptime(s.split("\n")[0], "%H:%M").time()
        else:
            return s

    schedule["BEGIN TIME"] = schedule["Delivery times - Start time"].map(map_time)
    schedule["END TIME"] = schedule["Delivery times - End time"].map(map_time)

    # Calculating the end time is painful because everything is imported as datetime.time objects, which aren't add/subtractable.
    # from datetime import datetime, date, time
    # schedule["START"] = schedule["Start time"].map(lambda t: datetime.combine(date.today(), t))
    # schedule["DUR"] = schedule["Duration"].map(lambda t: datetime.combine(date.today(), t) - datetime.combine(date.today(), time(0,0)))
    # schedule["END TIME"] = schedule["START"] + schedule["DUR"]
    # schedule["END TIME"] = schedule["END TIME"].map(lambda d: d.time())

    schedule["INSTRUCTORS"] = schedule["Professor - Last name"].map(str)

    # Maps the days from full names to UTR style.
    def map_day(day_string):
        if type(day_string) != str:
            return ""
        day_dict = {
            "Sunday": "U",
            "Monday": "M",
            "Tuesday": "T",
            "Wednesday": "W",
            "Thursday": "R",
            "Friday": "F",
            "Saturday": "S",
        }
        days = day_string.split("\n")
        res = ""
        for day in days:
            res += day_dict.get(day, "")
        return res

    schedule["DAY"] = schedule["Delivery times - Day"].map(map_day)

    # Get the course titles
    schedule["COURSE TITLE"] = schedule.apply(
        lambda row: getCourseTitle(row["COURSE"]), axis=1
    )

    schedule["UNITS"] = schedule.apply(
        lambda row: getCourseUnits(row["COURSE"]), axis=1
    )

    schedule = schedule[
        [
            "COURSE",
            "SECTION",
            "COURSE TITLE",
            "UNITS",
            #'MINI',
            "DAY",
            "BEGIN TIME",
            "END TIME",
            "INSTRUCTORS",
        ]
    ]

    # Adds column with pre-reqs
    schedule["Pre-reqs"] = schedule.apply(
        lambda row: getPreReqs(row["COURSE"]), axis=1
    )

    # Figure out what it counts for
    audit = pd.read_excel(
        "data/audits-xlsx/cs-audit.xlsx", dtype={"Course or code": str}
    )
    schedule["counts-for"] = schedule.apply(
        lambda row: countsForCS(row["COURSE"], audit), axis=1
    )

    return schedule, audit
