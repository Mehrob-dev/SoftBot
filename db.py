from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, BigInteger
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

db_url = 'postgresql://postgres:Programmer.33@localhost:5432/softbot'
engine = create_engine(db_url)

Base = declarative_base()


class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    tg_id = Column(BigInteger, unique=True, index=True)
    username = Column(String)
    registered_on = Column(DateTime, default=datetime.now)
    language = Column(String(4), default='en')

    student = relationship("Student", back_populates="user", uselist=False, cascade="all, delete-orphan")


class Student(Base):
    __tablename__ = 'students'

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    name = Column(String)
    surname = Column(String)
    age = Column(Integer)
    registered_on = Column(DateTime, default=datetime.now)
    phone_number = Column(String(20))

    current_course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)

    user = relationship("Users", back_populates="student")

    current_course = relationship("Courses", foreign_keys=[current_course_id])

    courses = relationship("Courses", secondary="studentcourses", back_populates="students")


class Courses(Base):
    __tablename__ = 'courses'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    duration = Column(Integer)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.now)

    students = relationship("Student", secondary="studentcourses", back_populates="courses")


class StudentCourses(Base):
    __tablename__ = 'studentcourses'

    id = Column(Integer, primary_key=True)

    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)

    enrolled_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        UniqueConstraint("student_id", "course_id", name="uq_student_course"),
    )


Base.metadata.create_all(engine)
