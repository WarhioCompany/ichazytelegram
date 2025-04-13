from db_data.db_session import session_scope, global_init
from db_data.models import Base, User, Promocode
import sqlalchemy
from xlsxwriter.workbook import Workbook
from io import BytesIO


def promo_worksheet():
    # promocode_name username promocode_contact
    data = []
    with session_scope() as session:
        promocodes = session.query(Promocode).all()
        for promocode in promocodes:
            for user in promocode.users_used:
                data.append({
                    'promocode_name': promocode.promo,
                    'username': user.name,
                    'contact': promocode.telegram_contact
                })
    return data


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


def worksheet_from_dict(workbook, data, worksheet_name):
    print(data)
    worksheet = workbook.add_worksheet(worksheet_name)
    if not data:
        return

    worksheet.write_row(0, 0, list(data[0].keys()))
    for i, row in enumerate(data):
        worksheet.write_row(i + 1, 0, list(row.values()))


def add_db_tables(workbook):
    data = table_to_dict()
    for table in data:
        worksheet_from_dict(workbook, data[table], table)


def add_additional_tables(workbook):
    data = {'promocodes_usage': promo_worksheet()}
    for table in data:
        worksheet_from_dict(workbook, data[table], table)

def convert_to_xlsx():
    output = BytesIO()

    output.name = 'database.xlsx'
    workbook = Workbook(output)

    add_db_tables(workbook)
    add_additional_tables(workbook)

    workbook.close()
    output.seek(0)
    return output
