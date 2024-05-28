"""Test Cassandra prompt template."""
import os
from typing import Iterable, Tuple

import cassio
import pytest
from cassandra.cluster import Cluster, Session

from langchain_community.prompts import CassandraReaderPromptTemplate

KEYSPACE = "reader_test_x"
P_TABLE_NAME = "people_x"
C_TABLE_NAME = "nicknames_x"


@pytest.fixture(scope="module")
def extractor_tables() -> Iterable[Tuple[Session, str, str, str]]:
    # get db connection
    if "CASSANDRA_CONTACT_POINTS" in os.environ:
        contact_points = os.environ["CASSANDRA_CONTACT_POINTS"].split(",")
        cluster = Cluster(contact_points)
    else:
        cluster = Cluster()
    #
    session = cluster.connect()
    # prepare DB
    session.execute(
        (
            f"CREATE KEYSPACE IF NOT EXISTS {KEYSPACE} "
            f"WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 1}}"
        )
    )
    session.execute(f"DROP TABLE IF EXISTS {KEYSPACE}.{C_TABLE_NAME};")
    session.execute(f"DROP TABLE IF EXISTS {KEYSPACE}.{P_TABLE_NAME};")
    session.execute(
        f"CREATE TABLE IF NOT EXISTS {KEYSPACE}.{P_TABLE_NAME} (city text, name text, age int, PRIMARY KEY (city, name)) WITH CLUSTERING ORDER BY (name ASC);"  # noqa: E501
    )
    session.execute(
        f"INSERT INTO {KEYSPACE}.{P_TABLE_NAME} (city, name, age) VALUES ('milan', 'alba', 11);"  # noqa: E501
    )
    session.execute(
        f"CREATE TABLE IF NOT EXISTS {KEYSPACE}.{C_TABLE_NAME} (city text PRIMARY KEY, nickname text);"  # noqa: E501
    )
    session.execute(
        f"INSERT INTO {KEYSPACE}.{C_TABLE_NAME} (city, nickname) VALUES ('milan', 'Taaac');"  # noqa: E501
    )

    yield (session, KEYSPACE, P_TABLE_NAME, C_TABLE_NAME)

    session.execute(f"DROP TABLE IF EXISTS {KEYSPACE}.{C_TABLE_NAME};")
    session.execute(f"DROP TABLE IF EXISTS {KEYSPACE}.{P_TABLE_NAME};")


@pytest.mark.usefixtures("extractor_tables")
def test_cassandra_reader_prompt_template(
    extractor_tables: Tuple[Session, str, str, str],
) -> None:
    session, keyspace, p_table, c_table = extractor_tables
    #
    prompt_template_string = (
        "r_age={r_age} r_age2={r_age2} r_name={r_name} r_nickname={r_nickname} "
        "r_nickname2={r_nickname2} r_nickname3={r_nickname3} r_city={r_city} "
        "external={external}"
    )
    f_mapper = {
        "r_age": (p_table, "age"),
        "r_age2": (p_table, "age"),
        "r_name": (p_table, "name"),
        "r_nickname": (c_table, "nickname"),
        "r_nickname2": (c_table, "nickname"),
        "r_nickname3": (c_table, lambda row: row["nickname"].upper()),
        "r_city": (c_table, "city"),
    }
    prompt_template = CassandraReaderPromptTemplate(
        session=session,
        keyspace=keyspace,
        template=prompt_template_string,
        field_mapper=f_mapper,
        admit_nulls=False,
    )
    result = prompt_template.format(city="milan", name="alba", external="external")
    expected = (
        "r_age=11 r_age2=11 r_name=alba r_nickname=Taaac "
        "r_nickname2=Taaac r_nickname3=TAAAC r_city=milan "
        "external=external"
    )
    assert result == expected


@pytest.mark.usefixtures("extractor_tables")
def test_cassandra_reader_prompt_template_admitnulls(
    extractor_tables: Tuple[Session, str, str, str],
) -> None:
    session, keyspace, p_table, c_table = extractor_tables
    #
    prompt_template_string = "r_age_t={r_age_t} r_age_t_d={r_age_t_d} r_age={r_age}"
    f_mapper = {
        "r_age_t": (p_table, "age", True),
        "r_age_t_d": (p_table, "age", True, 999),
        "r_age": (p_table, "age"),
    }
    prompt_template1 = CassandraReaderPromptTemplate(
        session=session,
        keyspace=keyspace,
        template=prompt_template_string,
        field_mapper=f_mapper,
        admit_nulls=False,
    )
    #
    result1 = prompt_template1.format(city="milan", name="alba")
    assert result1 == "r_age_t=11 r_age_t_d=11 r_age=11"

    with pytest.raises(ValueError):
        _ = prompt_template1.format(city="milan", name="albax")

    prompt_template2 = CassandraReaderPromptTemplate(
        session=session,
        keyspace=keyspace,
        template=prompt_template_string,
        field_mapper=f_mapper,
        admit_nulls=True,
    )
    result2 = prompt_template2.format(city="milanx", name="albax")
    assert result2 == "r_age_t=None r_age_t_d=999 r_age=None"


@pytest.mark.usefixtures("extractor_tables")
def test_cassandra_reader_prompt_template_cassioinit(
    extractor_tables: Tuple[Session, str, str, str],
) -> None:
    session, keyspace, p_table, _ = extractor_tables
    cassio.init(session=session, keyspace=keyspace)
    #
    prompt_template_string = "r_age={r_age}"
    f_mapper = {"r_age": (p_table, "age")}
    prompt_template = CassandraReaderPromptTemplate(
        template=prompt_template_string,
        field_mapper=f_mapper,
    )
    result = prompt_template.format(city="milan", name="alba")
    expected = "r_age=11"
    assert result == expected
