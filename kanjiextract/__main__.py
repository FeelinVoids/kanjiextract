from fire import Fire

from . import utils

VERSION = "0.1.1"


class IgnoreFilePipeline:
    def set(self, path: str = "", move: bool = False):
        """
        Change the path of the ignore list file.

        Use --move flag to add existing kanji to it.
        """
        if len(path) == 0:
            path = None

        p = utils.set_ignored_file_path(path, move)
        if p is None:
            print("External ignore list disabled")
        else:
            print(f"Ignore list file path set to {p}")

            if not move:
                print(f"If you want to move your previously added kanji,"
                      f" execute this command with --move flag")

    def path(self):
        """ Print the external ignore list file path """
        internal_config = utils.get_internal_config()
        if internal_config.external_ignored_file_path is not None:
            print(internal_config.external_ignored_file_path)


class IgnoreListPipeline:
    def __init__(self):
        self.file = IgnoreFilePipeline()

    def add(self, kanji: str = "", file: str | None = None):
        """
        Add kanji to the ignore list.

        Use --file <path> to add all kanji from the file
        """
        if file is not None:
            with open(utils.normalize_path(file), "r", encoding="utf-8") as f:
                count = utils.add_ignored_kanji(f.read())
        else:
            count = utils.add_ignored_kanji(kanji)

        print(f"Added {count} new kanji to the ignore list")

    def remove(self, kanji: str = "", file: str | None = None):
        """
        Remove kanji from the ignore list.

        Use --file <path> to remove all kanji contained in the file
        """
        if file is not None:
            with open(utils.normalize_path(file), "r", encoding="utf-8") as f:
                count = utils.remove_ignored_kanji(f.read())
        else:
            count = utils.remove_ignored_kanji(kanji)

        print(f"Removed {count} kanji from the ignore list")

    def list(self, no_spaces: bool = False):
        """
        Print the kanji contained in the ignore list

        --no_spaces - print without spaces
        """
        j = " "
        if no_spaces:
            j = ""
        print(j.join(utils.get_ignored_kanji()))

    def set(self, kanji: str = "", file: str | None = None):
        """
        Overwrite kanji ignore list with new contents.
        Execute without parameters to clear the ignore list.

        Use --file <path> to read all kanji contained in the file
        """
        if file is not None:
            with open(utils.normalize_path(file), "r", encoding="utf-8") as f:
                old, new = utils.set_ignored_kanji(f.read())
        else:
            old, new = utils.set_ignored_kanji(kanji)

        print(f"{old} -> {new}")
        print(f"({len(old)} -> {len(new)})")


class Pipeline:
    def __init__(self):
        self.ignore = IgnoreListPipeline()

    def extract(self, filepath: str, all: bool = False):
        """
        Find all kanji in the file and make links to jisho.org

        --all - do not use ignore list
        """
        utils.extract(filepath, use_ignore_list=not all)


def main():
    Fire(Pipeline)


if __name__ == "__main__":
    main()
