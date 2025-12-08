def download_photo(bot, message): # download sended photo in the best quality
    file_info = bot.get_file(message.photo[-1].file_id)
    return download(bot, file_info)


def download_video(bot, message): # download sended video
    file_info = bot.get_file(message.video.file_id)
    return download(bot, file_info)


def download(bot, file_info):
    return bot.download_file(file_info.file_path)