from typing import Optional
import datetime
import decimal

from sqlalchemy import BigInteger, Boolean, CheckConstraint, Column, Date, DateTime, Double, Enum, ForeignKeyConstraint, Identity, Integer, Numeric, PrimaryKeyConstraint, String, Table, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import OID, TIMESTAMP
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass


t_pg_stat_statements = Table(
    'pg_stat_statements', Base.metadata,
    Column('userid', OID),
    Column('dbid', OID),
    Column('toplevel', Boolean),
    Column('queryid', BigInteger),
    Column('query', Text),
    Column('plans', BigInteger),
    Column('total_plan_time', Double(53)),
    Column('min_plan_time', Double(53)),
    Column('max_plan_time', Double(53)),
    Column('mean_plan_time', Double(53)),
    Column('stddev_plan_time', Double(53)),
    Column('calls', BigInteger),
    Column('total_exec_time', Double(53)),
    Column('min_exec_time', Double(53)),
    Column('max_exec_time', Double(53)),
    Column('mean_exec_time', Double(53)),
    Column('stddev_exec_time', Double(53)),
    Column('rows', BigInteger),
    Column('shared_blks_hit', BigInteger),
    Column('shared_blks_read', BigInteger),
    Column('shared_blks_dirtied', BigInteger),
    Column('shared_blks_written', BigInteger),
    Column('local_blks_hit', BigInteger),
    Column('local_blks_read', BigInteger),
    Column('local_blks_dirtied', BigInteger),
    Column('local_blks_written', BigInteger),
    Column('temp_blks_read', BigInteger),
    Column('temp_blks_written', BigInteger),
    Column('shared_blk_read_time', Double(53)),
    Column('shared_blk_write_time', Double(53)),
    Column('local_blk_read_time', Double(53)),
    Column('local_blk_write_time', Double(53)),
    Column('temp_blk_read_time', Double(53)),
    Column('temp_blk_write_time', Double(53)),
    Column('wal_records', BigInteger),
    Column('wal_fpi', BigInteger),
    Column('wal_bytes', Numeric),
    Column('jit_functions', BigInteger),
    Column('jit_generation_time', Double(53)),
    Column('jit_inlining_count', BigInteger),
    Column('jit_inlining_time', Double(53)),
    Column('jit_optimization_count', BigInteger),
    Column('jit_optimization_time', Double(53)),
    Column('jit_emission_count', BigInteger),
    Column('jit_emission_time', Double(53)),
    Column('jit_deform_count', BigInteger),
    Column('jit_deform_time', Double(53)),
    Column('stats_since', DateTime(True)),
    Column('minmax_stats_since', DateTime(True))
)


t_pg_stat_statements_info = Table(
    'pg_stat_statements_info', Base.metadata,
    Column('dealloc', BigInteger),
    Column('stats_reset', DateTime(True))
)


class Users(Base):
    __tablename__ = 'users'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='users_pkey'),
        UniqueConstraint('email', name='users_email_key'),
        UniqueConstraint('phone_number', name='users_phone_number_key')
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(100))
    email: Mapped[Optional[str]] = mapped_column(String(150))
    phone_number: Mapped[Optional[str]] = mapped_column(String(15))
    password_hash: Mapped[Optional[str]] = mapped_column(String(255))
    is_verified: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('true'))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('now()'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('now()'))

    auth_sessions: Mapped[list['AuthSessions']] = relationship('AuthSessions', back_populates='user')
    oauth_accounts: Mapped[list['OauthAccounts']] = relationship('OauthAccounts', back_populates='user')
    otp_verifications: Mapped[list['OtpVerifications']] = relationship('OtpVerifications', back_populates='user')
    user_profiles: Mapped['UserProfiles'] = relationship('UserProfiles', uselist=False, back_populates='user')
    wounds: Mapped[list['Wounds']] = relationship('Wounds', back_populates='user')


class AuthSessions(Base):
    __tablename__ = 'auth_sessions'
    __table_args__ = (
        ForeignKeyConstraint(['user_id'], ['users.id'], name='fkpu507182mdfutajr71rgk67l'),
        PrimaryKeyConstraint('id', name='auth_sessions_pkey')
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    access_token: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=6))
    device_info: Mapped[Optional[str]] = mapped_column(String(255))
    expires_at: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=6))
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))

    user: Mapped['Users'] = relationship('Users', back_populates='auth_sessions')


