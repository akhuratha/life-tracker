import logging
logger = logging.getLogger(__name__)

import os
from typing import Iterable, Sequence
from uuid import uuid4

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, select, Date, Table
from sqlalchemy.orm import sessionmaker, declarative_base, validates, relationship
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.associationproxy import association_proxy
from datetime import date

Base = declarative_base()

from pathlib import Path

db_folder = str(Path(__file__).parent)


class XPProgression(Base):
    __tablename__ = 'xp_progressions'
    id = Column(String, primary_key=True)
    type = Column(String)
    xp = Column(Integer)
    level = Column(Integer)
    base = Column(Float)
    rate = Column(Float)

    @validates('type')
    def validate_type(self, key, value):
        assert value in ("LINEAR", "EXPONENTIAL"), "XPProgression type must be LINEAR or EXPONENTIAL"
        return value


class Goal(Base):
    __tablename__ = 'goals'
    id = Column(String, primary_key=True)
    name = Column(String)
    description = Column(String)
    parent_id = Column(String, ForeignKey('goals.id'))
    is_completed = Column(Boolean)
    due_date = Column(Date)


class Skill(Base):
    __tablename__ = 'skills'
    id = Column(String, primary_key=True)
    name = Column(String)
    description = Column(String)
    xp_progression_id = Column(String)


class Grind(Base):
    __tablename__ = 'grinds'
    id = Column(String, primary_key=True)
    name = Column(String)
    skill_id = Column(String)
    description = Column(String)
    xp_progression_id = Column(String)


class Habit(Base):
    __tablename__ = 'habits'
    id = Column(String, primary_key=True)
    name = Column(String)
    description = Column(String)
    is_binary_habit = Column(Boolean)
    is_negative_habit = Column(Boolean)
    target_frequency_value = Column(Float)
    target_frequency_unit = Column(String)
    target_period_in_days = Column(Integer)


class HabitLog(Base):
    __tablename__ = 'habit_logs'

    habit_id = Column(String, ForeignKey('habits.id'), primary_key=True)
    log_date = Column(Date, primary_key=True)
    value = Column(Float)

    habit = relationship("Habit")


class Task(Base):
    __tablename__ = 'tasks'
    id = Column(String, primary_key=True)
    title = Column(String)
    description = Column(String)
    is_completed = Column(Boolean)
    goal_id = Column(String, ForeignKey('goals.id'))
    grind_id = Column(String, ForeignKey('grinds.id'))
    habit_id = Column(String, ForeignKey('habits.id'))
    xp = Column(Integer)
    due_date = Column(Date)


class Account(Base):
    __tablename__ = 'accounts'
    id = Column(String, primary_key=True)
    name = Column(String)
    balance = Column(Float)
    type = Column(String)


transaction_tag_table = Table(
    'transaction_tags', Base.metadata,
    Column('transaction_id', String, ForeignKey('transactions.id'), primary_key=True),
    Column('tag_name', String, ForeignKey('tags.name'), primary_key=True)
)

class Tag(Base):
    __tablename__ = 'tags'
    name = Column(String, primary_key=True)
    transactions = relationship("Transaction", secondary=transaction_tag_table, back_populates="tags")


class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(String, primary_key=True)
    account_id = Column(String, ForeignKey('accounts.id'))
    amount = Column(Float)
    date = Column(Date)
    description = Column(String)
    tags = relationship("Tag", secondary=transaction_tag_table, back_populates="transactions")


def setup_database(db_url='sqlite:///database.db'):
    engine = create_engine(db_url)
    try:
        Base.metadata.create_all(engine)
        print("Database setup successfully")
    except SQLAlchemyError as e:
        print(f"Error setting up database: {e}")


def get_session(db_url='sqlite:///database.db'):
    # Extract path from db_url (works for sqlite file URL)
    if db_url.startswith("sqlite:///"):
        db_path = db_url.replace("sqlite:///", "")
    else:
        db_path = None  # For other DB types you can adjust logic

    engine = create_engine(db_url)

    # If SQLite file does NOT exist, create tables
    if db_path and not os.path.exists(db_path):
        setup_database(db_url)

    Session = sessionmaker(bind=engine)
    return Session()


