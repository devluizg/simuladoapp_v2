from django.db import migrations, connection

def check_column_exists(table_name, column_name):
    """Verifica se uma coluna existe na tabela"""
    with connection.cursor() as cursor:
        cursor.execute(f"SHOW COLUMNS FROM {table_name} LIKE '{column_name}';")
        return cursor.fetchone() is not None

def check_table_exists(table_name):
    """Verifica se uma tabela existe"""
    with connection.cursor() as cursor:
        cursor.execute(f"SHOW TABLES LIKE '{table_name}';")
        return cursor.fetchone() is not None

class Migration(migrations.Migration):

    dependencies = [
        ('questions', '0013_remove_questaoglobalsimulado_questao_global_and_more'),
    ]

    operations = [
        # Remover colunas antigas se existirem
        migrations.RunSQL(
            """
            SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='';
            SET @column_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                                WHERE TABLE_SCHEMA = DATABASE()
                                AND TABLE_NAME = 'questions_detalhesresposta'
                                AND COLUMN_NAME = 'questao_global_id');
            SET @sql = IF(@column_exists > 0,
                         'ALTER TABLE questions_detalhesresposta DROP COLUMN questao_global_id;',
                         'SELECT "Column questao_global_id does not exist" AS message;');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;
            SET SQL_MODE=@OLD_SQL_MODE;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),

        migrations.RunSQL(
            """
            SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='';
            SET @column_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                                WHERE TABLE_SCHEMA = DATABASE()
                                AND TABLE_NAME = 'questions_simulado'
                                AND COLUMN_NAME = 'questoes_globais');
            SET @sql = IF(@column_exists > 0,
                         'ALTER TABLE questions_simulado DROP COLUMN questoes_globais;',
                         'SELECT "Column questoes_globais does not exist" AS message;');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;
            SET SQL_MODE=@OLD_SQL_MODE;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),

        migrations.RunSQL(
            """
            SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='';
            SET @column_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                                WHERE TABLE_SCHEMA = DATABASE()
                                AND TABLE_NAME = 'questions_questao'
                                AND COLUMN_NAME = 'questao_global_origem_id');
            SET @sql = IF(@column_exists > 0,
                         'ALTER TABLE questions_questao DROP COLUMN questao_global_origem_id;',
                         'SELECT "Column questao_global_origem_id does not exist" AS message;');
            PREPARE stmt FROM @sql;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;
            SET SQL_MODE=@OLD_SQL_MODE;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),

        # Remover tabelas antigas se existirem
        migrations.RunSQL(
            "DROP TABLE IF EXISTS questions_questaoglobalsimulado;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            "DROP TABLE IF EXISTS questions_questaoglobal;",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]