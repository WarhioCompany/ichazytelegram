def get_element_by_id(session, model, el_id, *criterion):
    return session.query(model).filter(*criterion).offset(el_id).limit(1).first()


def get_table_count(session, model):
    return session.query(model).count()


def get_empty_image():
    return open('data/pics/no_image.jpg', 'rb').read()