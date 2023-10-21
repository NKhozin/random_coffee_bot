import psycopg2
import sqlalchemy.exc
import pandas as pd
import random
import configparser

config_obj = configparser.ConfigParser()
config_obj.read("C:\\Users\\nkhozin\\Downloads\\jupyter_notebooks\\tula_hack\\configfile.ini")

dbparam = config_obj["postgresql"]

user = dbparam["user"]
password = dbparam["password"]
host = dbparam["host"]
dbase = dbparam["db"]

def get_engine():
    conn = psycopg2.connect(user="postgres",password=password,host=host,database=dbase)
    engine = sqlalchemy.create_engine(f'postgresql://{user}:{password}@{host}/{dbase}') #, encoding='utf8'
    return conn, engine

def drop_table(table_name):
    """Функция удаления таблицы по имени из БД"""
    conn, engine = get_engine()
    cur = conn.cursor()
    cur.execute(f"DROP TABLE IF EXISTS {table_name}")
    conn.commit()
    conn.close()
    
def create_table_members():
    """Создание таблицы с пользователями"""
    conn, engine = get_engine()
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS members(member_id INTEGER, first_name TEXT, username TEXT)")
    conn.commit()
    conn.close()
    
def create_table_members_free_time():
    """Создание таблицы с пользователями и их удобным временем для встречи"""
    conn, engine = get_engine()
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS members_free_time(member_id INTEGER, free_time TIMESTAMP)")
    conn.commit()
    conn.close()

def create_table_pairs():
    """Создание таблицы с парами пользователей"""
    conn, engine = get_engine()
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS pairs(pair_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, member_id_1 INTEGER, member_id_2 INTEGER, happened BOOLEAN)")
    conn.commit()
    conn.close()
    
def create_table_rooms():
    """Создание таблицы с комнатами и парами, которые должны там встретиться"""
    conn, engine = get_engine()
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS rooms(room_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, room_number INTEGER, time_start TIMESTAMP, pair_id INTEGER)")
    conn.commit()
    conn.close()
    
def change_meeting_status(pair_id, member_id_1, member_id_2):
    """Изменение статуса комнаты. Происходит только по вызову этой функции, без доп условий"""
    conn, engine = get_engine()
    cur = conn.cursor()
    query = f"""
        UPDATE pairs 
        SET happened = true
        WHERE pair_id = {pair_id}
    """
    cur.execute(query)
    conn.commit()
    conn.close()
    return f'Встреча пары {pair_id} между ({get_first_name(member_id_1)}, {get_first_name(member_id_2)}) успешно прошла!'

def insert_pairs(member_id_1, member_id_2):
    """Добавление пары в БД"""
    try:
        conn, engine = get_engine()
        cursor = conn.cursor()
        query = f"""
            INSERT INTO 
            pairs(member_id_1, member_id_2, happened)
            VALUES
            ({member_id_1},{member_id_2},False)
        """
        cursor.execute(query)
        conn.commit()

        return print("Record inserted successfully into table")
    except (Exception,psycopg2.Error)as error:
        if(conn):
            str_error = f"""Failed to insert record into mobile table! Error:{error}"""
            return print(str_error)
    finally:
        if(conn):
            cursor.close()
            conn.close()
            return print("PostgreSQL connection is closed")

def insert_members(member_id, first_name, username):
    """Добавление пользователя в БД"""
    try:
        conn, engine = get_engine()
        cursor = conn.cursor()
        query = f"""
            INSERT INTO 
            members(member_id, first_name, username)
            VALUES
            ({member_id},'{first_name}','{username}')
        """
        cursor.execute(query)
        conn.commit()

        return print("Record inserted successfully into table")
    except (Exception,psycopg2.Error)as error:
        if(conn):
            str_error = f"""Failed to insert record into mobile table! Error:{error}"""
            return print(str_error)
    finally:
        if(conn):
            cursor.close()
            conn.close()
            return print("PostgreSQL connection is closed")
        
