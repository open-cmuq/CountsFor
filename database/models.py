from sqlalchemy import Column, Integer, String, Boolean, SmallInteger, ForeignKey, Text, PrimaryKeyConstraint, ForeignKeyConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Course(Base):
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
    dep_code = Column(String(20))
    prereqs_text = Column(Text)
    
    prerequisites = relationship("Prereqs", back_populates="course")
    counts_for = relationship("CountsFor", back_populates="course")
    offerings = relationship("Offering", back_populates="course")
    instructor = relationship("CourseInstructor", back_populates="course")

class Prereqs(Base):
    __tablename__ = 'prereqs'
    course_code = Column(String(20), ForeignKey('course.course_code'), primary_key=True)
    prerequisite = Column(String(20), primary_key=True)
    group_id = Column(Integer, primary_key=True)
    logic_type = Column(String(20))
    
    course = relationship("Course", back_populates="prerequisites")

class Offering(Base):
    __tablename__ = 'offering'
    offering_id = Column(String(50), primary_key=True)
    semester = Column(String(20))
    course_code = Column(String(20), ForeignKey('course.course_code'))
    campus_id = Column(Integer)
    
    course = relationship("Course", back_populates="offerings")

class Instructor(Base):
    __tablename__ = 'instructor'
    andrew_id = Column(Text, primary_key=True)
    first_name = Column(Text)
    last_name = Column(Text)    

    courses = relationship("CourseInstructor", back_populates="instructor")

class CourseInstructor(Base):
    __tablename__ = 'course_instructor'
    andrew_id = Column(Text, ForeignKey('instructor.andrew_id'), primary_key=True)
    course_code = Column(String(20), ForeignKey('course.course_code'), primary_key=True)
    course = relationship("Course", back_populates="instructor")
    instructor = relationship("Instructor", back_populates="courses")

class CountsFor(Base):
    __tablename__ = 'countsfor'
    course_code = Column(String(20), ForeignKey('course.course_code'), primary_key=True)
    requirement = Column(Text, ForeignKey('requirement.requirement'), primary_key=True)
    
    course = relationship("Course", back_populates="counts_for")
    requirement_rel = relationship("Requirement", back_populates="counts_for")

class Requirement(Base):
    __tablename__ = 'requirement'
    requirement = Column(Text, primary_key=True)
    audit_id = Column(String(100), ForeignKey('audit.audit_id'))  # Reference to new audit_id
        
    counts_for = relationship("CountsFor", back_populates="requirement_rel")

class Audit(Base):
    __tablename__ = 'audit'
    audit_id = Column(String(100), primary_key=True)
    name = Column(Text)
    type = Column(Boolean)
    major = Column(Text)

class Enrollment(Base):
    __tablename__ = 'enrollment'
    enrollment_id = Column(String(50), primary_key=True)
    class_ = Column("class", Integer)
    enrollment_count = Column(Integer)
    department = Column(String(20))
    section = Column(String(20))
    offering_id = Column(String(50), ForeignKey('offering.offering_id'))




