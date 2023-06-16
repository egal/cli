import re


class ComposeFileNamesValidator:
    environment = None
    words_regex = r"(\.[A-Za-z0-9\-]+)*?"
    file_name_regex = None

    def __init__(self, environment):
        self.environment = environment

        if self.environment != "local":
            environment_regex = rf"({self.words_regex}(\.#deploy({self.words_regex}(\.@{self.environment}({self.words_regex})?)?)?)?)?"
        else:
            environment_regex = rf"({self.words_regex}(\.@{self.environment}({self.words_regex})?)?)?"
        self.file_name_regex = rf"^docker-compose({self.words_regex}{environment_regex})?\.(yml|yaml)$"

    def validate(self, file_name):
        return re.match(self.file_name_regex, file_name)
