"""
this script contains all the models for the gened database
"""

from sqlalchemy import Column, Integer, String, Boolean, SmallInteger, ForeignKey, Text
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Department(Base):
    """
    Department model
    """
    __tablename__ = 'department'
    dep_code = Column(String(20), primary_key=True)
    name = Column(Text)

    courses = relationship("Course", back_populates="department")

class Course(Base):
    """
    Course model
    """
    __tablename__ = 'course'
    course_code = Column(String(20), primary_key=True)
    name = Column(Text)
    units = Column(SmallInteger)
    min_units = Column(SmallInteger)
    max_units = Column(SmallInteger)
    offered_qatar = Column(Boolean)
    offered_pitts = Column(Boolean)
    short_name = Column(Text)
    description = Column(Text)
    dep_code = Column(String(20), ForeignKey('department.dep_code'))
    prereqs_text = Column(Text)

    prerequisites = relationship("Prereqs", back_populates="course")
    counts_for = relationship("CountsFor", back_populates="course")
    offerings = relationship("Offering", back_populates="course")
    instructor = relationship("CourseInstructor", back_populates="course")
    department = relationship("Department", back_populates="courses")

class Prereqs(Base):
    """
    Prereqs model
    """
    __tablename__ = 'prereqs'
    course_code = Column(String(20), ForeignKey('course.course_code'), primary_key=True)
    prerequisite = Column(String(20), primary_key=True)
    group_id = Column(Integer, primary_key=True)
    logic_type = Column(String(20))

    course = relationship("Course", back_populates="prerequisites")

class Offering(Base):
    """
    Offering model: offerings od courses in the past
    """
    __tablename__ = 'offering'
    offering_id = Column(String(50), primary_key=True)
    semester = Column(String(20))
    course_code = Column(String(20), ForeignKey('course.course_code'))
    campus_id = Column(Integer)

    course = relationship("Course", back_populates="offerings")

class Instructor(Base):
    """
    Instructor model
    """
    __tablename__ = 'instructor'
    andrew_id = Column(Text, primary_key=True)
    first_name = Column(Text)
    last_name = Column(Text)

    courses = relationship("CourseInstructor", back_populates="instructor")

class CourseInstructor(Base):
    """
    CourseInstructor model: many-to-many relationship between course and instructor
    """
    __tablename__ = 'course_instructor'
    andrew_id = Column(Text, ForeignKey('instructor.andrew_id'), primary_key=True)
    course_code = Column(String(20), ForeignKey('course.course_code'), primary_key=True)
    course = relationship("Course", back_populates="instructor")
    instructor = relationship("Instructor", back_populates="courses")

class CountsFor(Base):
    """
    CountsFor model: many-to-many relationship between course and requirement
    """
    __tablename__ = 'countsfor'
    course_code = Column(String(20), ForeignKey('course.course_code'), primary_key=True)
    requirement = Column(Text, ForeignKey('requirement.requirement'), primary_key=True)

    course = relationship("Course", back_populates="counts_for")
    requirement_rel = relationship("Requirement", back_populates="counts_for")

class Requirement(Base):
    """
    Requirement model: requirements in each audit
    """
    __tablename__ = 'requirement'
    requirement = Column(Text, primary_key=True)
    audit_id = Column(String(100), ForeignKey('audit.audit_id'))  # Reference to new audit_id

    counts_for = relationship("CountsFor", back_populates="requirement_rel")

class Audit(Base):
    """
    Audit model: audit for each major
    """
    __tablename__ = 'audit'
    audit_id = Column(String(100), primary_key=True)
    name = Column(Text)
    type = Column(Boolean)
    major = Column(Text)

class Enrollment(Base):
    """
    Enrollment model: enrollment data for each class
    """
    __tablename__ = 'enrollment'
    enrollment_id = Column(String(100), primary_key=True)
    class_ = Column("class", Integer)
    enrollment_count = Column(Integer)
    department = Column(String(20))
    section = Column(String(20))
    offering_id = Column(String(50), ForeignKey('offering.offering_id'))