def insert_members_free_time(member_id, free_time):
    """Добавление пользователя и его удобное время для встречи БД"""
    try:
        conn, engine = get_engine()
        cursor = conn.cursor()
        query = f"""
            INSERT INTO 
            members_free_time(member_id, free_time)
            VALUES
            ({member_id},'{free_time}')
        """
        cursor.execute(query)
        conn.commit()

        return print("Record inserted successfully into table")
    except (Exception,psycopg2.Error)as error:
        if(conn):
            str_error = f"""Failed to insert record into mobile table! Error:{error}"""
            return print(str_error)
    finally:
        if(conn):
            cursor.close()
            conn.close()
            return print("PostgreSQL connection is closed")

def delete_members(member_id):
    """Удаление пользователя из БД"""
    try:
        conn, engine = get_engine()
        cursor = conn.cursor()
        query = f"""
            DELETE FROM members
            WHERE member_id={member_id}
        """
        cursor.execute(query)
        conn.commit()

        return print("Record inserted successfully into table")
    except (Exception,psycopg2.Error)as error:
        if(conn):
            str_error = f"""Failed to insert record into mobile table! Error:{error}"""
            return print(str_error)
    finally:
        if(conn):
            cursor.close()
            conn.close()
            return print("PostgreSQL connection is closed")
        
def insert_room(room_number, time_start, pair_id, member_id_1, member_id_2):
    """Добавление комнат и пользователей, которые должны в ней встретиться в БД"""
    try:
        conn, engine = get_engine()
        cursor = conn.cursor()
        query = f"""
            INSERT INTO 
            rooms(room_number, time_start, pair_id)
            VALUES
            ({room_number},'{time_start}',{pair_id})
        """
        cursor.execute(query)
        conn.commit()

        text = f"Комната {room_number} успешно забронирована на {time_start} для встречи пары {pair_id} - ({get_first_name(member_id_1)}, {get_first_name(member_id_2)})"
        return text
    except (Exception,psycopg2.Error) as error:
        if(conn):
            str_error = f"""Failed to insert record into mobile table! Error:{error}"""
            return print(str_error)
    finally:
        if(conn):
            cursor.close()
            conn.close()
            print("PostgreSQL connection is closed")
            return text
    
def get_last_pair_id():
    """Получение pair_id по последней добавленной паре. pair_id формируется автоматически в таблице при добавлении"""
    conn, engine = get_engine()
    query = f"""
        select pair_id
        from pairs
        order by pair_id desc
        limit 1
    """
    data = pd.read_sql_query(query, engine)
    return data.pair_id.to_list()[0]
    
def choose_free_room(time):
    """Проверка на наличие свободных комнат в заданное время. Выбор случайной свободной комнаты при наличии"""
    conn, engine = get_engine()
    query = f"""
         select room_number
         from rooms
         where time_start='{time}'
    """
    data = pd.read_sql_query(query, engine)
    
    #Этим списком формируется количество свободных комнат и их номера.
    #all_room_numbers = [i for i in range(1,6)]
    all_room_numbers = [i for i in range(1,6)]

    if data.empty:
        return random.sample(all_room_numbers, 1)[0]
    else:
        book_room = data.room_number.to_list()
        free_rooms = list(set(all_room_numbers)-set(book_room))
        if not free_rooms:
            return print('Свободных комнат нет!')
        else:
            return random.sample(free_rooms, 1)[0]
    
def check_if_all_meetings_happened(iteration):
    """Проверка на то, что все встречи прошли"""
    conn, engine = get_engine()
    query = f"""
    select count(*) as cnt
    from pairs
    where iteration={iteration}
    and happened is false
    """
    
    data = pd.read_sql_query(query, engine)
    cnt = data.cnt.to_list()[0]
    if cnt>0:
        return False
    else:
        return True