class OauthAccounts(Base):
    __tablename__ = 'oauth_accounts'
    __table_args__ = (
        ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE', name='oauth_accounts_user_id_fkey'),
        PrimaryKeyConstraint('id', name='oauth_accounts_pkey'),
        UniqueConstraint('provider', 'provider_user_id', name='ukqattdvs18omb33um7ge1tb5ex'),
        UniqueConstraint('provider', 'provider_user_id', name='oauth_accounts_provider_provider_user_id_key')
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('now()'))

    user: Mapped['Users'] = relationship('Users', back_populates='oauth_accounts')


class OtpVerifications(Base):
    __tablename__ = 'otp_verifications'
    __table_args__ = (
        ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE', name='otp_verifications_user_id_fkey'),
        PrimaryKeyConstraint('id', name='otp_verifications_pkey')
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    otp_code: Mapped[int] = mapped_column(Integer, nullable=False)
    expiry_time: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text("(now() + '00:10:00'::interval)"))
    contact_value: Mapped[Optional[str]] = mapped_column(String(150))
    is_used: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('now()'))

    user: Mapped['Users'] = relationship('Users', back_populates='otp_verifications')


class UserProfiles(Base):
    __tablename__ = 'user_profiles'
    __table_args__ = (
        ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE', name='user_profiles_user_id_fkey'),
        PrimaryKeyConstraint('id', name='user_profiles_pkey'),
        UniqueConstraint('user_id', name='user_profiles_user_id_key')
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(100))
    phone_number: Mapped[Optional[str]] = mapped_column(String(15))
    location: Mapped[Optional[str]] = mapped_column(Text)
    blood_type: Mapped[Optional[str]] = mapped_column(String(10))
    blood_pressure: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    blood_sugar: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    weight: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(6, 2))
    height: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(5, 2))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('now()'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('now()'))

    user: Mapped['Users'] = relationship('Users', back_populates='user_profiles')


class Wounds(Base):
    __tablename__ = 'wounds'
    __table_args__ = (
        ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE', name='wounds_user_id_fkey'),
        PrimaryKeyConstraint('id', name='wounds_pkey')
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    wound_type: Mapped[str] = mapped_column(Enum('surgical', 'burn', 'accident', 'other', name='wound_type'), nullable=False)
    status: Mapped[str] = mapped_column(Enum('open', 'healing', 'infected', 'closed', name='wound_status'), nullable=False, server_default=text("'open'::wound_status"))
    first_noted_at: Mapped[datetime.date] = mapped_column(Date, nullable=False, server_default=text('CURRENT_DATE'))
    location: Mapped[Optional[str]] = mapped_column(String(100))
    closed_at: Mapped[Optional[datetime.date]] = mapped_column(Date)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('now()'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('now()'))

    user: Mapped['Users'] = relationship('Users', back_populates='wounds')
    wound_history: Mapped[list['WoundHistory']] = relationship('WoundHistory', back_populates='wound')


class WoundHistory(Base):
    __tablename__ = 'wound_history'
    __table_args__ = (
        CheckConstraint('pain_level >= 1 AND pain_level <= 10', name='wound_history_pain_level_check'),
        ForeignKeyConstraint(['wound_id'], ['wounds.id'], ondelete='CASCADE', name='wound_history_wound_id_fkey'),
        PrimaryKeyConstraint('id', name='wound_history_pkey'),
        UniqueConstraint('wound_id', 'recorded_at', name='wound_history_wound_id_recorded_at_key')
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True)
    wound_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    recorded_at: Mapped[datetime.date] = mapped_column(Date, nullable=False, server_default=text('CURRENT_DATE'))
    status: Mapped[str] = mapped_column(Enum('open', 'healing', 'infected', 'closed', name='wound_status'), nullable=False, server_default=text("'open'::wound_status"))
    job_id: Mapped[Optional[str]] = mapped_column(String(64))
    wound_image_url: Mapped[Optional[str]] = mapped_column(Text)
    pain_level: Mapped[Optional[int]] = mapped_column(Integer)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('now()'))

    wound: Mapped['Wounds'] = relationship('Wounds', back_populates='wound_history')
