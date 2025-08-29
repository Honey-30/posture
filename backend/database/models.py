from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Profile information
    full_name = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    height = Column(Float, nullable=True)  # in cm
    weight = Column(Float, nullable=True)  # in kg
    gender = Column(String, nullable=True)
    fitness_level = Column(String, nullable=True)  # beginner, intermediate, advanced
    
    # User settings
    preferences = Column(JSON, nullable=True)
    
    # Relationships
    workouts = relationship("Workout", back_populates="user")
    exercise_logs = relationship("ExerciseLog", back_populates="user")
    achievements = relationship("UserAchievement", back_populates="user")

class Workout(Base):
    __tablename__ = "workouts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    calories_burned = Column(Float, nullable=True)
    name = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="workouts")
    exercise_logs = relationship("ExerciseLog", back_populates="workout")

class ExerciseLog(Base):
    __tablename__ = "exercise_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    workout_id = Column(Integer, ForeignKey("workouts.id"), nullable=True)
    exercise_type = Column(String)  # push_up, squat, plank, etc.
    reps = Column(Integer, nullable=True)
    sets = Column(Integer, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    form_score = Column(Float, nullable=True)  # 0-1 score for exercise form
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Detailed performance data
    performance_data = Column(JSON, nullable=True)  # For storing detailed form analysis
    
    # Relationships
    user = relationship("User", back_populates="exercise_logs")
    workout = relationship("Workout", back_populates="exercise_logs")

class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    description = Column(Text)
    badge_image = Column(String, nullable=True)
    requirement_type = Column(String)  # workout_count, rep_count, streak, etc.
    requirement_value = Column(Integer)
    
    # Relationships
    users = relationship("UserAchievement", back_populates="achievement")

class UserAchievement(Base):
    __tablename__ = "user_achievements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    achievement_id = Column(Integer, ForeignKey("achievements.id"))
    earned_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="achievements")
    achievement = relationship("Achievement", back_populates="users")

class NutritionLog(Base):
    __tablename__ = "nutrition_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(DateTime(timezone=True), server_default=func.now())
    meal_type = Column(String)  # breakfast, lunch, dinner, snack
    food_name = Column(String)
    calories = Column(Float)
    protein = Column(Float)
    carbs = Column(Float)
    fats = Column(Float)
    portion_size = Column(Float, nullable=True)
    
    # Relationship
    user = relationship("User")

class WaterIntake(Base):
    __tablename__ = "water_intake"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(DateTime(timezone=True), server_default=func.now())
    amount_ml = Column(Integer)  # Amount in milliliters
    
    # Relationship
    user = relationship("User")

class PostureLog(Base):
    __tablename__ = "posture_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    posture_score = Column(Float)  # 0-100 score
    posture_analysis = Column(JSON)  # Detailed posture data
    alert_triggered = Column(Boolean, default=False)
    correction_applied = Column(Boolean, default=False)
    
    # Relationship
    user = relationship("User")

class UserStats(Base):
    __tablename__ = "user_stats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(DateTime(timezone=True), server_default=func.now())
    
    # Daily stats
    steps_count = Column(Integer, default=0)
    active_minutes = Column(Integer, default=0)
    calories_consumed = Column(Float, default=0)
    calories_burned = Column(Float, default=0)
    water_intake_ml = Column(Integer, default=0)
    avg_posture_score = Column(Float, nullable=True)
    
    # Weekly/Monthly aggregates
    weekly_workout_count = Column(Integer, default=0)
    monthly_workout_count = Column(Integer, default=0)
    
    # Relationship
    user = relationship("User")