def get_free_time_and_pairs():
    """Функция получения из БД пар участников, у которых удобное время для встречь пересекается, при этом встречи не было или она не забронирована на будущее"""
    conn, engine = get_engine()
    query = """
    with members_free_time as 
    (
        select distinct member_id, free_time
        from members_free_time),
    pairs as (
        select (member_id_1, member_id_2) as pairs_1, (member_id_2, member_id_1) as pairs_2
        from pairs
        )
    select *
    from
        (select *, (member_id_1, member_id_2) as our_pairs
        from
            (select m1.member_id as member_id_1, m1.free_time as free_time
            ,case when m1.member_id<m2.member_id then m1.member_id else m2.member_id end as member_id_2
            from members_free_time m1
            left join members_free_time m2 on m1.free_time=m2.free_time and m1.member_id!=m2.member_id
            where m2.member_id is not null)
        where member_id_1!=member_id_2)
    where our_pairs not in (select pairs_1 from pairs)
    and our_pairs not in (select pairs_2 from pairs)
    order by free_time
    """

    data = pd.read_sql_query(query, engine)
    return data

def was_a_meeting(member_id_1, member_id_2):
    """Проверка была ли встреча между member_id_1 и member_id_2"""
    conn, engine = get_engine()
    query = f"""
    select count(*) as cnt
    from pairs
    where ((member_id_1={member_id_1} and member_id_2={member_id_2}) or (member_id_2={member_id_1} and member_id_1={member_id_2}))
    and happened is true
    """
    data = pd.read_sql_query(query, engine)
    cnt = data.cnt.to_list()[0]
    if cnt>0:
        return True
    else:
        return False
    
def will_by_a_meeting(member_id_1, member_id_2):
    """Проверка будет ли встреча между member_id_1 и member_id_2"""
    conn, engine = get_engine()
    query = f"""
    select count(*) as cnt
    from pairs p
    left join rooms r on p.pair_id=r.pair_id
    where (member_id_1 in ({member_id_1},{member_id_2}) or member_id_2 in ({member_id_1},{member_id_2}))
    and happened is false
    and time_start > NOW()
    """
    data = pd.read_sql_query(query, engine)
    cnt = data.cnt.to_list()[0]
    if cnt>0:
        return True
    else:
        return False

def get_first_name(member_id):
    """Получение имени пользователя по его member_id из БД"""
    conn, engine = get_engine()
    query = f"""
    select first_name
    from members
    where member_id={member_id}
    """
    data = pd.read_sql_query(query, engine)
    return data.first_name.to_list()[0]

def get_pairs_without_rooms():
    """Функция получения информации по тем парам, которые создались, но по которым не создалась комната по причине того, что они все заняты"""
    conn, engine = get_engine()
    query = """
    select *
    from pairs p
    left join rooms r on p.pair_id=r.pair_id
    where happened is false
    and r.pair_id is null
    """
    data = pd.read_sql_query(query, engine)
    return data

def get_count_members():
    """Функция получения количества участников в чате"""
    conn, engine = get_engine()
    query = """
    select count(distinct member_id) as cnt
    from members
    """
    data = pd.read_sql_query(query, engine)
    return data.cnt.to_list()[0]

def get_count_completed_and_booked(): 
    """Функция получения количества прошедших и забронированных встреч"""
    conn, engine = get_engine()
    query = """
    select count(distinct pair_id) as cnt
    from rooms
    """
    data = pd.read_sql_query(query, engine)
    return data.cnt.to_list()[0]

def С(n, k):
    """Число сочетаний из n по k. Для расчета максимального количества пар участников"""
    if 0 <= k <= n:
        nn = 1
        kk = 1
        for t in range(1, min(k, n - k) + 1):
            nn *= n
            kk *= t
            n -= 1
        return nn // kk
    else:
        return 0

def if_all_meets_completed_or_booked():
    """Проверка, что все возможные встречи забронированы или прошли"""
    n = get_count_members()
    return С(n, 2)==get_count_completed_and_booked()

def change_meeting_status_by_time():
    """Изменение статуса комнаты. Происходит, если время встречи+30 минут уже прошло"""
    conn, engine = get_engine()
    cur = conn.cursor()
    query = f"""
    with meet_hep as  
    (   select p.pair_id
        from pairs p
        join rooms r on p.pair_id=r.pair_id
        where time_start+ interval '30 minute'>NOW())
    UPDATE pairs
    SET happened=true
    where pair_id in (select pair_id from meet_hep)
    """
    cur.execute(query)
    conn.commit()
    conn.close()