class DbOps:
    def __init__(self, db_name="database.db"):

        db_url = f'sqlite:///{db_folder}/{db_name}'
        self.db = get_session(db_url)

    def create_goal(
            self,
            name: str,
            description: str,
            due_date: date,
            parent_goal: Goal | None = None
    ) -> Goal:
        goal = Goal(
            id=str(uuid4()),
            name=name,
            description=description,
            parent_id=parent_goal.id if parent_goal else None,
            is_completed=False,
            due_date=due_date,
        )

        self.db.add(goal)
        self.db.commit()
        self.db.refresh(goal)
        logger.info(f"Added goal: {goal.name} to the db")

        return goal

    def get_all_goals(self) -> Sequence[Goal]:
        return self.db.execute(select(Goal)).scalars().all()

    def create_habit(
            self,
            name: str,
            description: str,
            is_binary_habit: bool,
            is_negative_habit: bool,
            target_frequency_value: float,
            target_frequency_unit: str,
            target_period_in_days: int,
    ) -> Habit:
        habit = Habit(
            id=str(uuid4()),
            name=name,
            description=description,
            is_binary_habit=is_binary_habit,
            is_negative_habit=is_negative_habit,
            target_frequency_value=target_frequency_value,
            target_frequency_unit=target_frequency_unit,
            target_period_in_days=target_period_in_days,
        )

        self.db.add(habit)
        self.db.commit()
        self.db.refresh(habit)

        logger.info(f"Added Habit {habit.name} to the db")

        return habit

    def list_all_habits(self) -> Sequence[Habit]:
        return self.db.execute(select(Habit)).scalars().all()

    def add_habit_logs(

            self,
            log_date: date,
            habit_value_map: dict[str, float]
    ) -> list[HabitLog]:
        """
        Add habit logs for the specified date.

        Args:
            log_date: The date of the logs.
            habit_value_map: Dictionary mapping habit_id to the logged value.

        Returns:
            List of HabitLog instances added.
        """
        updated_logs = []

        for habit_id, value in habit_value_map.items():
            stmt = select(HabitLog).where(
                HabitLog.habit_id == habit_id,
                HabitLog.log_date == log_date
            )
            existing_log = self.db.execute(stmt).scalar_one_or_none()

            if existing_log:
                existing_log.value = value
                logger.info(f"Updated HabitLog for habit_id={habit_id}, date={log_date}")
                updated_logs.append(existing_log)
            else:
                new_log = HabitLog(
                    habit_id=habit_id,
                    log_date=log_date,
                    value=value
                )
                self.db.add(new_log)
                updated_logs.append(new_log)
                logger.info(f"Created HabitLog for habit_id={habit_id}, date={log_date}")

        self.db.commit()

        for log in updated_logs:
            self.db.refresh(log)

        logger.info(f"Processed {len(updated_logs)} habit logs for date {log_date}")

        return updated_logs

    def get_habit_logs_for_day(self, target_date: date) -> Sequence[HabitLog]:
        """Retrieve all HabitLog entries for a given date."""
        logs = self.db.execute(
            select(HabitLog).where(HabitLog.log_date == target_date)
        ).scalars().all()
        logger.info(f"Retrieved {len(logs)} habit logs for date {target_date}")
        return logs

    def get_habit_logs_by_habit(
            self,
            habit_id: str
    ) -> list[HabitLog]:
        """
        Retrieve all HabitLog entries for a specific habit, ordered by date descending.

        Args:
            habit_id: The ID of the habit.

        Returns:
            A list of HabitLog entries with the most recent log first.
        """
        logs = self.db.execute(
            select(HabitLog)
            .where(HabitLog.habit_id == habit_id)
            .order_by(HabitLog.log_date.desc())
        ).scalars().all()

        logger.info(f"Retrieved {len(logs)} habit logs for habit_id {habit_id}")
        return logs

    def create_xp_progression(
            self,
            xp_type: str,
            base: float,
            rate: float
    ) -> XPProgression:
        xp_prog = XPProgression(
            id=str(uuid4()),
            type=xp_type,
            xp=0,
            level=1,
            base=base,
            rate=rate
        )
        self.db.add(xp_prog)
        self.db.commit()
        self.db.refresh(xp_prog)
        logger.info(f"Added new XPProgression with type {xp_type}")
        return xp_prog

    def list_xp_progressions(self) -> Sequence[XPProgression]:
        return self.db.execute(select(XPProgression)).scalars().all()

    def update_xp_progression(
            self,
            xp_prog_id: str,
            new_xp: int,
            new_level: int
    ):
        xp_prog = self.db.get(XPProgression, xp_prog_id)
        if xp_prog is None:
            logger.error(f"XPProgression with id {xp_prog_id} not found.")
            return Exception("Invalid XP Progression")

        xp_prog.xp = new_xp
        xp_prog.level = new_level
        self.db.commit()
        logger.info(f"Updated XPProgression {xp_prog_id}: XP={new_xp}, Level={new_level}")

    def add_grind(
            self,
            name: str,
            skill: Skill,
            description: str,
            xp_type: str,
            base: float,
            rate: float
    ) -> Grind:
        xp_prog = self.create_xp_progression(xp_type, base, rate)

        grind = Grind(
            id=str(uuid4()),
            name=name,
            skill_id=skill.id,
            description=description,
            xp_progression_id=xp_prog.id
        )
        self.db.add(grind)
        self.db.commit()
        self.db.refresh(grind)
        logger.info(f"Added Grind {name}")

        return grind

    def list_grinds(self) -> Sequence[Grind]:
        return self.db.execute(select(Grind)).scalars().all()

    def add_task(
            self,
            title: str,
            description: str,
            xp: int,
            due_date: date,
            is_completed: bool = False,
            goal_id: str = None,
            grind_id: str = None,
            habit_id: str = None,
    ) -> Task:
        task = Task(
            id=str(uuid4()),
            title=title,
            description=description,
            goal_id=goal_id,
            grind_id=grind_id,
            habit_id=habit_id,
            xp=xp,
            due_date=due_date,
            is_completed=is_completed
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        logger.info(f"Added Task {title}")

        return task

    def mark_task_completed(self, task_id: str) -> Task:
        task = self.db.get(Task, task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found.")
        task.is_completed = True
        self.db.commit()
        logger.info(f"Task {task_id} marked as completed")
        self.db.refresh(task)
        return task

    def list_tasks(self) -> Sequence[Task]:
        return self.db.execute(select(Task)).scalars().all()

    def add_account(
            self,
            name: str,
            balance: float,
            acc_type: str
    ) -> Account:
        account = Account(
            id=str(uuid4()),
            name=name,
            balance=balance,
            type=acc_type
        )

        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)

        logger.info(f"Added Account {name}")

        return account

    def list_accounts(self) -> Sequence[Account]:
        return self.db.execute(select(Account)).scalars().all()

    def create_transaction(
            self,
            account: Account,
            amount: float,
            txn_date: date,
            description: str,
            tag_names: list[str] = None
    ) -> Transaction:
        transaction = Transaction(
            id=str(uuid4()),
            account_id=account.id,
            amount=amount,
            date=txn_date,
            description=description
        )

        self.db.add(transaction)  # Add first to ensure it's attached to session
        account.balance = account.balance - amount
        self.db.flush()  # Ensure transaction gets an ID and is tracked

        # Handle tags
        if tag_names:
            for tag_name in tag_names:
                tag = self.db.get(Tag, tag_name)
                if not tag:
                    tag = Tag(name=tag_name)
                    self.db.add(tag)
                transaction.tags.append(tag)

        self.db.commit()
        self.db.refresh(transaction)

        logger.info(f"Created transaction {transaction.id} with tags: {tag_names}")
        logger.info(f"Account balance: {account.balance}")
        return transaction

    def list_transactions(self) -> Sequence[Transaction]:
        return self.db.execute(select(Transaction)).scalars().all()

    def list_tags(self) -> Sequence[Tag]:
        return self.db.execute(select(Tag)).scalars().all()




db_ops = DbOps("prod.db")
# db_ops.create_goal(name="t1", description="t1", due_date=date(2025, 5, 30))
# print(db_ops.get_all_goals())
#

if __name__ == "__main__":

    from src.logging_config import setup_logging
    setup_logging()

    # test
    # db_ops = DbOps(db_url="sqlite:///test.db")
    db_ops.create_goal(name="t1", description="t1", due_date=date(2025, 5, 30))
    print(db_ops.get_all_goals())

    # prod
    # db_ops = DbOps()
    # db_ops.create_goal(name="t1", description="t1", due_date=date(2025, 5, 30))
    # print(db_ops.get_all_goals())



