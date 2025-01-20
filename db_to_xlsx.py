from db_data.db_session import session_scope, global_init
from db_data.models import Base, User
import sqlalchemy
from xlsxwriter.workbook import Workbook
from io import BytesIO


def table_to_dict():
    data = {}
    with session_scope() as session:
        metadata = sqlalchemy.MetaData()
        metadata.reflect(session.get_bind())

        for table_name in list(Base.metadata.tables.keys()):
            data[table_name] = []
            table = metadata.tables[table_name]
            for row in session.query(table).all():
                row_data = dict()
                keys = table.columns.keys()
                for key in keys:
                    if key not in ['data', 'image', 'video']:
                        row_data[key] = getattr(row, key)
                data[table_name].append(row_data)

    return data


def convert_to_xlsx():
    data = table_to_dict()
    output = BytesIO()

    output.name = 'database.xlsx'
    workbook = Workbook(output)
    for table in data:
        worksheet = workbook.add_worksheet(table)
        if data[table]:
            worksheet.write_row(0, 0, list(data[table][0].keys()))
            for i, row in enumerate(data[table]):
                worksheet.write_row(i + 1, 0, list(row.values()))
    workbook.close()
    output.seek(0)
    return output
