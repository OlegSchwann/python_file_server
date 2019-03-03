import typing

# Логика поиска файла в файловой системе.
# {
# '/':                        '<document_root>/index.html',
# '/<file>.html':             '<document_root>/<file>.html',
# '/<directory>/':            '<document_root>/<directory>/index.html',
# '/<directory>/<file>.html': '<document_root>/<directory>/<file>.html',
# }


DEFAULT_FILE_IN_FOLDER = 'index.html'


def path_converter(url_path: str, root_directory: str) -> typing.Tuple[str, typing.Optional[str]]:
    if "/../" in url_path:  # Если пытаются подняться по иерархии файлов:
        raise PermissionError

    try:
        url_path, get_params = url_path.split('?')
    except ValueError:
        get_params = None

    if url_path[-1] == "/":
        url_path += DEFAULT_FILE_IN_FOLDER

    url_path = root_directory + url_path
    return url_path, get_params
