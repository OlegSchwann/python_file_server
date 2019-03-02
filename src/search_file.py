# Логика поиска файла в файловой системе.
# {
# '/':                        '<document_root>/index.html',
# '/<file>.html':             '<document_root>/<file>.html',
# '/<directory>/':            '<document_root>/<directory>/index.html',
# '/<directory>/<file>.html': '<document_root>/<directory>/<file>.html',
# }


class ExceptionForbidden:
    pass


DEFAULT_FILE_IN_FOLDER = 'index.html'


def path_converter(url_path: str, root_directory: str) -> str:
    if "/../" in url_path:  # если пытаються подняться по иерархии файлов:
        raise ExceptionForbidden

    if url_path[-1] == "/":
        url_path += DEFAULT_FILE_IN_FOLDER

    url_path = root_directory + url_path
    return url_path
