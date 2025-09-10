from aiogram import types
from app.config import YDB_DATABASE, YDB_ENDPOINT
import ydb

tables_created = False

async def ensure_tables_created():
    global tables_created
    if not tables_created:
        await create_tables()
        tables_created = True

async def create_tables():
    create_quiz_state = """
        CREATE TABLE IF NOT EXISTS `quiz_state` (
            `user_id` Uint64,
            `question_index` Uint64,
            `score` Uint64,
            PRIMARY KEY (`user_id`)
        )
    """
    
    create_leaderboard = """
        CREATE TABLE IF NOT EXISTS `leaderboard` (
            `user_id` Uint64,
            `username` Utf8,
            `score` Uint64,
            PRIMARY KEY (`user_id`)
        )
    """
    
    execute_update_query(pool, create_quiz_state)
    execute_update_query(pool, create_leaderboard)    

async def update_quiz_index(user_id, index):
    set_quiz_state = f"""
        DECLARE $user_id AS Uint64;
        DECLARE $question_index AS Uint64;

        UPSERT INTO `quiz_state` (`user_id`, `question_index`)
        VALUES ($user_id, $question_index);
    """

    execute_update_query(
        pool,
        set_quiz_state,
        user_id=user_id,
        question_index=index,
    )    

async def get_quiz_index(user_id):
    get_user_index = f"""
        DECLARE $user_id AS Uint64;

        SELECT question_index
        FROM `quiz_state`
        WHERE user_id == $user_id;
    """
    results = execute_select_query(pool, get_user_index, user_id=user_id)

    if len(results) == 0:
        return 0
    if results[0]["question_index"] is None:
        return 0
    return results[0]["question_index"]        
            
async def get_user_score(user_id):
    get_user_score_query = """
        DECLARE $user_id AS Uint64;

        SELECT score
        FROM `quiz_state`
        WHERE user_id == $user_id;
    """
    
    results = execute_select_query(pool, get_user_score_query, user_id=user_id)

    if len(results) == 0:
        return 0
    if results[0]["score"] is None:
        return 0
    return results[0]["score"]        

async def update_user_score(user_id, score, username=None):
    update_score_query = """
        DECLARE $user_id AS Uint64;
        DECLARE $score AS Uint64;

        UPSERT INTO `quiz_state` (`user_id`, `score`)
        VALUES ($user_id, $score);
    """
    
    execute_update_query(
        pool,
        update_score_query,
        user_id=user_id,
        score=score,
    )           
            
async def update_leaderboard(user_id, username, score):
    get_current_score_query = """
        DECLARE $user_id AS Uint64;

        SELECT score
        FROM `leaderboard`
        WHERE user_id = $user_id;
    """
    
    current_score_result = execute_select_query(
        pool, 
        get_current_score_query, 
        user_id=user_id
    )

    if not current_score_result or score > current_score_result[0].get('score', 0):
        update_leaderboard_query = """
            DECLARE $user_id AS Uint64;
            DECLARE $username AS Utf8;
            DECLARE $score AS Uint64;

            UPSERT INTO `leaderboard` (`user_id`, `username`, `score`)
            VALUES ($user_id, $username, $score);
        """
        
        execute_update_query(
            pool,
            update_leaderboard_query,
            user_id=user_id,
            username=username,
            score=score,
        )  

async def show_leaderboard(message: types.Message):
    get_leaderboard_query = """
        SELECT username, score
        FROM `leaderboard`
        ORDER BY score DESC
        LIMIT 10;
    """
    
    results = execute_select_query(pool, get_leaderboard_query)
    
    leaderboard_message = "🏆 Leaderboard (Top 10):\n\n"
    if not results:
        leaderboard_message += "No records yet. Be the first!"
    else:
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        for i, row in enumerate(results):
            if i < len(medals):
                medal = medals[i]
            else:
                medal = f"{i+1}."

            username = row.get("username", "Unknown")
            score = row.get("score", 0)
            leaderboard_message += f"{medal} {username}: {score} points\n"    

    await message.answer(leaderboard_message)

async def reset_user_score(user_id):
    reset_score_query = """
        DECLARE $user_id AS Uint64;

        UPSERT INTO `quiz_state` (`user_id`, `score`)
        VALUES ($user_id, 0);
    """

    execute_update_query(
        pool,
        reset_score_query,
        user_id=user_id
    )    

def get_ydb_pool(ydb_endpoint, ydb_database, timeout=30):
    ydb_driver_config = ydb.DriverConfig(
        ydb_endpoint,
        ydb_database,
        credentials=ydb.credentials_from_env_variables(),
        root_certificates=ydb.load_ydb_root_certificate(),
    )

    ydb_driver = ydb.Driver(ydb_driver_config)
    ydb_driver.wait(fail_fast=True, timeout=timeout)

    return ydb.SessionPool(ydb_driver)

def _format_kwargs(kwargs):
    return {"${}".format(key): value for key, value in kwargs.items()}

def execute_update_query(pool, query, **kwargs):
    def callee(session):
        prepared_query = session.prepare(query)

        session.transaction(ydb.SerializableReadWrite()).execute(
            prepared_query, _format_kwargs(kwargs), commit_tx=True
        )
    return pool.retry_operation_sync(callee)


def execute_select_query(pool, query, **kwargs):
    def callee(session):
        prepared_query = session.prepare(query)
        result_sets = session.transaction(ydb.SerializableReadWrite()).execute(
            prepared_query, _format_kwargs(kwargs), commit_tx=True
        )
        return result_sets[0].rows

    return pool.retry_operation_sync(callee)

pool = get_ydb_pool(YDB_ENDPOINT, YDB_DATABASE)