from db_data.db_session import session_scope
import logging

logger = logging.getLogger(__name__)


class DBManager:
    def __init__(self):
        pass

    def remove_element(self, model, element_id):
        with session_scope() as session:
            element = session.query(model).filter(model.id == element_id)
            if len(element.all()) == 0:
                return False
            logger.info(f'ADMIN DB_MANAGER {model.__name__} with id {element_id} is deleted')
            element.delete()
            session.commit()
            return True